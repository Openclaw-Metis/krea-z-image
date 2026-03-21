# Krea Z Image API (quick reference)

Endpoints (auth: `Authorization: Bearer <token>`):

- **Create job**: `POST https://api.krea.ai/generate/image/z-image/z-image`
- **Poll job**: `GET https://api.krea.ai/jobs/{job_id}`

## Create job payload (JSON)
Required:
- `prompt` (string)
- `width` (number)
- `height` (number)

Optional (common):
- `batchSize` (int, 1..4, default 1)
- `seed` (string, digits)
- `imageUrl` (string, uri) - init/reference image
- `denoising_strength` (number, 0..1, default 0.6)
- `skipPromptExpansion` (bool)
- `styles` (array of `{ id: string, strength: number (-2..2) }`)
- `styleImages` (array of `{ url: string, strength: number (-2..2) }`)

## Job status values
`backlogged | queued | scheduled | processing | sampling | intermediate-complete | completed | failed | cancelled`

## Completed job result
`result.urls`: array of image URLs.

## Script CLI flags

| Flag | Default | Description |
|------|---------|-------------|
| `--prompt` | (required) | Text prompt |
| `--width` | (required) | Image width (multiple of 64) |
| `--height` | (required) | Image height (multiple of 64) |
| `--batch-size` | 1 | Number of images (1–4) |
| `--seed` | — | Numeric string for reproducibility |
| `--image-url` | — | Init/reference image URL |
| `--denoising-strength` | 0.6 | Init image influence (0=ignore prompt, 1=ignore image) |
| `--skip-prompt-expansion` | false | Disable Krea's auto prompt rewriting |
| `--styles-json` | — | JSON array: `[{id, strength}, ...]` |
| `--style-images-json` | — | JSON array: `[{url, strength}, ...]` |
| `--download` | false | Download result images locally |
| `--out-dir` | `generated` | Download directory |
| `--out-prefix` | `krea_z_image` | Filename prefix |
| `--poll-interval` | 1.5 | Seconds between status polls |
| `--timeout` | 180 | Max wait in seconds |
| `--token` | — | API token (prefer env var) |
| `--quiet` | false | Suppress progress logs |

## Common errors
- **401** unauthenticated (token missing/invalid)
- **402** out of credits
- **429** too many concurrent jobs
- **400** invalid body
- **403 + “error code: 1010”** Cloudflare block (often fixed by setting a browser-like `User-Agent`)
