"""Tests for the tutorial. Run:  pytest"""

import csv
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import job  # noqa: E402
import step3_task_scheduler as ts  # noqa: E402


def read(path):
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def test_runs_are_numbered_and_record_the_method(tmp_path):
    out = tmp_path / "runs.csv"
    assert job.run_job("manual", out) == 1
    assert job.run_job("schedule", out) == 2
    rows = read(out)
    assert [r["run_number"] for r in rows] == ["1", "2"]
    assert [r["started_by"] for r in rows] == ["manual", "schedule"]


def test_header_written_once(tmp_path):
    out = tmp_path / "runs.csv"
    for _ in range(3):
        job.run_job("manual", out)
    assert out.read_text().count("run_number") == 1


def test_script_works_from_another_folder(tmp_path):
    # Automation tools start scripts from other folders: the output must
    # still go next to job.py, and the exit code must be 0.
    result = subprocess.run([sys.executable, str(ROOT / "job.py"), "--started-by", "test"],
                            cwd=tmp_path, capture_output=True, text=True)
    assert result.returncode == 0
    assert not (tmp_path / "output").exists()
    rows = read(ROOT / "output" / "job_runs.csv")
    assert rows[-1]["started_by"] == "test"


def test_exit_code_1_on_failure(tmp_path, monkeypatch):
    def broken(*args, **kwargs):
        raise OSError("disk full")
    monkeypatch.setattr(job, "run_job", broken)
    monkeypatch.setattr(sys, "argv", ["job.py"])
    assert job.main() == 1


def test_task_every_minute():
    cmd = ts.build_command("create")
    assert cmd[:4] == ["schtasks", "/Create", "/TN", ts.TASK_NAME]
    assert cmd[cmd.index("/SC") + 1] == "MINUTE"
    run = cmd[cmd.index("/TR") + 1]
    assert sys.executable in run and "job.py" in run and "task_scheduler" in run


def test_task_weekdays():
    cmd = ts.build_command("create", "17:30")
    assert cmd[cmd.index("/SC") + 1] == "WEEKLY"
    assert cmd[cmd.index("/D") + 1] == "MON,TUE,WED,THU,FRI"
    assert cmd[cmd.index("/ST") + 1] == "17:30"


def test_other_task_commands():
    assert ts.build_command("run") == ["schtasks", "/Run", "/TN", ts.TASK_NAME]
    assert ts.build_command("delete")[-1] == "/F"
