# watch_test.py
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
    print(f'   Response: {r["response"][:150]}')
    print(f'   Cart: {r["cart"]}')
    return r

chat('hey what do you have?')
time.sleep(3)
chat('show me watches')
time.sleep(3)
chat('I want Titan Edge Ceramic')
time.sleep(3)
chat('what is my cart?')
time.sleep(3)
chat('show me something nice')
time.sleep(3)
chat('I need a budget phone')