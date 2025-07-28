import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / 'root_mas' / 'root_mas'))

from tools.cron import CronScheduler


def test_cron_runs_job_immediately():
    scheduler = CronScheduler()
    flag = {"ran": False}

    def job():
        flag["ran"] = True

    scheduler.add_job(job, interval=1, run_immediately=True)
    scheduler.run_pending()
    assert flag["ran"]
