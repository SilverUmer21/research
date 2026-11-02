# Original 30-second film

These two parts contain the exact original Cinder / Glacier / Vesper movie, including the powerful magenta Vesper sequence. Splitting is required by the connected uploader's request-size limit.

After downloading or cloning this branch, run from the `afterlight` folder:

```bash
python3 original_video/restore_video.py
```

On Windows, `python original_video/restore_video.py` also works. This writes `AFTERLIGHT_30s_original.mp4`, then checks its size and SHA-256. No package installation is needed.

The adjacent `AFTERLIGHT_30s.mp4` is a smaller playable encoding of the same 30-second film. The source archive and all three car models are unchanged from the selected original version.
