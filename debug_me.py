from fastapi.testclient import TestClient
import traceback

from backend.main import app

client = TestClient(app)

try:
    print('Logging in...')
    resp = client.post('/api/auth/login', data={'username': 'admin', 'password': '4b-EFLTXGhX6LfUmoNY'})
    print('Login status:', resp.status_code, resp.text)
    token = resp.json().get('access_token')
    print('Token:', token)

    print('Calling /api/auth/me...')
    headers = {'Authorization': f'Bearer {token}'}
    resp2 = client.get('/api/auth/me', headers=headers)
    print('Me status:', resp2.status_code)
    try:
        print('Me JSON:', resp2.json())
    except Exception:
        print('Me text:', resp2.text)

except Exception as e:
    print('Exception in debug client:')
    traceback.print_exc()
