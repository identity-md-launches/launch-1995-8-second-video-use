# Fawn dance loop

Delivered video: `artifacts/video.mp4` (`video/mp4`).

- Duration: 8.000 seconds; 192 frames at 24 fps.
- Dimensions: 1376 × 768 pixels, full-body framing and static camera.
- Video: H.264, yuv420p; MP4 with fast-start metadata.
- Audio: AAC stereo, 48 kHz, intentional silence. No music or speech was requested.
- Source: the requester-supplied PNG, bundled as `assets/reference.png`.

The sequence contains a shoulder shimmy, two alternating forward hoof gestures,
a quick axial turn, sunglasses lowered over the eyes, a nod, and a return to the
starting pose. The first and last rendered frames are pixel-identical to the
source PNG before lossy video encoding. There are no titles or additional characters.

## Limitations

The available video tool encodes frames; it does not generate video. This is a
locally rendered **2.5D image-puppet approximation**, not a fully rigged 3D character.
The supplied image's front-facing fur, face, clothing, watch, and lighting remain
the visual basis. The rear view during the fast turn is a simplified illustration;
the turn uses planar foreshortening. Hoof-points use local image deformation rather
than articulated fingers or a true change in camera perspective. The sunglasses
slide uses extracted lens textures and an approximate forehead repair. These
techniques can show flattening, texture stretching, and edge artifacts. The
character cannot remain exactly identical from unseen viewpoints with this method.

## Reproduction

From the repository root, with Python 3, Pillow, NumPy and FFmpeg available:

```sh
python3 src/render.py
ffmpeg -y -framerate 24 -i test/scratch/frames/%04d.png -i test/scratch/silence.wav -c:v libx264 -crf 18 -pix_fmt yuv420p -c:a aac -ar 48000 -movflags +faststart -t 8 artifacts/video.mp4
```

No dependencies were downloaded or installed. All visual source assets and the
rendering source are included. Intermediate frames are intentionally not delivered.
See `validation.json` for measured media properties and local checks.
