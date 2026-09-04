from services.eros_frontend_adapter import EROSFrontendAdapter

adapter = EROSFrontendAdapter()

exists = hasattr(adapter, "decision_traceability")

print(
    "decision_traceability : "
    + ("PRESENT" if exists else "ABSENT")
)

if exists:
    raise RuntimeError(
        "V37_API_ALREADY_PRESENT"
    )

print("V3.7 API : ABSENT")