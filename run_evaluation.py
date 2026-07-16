import json
from generate_answer import generate_answer

def run_evaluation(eval_path, output_path):
    with open(eval_path, "r", encoding="utf-8") as f:
        eval_questions = json.load(f)

    results = []
    for item in eval_questions:
        print(f"\nRunning Q{item['id']}: {item['question']}")
        
        answer, sources = generate_answer(item['question'], k=5)
        
        source_summary = [f"{s['company']} p.{s['page_number']}" for s in sources]
        
        results.append({
            "id": item['id'],
            "question": item['question'],
            "expected_answer": item['expected_answer'],
            "generated_answer": answer,
            "sources_retrieved": source_summary,
            "type": item['type'],
            # You'll fill these in manually after reviewing:
            "retrieval_correct": None,   # Did it retrieve the right chunk(s)?
            "answer_correct": None,      # Was the generated answer factually right?
            "citation_correct": None,    # Were source numbers/pages attributed correctly?
            "model_declined_to_answer": None   # NEW: True if model said "not enough info" / "don't know"
        })
        print(f"  Answer: {answer[:150]}...")

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"\n\nSaved {len(results)} results to {output_path}")


if __name__ == "__main__":
    run_evaluation("data/evaluation/eval_questions.json", "data/evaluation/eval_results.json")  