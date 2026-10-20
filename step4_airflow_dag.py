"""
step4_airflow_dag.py: AUTOMATION WITH APACHE AIRFLOW
----------------------------------------------------
STEP 4 of the tutorial (Linux, macOS, or Windows with WSL2 or Docker).

HOW IT WORKS
    Airflow is a platform with an always-running SCHEDULER. You describe a
    workflow in a Python file, a DAG (directed acyclic graph): a set of tasks
    and the order they run in. The scheduler reads the file from its dags/
    folder and runs the workflow at each scheduled time.

    Compared with steps 2 and 3, Airflow adds:
      - several tasks in order: task B runs only if task A succeeded;
      - automatic retries of a failed task;
      - a web interface with the history and the logs of every run;
      - values passed from one task to the next.

THIS DAG: three tasks in a chain

    check_folder  >>  record_run  >>  summarise
    (output folder    (runs the job,   (reads the CSV and counts
     is writable)      returns the      the runs per method)
                       run number)

SETUP: see the README, step 4. In short:
    1. Install Airflow and start it:  airflow standalone
    2. Copy THIS file and job.py into the dags/ folder (~/airflow/dags/).
    3. Open http://localhost:8080, find "automation_tutorial", switch it on.
"""

from datetime import datetime, timedelta

try:                                     # Airflow 3
    from airflow.sdk import dag, task
except ImportError:                      # Airflow 2
    from airflow.decorators import dag, task


@dag(
    dag_id="automation_tutorial",
    # WHEN: cron syntax, as in crontab. Every 2 minutes, to watch it work.
    # For real use, weekdays at 16:30 UTC:  "30 16 * * 1-5"
    schedule="*/2 * * * *",
    start_date=datetime(2026, 1, 1),
    catchup=False,             # don't run every missed slot since start_date
    max_active_runs=1,         # never two runs of this DAG at the same time
    default_args={
        "retries": 2,                          # a failed task is retried twice...
        "retry_delay": timedelta(seconds=30),  # ...30 seconds apart
    },
    tags=["tutorial"],
)
def automation_tutorial():

    # @task turns a Python function into an Airflow task: Airflow runs it,
    # logs it, retries it on failure, and shows it in the web interface.

    @task
    def check_folder() -> str:
        """Task 1: make sure the output folder exists and is writable."""
        from job import OUTPUT_FILE        # import inside the task: see the README
        OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
        probe = OUTPUT_FILE.parent / ".write_test"
        probe.write_text("ok")             # raises an error if not writable
        probe.unlink()
        return str(OUTPUT_FILE)

    @task
    def record_run(output_path: str) -> int:
        """Task 2: run the job. Its return value goes to the next task."""
        from pathlib import Path
        from job import run_job
        return run_job(started_by="airflow", output_file=Path(output_path))

    @task
    def summarise(run_number: int, output_path: str) -> dict:
        """Task 3: count the runs per method, and log the summary."""
        import csv
        with open(output_path, newline="", encoding="utf-8") as f:
            methods = [row["started_by"] for row in csv.DictReader(f)]
        counts = {m: methods.count(m) for m in sorted(set(methods))}
        print(f"Run {run_number} recorded. Runs per method so far: {counts}")
        return counts

    # THE ORDER OF THE TASKS
    # Passing a task's result to another task creates the dependency:
    # record_run waits for check_folder; summarise waits for both.
    path = check_folder()
    number = record_run(path)
    summarise(number, path)


automation_tutorial()
