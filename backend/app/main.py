from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.benchmark import load_latest_results, run_benchmark

app = FastAPI(title="EvoAudit Bench API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {
        "name": "EvoAudit Bench",
        "description": "Procedural EVM benchmark for LLM smart contract auditing.",
    }


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/results")
def results():
    return load_latest_results()


@app.post("/run")
def run():
    result = run_benchmark()
    return result.model_dump()