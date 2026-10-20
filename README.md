# Automating a Python job: schedule, Task Scheduler and Airflow

![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![Licence](https://img.shields.io/badge/licence-MIT-green)

A step-by-step tutorial: one simple Python job, run by hand, then
automated three ways, from the simplest to the most powerful.

| Step | File | Who does the waiting | Runs on |
|---|---|---|---|
| 1. By hand | `job.py` | you | any system |
| 2. `schedule` library | `step2_schedule.py` | a Python loop | any system |
| 3. Task Scheduler | `step3_task_scheduler.py` | Windows | Windows |
| 4. Airflow | `step4_airflow_dag.py` | the Airflow scheduler | Linux, macOS, Windows via WSL2 or Docker |

Each run of the job adds one line to `output/job_runs.csv`, recording
**which method started it**. Open the file after each step to see the
automation working:

```
run_number,run_at,started_by
1,2026-10-20 13:56:33,manual
2,2026-10-20 13:57:34,schedule
3,2026-10-20 13:58:34,schedule
4,2026-10-20 14:02:00,task_scheduler
5,2026-10-20 14:04:00,airflow
```

---

## Contents

- [Set-up](#set-up)
- [Step 1: the job, run by hand](#step-1-the-job-run-by-hand)
- [Step 2: the schedule library](#step-2-the-schedule-library)
- [Step 3: Windows Task Scheduler](#step-3-windows-task-scheduler)
- [Step 4: Apache Airflow](#step-4-apache-airflow)
- [Comparison](#comparison)
- [Automating your own job](#automating-your-own-job)

---

## Set-up

```bash
cd automation-tutorial
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt  # schedule and pytest
```

Airflow has its own installation, in step 4.

---

## Step 1: the job, run by hand

```bash
python job.py
```

```
Run 1 at 2026-10-20 13:56:33, started by: manual
```

`job.py` contains one function, `run_job()`, which appends a line to the
CSV file. Every automation method below calls this same function.

Three details make the job ready to be automated:

| Detail | Why |
|---|---|
| Paths built from `Path(__file__)` | automation tools start scripts from unpredictable folders |
| Exit code: `0` success, `1` failure | the only way a tool knows a run failed |
| `--started-by` option | records which method ran the job |

Before automating anything, check that the job works by hand.
Automation runs a broken job just as reliably as a working one.

---

## Step 2: the schedule library

```bash
python step2_schedule.py
```

```
Scheduled: every 1 minute. Next run in 60 seconds. Stop with Ctrl+C.
Run 2 at 2026-10-20 13:57:34, started by: schedule
Next run in 60 seconds
Run 3 at 2026-10-20 13:58:34, started by: schedule
Next run in 60 seconds
```

Leave it running for a few minutes, then stop it with **Ctrl+C**.

### How it works

**1. Register the job.**

```python
schedule.every(1).minutes.do(job)
```

Nothing runs yet: the library only stores the rule and calculates the
next run time. `.do(job)` receives the function itself, `job`, not
`job()`: `job()` would run it immediately.

Other rules, in the file's comments:

```python
schedule.every(10).seconds.do(job)
schedule.every().hour.at(":15").do(job)        # every hour, minute 15
schedule.every().day.at("17:30").do(job)       # every day, 17:30
schedule.every().monday.at("17:30").do(job)    # every Monday, 17:30
```

Times use the computer's local clock.

**2. The loop that does the automating.**

```python
while True:
    if schedule.idle_seconds() <= 0:     # a job is due
        schedule.run_pending()           # run it; set the next time
    time.sleep(1)                        # check again in one second
```

Every second, the loop asks: "is a job due?" Almost always the answer
is no, and it sleeps. When a job is due, it runs, and the library moves
its next run time forward.

**3. Survive failures.**

```python
def job():
    try:
        run_job(started_by="schedule")
    except Exception as error:
        print(f"Run failed: {error}. ...")
```

Without the `try`, one failed run would stop the loop, and every future
run with it.

### The limit

The automation **is** the loop. It lasts as long as the script runs:
closing the terminal, restarting the computer or putting it to sleep
stops it, and missed runs are not caught up.

**Use it for:** learning, tests, or a machine that never switches off.

---

## Step 3: Windows Task Scheduler

Windows only. `step3_task_scheduler.py` creates the scheduled task for
you, using `schtasks`, the command-line tool of Task Scheduler.

### Create the task

```bash
python step3_task_scheduler.py create
```

The task runs `job.py` **every minute**, so you can watch it work.

**Now close the terminal.** The job keeps running: open
`output/job_runs.csv` a few minutes later and new `task_scheduler` lines
appear.

### How it works

Task Scheduler is part of Windows and is always running. The script
sends it this command:

```
schtasks /Create /TN "Python tutorial - job"
         /TR "C:\...\python.exe C:\...\job.py --started-by task_scheduler"
         /SC MINUTE /MO 1 /F
```

| Part | Meaning |
|---|---|
| `/Create` | create a task |
| `/TN "Python tutorial - job"` | task name |
| `/TR "..."` | task run: the command to start |
| `/SC MINUTE /MO 1` | schedule: every 1 minute |
| `/F` | replace the task if it already exists |

The `/TR` command uses the **full path** of the Python running the
script (`sys.executable`). Inside a virtual environment, that is the
environment's Python, so the task finds the same packages.

**The key difference from step 2:** here, Windows does the waiting.
Nothing of yours needs to stay open, and the task survives restarts.

### See it in Task Scheduler

1. Press the Windows key, type **Task Scheduler**, press Enter.
2. Click **Task Scheduler Library** in the left panel.
3. Find **Python tutorial - job**.

| Column | Meaning |
|---|---|
| Next Run Time | when Windows will start it next |
| Last Run Time | when it last ran |
| Last Run Result | `0x0` = success; `0x1` = `job.py` returned exit code 1 |

### The other commands

```bash
python step3_task_scheduler.py run      # run it now
python step3_task_scheduler.py status   # next run, last run, last result
python step3_task_scheduler.py delete   # remove the task
```

### Real use: weekdays at 17:30

```bash
python step3_task_scheduler.py create --weekdays-at 17:30
```

This replaces the every-minute task (`/F`) with
`/SC WEEKLY /D MON,TUE,WED,THU,FRI /ST 17:30`.

**Remember to delete the every-minute task** when you have finished the
tutorial, or it keeps running:

```bash
python step3_task_scheduler.py delete
```

### Settings worth changing

In the task's **Properties** window:

- **General** tab: tick **Run whether user is logged on or not**.
  Otherwise the task runs only while you are logged in.
- **Settings** tab: tick **Run task as soon as possible after a
  scheduled start is missed**. If the PC was off, the task runs as soon
  as it is switched back on.

A console window flashes at each run. To avoid it, edit the task's
action and replace `python.exe` with `pythonw.exe`, in the same folder.

### On macOS and Linux

The script prints the equivalent **cron** line instead:

```
* * * * *  /path/to/python /path/to/job.py --started-by cron
```

Add it with `crontab -e`. Cron does the same job as Task Scheduler.

**Use it for:** reliable automation on your own Windows PC or server.

---

## Step 4: Apache Airflow

Airflow is a workflow platform. Its **scheduler** is always running,
like Task Scheduler, but it adds what the previous methods lack:

- **several tasks in order:** task B runs only if task A succeeded;
- **automatic retries** of a failed task;
- **a web interface** with the history and logs of every run;
- **values passed** from one task to the next.

### The DAG

A **DAG** (directed acyclic graph) is a workflow: tasks and the order
they run in. `step4_airflow_dag.py` defines three tasks:

```
check_folder  >>  record_run  >>  summarise
```

| Task | Does | Returns |
|---|---|---|
| `check_folder` | creates the output folder and tests it is writable | the CSV path |
| `record_run` | runs the job | the run number |
| `summarise` | counts the runs per method, logs the result | the counts |

```python
@dag(
    dag_id="automation_tutorial",
    schedule="*/2 * * * *",           # every 2 minutes (cron syntax)
    start_date=datetime(2026, 1, 1),
    catchup=False,
    max_active_runs=1,
    default_args={"retries": 2,
                  "retry_delay": timedelta(seconds=30)},
)
def automation_tutorial():

    @task
    def check_folder() -> str: ...

    @task
    def record_run(output_path: str) -> int: ...

    @task
    def summarise(run_number: int, output_path: str) -> dict: ...

    path = check_folder()
    number = record_run(path)
    summarise(number, path)
```

| Setting | Meaning |
|---|---|
| `schedule="*/2 * * * *"` | when to run, in cron syntax: every 2 minutes |
| `start_date` | the first date the schedule applies from |
| `catchup=False` | do not run every missed slot since `start_date` |
| `max_active_runs=1` | never two runs at the same time |
| `retries=2` | a failed task is retried twice, 30 seconds apart |

- `@dag` turns the function into a workflow; `@task` turns each inner
  function into a task Airflow runs, logs and retries.
- **The order comes from the data.** `record_run(path)` uses the result
  of `check_folder()`, so Airflow runs `check_folder` first. No separate
  instruction is needed.
- **Imports go inside the tasks** (`from job import run_job`). Airflow
  reads every DAG file every few seconds to find changes; anything at
  the top of the file runs each time. Keeping imports inside the tasks
  makes that reading fast.

For real use, change the schedule to weekdays at 16:30 UTC:
`schedule="30 16 * * 1-5"`. Airflow times are in **UTC**.

### Install Airflow

Airflow does not run directly on Windows. On a Windows PC, use **WSL2**
(Linux inside Windows: run `wsl --install` in PowerShell as
administrator, restart, then follow the Linux steps) or **Docker
Desktop**.

In its own virtual environment, separate from the tutorial's:

```bash
python -m venv airflow-venv
source airflow-venv/bin/activate

AIRFLOW_VERSION=3.3.2
PY=$(python -c 'import sys; print("%d.%d" % sys.version_info[:2])')
BASE=https://raw.githubusercontent.com/apache/airflow
pip install "apache-airflow==$AIRFLOW_VERSION" \
  --constraint "$BASE/constraints-$AIRFLOW_VERSION/constraints-$PY.txt"
```

The **constraints file** fixes the versions of Airflow's many
dependencies. Without it, the installation often breaks. Check the
latest version at [airflow.apache.org](https://airflow.apache.org).

### Add the DAG

```bash
mkdir -p ~/airflow/dags
cp step4_airflow_dag.py job.py ~/airflow/dags/
```

`~/airflow` is Airflow's default home folder. `job.py` goes in the same
folder, so the DAG can import it.

### Test it once, without the scheduler

```bash
airflow dags test automation_tutorial
```

This runs the three tasks once, in order, and prints their logs:

```
Run 1 recorded. Runs per method so far: {'airflow': 1}
... DagRun Finished: dag_id=automation_tutorial, ... state=success
```

Test with `dags test` first: errors show immediately in the terminal.

### Start Airflow

```bash
airflow standalone
```

This one command starts every Airflow service: the scheduler, the DAG
processor (which reads the DAG files), the web server and the
triggerer. It prints a username and password: keep them.

**Run it with the Airflow virtual environment activated.**
`standalone` starts each service by calling the `airflow` command; if
the environment is not active, the services fail with
`FileNotFoundError: ... 'airflow'`.

### Switch the DAG on

1. Open **http://localhost:8080** and log in.
2. Find **automation_tutorial** in the list.
3. New DAGs start **paused**: click the toggle to switch it on.

From the terminal, the same: `airflow dags unpause automation_tutorial`.

The scheduler now starts a run every 2 minutes. Click a run to see its
three tasks:

| Colour | Meaning |
|---|---|
| green | success |
| orange | up for retry |
| red | failed |

Click a task to read its log: the `summarise` task shows the count of
runs per method.

What a test run of this tutorial looked like (Airflow 3.3.2):

```
scheduled__2026-10-20T13:02:00  success  started 13:02:01
scheduled__2026-10-20T13:04:00  success  started 13:04:01
```

- One run every 2 minutes, started by the scheduler with nothing else
  running.
- The run names are in **UTC**; the CSV shows the same runs at 14:02 and
  14:04, UK summer time.
- Just after switching the DAG on, one or two runs may start straight
  away: the scheduler runs the most recent due slot, even with
  `catchup=False`. After that, the 2-minute rhythm sets in.

### Stop it

Press **Ctrl+C** in the `airflow standalone` terminal, or pause the DAG
with its toggle.

### The limit

Like Task Scheduler, Airflow's scheduler must keep running: on your PC,
it stops when the PC does. In companies, Airflow runs on a server or as
a managed service: Amazon MWAA, Google Cloud Composer, Astronomer.

**Use it for:** pipelines of several steps that depend on each other,
run by a team. Common in data engineering job descriptions.

---

## Comparison

| | `schedule` | Task Scheduler | Airflow |
|---|---|---|---|
| Installation | `pip install schedule` | built into Windows | a platform to install |
| Who waits | your Python script | Windows | the Airflow scheduler |
| Must stay open | the Python script | nothing | the Airflow services |
| Survives a restart | no | yes | yes, if Airflow starts on boot |
| Catches up missed runs | no | with one setting | with `catchup=True` |
| Retries a failure | write it yourself | one setting | built in, per task |
| Several tasks in order | write it yourself | no | built in |
| History of runs | your own log | History tab | web interface |
| Time zone | local | local | UTC |
| Best for | learning, tests | one job on a Windows PC | multi-step pipelines, teams |

The progression: **step 2** shows what automation is (a loop that
checks the clock); **step 3** hands the waiting to the operating
system; **step 4** adds ordering, retries and monitoring for many tasks.

---

## Automating your own job

1. Replace the body of `run_job()` in `job.py` with your own code:
   fetch an API, clean data, load a database.
2. Keep its return of exit code `1` on failure.
3. Test it by hand: `python job.py`.
4. Choose a method from the comparison table.

---

## Tests

```bash
pytest
```

The tests cover the job (numbering, the CSV header, the exit code, runs
from another folder) and the commands built for Task Scheduler.

## Project structure

```
automation-tutorial/
├── job.py                     step 1: the job
├── step2_schedule.py          step 2: schedule library
├── step3_task_scheduler.py    step 3: Windows Task Scheduler
├── step4_airflow_dag.py       step 4: Airflow DAG
├── tests/test_tutorial.py
├── requirements.txt
├── LICENSE
└── README.md
```

## Licence

MIT
