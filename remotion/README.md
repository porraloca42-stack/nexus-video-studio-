# NEXUS Remotion Engine (isolated proof of concept)

This project is intentionally isolated from the Streamlit/FFmpeg renderer until the render pipeline is validated.

## Install and preview
```bash
npm install
npm run studio
```

## Render the initial demo
```bash
npm run render:demo
```

## Manifest-driven composition
The `NexusFromManifest` composition accepts a JSON input with:
- project dimensions, fps and duration;
- scenes with duration, narration text and visual mode (`graphic`, `image`, `video`);
- optional local/public asset path, headline, description and accent color;
- optional narration/music audio paths;
- caption segments with start/end frame positions.

Example:
```bash
npx remotion render src/index.ts NexusFromManifest out/manifest.mp4 --props=public/sample-manifest.json --codec=h264 --pixel-format=yuv420p
```

Place local media under `public/` and reference it as `/filename.mp4` or `/filename.jpg`. Keep media assets local to the render worker for deterministic, reproducible output.

This is a technical prototype, not yet connected to the Python director or deployed Streamlit app.
