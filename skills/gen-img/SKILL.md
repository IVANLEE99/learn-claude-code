---
name: gen-img
description: Generate images using GPT-Image-2 API. Trigger when user says "generate image", "create image", "draw", "画图", "生成图片", "生图", "create a picture", or asks to generate/create/draw any visual content.
version: 1.0.0
---

# gen-img — GPT-Image-2 Image Generation Skill

Generate images via OpenAI-compatible GPT-Image-2 API and save locally.

## Trigger Conditions

Activate when user requests:
- Generate / create / draw an image
- "画图", "生成图片", "生图", "出图"
- Any request to produce visual content from text

## Environment Variables

The following env vars MUST be set (configured in `~/.claude/settings.json`):

| Variable | Value |
|----------|-------|
| `GEN_IMG_API_URL` | `https://sin.ioll.pp.ua` |
| `GEN_IMG_API_KEY` | `sk-orADtHAw4d1ifXPAdqKBKFdIDSZ0oqxdGqRdAP884rLUbMiZ` |

If not set in settings, read them from settings.json at runtime:

```bash
python3 -c "
import json
with open('$HOME/.claude/settings.json') as f:
    s = json.load(f)
env = s.get('env', {})
print(env.get('GEN_IMG_API_URL', 'https://sin.ioll.pp.ua'))
print(env.get('GEN_IMG_API_KEY', ''))
"
```

## Execution Steps

### Step 1: Parse User Request

Extract from the user's message:
- **prompt** (required): The image description / generation prompt
- **size** (optional): Image size, default `1024x1024`. Options: `1024x1024`, `1536x1024`, `1024x1536`, `auto`
- **quality** (optional): Image quality, default `auto`. Options: `auto`, `low`, `medium`, `high`
- **n** (optional): Number of images, default `1`
- **output_format** (optional): Format, default `png`. Options: `png`, `jpeg`, `webp`
- **output** (optional): Output file path, default auto-generated timestamp-based name

If the user only provides a prompt without specifying parameters, use defaults.

### Step 2: Generate Image

Execute the generation script:

```bash
bash ~/.claude/skills/gen-img/scripts/gen-img.sh "<PROMPT>" [OUTPUT_PATH] [SIZE] [QUALITY] [N] [FORMAT]
```

Or call the API directly with curl:

```bash
# Read API config
eval "$(python3 -c "
import json
with open('$HOME/.claude/settings.json') as f:
    s = json.load(f)
env = s.get('env', {})
url = env.get('GEN_IMG_API_URL', 'https://sin.ioll.pp.ua')
key = env.get('GEN_IMG_API_KEY', '')
print(f'API_URL=\"{url}\"')
print(f'API_KEY=\"{key}\"')
")"

curl -s "${API_URL}/v1/images/generations" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${API_KEY}" \
  -d "{
    \"model\": \"gpt-image-2\",
    \"prompt\": \"${PROMPT}\",
    \"size\": \"${SIZE:-1024x1024}\",
    \"quality\": \"${QUALITY:-auto}\",
    \"n\": ${N:-1},
    \"output_format\": \"${FORMAT:-png}\",
    \"response_format\": \"b64_json\"
  }"
```

### Step 3: Save Image

Decode the base64 response and save to file:

```python
import base64, json, sys, os
from datetime import datetime

resp = json.loads(sys.stdin.read())
if 'error' in resp:
    print(f"Error: {resp['error'].get('message', resp['error'])}", file=sys.stderr)
    sys.exit(1)

data = resp.get('data', [])
if not data:
    print("Error: No images returned", file=sys.stderr)
    sys.exit(1)

output_dir = os.path.expanduser("~/Documents/learn-claude-code/generated-images")
os.makedirs(output_dir, exist_ok=True)

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
output_path = os.path.join(output_dir, f"gen_{timestamp}.png")

b64 = data[0].get('b64_json', '')
if b64:
    with open(output_path, 'wb') as f:
        f.write(base64.b64decode(b64))
    print(f"Saved: {output_path}")
else:
    url = data[0].get('url', '')
    if url:
        print(f"URL: {url}")
    else:
        print("Error: No image data in response", file=sys.stderr)
        sys.exit(1)
```

### Step 4: Display Result

Show the generated image to the user using the Read tool on the saved file path.

Report:
- Output file path
- Image size and format used
- Any revised prompt from the API response

## API Reference

**Endpoint:** `{API_URL}/v1/images/generations`

**Request Body:**

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `model` | string | `gpt-image-2` | Model identifier |
| `prompt` | string | (required) | Image description |
| `size` | string | `1024x1024` | `1024x1024`, `1536x1024`, `1024x1536`, `auto` |
| `quality` | string | `auto` | `auto`, `low`, `medium`, `high` |
| `n` | int | `1` | Number of images (1-10) |
| `output_format` | string | `png` | `png`, `jpeg`, `webp` |
| `output_compression` | int | null | Compression level (for jpeg/webp) |
| `moderation` | string | `auto` | `auto`, `low` |
| `response_format` | string | `b64_json` | `b64_json` or `url` |

**Response:**
```json
{
  "data": [
    {
      "b64_json": "...",
      "revised_prompt": "..."
    }
  ]
}
```

## Error Handling

- **401 Unauthorized**: Check API key is correct
- **429 Rate Limited**: Wait and retry
- **Timeout**: Increase timeout or simplify prompt
- **Network error**: Check API_URL connectivity

## Notes

- Images are saved to `~/Documents/learn-claude-code/generated-images/` by default
- The API supports both `b64_json` and `url` response formats
- `gpt-image-2` is the latest OpenAI image generation model
- For reference image editing, use the `/v1/images/edits` endpoint with multipart form data
