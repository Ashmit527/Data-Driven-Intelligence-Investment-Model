import ollama
import json
import re
import os

from tools_document_search import search_documents
from tools_live_data import get_live_price, get_ttm_metrics, get_financial_metrics
from tools_calculator import calculate_pe_ratio, calculate_yoy_growth, calculate_profit_margin
from tool_schema import TOOLS, COMPANY_KEYS
from tool_sanitizer import (
    sanitize_tool_args, EXPECTED_PARAMS, extract_numeric_values,
    verify_calculator_grounding
)
OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
MODEL_NAME = "finance-agent"  # custom model built from Modelfile (qwen2.5:7b based)

TOOL_FUNCTIONS = {
    "search_documents": search_documents,
    "get_live_price": get_live_price,
    "get_financial_metrics": get_financial_metrics,
    "calculate_pe_ratio": calculate_pe_ratio,
    "calculate_yoy_growth": calculate_yoy_growth,
    "calculate_profit_margin": calculate_profit_margin,
}

FAKE_TOOL_CALL_MARKERS = [
    r'"name"\s*:\s*"',
    r'"parameters"\s*:',
    r'\{"name":',
    r'tool call[s]?:',
]


def looks_like_fake_tool_call(text: str) -> bool:
    if not text:
        return False
    return any(re.search(pattern, text, re.IGNORECASE) for pattern in FAKE_TOOL_CALL_MARKERS)


def run_agent(user_question: str, max_steps: int = 8) -> tuple:
    """Returns (final_answer, tool_call_trace)."""
    messages = [{"role": "user", "content": user_question}]
    trace = []
    nudge_count = 0
    max_nudges = 2

    # Pool of every real numeric value returned by any tool so far this run -
    # used to verify calculator inputs are actually grounded, not fabricated
    retrieved_values = set()

    for step in range(max_steps):
        client = ollama.Client(host=OLLAMA_HOST)
        response = client.chat(model=MODEL_NAME, messages=messages, tools=TOOLS)
        message = response['message']
        messages.append(message)

        if not message.get('tool_calls'):
            content = message.get('content', '')
            if looks_like_fake_tool_call(content) and nudge_count < max_nudges:
                nudge_count += 1
                trace.append({"event": "fake_tool_call_detected", "content_snippet": content[:200]})
                messages.append({
                    "role": "user",
                    "content": "Do not write tool calls as text. Use the actual function-calling mechanism to call the tool now, with real values only."
                })
                continue

            return content, trace

        for tool_call in message['tool_calls']:
            func_name = tool_call['function']['name']
            func_args = tool_call['function']['arguments']
            trace.append({"tool": func_name, "raw_args": func_args})

            if func_name not in TOOL_FUNCTIONS:
                result = {"error": f"Unknown tool: {func_name}"}
            else:
                expected = EXPECTED_PARAMS.get(func_name, set(func_args.keys()))
                sanitized = sanitize_tool_args(func_name, func_args, expected)

                if sanitized["error"]:
                    result = {"error": sanitized["error"]}
                else:
                    # NEW: grounding check - block calculator calls whose
                    # numbers don't match anything actually retrieved yet
                    grounding_error = verify_calculator_grounding(
                        func_name, sanitized["clean_args"], retrieved_values
                    )
                    if grounding_error:
                        result = {"error": grounding_error}
                        trace[-1]["blocked_ungrounded"] = True
                    else:
                        try:
                            result = TOOL_FUNCTIONS[func_name](**sanitized["clean_args"])
                        except Exception as e:
                            result = {"error": f"Tool execution failed: {str(e)}"}

            trace[-1]["result"] = result

            # Add any real numbers this result contained to our grounding pool
            # (only from non-error, non-calculator results - i.e. actual data fetches)
            if func_name not in {"calculate_pe_ratio", "calculate_yoy_growth", "calculate_profit_margin"} \
               and isinstance(result, dict) and not result.get("error"):
                retrieved_values.update(extract_numeric_values(result))

            messages.append({
                "role": "tool",
                "content": json.dumps(result, default=str)
            })

    return "Agent reached max steps without a final answer.", trace


if __name__ == "__main__":
    test_questions = [
        "What is SBI's net profit margin for FY26?",
        "Calculate the YoY revenue growth for Tata Motors between FY25 and FY26 using exact figures.",
        "What is Adani's P/E ratio using their current price and latest EPS?",
    ]

    for q in test_questions:
        print(f"\n{'='*60}\nQUESTION: {q}\n{'='*60}")
        answer, trace = run_agent(q)
        for t in trace:
            if "event" in t:
                print(f"  [NUDGE TRIGGERED] {t['content_snippet']}")
            else:
                blocked = " [BLOCKED - UNGROUNDED]" if t.get("blocked_ungrounded") else ""
                print(f"  [{t['tool']}]{blocked} args={t['raw_args']} -> result={t['result']}")
        print(f"\nFINAL ANSWER:\n{answer}")