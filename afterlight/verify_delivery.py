"""Validate the three-car master, extract encoded frames, and package source."""
from pathlib import Path
import json, subprocess, zipfile, struct
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
movie = ROOT / 'AFTERLIGHT_30s.mp4'
info = json.loads(subprocess.check_output([
    'ffprobe', '-v', 'error', '-show_streams', '-show_format', '-of', 'json', str(movie)]))
v = next(s for s in info['streams'] if s['codec_type'] == 'video')
a = next(s for s in info['streams'] if s['codec_type'] == 'audio')
assert (v['width'], v['height'], v['avg_frame_rate'], v['nb_frames']) == (1920, 1080, '30/1', '900')
assert v['color_space'] == 'bt709' and a['channels'] == 2 and int(a['sample_rate']) == 48000
assert abs(float(info['format']['duration']) - 30) < .001
subprocess.run(['ffmpeg', '-v', 'error', '-i', str(movie), '-f', 'null', '-'], check=True)

shots = [(45, 'CINDER / FRONT'), (126, 'CINDER / VEINS'), (216, 'CINDER / BOOST'),
         (315, 'GLACIER / FRONT'), (396, 'GLACIER / VEINS'), (486, 'GLACIER / BOOST'),
         (585, 'VESPER / FRONT'), (666, 'VESPER / VEINS'), (756, 'VESPER / BOOST'),
         (855, 'THREE-CAR LINEUP')]
renders = ROOT / 'renders'
renders.mkdir(exist_ok=True)
select = '+'.join(f'eq(n,{n})' for n, _ in shots)
subprocess.run(['ffmpeg', '-y', '-hide_banner', '-loglevel', 'error', '-i', str(movie),
                '-vf', f"select='{select}'", '-fps_mode', 'vfr', str(renders / 'delivery_%02d.png')], check=True)
font_path = str(ROOT / 'fonts/BarlowCondensed-Bold.ttf')
font = ImageFont.truetype(font_path, 29)
small = ImageFont.truetype(font_path, 24)
big = ImageFont.truetype(font_path, 38)
bg, ink = '#040813', '#e4ecff'
colors = ['#ffae65', '#69f4e4', '#ff71df']

# Three columns make it easy to compare geometry and energy colors.
preview = Image.new('RGB', (1920, 1250), bg)
d = ImageDraw.Draw(preview)
for col, name in enumerate(['CINDER / 07', 'GLACIER / 08', 'VESPER / 09']):
    d.text((col * 640 + 20, 12), name, font=big, fill=colors[col])
    for row, label in enumerate(['LOW FRONT', 'FLOWING VEINS', 'TWIN BOOSTERS']):
        idx = col * 3 + row
        with Image.open(renders / f'delivery_{idx+1:02d}.png') as im:
            im.load()
            preview.paste(im.resize((640, 360), Image.Resampling.LANCZOS), (col * 640, 66 + row * 394))
        d.text((col * 640 + 20, 428 + row * 394), label, font=small, fill=ink)
preview.save(ROOT / 'AFTERLIGHT_Preview.png')

contact = Image.new('RGB', (1920, 1568), bg)
d = ImageDraw.Draw(contact)
for i, (frame, label) in enumerate(shots):
    x, y = i % 3 * 640, i // 3 * 392
    with Image.open(renders / f'delivery_{i+1:02d}.png') as im:
        contact.paste(im.resize((640, 360), Image.Resampling.LANCZOS), (x, y))
    d.text((x+12, y+362), f'{frame/30:.1f}s / {label}', font=small, fill=ink)
contact.save(renders / 'delivery_contact.png')

# Preserve the comparison artifact as a record of the three-car revision.
old = ROOT.parent / 'afterlight_showcase' / 'renders' / 'delivery_01.png'
if old.exists():
    comparison = Image.new('RGB', (1920, 598), bg)
    d = ImageDraw.Draw(comparison)
    for i, (path, label) in enumerate([
        (old, 'PREVIOUS CAR'), (renders / 'delivery_10.png', 'THREE-CAR VEIN SERIES')]):
        with Image.open(path) as im:
            comparison.paste(im.resize((960, 540), Image.Resampling.LANCZOS), (i*960, 0))
        d.text((i*960+22, 551), label, font=font, fill=ink)
    comparison.save(ROOT / 'AFTERLIGHT_Lighting_Comparison.png')

models = []
for name in ['CINDER', 'GLACIER', 'VESPER']:
    p = ROOT / 'models' / f'{name}.glb'
    b = p.read_bytes()
    magic, version, size = struct.unpack_from('<III', b)
    assert magic == 0x46546c67 and version == 2 and size == len(b)
    n, kind = struct.unpack_from('<II', b, 12)
    assert kind == 0x4e4f534a
    doc = json.loads(b[20:20+n])
    assert sum(node['name'].startswith('wheel_') for node in doc['nodes']) == 4
    assert sum(node['name'].startswith('petal_') for node in doc['nodes']) == 12
    assert any(node['name'].startswith('veins_') for node in doc['nodes'])
    assert any(m.get('alphaMode') == 'BLEND' for m in doc['materials'] if m['name'].startswith('glass'))
    assert any(m.get('extras', {}).get('flowCoordinates') for m in doc['materials'])
    models.append(str(p.relative_to(ROOT)))

files = ['README.md', 'COLOR_AND_MOTION_STUDY.md', 'THIRD_PARTY_NOTICES.txt', 'requirements.txt',
         'showcase.py', 'car_geometry.py', 'styles.py', 'veins.py', 'boosters.py', 'engine.py',
         'sound.py', 'master.py', 'export_model.py', 'verify_delivery.py', 'atlas.png',
         'AFTERLIGHT_score.wav', 'AFTERLIGHT_Preview.png'] + models
files += [str(p.relative_to(ROOT)) for directory in ['fonts', 'shaders']
          for p in sorted((ROOT/directory).glob('*')) if p.is_file()]
with zipfile.ZipFile(ROOT/'AFTERLIGHT_Source.zip', 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as z:
    for name in files:
        z.write(ROOT/name, 'AFTERLIGHT/'+name)
with zipfile.ZipFile(ROOT/'AFTERLIGHT_Source.zip') as z:
    assert z.testzip() is None
print('FLEET VERIFIED', {'duration': 30, 'frames': 900, 'resolution': '1920x1080',
    'color': 'BT.709', 'audio': '48k stereo AAC', 'cars': 3, 'shots': 10,
    'movie_bytes': movie.stat().st_size, 'source_bytes': (ROOT/'AFTERLIGHT_Source.zip').stat().st_size})
