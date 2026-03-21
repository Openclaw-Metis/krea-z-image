---
name: krea-z-image
description: "Generate images using the Krea Z Image API. Use when the user asks to generate, create, or draw images via Krea — 觸發: 'Krea 生圖', '用 Krea 出圖', 'z-image', '幫我跑一張圖', '用 krea 畫', 'krea z image', '幫我用 Krea 生成圖片'. Not for editing existing images, non-Krea generation, or image analysis. Output: image URL(s) in chat + downloaded file(s) attached inline."
---

# Krea Z Image

## Quick start

```bash
python3 {baseDir}/scripts/krea_z_image.py \
  --prompt "a cat astronaut floating in space, digital art" \
  --width 576 --height 1024 \
  --download --out-dir generated
```

The script creates a job, polls until done, optionally downloads. Stdout is a single JSON: `{ job_id, status, urls, files, width, height }`.

## Auth

Never echo the Krea token back to the user.

Token resolution (in order):
1. `--token` CLI flag
2. `KREA_API_KEY` or `KREA_TOKEN` env var
3. OpenClaw config: `~/.openclaw/openclaw.json` → `skills.entries.krea-z-image.env.KREA_API_KEY`

For persistent deployments, inject the env var via systemd drop-in or equivalent. If a user pastes a token directly, recommend they rotate it afterward.

## Workflow

### 1) Build the prompt

Write a descriptive English prompt — subject, style, lighting, composition. See `references/prompt-guide.md`.

### 2) Pick size and batch

Width/height must be multiples of 64. Common presets:

| Preset | Ratio | Notes |
|--------|-------|-------|
| 576×1024 | 9:16 | portrait, fast |
| 1024×576 | 16:9 | landscape |
| 1024×1024 | 1:1 | square |
| 1152×2048 | 9:16 | portrait, high-res |

Batch: 1–4 images (default 1). More images = more credits.

### 3) Run the script

```bash
python3 {baseDir}/scripts/krea_z_image.py \
  --prompt "..." \
  --width 576 --height 1024 \
  --download --out-dir generated
```

Always pass `--download`. For all flags and advanced parameters (init image, seed, styles), see `references/z-image-api.md`.

### 4) Present the result — follow the output contract below.

## Output contract

When the script completes, always do **both**:

1. **Show the URL(s)** in your text response so the user can open them in a browser.
2. **Attach the downloaded file(s)** so the image renders inline in chat.

Attach via the `message` tool with `path=<local file>`. If attachments are not supported on the current surface, fall back to URL-only and tell the user.

Required response format:

```
Image generated successfully.
- Size: {width}x{height}
- URL: https://...
[attached: generated/krea_z_image_{job_id}_1.png]
```

Never omit the URL. Never skip attachment when local files are available.

## Error handling

If the script fails, consult `references/error-handling.md`. Common issues: expired token (401), insufficient credits (402), Cloudflare block (403/1010), rate limit (429).

## References

- `references/z-image-api.md` — API fields, all CLI flags, job statuses
- `references/prompt-guide.md` — prompt writing tips and examples
- `references/error-handling.md` — error codes, retry logic, polling behavior
