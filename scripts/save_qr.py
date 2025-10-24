import json
import base64
import sys

in_path = 'reports/qr_raw.json'
out_path = 'reports/qr_from_api.png'

try:
    with open(in_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
except FileNotFoundError:
    print('Input file not found:', in_path)
    sys.exit(2)
except Exception as e:
    print('Failed to read JSON:', e)
    sys.exit(3)

qr = data.get('qr_code')
if not qr:
    print('No qr_code field in JSON; content:')
    print(json.dumps(data)[:1000])
    sys.exit(4)

prefix = 'data:image/png;base64,'
if qr.startswith(prefix):
    b = base64.b64decode(qr[len(prefix):])
    with open(out_path, 'wb') as out:
        out.write(b)
    print('Saved', out_path)
    sys.exit(0)

print('Unexpected QR format; first 200 chars:')
print(qr[:200])
sys.exit(5)
