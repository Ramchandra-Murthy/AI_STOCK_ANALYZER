from backend.tasks.celery_config import celery_broker

queues = celery_broker.config.TASK_QUEUES
routes = celery_broker.config.TASK_ROUTES

print("=== TASK_QUEUES ===")
print("TYPE:", type(queues))
print("COUNT:", len(queues))
print()

for i, q in enumerate(queues):
    print(f"QUEUE {i}")
    print("  TYPE :", type(q))
    print("  NAME :", getattr(q, "name", None))
    print("  VALUE:", q)
    print()

print("=== ROUTES ===")
print("TYPE:", type(routes))
print()

for key, value in routes.items():
    print(f"{key} -> {value}")

print()
print("=== NORMALIZED QUEUE NAMES ===")

queue_names = [
    getattr(q, "name", str(q))
    for q in queues
]

for name in queue_names:
    print(name)

print()
print("=== CONTRACT CHECK ===")

required = [
    "valuation_queue",
    "forecast_queue",
    "report_queue",
    "portfolio_queue",
]

for name in required:
    print(
        f"{name}:",
        "PASS" if name in queue_names else "MISSING"
    )

print()
print("=== ROUTE CHECK ===")

required_routes = [
    "valuation.*",
    "forecast.*",
]

for route in required_routes:
    print(
        f"{route}:",
        "PASS" if route in routes else "MISSING"
    )
