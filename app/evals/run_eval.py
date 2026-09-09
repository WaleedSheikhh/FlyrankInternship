import json
import requests
import os

script_dir = os.path.dirname(os.path.abspath(__file__))
cases_path = os.path.join(script_dir, "cases.json")

with open(cases_path) as f:
    cases = json.load(f)
                      
correct = 0
failures = []

for i, case in enumerate(cases, 1):
    response = requests.post(
        "http://app:8000/enrich",
        json=case["input"],
        timeout=30
    )
    if response.status_code != 200:
        failures.append((i, case["input"]["title"], f"HTTP {response.status_code}"))
        continue

    result = response.json()
    actual = result["category"]
    expected = case["expected_category"]

    if actual == expected:
        correct += 1
        print(f"[{i}/8] PASS: {case['input']['title']} -> {actual}")
    else:
        failures.append((i, case["input"]["title"], f"expected {expected}, got {actual}"))
        print(f"[{i}/8] FAIL: {case['input']['title']} -> expected {expected}, got {actual}")

print(f"\nScore: {correct}/{len(cases)}")
if failures:
    print("\nFailures:")
    for i, title, reason in failures:
        print(f"  [{i}] {title}: {reason}")