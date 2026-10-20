"""
step3_task_scheduler.py: AUTOMATION WITH WINDOWS TASK SCHEDULER
---------------------------------------------------------------
STEP 3 of the tutorial (Windows only).

This Python script creates, tests and removes a Windows scheduled task for
job.py. It calls `schtasks`, the command-line tool of Task Scheduler.

    python step3_task_scheduler.py create       # every minute (to watch it work)
    python step3_task_scheduler.py create --weekdays-at 17:30
    python step3_task_scheduler.py run          # run it now, without waiting
    python step3_task_scheduler.py status       # last run time and result
    python step3_task_scheduler.py delete       # remove the task

HOW IT WORKS
    Task Scheduler is part of Windows and is always running. Once the task
    is created, WINDOWS starts job.py at each scheduled time: this script,
    your terminal and Python can all be closed. The task survives restarts.

    Compare with step 2: there, a Python loop did the waiting, so it had to
    stay open. Here, the operating system does the waiting.

SEE IT IN THE WINDOW
    Press Windows key, type "Task Scheduler", open "Task Scheduler Library":
    the task "Python tutorial - job" appears there, with its history.
    "Last Run Result" 0x0 means success; 0x1 means job.py returned exit code 1.

NOTES
    - The task runs only while you are logged in. To run it when logged out,
      open the task's Properties and tick "Run whether user is logged on or not".
    - A console window flashes at each run. Replace python.exe by pythonw.exe
      (same folder) to run without a window.
"""

import argparse
import platform
import subprocess
import sys
from pathlib import Path

TASK_NAME = "Python tutorial - job"
JOB_FILE = Path(__file__).resolve().parent / "job.py"


def build_command(action: str, weekdays_at: str | None = None) -> list[str]:
    """Return the schtasks command for an action, as a list of arguments."""
    if action == "create":
        # /TR: the program to run. sys.executable is the full path of the Python
        # running this script: inside a virtual environment, it is that
        # environment's Python, so the task uses the same packages.
        program = subprocess.list2cmdline(
            [sys.executable, str(JOB_FILE), "--started-by", "task_scheduler"])
        if weekdays_at:
            # /SC WEEKLY /D MON,...,FRI /ST 17:30 : weekdays at 17:30
            trigger = ["/SC", "WEEKLY", "/D", "MON,TUE,WED,THU,FRI", "/ST", weekdays_at]
        else:
            # /SC MINUTE /MO 1 : every 1 minute
            trigger = ["/SC", "MINUTE", "/MO", "1"]
        # /F: replace the task if it already exists
        return ["schtasks", "/Create", "/TN", TASK_NAME, "/TR", program, *trigger, "/F"]
    if action == "run":
        return ["schtasks", "/Run", "/TN", TASK_NAME]
    if action == "status":
        return ["schtasks", "/Query", "/TN", TASK_NAME, "/V", "/FO", "LIST"]
    if action == "delete":
        return ["schtasks", "/Delete", "/TN", TASK_NAME, "/F"]
    raise ValueError(f"Unknown action: {action}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Manage the Windows scheduled task for job.py.")
    parser.add_argument("action", choices=["create", "run", "status", "delete"])
    parser.add_argument("--weekdays-at", metavar="HH:MM",
                        help="run on weekdays at this time instead of every minute")
    args = parser.parse_args()

    command = build_command(args.action, args.weekdays_at)

    if platform.system() != "Windows":
        print("Task Scheduler exists only on Windows. On this system, use cron instead.")
        print("Equivalent cron line (add it with `crontab -e`):")
        timing = "* * * * *" if not args.weekdays_at else \
            f"{args.weekdays_at[3:]} {args.weekdays_at[:2]} * * 1-5"
        print(f"  {timing}  {sys.executable} {JOB_FILE} --started-by cron")
        print("\nThe command that would run on Windows:")
        print("  " + subprocess.list2cmdline(command))
        return 1

    print("Running:", subprocess.list2cmdline(command))
    result = subprocess.run(command, capture_output=True, text=True)
    print(result.stdout or result.stderr)

    if args.action == "status" and result.returncode == 0:
        # Pick out the most useful lines of the long status report.
        for line in result.stdout.splitlines():
            if any(key in line for key in ("Next Run Time", "Last Run Time", "Last Result")):
                print("->", line.strip())
    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
