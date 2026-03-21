# Prompt Guide for Krea Z Image

## Basics

Krea works best with English prompts. Write naturally but include enough detail for the model to understand what you want.

A good prompt covers:
- **Subject**: what is in the image ("a woman reading a book", "a futuristic city skyline")
- **Style**: artistic direction ("watercolor", "photorealistic", "anime", "oil painting", "3D render")
- **Lighting/mood**: atmosphere ("golden hour", "dramatic shadows", "soft diffused light", "neon glow")
- **Composition**: framing ("close-up portrait", "wide angle", "bird's eye view", "centered")

## Prompt structure

Put the most important elements first. Krea gives more weight to earlier tokens.

Pattern: `[subject], [style], [lighting], [details], [quality modifiers]`

## Examples

**Portrait**
`a young woman with short silver hair, wearing a leather jacket, cyberpunk style, neon city background, cinematic lighting, highly detailed, 8k`

**Landscape**
`vast desert with towering red rock formations, sunset, dramatic clouds, photorealistic, wide angle lens, golden hour lighting`

**Product shot**
`a minimalist ceramic coffee mug on a wooden table, soft natural light from window, clean background, product photography, shallow depth of field`

**Illustration**
`a cat wearing a tiny astronaut helmet floating in space, surrounded by colorful nebulas, digital illustration, vibrant colors, whimsical`

**Abstract**
`flowing liquid metal in iridescent colors, abstract art, macro photography, high contrast, reflections`

## skipPromptExpansion

By default, Krea automatically expands your prompt (adds detail and quality keywords). This usually improves results.

Set `--skip-prompt-expansion` when:
- You want exact control over the prompt wording
- Your prompt is already very detailed
- Krea's expansion produces unwanted style shifts

## Using reference images (imageUrl)

When passing `--image-url`, the model blends your text prompt with the reference image.

- `--denoising-strength 0.3`: output stays close to the reference image
- `--denoising-strength 0.6` (default): balanced blend
- `--denoising-strength 0.9`: output follows the text prompt more, reference image is a loose guide

## Tips

- Avoid negative phrasing ("no trees", "without people"); the model responds better to describing what you want, not what you don't want.
- Quality modifiers like "highly detailed", "8k", "professional" can nudge results toward higher fidelity.
- If results are too generic, add specific references ("in the style of Studio Ghibli", "Moebius-inspired linework").
- For batch generation (`--batch-size 2-4`), each image will be a variation. Use `--seed` if you want reproducible starting points.
