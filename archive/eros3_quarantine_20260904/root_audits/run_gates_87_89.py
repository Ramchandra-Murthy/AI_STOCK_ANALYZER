import os
import subprocess
import sys


def run_command(command, description):
    print(f"\n[RUNNING] {description}...")
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)
    if result.returncode != 0:
        print(f"[FAILED] {description} exited with code {result.returncode}")
        sys.exit(result.returncode)
    print(f"[PASSED] {description}")
    return result.stdout


def main():
    os.chdir(r"D:\Users\User\Desktop\AI_STOCK_ANALYZER")

    print("==================================================")
    print(" EROS GATES 87-89 BATCH VERIFICATION SUITE")
    print("==================================================")

    container_cmd = "docker compose -f docker-compose.production.yml ps -q api"
    api_container = subprocess.run(
        container_cmd, shell=True, capture_output=True, text=True
    ).stdout.strip()

    if not api_container:
        print("[ERROR] Could not determine active API container")
        sys.exit(1)
    print(f"API_CONTAINER={api_container}")

    print("\n--------------------------------------------------")
    print(" EXECUTING GATE 87: PERSISTENCE & CONCURRENCY")
    print("--------------------------------------------------")
    run_command(
        "docker compose -f docker-compose.production.yml exec -T -e PYTHONPATH=/app api python services/quantitative/block87_test_harness.py",
        "Gate 87 Test Harness",
    )

    print("\n--------------------------------------------------")
    print(" EXECUTING GATE 88: AUDIT RECONCILIATION")
    print("--------------------------------------------------")
    run_command(
        "docker compose -f docker-compose.production.yml exec -T -e PYTHONPATH=/app api python services/quantitative/block88_test_harness.py",
        "Gate 88 Test Harness",
    )

    print("\n--------------------------------------------------")
    print(" EXECUTING GATE 89: SETTLEMENT ENGINE")
    print("--------------------------------------------------")
    run_command(
        "docker compose -f docker-compose.production.yml exec -T -e PYTHONPATH=/app api python services/quantitative/block89_test_harness.py",
        "Gate 89 Test Harness",
    )

    print("\n==================================================")
    print(" GATES 87, 88, AND 89 VERIFIED SUCCESSFUL")
    print("==================================================")


if __name__ == "__main__":
    main()
