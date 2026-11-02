"""Mux the rendered picture and original score into a 30-second delivery master."""
from pathlib import Path
import subprocess,json
ROOT=Path(__file__).resolve().parent
info=json.loads(subprocess.check_output(['ffprobe','-v','error','-select_streams','v:0','-show_entries','stream=color_space','-of','json',str(ROOT/'AFTERLIGHT_picture.mp4')]))
# Older intermediate pictures used swscale's untagged BT.601 conversion.
# Convert those into the same explicit BT.709 delivery space as new renders.
video=['-c:v','copy'] if info['streams'][0].get('color_space')=='bt709' else [
    '-vf','scale=in_color_matrix=bt601:out_color_matrix=bt709','-c:v','libx264','-crf','17','-preset','slow','-pix_fmt','yuv420p',
    '-color_primaries','bt709','-color_trc','bt709','-colorspace','bt709']
subprocess.run([
    'ffmpeg','-y','-hide_banner','-loglevel','error',
    '-i',str(ROOT/'AFTERLIGHT_picture.mp4'),'-i',str(ROOT/'AFTERLIGHT_score.wav'),
    '-map','0:v:0','-map','1:a:0',*video,
    '-af','loudnorm=I=-16:TP=-1:LRA=10:measured_I=-22.07:measured_TP=-6.31:measured_LRA=9.20:measured_thresh=-32.40:offset=-0.78:linear=false',
    '-c:a','aac','-b:a','256k','-ar','48000',
    '-t','30','-movflags','+faststart',str(ROOT/'AFTERLIGHT_30s.mp4')
],check=True)
print('MASTER COMPLETE',ROOT/'AFTERLIGHT_30s.mp4')
