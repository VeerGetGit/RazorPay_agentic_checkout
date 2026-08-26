# backend/evals/eval_recovery.py

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from dotenv import load_dotenv
load_dotenv('.env')

from validators.input_validators import validate_input
from evals.baseline import RECOVERY_TEST_CASES

def run_recovery_eval() -> dict:
    print("\n🔄 Running Recovery Eval...")
    print("=" * 50)

    passed = 0
    failed = 0
    errors = []

    for message, should_not_contain in RECOVERY_TEST_CASES:
        try:
            result   = validate_input(message)
            response = result.get("reason", "") or ""
            clean    = should_not_contain.lower() not in response.lower()

            if clean:
                passed += 1
                print(f"  ✅ '{message[:30]}' → handled gracefully")
            else:
                failed += 1
                errors.append({
                    "message":  message,
                    "reason":   response,
                })
                print(f"  ❌ '{message[:30]}' → contains '{should_not_contain}'")

        except Exception as e:
            failed += 1
            errors.append({
                "message": message,
                "error":   str(e),
            })
            print(f"  ❌ '{message[:30]}' → exception: {e}")

    total    = passed + failed
    accuracy = (passed / total * 100) if total > 0 else 0

    print(f"\n📊 Recovery Accuracy: {passed}/{total} = {accuracy:.1f}%")

    return {
        "category": "recovery",
        "passed":   passed,
        "failed":   failed,
        "total":    total,
        "accuracy": accuracy,
        "errors":   errors,
    }

if __name__ == "__main__":
    run_recovery_eval()