# backend/test_a2a.py
# A2A Commerce Demo — AI Buyer Agent

import httpx

BASE = 'https://razorpay-agentic-checkout.onrender.com'

class BuyerAgent:
    def __init__(self, budget: float, category: str = None):
        self.budget   = budget
        self.category = category
        self.session  = None
        self.token    = None

    def setup(self):
        r            = httpx.post(f'{BASE}/api/session/create').json()
        self.session = r['session_id']
        self.token   = r['token']
        return r

    def discover(self):
        return httpx.get(f'{BASE}/api/catalog/agent/discover').json()

    def select(self, catalog):
        products = [
            p for p in catalog['products']
            if p['price'] <= self.budget
            and p['available']
            and (self.category is None or p['category'] == self.category)
        ]
        if not products:
            return None
        return max(products, key=lambda p: p['price'])

    def chat(self, message):
        return httpx.post(
            f'{BASE}/api/chat',
            json    = {'message': message, 'session_id': self.session},
            headers = {'X-Session-Token': self.token},
            timeout = 60,
        ).json()

    def buy(self, product):
        self.chat(product['buy_intent'])
        return self.chat('buy it')


def run():
    print("\n" + "=" * 60)
    print("A2A COMMERCE — AI Buyer Simulation")
    print("=" * 60)

    # ── Scenario 1: Normal purchase ────────────────────────────────
    print("\n📱 Scenario 1: AI Buyer needs phone under ₹85,000")
    buyer = BuyerAgent(budget=85000, category="phones")
    s = buyer.setup()
    print(f"  ✅ Session: {s['session_id'][:8]}...")

    catalog = buyer.discover()
    print(f"  ✅ Catalog: {len(catalog['products'])} products discovered")

    product = buyer.select(catalog)
    print(f"  ✅ Selected: {product['name']} — ₹{product['price']:,.0f}")

    result = buyer.buy(product)
    print(f"  ✅ Payment: {result.get('payment_status')}")
    print(f"  ✅ Remaining: ₹{result.get('remaining_limit', 0):,.0f}")
    print(f"  ✅ Response: {result.get('response', '')[:100]}")

    if result.get('order_data'):
        od = result['order_data']
        print(f"\n  📦 Structured Order Confirmation:")
        print(f"     Protocol: {od.get('protocol')}")
        print(f"     Order ID: {od.get('order_id')}")
        print(f"     Amount:   ₹{od.get('amount'):,.0f}")
        print(f"     Items:    {[i['name'] for i in od.get('items', [])]}")

    # ── Scenario 2: Failure case ───────────────────────────────────
    print("\n❌ Scenario 2: Attempting purchase exceeding limit")
    r1 = buyer.chat('add Apple Watch Series 9 to cart')
    r2 = buyer.chat('buy it')
    print(f"  Payment: {r2.get('payment_status')}")
    print(f"  Response: {r2.get('response', '')[:100]}")

    # ── Merchant Dashboard ─────────────────────────────────────────
    print("\n📈 Merchant Revenue Dashboard:")
    metrics = httpx.get(f'{BASE}/api/analytics/revenue').json()
    s = metrics.get('summary', {})
    print(f"  Total Revenue:  ₹{s.get('total_revenue', 0):,.0f}")
    print(f"  Total Orders:   {s.get('total_orders', 0)}")
    print(f"  Avg Order Value: ₹{s.get('avg_order_value', 0):,.0f}")
    print(f"  Agent Revenue:  ₹{s.get('agent_revenue', 0):,.0f} ({s.get('agent_revenue_pct', '0%')})")
    print(f"  Upsell Rate:    {s.get('upsell_rate', '0%')}")

    print("\n" + "=" * 60)
    print("A2A COMPLETE — Zero human involvement!")
    print("=" * 60)


if __name__ == "__main__":
    run()