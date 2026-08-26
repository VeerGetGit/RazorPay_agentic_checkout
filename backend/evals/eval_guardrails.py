# backend/evals/eval_guardrails.py

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from dotenv import load_dotenv
load_dotenv('.env')

from validators.input_validators import validate_input
from evals.baseline import GUARDRAIL_TEST_CASES

def run_guardrail_eval() -> dict:
    print("\n🛡️ Running Guardrail Eval...")
    print("=" * 50)

    passed = 0
    failed = 0
    errors = []

    for message, should_block in GUARDRAIL_TEST_CASES:
        result   = validate_input(message)
        blocked  = not result["passed"]
        correct  = blocked == should_block

        if correct:
            passed += 1
            status = "BLOCKED" if blocked else "ALLOWED"
            print(f"  ✅ '{message[:40]}' → {status}")
        else:
            failed += 1
            expected = "BLOCKED" if should_block else "ALLOWED"
            got      = "BLOCKED" if blocked else "ALLOWED"
            errors.append({
                "message":  message,
                "expected": expected,
                "got":      got,
            })
            print(f"  ❌ '{message[:40]}' → got={got} expected={expected}")

    total    = passed + failed
    accuracy = (passed / total * 100) if total > 0 else 0

    print(f"\n📊 Guardrail Accuracy: {passed}/{total} = {accuracy:.1f}%")

    return {
        "category": "guardrails",
        "passed":   passed,
        "failed":   failed,
        "total":    total,
        "accuracy": accuracy,
        "errors":   errors,
    }

if __name__ == "__main__":
    run_guardrail_eval()