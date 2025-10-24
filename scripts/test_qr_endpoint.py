import requests
import json

BASE = 'http://127.0.0.1:8000'

# Login
print('Logging in...')
resp = requests.post(f'{BASE}/api/auth/login', 
                     data={'username': 'admin', 'password': '4b-EFLTXGhX6LfUmoNY'},
                     headers={'Content-Type': 'application/x-www-form-urlencoded'})
print(f'Login status: {resp.status_code}')
if resp.status_code != 200:
    print('Login failed:', resp.text)
    exit(1)

token = resp.json()['access_token']
print(f'Token: {token[:50]}...')

# Get QR
print('\nRequesting QR...')
resp2 = requests.get(f'{BASE}/api/whatsapp/qr-code',
                     headers={'Authorization': f'Bearer {token}'})
print(f'QR status: {resp2.status_code}')
print(f'Response: {resp2.text[:500]}')

if resp2.status_code == 200:
    data = resp2.json()
    if data.get('qr_code'):
        print('\n✓ QR code received!')
        print(f'  QR length: {len(data["qr_code"])} chars')
    else:
        print('\n✗ No QR code in response')
        print(f'  Response keys: {list(data.keys())}')
else:
    print(f'\n✗ Error: {resp2.status_code}')
