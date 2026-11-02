"""Restore the byte-identical original film from its two upload-sized parts."""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parent
m=json.loads((ROOT/'manifest.json').read_text());out=ROOT.parent/m['output']
if out.exists():
    if hashlib.sha256(out.read_bytes()).hexdigest()!=m['sha256']:raise FileExistsError('An existing file differs from the original; move it before restoring.')
else:
    temp=out.with_suffix('.mp4.tmp');digest=hashlib.sha256()
    with temp.open('wb') as w:
        for item in m['parts']:
            b=(ROOT/item['file']).read_bytes()
            if len(b)!=item['bytes'] or hashlib.sha256(b).hexdigest()!=item['sha256']:raise ValueError('Part verification failed: '+item['file'])
            w.write(b);digest.update(b)
    if temp.stat().st_size!=m['bytes'] or digest.hexdigest()!=m['sha256']:
        temp.unlink();raise ValueError('Original movie verification failed')
    temp.replace(out)
print('Restored original three-car film:',out)
