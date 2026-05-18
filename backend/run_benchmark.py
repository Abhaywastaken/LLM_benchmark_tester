from app.benchmark import run_benchmark
from app.report import generate_markdown_report


if __name__ == "__main__":
    run = run_benchmark()
    print(f"Finished benchmark run: {run.run_id}")

    report = generate_markdown_report()
    print("Generated report:")
    print(report[:1000])