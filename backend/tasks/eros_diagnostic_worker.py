from celery import Celery

BROKER_URL = "redis://127.0.0.1:6380/0"

celery_app = Celery(
    "eros_diagnostic_worker",
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


@celery_app.task(name="eros.diagnostic.worker_echo")
def worker_echo(token):
    return {
        "status": "EXECUTED",
        "token": token,
    }
