import requests, json, sys

LOGIN_URL = "http://localhost:8000/api/auth/login"
QR_URL = "http://localhost:8000/api/whatsapp/qr-code"
CREDENTIALS = {"username": "admin", "password": "4b-EFLTXGhX6LfUmoNY"}

print('Logging in...')
# OAuth2PasswordRequestForm expects form-encoded data (application/x-www-form-urlencoded)
resp = requests.post(LOGIN_URL, data=CREDENTIALS, timeout=30)
print('Login status:', resp.status_code)
try:
    login_json = resp.json()
except Exception:
    print('Login response not JSON:')
    print(resp.text)
    sys.exit(1)

print('Login JSON:')
print(json.dumps(login_json, indent=2))

# try common token keys
token = login_json.get('access_token') or login_json.get('token') or login_json.get('access') or login_json.get('accessToken')
if not token:
    print('ERROR: no access token found in login response')
    sys.exit(2)

print('\nGot token (truncated):', token[:40] + '...')

headers = {'Authorization': f'Bearer {token}'}
print('\nRequesting QR endpoint...')
qr = requests.get(QR_URL, headers=headers, timeout=60)
print('QR status:', qr.status_code)
try:
    qr_json = qr.json()
    print('QR JSON:')
    print(json.dumps(qr_json, indent=2))
    # If there's a base64 PNG data URL, save it to a file for easy viewing
    qr_data = qr_json.get('qr_code')
    if qr_data and qr_data.startswith('data:image'):
        import base64, os, datetime
        header, b64 = qr_data.split(',', 1)
        img_bytes = base64.b64decode(b64)
        os.makedirs('reports', exist_ok=True)
        filename = f"reports/whatsapp_qr_{datetime.datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.png"
        with open(filename, 'wb') as f:
            f.write(img_bytes)
        print('Saved QR image to', filename)
except Exception:
    print('QR response not JSON:')
    print(qr.text)
    sys.exit(3)
