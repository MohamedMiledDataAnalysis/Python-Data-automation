"""
step2_schedule.py: AUTOMATION WITH THE `schedule` LIBRARY
---------------------------------------------------------
STEP 2 of the tutorial.

Install:  pip install schedule
Run:      python step2_schedule.py
Stop:     Ctrl+C

HOW IT WORKS
    1. You register the job with a rule: "every minute", "every Monday at 17:30".
       Nothing runs yet: the library only stores the rule.
    2. An endless loop asks the library, every second: "is a job due now?"
       If yes, the library runs it, then calculates the next run time.

    The automation IS that loop. It lasts as long as this script runs:
    close the terminal or restart the computer, and it stops.

WHAT YOU WILL SEE
    Scheduled: every 1 minute. Next run in 60 seconds. Stop with Ctrl+C.
    Run 2 at 2026-10-20 14:01:00, started by: schedule
    Next run in 60 seconds
    Run 3 at 2026-10-20 14:02:00, started by: schedule
"""

import time

import schedule

from job import run_job


def job() -> None:
    # try/except: a failed run is reported, and the loop continues.
    # Without it, one error would stop every future run.
    try:
        run_job(started_by="schedule")
    except Exception as error:
        print(f"Run failed: {error}. Next attempt at the next scheduled time.")


# ---------------------------------------------------------------------------
# 1. REGISTER THE JOB
# Every minute, so you can watch it work. For real use, replace with one of
# the rules below (times use the computer's local clock).
# ---------------------------------------------------------------------------
schedule.every(1).minutes.do(job)

# schedule.every(10).seconds.do(job)                 # every 10 seconds
# schedule.every().hour.at(":15").do(job)            # every hour, at minute 15
# schedule.every().day.at("17:30").do(job)           # every day at 17:30
# schedule.every().monday.at("17:30").do(job)        # every Monday at 17:30
# for day in ("monday", "tuesday", "wednesday", "thursday", "friday"):
#     getattr(schedule.every(), day).at("17:30").do(job)   # weekdays at 17:30

# .do(job) receives the function itself: job, not job().
# job() would run it now and register its result instead.


# ---------------------------------------------------------------------------
# 2. THE LOOP THAT DOES THE AUTOMATING
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print(f"Scheduled: every 1 minute. Next run in {schedule.idle_seconds():.0f} seconds. "
          "Stop with Ctrl+C.")
    try:
        while True:
            if schedule.idle_seconds() <= 0:     # a job is due
                schedule.run_pending()           # run it; the library sets the next time
                print(f"Next run in {schedule.idle_seconds():.0f} seconds")
            time.sleep(1)                        # check again in one second
    except KeyboardInterrupt:
        print("\nStopped. Nothing will run until you start this script again.")
