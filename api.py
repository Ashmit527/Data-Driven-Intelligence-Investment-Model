from fastapi import FastAPI
from pydantic import BaseModel
from agent import run_agent
from request_logger import log_request
import time

app = FastAPI(title="AI Trading Research Assistant API")


class QuestionRequest(BaseModel):
    question: str


class QuestionResponse(BaseModel):
    question: str
    answer: str
    tool_calls: list
    latency_seconds: float


@app.get("/")
def root():
    return {"statuss": "ok", "message": "AI Trading Research Assistant API is running"}


@app.post("/ask", response_model=QuestionResponse)
def ask_question(request: QuestionRequest):
    start_time = time.time()
    error_message = None

    try:
        answer, trace = run_agent(request.question)
        tool_calls_summary = [
            {"tool": t.get("tool"), "args": t.get("raw_args")}
            for t in trace if "tool" in t
        ]
    except Exception as e:
        error_message = str(e)
        answer = "An error occurred while processing your question."
        tool_calls_summary = []

    latency = time.time() - start_time

    log_request(
        question=request.question,
        answer=answer,
        tool_calls=tool_calls_summary,
        latency_seconds=round(latency, 2),
        error=error_message
    )

    return QuestionResponse(
        question=request.question,
        answer=answer,
        tool_calls=tool_calls_summary,
        latency_seconds=round(latency, 2)
    )