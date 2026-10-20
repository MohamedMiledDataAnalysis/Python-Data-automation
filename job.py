"""
job.py: THE JOB TO AUTOMATE
---------------------------
STEP 1 of the tutorial: run it by hand.

    python job.py

Each run appends one line to output/job_runs.csv:

    run_number,run_at,started_by
    1,2026-10-20 17:30:00,manual
    2,2026-10-20 17:31:00,schedule
    3,2026-10-20 17:32:00,task_scheduler
    4,2026-10-20 17:33:00,airflow

The `started_by` column records WHICH automation method started the run,
so you can open the CSV and see each method working.

In a real project, this function would fetch an API, clean data and load
a database. Here it stays simple on purpose: the subject is the automation,
not the job. To automate your own work, replace the body of run_job().
"""

import argparse
import csv
import sys
from datetime import datetime
from pathlib import Path

# Paths built from this file's location, not from the current folder:
# automation tools start scripts from unpredictable folders.
HERE = Path(__file__).resolve().parent
OUTPUT_FILE = HERE / "output" / "job_runs.csv"


def run_job(started_by: str = "manual", output_file: Path = OUTPUT_FILE) -> int:
    """Append one line to the output file. Returns the run number."""
    output_file.parent.mkdir(parents=True, exist_ok=True)

    # Count the existing runs to number this one.
    previous_runs = 0
    if output_file.exists():
        with output_file.open(newline="", encoding="utf-8") as f:
            previous_runs = sum(1 for _ in csv.DictReader(f))

    run_number = previous_runs + 1
    run_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    new_file = not output_file.exists()
    with output_file.open("a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if new_file:
            writer.writerow(["run_number", "run_at", "started_by"])
        writer.writerow([run_number, run_at, started_by])

    print(f"Run {run_number} at {run_at}, started by: {started_by}")
    return run_number


def main() -> int:
    parser = argparse.ArgumentParser(description="The job to automate.")
    parser.add_argument("--started-by", default="manual",
                        help="who started this run: manual, schedule, task_scheduler, airflow")
    args = parser.parse_args()
    try:
        run_job(args.started_by)
        return 0          # exit code 0: success
    except Exception as error:
        print(f"Job failed: {error}", file=sys.stderr)
        return 1          # exit code 1: failure; automation tools read this code


if __name__ == "__main__":
    sys.exit(main())
