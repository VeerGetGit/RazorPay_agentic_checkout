# backend/evals/eval_report.py
# Run: python evals/eval_report.py

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from dotenv import load_dotenv
load_dotenv('.env')

from evals.eval_intent      import run_intent_eval
from evals.eval_guardrails  import run_guardrail_eval
from evals.eval_payment     import run_payment_eval
from evals.eval_recovery    import run_recovery_eval
from evals.llm_eval_quality import run_llm_quality_eval
import json
from datetime import datetime

def run_all_evals():
    print("\n" + "=" * 60)
    print("RAZORPAY AGENTIC CHECKOUT — EVAL REPORT")
    print(f"Run at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    results = []

    # Run all evals
    results.append(run_guardrail_eval())
    results.append(run_payment_eval())
    results.append(run_recovery_eval())
    results.append(run_intent_eval())
    results.append(run_llm_quality_eval())

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    total_passed = 0
    total_failed = 0

    for r in results:
        status = "✅" if r["accuracy"] >= 80 else "❌"
        extra = f"avg={r['avg_score']:.1f}/10" if "avg_score" in r else ""
        print(f"{status} {r['category'].upper():15} {r['passed']:3}/{r['total']:3} = {r['accuracy']:6.1f}% {extra}")
        total_passed += r["passed"]
        total_failed += r["failed"]

    total   = total_passed + total_failed
    overall = (total_passed / total * 100) if total > 0 else 0

    print(f"\n{'OVERALL':15} {total_passed:3}/{total:3} = {overall:.1f}%")

    if overall >= 90:
        print("\n🎉 EXCELLENT — Agent is production ready!")
    elif overall >= 80:
        print("\n✅ GOOD — Agent is working well")
    elif overall >= 70:
        print("\n⚠️  FAIR — Some improvements needed")
    else:
        print("\n❌ NEEDS WORK — Multiple issues found")

    # Save report
    report = {
        "timestamp": datetime.now().isoformat(),
        "overall":   overall,
        "results":   results,
    }

    os.makedirs("evals", exist_ok=True)
    with open("evals/eval_report.json", "w") as f:
        json.dump(report, f, indent=2)

    print(f"\n📄 Report saved to evals/eval_report.json")
    return report

if __name__ == "__main__":
    run_all_evals()