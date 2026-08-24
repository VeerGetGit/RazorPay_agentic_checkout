import httpx
import time

base = 'http://127.0.0.1:8000'
s = httpx.post(f'{base}/api/session/create').json()
sid = s['session_id']
tok = s['token']
h = {'X-Session-Token': tok}

print(f'Session: {sid[:8]}')

def chat(msg):
    r = httpx.post(f'{base}/api/chat',
        json={'message': msg, 'session_id': sid},
        headers=h, timeout=60.0).json()
    print(f'\n>> {msg}')
    print(f'   Intent: {r["intent"]}')
    print(f'   Cart total: {r["cart_total"]}')
    print(f'   Cart items: {r["cart"]}')
    print(f'   Awaiting consent: {r["awaiting_consent"]}')
    print(f'   Response: {r["response"][:100]}')
    return r

chat('add the Pixel 8 to cart')
time.sleep(3)
chat('buy it')
time.sleep(3)
chat('yes confirm')