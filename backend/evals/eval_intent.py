# backend/evals/eval_intent.py

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from dotenv import load_dotenv
load_dotenv('.env')

from agent.nodes.intent_node import intent_node
from langchain_core.messages import HumanMessage
from evals.baseline import INTENT_TEST_CASES
import time

def make_state(message: str) -> dict:
    return {
        "messages":          [HumanMessage(content=message)],
        "session_id":        "eval-session",
        "session_token":     "eval-token",
        "spend_limit":       100000.0,
        "spent_so_far":      0.0,
        "remaining_limit":   100000.0,
        "cart":              [],
        "cart_total":        0.0,
        "intent":            "",
        "input_blocked":     False,
        "block_reason":      "",
        "spend_blocked":     False,
        "spend_block_reason": "",
        "payment_amount":    0.0,
        "awaiting_consent":  False,
        "consent_given":     False,
        "payment_status":    "pending",
        "payment_failed":    False,
        "failure_reason":    "",
        "retry_count":       0,
        "razorpay_order_id": "",
        "final_response":    "",
        "audit_log":         [],
    }

def run_intent_eval() -> dict:
    print("\n🎯 Running Intent Eval...")
    print("=" * 50)

    passed = 0
    failed = 0
    errors = []

    for message, expected in INTENT_TEST_CASES:
        try:
            state  = make_state(message)
            result = intent_node(state)
            intent = result.get("intent", "unknown")

            if intent == expected:
                passed += 1
                print(f"  ✅ '{message[:40]}' → {intent}")
            else:
                failed += 1
                errors.append({
                    "message":  message,
                    "expected": expected,
                    "got":      intent,
                })
                print(f"  ❌ '{message[:40]}' → got={intent} expected={expected}")

        except Exception as e:
            failed += 1
            errors.append({"message": message, "error": str(e)})
            print(f"  ❌ '{message[:40]}' → exception: {e}")

        time.sleep(0.3)

    total    = passed + failed
    accuracy = (passed / total * 100) if total > 0 else 0

    print(f"\n📊 Intent Accuracy: {passed}/{total} = {accuracy:.1f}%")

    return {
        "category": "intent",
        "passed":   passed,
        "failed":   failed,
        "total":    total,
        "accuracy": accuracy,
        "errors":   errors,
    }

if __name__ == "__main__":
    run_intent_eval()