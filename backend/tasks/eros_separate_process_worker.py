from celery import Celery

BROKER_URL = "redis://127.0.0.1:6380/0"

celery_app = Celery(
    "eros_separate_process_worker",
    broker=BROKER_URL,
    backend=BROKER_URL,
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    task_track_started=True,
    timezone="UTC",
    enable_utc=True,
)


@celery_app.task(name="eros.diagnostic.separate_process_echo")
def separate_process_echo(token: str):
    return {
        "status": "EXECUTED",
        "token": token,
    }
