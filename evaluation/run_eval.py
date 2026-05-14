"""Simple evaluation runner for the customer support demo."""

import json
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from langchain_core.messages import HumanMessage

sys.path.insert(0, str(Path(__file__).parent.parent))
from src.agents.supervisor import supervisor_graph


def load_dataset():
    dataset_path = Path(__file__).parent / "dataset.json"
    with open(dataset_path) as f:
        return json.load(f)


def evaluate():
    dataset = load_dataset()
    results = []
    intent_correct = 0
    content_matches = 0
    total_content_checks = 0

    print(f"Running evaluation on {len(dataset)} test cases...\n")

    for i, case in enumerate(dataset):
        query = case["input"]
        expected_intent = case["expected_intent"]
        expected_contains = case["expected_contains"]

        result = supervisor_graph.invoke(
            {"messages": [HumanMessage(content=query)]}
        )

        actual_intent = result.get("intent", "unknown")
        response = result["messages"][-1].content

        intent_match = actual_intent == expected_intent
        if intent_match:
            intent_correct += 1

        content_hits = []
        for expected in expected_contains:
            hit = expected.lower() in response.lower()
            content_hits.append(hit)
            total_content_checks += 1
            if hit:
                content_matches += 1

        status = "PASS" if intent_match and all(content_hits) else "FAIL"
        results.append({
            "query": query,
            "expected_intent": expected_intent,
            "actual_intent": actual_intent,
            "intent_match": intent_match,
            "content_hits": content_hits,
            "status": status,
        })

        print(f"  [{status}] {i+1}. Intent: {actual_intent} (expected: {expected_intent})")
        if not all(content_hits):
            missed = [e for e, h in zip(expected_contains, content_hits) if not h]
            print(f"         Missing in response: {missed}")

    print(f"\n{'=' * 50}")
    print(f"Intent Accuracy: {intent_correct}/{len(dataset)} ({100*intent_correct/len(dataset):.0f}%)")
    if total_content_checks > 0:
        print(f"Content Match:   {content_matches}/{total_content_checks} ({100*content_matches/total_content_checks:.0f}%)")
    print(f"Overall Pass:    {sum(1 for r in results if r['status'] == 'PASS')}/{len(dataset)}")

    output_path = Path(__file__).parent / "eval_results.json"
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nDetailed results saved to: {output_path}")


if __name__ == "__main__":
    evaluate()
