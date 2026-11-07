"""Mux picture and score into the 30-second delivery master (two-pass loudness to -14 LUFS / -1 dBTP, social-feed level)."""
from pathlib import Path
import json, re, subprocess
ROOT = Path(__file__).resolve().parent
pic, wav, dst = ROOT / 'BLITZ_picture.mp4', ROOT / 'BLITZ_score.wav', ROOT / 'BLITZ_30s.mp4'
target = 'I=-14:TP=-1:LRA=11'
log = subprocess.run(['ffmpeg', '-hide_banner', '-nostats', '-i', str(wav), '-af', f'loudnorm={target}:print_format=json', '-f', 'null', '-'],
                     capture_output=True, text=True).stderr
mm = json.loads(re.search(r'\{[^{}]*"input_i"[^{}]*\}', log, re.S).group(0))
af = (f"loudnorm={target}:measured_I={mm['input_i']}:measured_TP={mm['input_tp']}:measured_LRA={mm['input_lra']}"
      f":measured_thresh={mm['input_thresh']}:offset={mm['target_offset']}:linear=true")
subprocess.run(['ffmpeg', '-y', '-hide_banner', '-loglevel', 'error', '-i', str(pic), '-i', str(wav), '-map', '0:v:0', '-map', '1:a:0',
                '-c:v', 'copy', '-af', af, '-c:a', 'aac', '-b:a', '256k', '-ar', '48000', '-t', '30', '-movflags', '+faststart', str(dst)], check=True)
print('MASTER COMPLETE', dst, 'measured', mm['input_i'], 'LUFS')
