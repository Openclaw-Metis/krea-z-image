#!/usr/bin/env python3
"""Generate images via Krea API Z Image (z-image).

- Creates a job: POST /generate/image/z-image/z-image
- Polls job: GET /jobs/{id}
- Optionally downloads result URLs to local files

Prints a single JSON object to stdout:
{
  "job_id": "...",
  "status": "completed",
  "urls": ["..."],
  "files": ["/abs/or/rel/path.png"],
  "width": 576,
  "height": 1024
}

Auth:
  Export KREA_API_KEY (or KREA_TOKEN) or pass --token.
  If neither is set, this script will also try to load the token from the
  local OpenClaw config (~/.openclaw/openclaw.json) under:
    skills.entries.krea-z-image.env.KREA_API_KEY

Note: Calls consume Krea credits.
"""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import subprocess
import sys
import time
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional, Tuple

API_BASE = "https://api.krea.ai"
DEFAULT_UA = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
)


def _eprint(*a: Any) -> None:
    print(*a, file=sys.stderr)


def _headers(token: str, user_agent: str) -> Dict[str, str]:
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": user_agent,
        "Accept-Language": "en-US,en;q=0.9",
    }


def _token_from_openclaw_config(skill_name: str = "krea-z-image", quiet: bool = False) -> Optional[str]:
    """Best-effort token lookup from the local OpenClaw config.

    This helps when running the script manually (outside the OpenClaw runtime)
    where skill-level env injection is not present.

    Config path:
      - OPENCLAW_CONFIG env var, else ~/.openclaw/openclaw.json

    Expected location:
      skills.entries.<skill_name>.env.KREA_API_KEY (or KREA_TOKEN)
    """

    cfg_path = os.environ.get("OPENCLAW_CONFIG") or os.path.expanduser("~/.openclaw/openclaw.json")
    try:
        with open(cfg_path, "r", encoding="utf-8") as f:
            cfg = json.load(f)
    except FileNotFoundError:
        return None
    except Exception as e:
        if not quiet:
            _eprint(f"Warning: failed to read OpenClaw config at {cfg_path}: {e}")
        return None

    try:
        env = (
            (((cfg.get("skills") or {}).get("entries") or {}).get(skill_name) or {}).get("env")
            or {}
        )
        tok = env.get("KREA_API_KEY") or env.get("KREA_TOKEN")
        return str(tok) if tok else None
    except Exception:
        return None


def _urllib_json(method: str, url: str, headers: Dict[str, str], body: Optional[dict]) -> Tuple[int, dict]:
    data = None
    if body is not None:
        data = json.dumps(body, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            if not raw:
                return resp.status, {}
            try:
                return resp.status, json.loads(raw)
            except json.JSONDecodeError:
                return resp.status, {"raw": raw}
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", errors="replace")
        try:
            j = json.loads(raw) if raw else {"error": e.reason}
        except json.JSONDecodeError:
            j = {"error": raw or str(e)}
        return e.code, j


def _curl_json(method: str, url: str, headers: Dict[str, str], body: Optional[dict]) -> Tuple[int, dict]:
    cmd = ["curl", "-sS", "-X", method]
    for k, v in headers.items():
        cmd += ["-H", f"{k}: {v}"]
    if body is not None:
        cmd += ["--data", json.dumps(body, ensure_ascii=False)]
    cmd += ["-w", "\n%{http_code}", url]

    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    out = p.stdout
    if not out:
        return 0, {"error": p.stderr.strip() or "empty response"}

    # Split last line as status code
    if "\n" not in out:
        return 0, {"error": out}
    body_txt, code_txt = out.rsplit("\n", 1)
    try:
        code = int(code_txt.strip())
    except ValueError:
        code = 0
    try:
        j = json.loads(body_txt) if body_txt else {}
    except json.JSONDecodeError:
        j = {"raw": body_txt}
    if p.returncode != 0 and "error" not in j:
        j["error"] = p.stderr.strip()
    return code, j


def http_json(method: str, path: str, token: str, user_agent: str, body: Optional[dict] = None) -> dict:
    url = f"{API_BASE}{path}"
    headers = _headers(token, user_agent)

    code, j = _urllib_json(method, url, headers, body)

    # Cloudflare 1010 commonly triggers when UA is "Python-urllib".
    # If it happens anyway, retry via curl which tends to work.
    if code in (401, 402, 400, 404, 429):
        raise RuntimeError(f"HTTP {code}: {json.dumps(j, ensure_ascii=False)}")
    if code == 403:
        raw_text = json.dumps(j, ensure_ascii=False).lower()
        if "1010" in raw_text or "access denied" in raw_text:
            code2, j2 = _curl_json(method, url, headers, body)
            if code2 in (401, 402, 400, 404, 429, 403):
                raise RuntimeError(f"HTTP {code2}: {json.dumps(j2, ensure_ascii=False)}")
            return j2
        raise RuntimeError(f"HTTP 403: {json.dumps(j, ensure_ascii=False)}")
    if code >= 400:
        raise RuntimeError(f"HTTP {code}: {json.dumps(j, ensure_ascii=False)}")
    return j


def download(url: str, out_path: pathlib.Path, user_agent: str) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(url, headers={"User-Agent": user_agent})
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            out_path.write_bytes(resp.read())
    except Exception:
        # Fallback to curl
        cmd = ["curl", "-L", "--fail", "-sS", "-H", f"User-Agent: {user_agent}", "-o", str(out_path), url]
        subprocess.run(cmd, check=True)


def main() -> int:
    ap = argparse.ArgumentParser(description="Generate images via Krea Z Image API and optionally download results.")
    ap.add_argument("--prompt", required=True, help="Text prompt")
    ap.add_argument("--width", type=int, required=True, help="Image width (recommend multiple of 64)")
    ap.add_argument("--height", type=int, required=True, help="Image height (recommend multiple of 64)")
    ap.add_argument("--batch-size", type=int, default=1, help="1-4")
    ap.add_argument("--seed", help="Numeric string seed")
    ap.add_argument("--image-url", help="Optional init image URL")
    ap.add_argument("--denoising-strength", type=float, help="0..1")
    ap.add_argument("--skip-prompt-expansion", action="store_true")
    ap.add_argument("--styles-json", help="JSON array for styles: [{id, strength}, ...]")
    ap.add_argument("--style-images-json", help="JSON array for styleImages: [{url, strength}, ...]")

    ap.add_argument("--token", help="Krea API token (prefer env KREA_API_KEY)")
    ap.add_argument("--user-agent", default=DEFAULT_UA)

    ap.add_argument("--poll-interval", type=float, default=1.5)
    ap.add_argument("--timeout", type=float, default=180)

    ap.add_argument("--download", action="store_true", help="Download completed image(s)")
    ap.add_argument("--out-dir", default="generated", help="Output directory for downloads")
    ap.add_argument("--out-prefix", default="krea_z_image", help="Filename prefix")

    ap.add_argument("--quiet", action="store_true", help="Suppress progress logs")

    args = ap.parse_args()

    # Validate inputs before network calls so errors are immediate and clear.
    if not (1 <= args.batch_size <= 4):
        raise SystemExit("--batch-size must be 1..4")

    token = args.token or os.environ.get("KREA_API_KEY") or os.environ.get("KREA_TOKEN")
    if not token:
        token = _token_from_openclaw_config(quiet=args.quiet)
        if token and not args.quiet:
            _eprint("Loaded Krea token from OpenClaw config (~/.openclaw/openclaw.json).")

    if not token:
        raise SystemExit(
            "Missing token. Provide --token, set KREA_API_KEY / KREA_TOKEN, "
            "or configure OpenClaw skill env (skills.entries.krea-z-image.env.KREA_API_KEY)."
        )

    body: Dict[str, Any] = {
        "prompt": args.prompt,
        "width": args.width,
        "height": args.height,
        "batchSize": args.batch_size,
    }
    if args.seed:
        body["seed"] = str(args.seed)
    if args.image_url:
        body["imageUrl"] = args.image_url
    if args.denoising_strength is not None:
        body["denoising_strength"] = args.denoising_strength
    if args.skip_prompt_expansion:
        body["skipPromptExpansion"] = True
    if args.styles_json:
        body["styles"] = json.loads(args.styles_json)
    if args.style_images_json:
        body["styleImages"] = json.loads(args.style_images_json)

    job = http_json("POST", "/generate/image/z-image/z-image", token, args.user_agent, body)
    job_id = job.get("job_id")
    if not job_id:
        raise SystemExit(f"No job_id in response: {json.dumps(job, ensure_ascii=False)}")

    t0 = time.time()
    last_status = job.get("status")
    if not args.quiet:
        _eprint(f"job_id={job_id} status={last_status}")

    final: dict = {}
    while True:
        if time.time() - t0 > args.timeout:
            raise SystemExit(f"Timed out after {args.timeout}s waiting for job completion (job_id={job_id}).")

        j = http_json("GET", f"/jobs/{job_id}", token, args.user_agent)
        status = j.get("status")

        if status != last_status and not args.quiet:
            _eprint(f"status={status}")
            last_status = status

        if status in ("completed", "failed", "cancelled"):
            final = j
            break

        time.sleep(args.poll_interval)

    if final.get("status") != "completed":
        raise SystemExit(json.dumps(final, ensure_ascii=False))

    urls: List[str] = (final.get("result") or {}).get("urls") or []
    out_files: List[str] = []

    if args.download and urls:
        out_dir = pathlib.Path(args.out_dir)
        for idx, u in enumerate(urls, start=1):
            # Keep extension if present
            ext = pathlib.Path(u.split("?", 1)[0]).suffix or ".png"
            out_path = out_dir / f"{args.out_prefix}_{job_id}_{idx}{ext}"
            download(u, out_path, args.user_agent)
            out_files.append(str(out_path))

    result = {
        "job_id": job_id,
        "status": "completed",
        "urls": urls,
        "files": out_files,
        "width": args.width,
        "height": args.height,
    }
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
