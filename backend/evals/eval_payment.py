# backend/evals/eval_payment.py

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from dotenv import load_dotenv
load_dotenv('.env')

from validators.spend_validators import validate_spend
from evals.baseline import PAYMENT_TEST_CASES

def run_payment_eval() -> dict:
    print("\n💳 Running Payment Eval...")
    print("=" * 50)

    passed = 0
    failed = 0
    errors = []

    for amount, limit, spent, should_pass in PAYMENT_TEST_CASES:
        result  = validate_spend(
            amount       = amount,
            spend_limit  = limit,
            spent_so_far = spent,
            session_id   = "test-session",
            cart         = [{"total": amount}] if amount > 0 else [],
        )
        did_pass = result["passed"]
        correct  = did_pass == should_pass

        if correct:
            passed += 1
            status = "PASSED" if did_pass else "BLOCKED"
            print(f"  ✅ ₹{amount} (limit=₹{limit}, spent=₹{spent}) → {status}")
        else:
            failed += 1
            expected = "PASS" if should_pass else "BLOCK"
            got      = "PASS" if did_pass else "BLOCK"
            errors.append({
                "amount":  amount,
                "limit":   limit,
                "spent":   spent,
                "expected": expected,
                "got":     got,
                "reason":  result.get("reason", ""),
            })
            print(f"  ❌ ₹{amount} → got={got} expected={expected} | {result.get('reason', '')}")

    total    = passed + failed
    accuracy = (passed / total * 100) if total > 0 else 0

    print(f"\n📊 Payment Accuracy: {passed}/{total} = {accuracy:.1f}%")

    return {
        "category": "payment",
        "passed":   passed,
        "failed":   failed,
        "total":    total,
        "accuracy": accuracy,
        "errors":   errors,
    }

if __name__ == "__main__":
    run_payment_eval()