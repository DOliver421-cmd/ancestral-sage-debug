# Creator Images for WAI Landing Page

This directory contains AI-generated images of Black creators for the landing page "Creators Like You" section.

## Image Files

| Filename | Subject | Alt Text |
|----------|---------|----------|
| `creator-1-poet.jpg` | Black poet/writer | Poet & Healer |
| `creator-2-artist.jpg` | Black visual artist | Visual Artist |
| `creator-3-healer.jpg` | Black wellness instructor | Wellness Guide |
| `creator-4-musician.jpg` | Black music producer | Music Producer |

## Generating Images

### Option 1: DALL-E 3 (Recommended - Highest Quality)
```
Use these exact prompts in ChatGPT Plus or DALL-E:

Poet:
"Portrait of a Black woman poet in her late 30s, sitting at a writing desk surrounded by candles and books, warm natural lighting from a window, expression of peaceful focus, wearing earth tones, spiritual and contemplative atmosphere, professional photography, shallow depth of field"

Artist:
"Black male artist in his 40s in a vibrant studio surrounded by colorful abstract paintings, holding a paintbrush, natural sunlight streaming in, creative energy, professional studio setting, warm color palette, confident expression, professional photography"

Healer:
"Black woman wellness instructor leading a meditation/yoga session with students visible in background, warm indoor lighting, peaceful demeanor, wearing comfortable spiritual clothing, authentic classroom setting, professional photography, community-focused atmosphere"

Musician:
"Black male music producer working at a professional recording studio, wearing headphones, hands on mixing board with colorful displays, creative focus, modern studio environment, professional photography, strong confidence, artistic energy"
```

### Option 2: Midjourney
Same prompts work well. Add `/imagine` prefix and adjust with:
- `--ar 1:1` for square format
- `--q 2` for higher quality
- `--style raw` for authentic look

### Option 3: Stable Diffusion XL
Use Hugging Face Spaces or local installation:
```bash
# Web: https://huggingface.co/spaces/stabilityai/SDXL
# Or: Download and run locally
```

## Image Specifications

- **Format**: JPG or WEBP (WEBP recommended for web performance)
- **Dimensions**: 400x400 pixels minimum (1:1 aspect ratio)
- **File Size**: < 100KB (use compression tools below)
- **Quality**: High contrast, clear faces, professional look

## Optimization

### Using ImageOptim (Mac)
1. Download from https://imageoptim.com
2. Drag images to ImageOptim window
3. Saves optimized versions in place

### Using TinyPNG (Web)
1. Go to https://tinypng.com
2. Upload images
3. Download compressed versions
4. Save to this directory

### Using FFmpeg (Command Line)
```bash
# Convert to WEBP (better compression)
ffmpeg -i creator-1-poet.jpg -c:v libwebp -q:v 80 creator-1-poet.webp

# Resize if needed
ffmpeg -i creator-1-poet.jpg -vf scale=400:400 creator-1-poet-optimized.jpg
```

## Diversity & Representation

**Requirements for all images:**
- ✅ Authentic representation of Black creators
- ✅ Diverse gender expressions
- ✅ Different ages (20s-50s range)
- ✅ Professional, dignified representation
- ✅ Warm, inviting atmosphere
- ✅ Clear faces and expressions
- ✅ No stereotypes or caricatures
- ✅ Real backgrounds (studios, classrooms, workspaces)

## Landing Page Integration

Images are referenced in `frontend/src/pages/Landing.jsx`:
- Lines 195-204 (Poet)
- Lines 206-215 (Artist)
- Lines 217-226 (Healer)
- Lines 228-237 (Musician)

Each image has an `onError` fallback to an SVG placeholder if the image doesn't exist.

## Styling Notes

Images are displayed in a 4-column grid on desktop, 2-column on tablet, 1-column on mobile:
- Border: `border border-ink/10`
- Hover effect: Scales to 105%, border changes to copper
- Aspect ratio: Square (1:1)
- Max container size: `lg:grid-cols-4`

## Testing Locally

```bash
# Start the frontend
cd frontend
npm run dev

# Visit http://localhost:3000
# Scroll to "Creators Like You" section
# Images should load or show fallback SVG
```

## Next Steps

1. Generate images using one of the tools above
2. Optimize for web using TinyPNG or ImageOptim
3. Save to this directory with exact filenames
4. Test in landing page
5. Commit: `git add frontend/public/images/creators/ && git commit -m "feat: add AI-generated creator images to landing page"`

## Maintenance

- If regenerating, keep same artistic style for consistency
- All creators should have similar lighting and professional quality
- Update this README when adding new images
- Check image loading on mobile and slow networks

---

**Note**: Images should reflect the WAI community values: diversity, dignity, community-first approach. These are real people who teach, create, and heal — treat with respect in representation.
