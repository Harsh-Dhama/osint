import json
import base64
from urllib import request, parse

BASE = 'http://127.0.0.1:8000'
LOGIN_PATH = '/api/auth/login'
QR_PATH = '/api/whatsapp/qr-code'

def post_form(url, data):
    data_enc = parse.urlencode(data).encode('utf-8')
    req = request.Request(url, data=data_enc, method='POST')
    req.add_header('Content-Type', 'application/x-www-form-urlencoded')
    with request.urlopen(req, timeout=30) as resp:
        return resp.read()

def get_with_bearer(url, token):
    req = request.Request(url, method='GET')
    req.add_header('Authorization', f'Bearer {token}')
    with request.urlopen(req, timeout=30) as resp:
        return resp.read()

def main():
    # Use admin credentials from TESTING_GUIDE
    username = 'admin'
    password = '4b-EFLTXGhX6LfUmoNY'

    print('Logging in...')
    raw = post_form(BASE + LOGIN_PATH, {'username': username, 'password': password})
    j = json.loads(raw)
    token = j.get('access_token')
    if not token:
        print('Login failed, response:', j)
        return 2

    print('Requesting QR...')
    raw2 = get_with_bearer(BASE + QR_PATH, token)
    j2 = json.loads(raw2)
    qr = j2.get('qr_code')
    if not qr:
        print('QR not present, response:', j2)
        return 3

    prefix = 'data:image/png;base64,'
    if not qr.startswith(prefix):
        print('Unexpected QR format; first 200 chars:', qr[:200])
        return 4

    data = base64.b64decode(qr[len(prefix):])
    out = 'reports/qr_from_api.png'
    with open(out, 'wb') as f:
        f.write(data)
    print('Saved', out)
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
