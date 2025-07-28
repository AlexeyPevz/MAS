"""Demo for creating a web application via GPT-Pilot."""
import time

from gpt_pilot import create_app, status


SPEC = {
    "name": "demo-app",
    "description": "Example specification",
}


def main() -> None:
    job_id = create_app(SPEC)
    print("job id:", job_id)
    if not job_id:
        return
    time.sleep(1)
    info = status(job_id)
    print("status:", info)


if __name__ == "__main__":
    main()

