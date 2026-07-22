import json
from agent import run_agent

def run_agent_evaluation(eval_path, output_path):
    with open(eval_path, "r", encoding="utf-8") as f:
        questions = json.load(f)

    results = []
    for item in questions:
        print(f"\n=== Q{item['id']}: {item['question']} ===")
        answer, trace = run_agent(item['question'])
        tools_called = [t['tool'] for t in trace]

        print(f"Tools called: {tools_called}")
        print(f"Answer: {answer[:150]}...")

        results.append({
            "id": item['id'],
            "question": item['question'],
            "type": item['type'],
            "expected_tools": item['expected_tools'],
            "tools_called": tools_called,
            "full_trace": trace,
            "generated_answer": answer,
            # Fill these in manually after review:
            "correct_tools_used": None,
            "answer_correct": None,
            "unnecessary_duplicate_calls": None,
            "unsupported_claims_present": None
        })

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"\n\nSaved {len(results)} results to {output_path}")


if __name__ == "__main__":
    run_agent_evaluation("data/evaluation/agent_evals.json", "data/evaluation/agent_eval_results/qwen.json")