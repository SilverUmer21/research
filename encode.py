"""Encode renders/video/final_####.png to an H.264 MP4 with Blender's built-in FFmpeg.

  blender -b --factory-startup --python encode.py -- [name.mp4]
"""
import sys
from pathlib import Path

import bpy

HERE = Path(__file__).resolve().parent
VID = HERE / 'renders/video'
args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
OUT = HERE / 'renders' / (args[0] if args else 'emotion-lanterns.mp4')

frames = sorted(VID.glob('final_*.png'))
sc = bpy.context.scene
sc.render.resolution_x, sc.render.resolution_y = 1080, 1350
sc.render.resolution_percentage = 100
sc.render.fps = 30
sc.frame_start, sc.frame_end = 1, len(frames)
ed = sc.sequence_editor_create()
strips = ed.strips if hasattr(ed, 'strips') else ed.sequences  # renamed in Blender 4.4
strip = strips.new_image('frames', str(frames[0]), 1, 1)
for p in frames[1:]:
    strip.elements.append(p.name)
strip.frame_final_duration = len(frames)
sc.view_settings.view_transform = 'Standard'
img = sc.render.image_settings
if hasattr(img, 'media_type'):  # Blender 5: choose video before the container
    img.media_type = 'VIDEO'
img.file_format = 'FFMPEG'
ff = sc.render.ffmpeg
ff.format = 'MPEG4'
ff.codec = 'H264'
ff.constant_rate_factor = 'HIGH'
ff.ffmpeg_preset = 'GOOD'
ff.audio_codec = 'NONE'
sc.render.filepath = str(OUT)
bpy.ops.render.render(animation=True)
print('WROTE', OUT, len(frames), 'frames')
