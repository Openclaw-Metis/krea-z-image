# Error Handling for Krea Z Image

## HTTP errors from the API

### 401 Unauthenticated
- Token is missing, expired, or invalid.
- Action: verify the token is set correctly. Try regenerating from the Krea dashboard.

### 402 Out of credits
- The Krea account has no remaining credits.
- Action: tell the user to top up credits at krea.ai. Do not retry.

### 400 Bad request
- Invalid payload (e.g., width/height not valid, missing required field, batch size out of range).
- Action: check that width and height are positive integers (multiples of 64 recommended), batch size is 1-4, and prompt is non-empty.

### 429 Too many concurrent jobs
- Rate limit hit. The account has too many jobs running at once.
- Action: wait 10-15 seconds, then retry once. If it fails again, tell the user to wait or cancel existing jobs.

### 403 with error code 1010
- Cloudflare is blocking the request, typically because the User-Agent looks like a bot.
- The bundled script already sets a browser-like User-Agent and falls back to curl automatically.
- If it still fails: check network/proxy settings, or try from a different IP.

## Job-level failures

### Job status: `failed`
- The generation failed server-side (could be a content filter, internal error, or invalid parameters).
- Action: simplify the prompt (remove potentially flagged content), try a different size, or retry. If repeated, the prompt may be hitting content moderation.

### Job status: `cancelled`
- The job was cancelled (by the user or system).
- Action: resubmit if desired.

### Timeout (script exits with timeout error)
- Default timeout is 180 seconds. Some high-res generations take longer.
- Action: increase timeout with `--timeout 300` (or higher). If it consistently times out, try a smaller resolution first to verify the prompt works.

## Polling behavior

The script polls `GET /jobs/{job_id}` at a configurable interval (default 1.5 seconds).

Job status progression:
`backlogged` -> `queued` -> `scheduled` -> `processing` -> `sampling` -> `intermediate-complete` -> `completed`

Any of these intermediate states is normal. The script waits until `completed`, `failed`, or `cancelled`.

You can adjust polling with:
- `--poll-interval 2.0` (seconds between checks)
- `--timeout 300` (max wait in seconds)

## Download failures

If the image URL download fails:
- The script tries urllib first, then falls back to curl.
- If both fail, the URL is still in the JSON output. You can download manually or provide the URL to the user.
- Common cause: temporary CDN issue. Wait a few seconds and retry the download.

## Retry guidance

- 401, 402: do not retry (auth/billing issue, needs user action)
- 400: do not retry without fixing the request
- 429: retry once after 10-15 seconds
- 403/1010: the script auto-retries via curl; if both fail, do not retry (network issue)
- Job `failed`: retry once with a simplified prompt or different parameters
- Timeout: retry with `--timeout 300` or smaller resolution
