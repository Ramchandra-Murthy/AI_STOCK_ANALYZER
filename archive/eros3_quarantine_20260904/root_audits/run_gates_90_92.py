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
    print(" EROS GATES 90-92 BATCH VERIFICATION SUITE")
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
    print(" EXECUTING BLOCK 90: PORTFOLIO STATE ENGINE")
    print("--------------------------------------------------")
    run_command(
        "docker compose -f docker-compose.production.yml exec -T -e PYTHONPATH=/app api python services/quantitative/block90_test_harness.py",
        "Block 90 Test Harness",
    )

    print("\n--------------------------------------------------")
    print(" EXECUTING BLOCK 91: PORTFOLIO VALUATION ENGINE")
    print("--------------------------------------------------")
    run_command(
        "docker compose -f docker-compose.production.yml exec -T -e PYTHONPATH=/app api python services/quantitative/block91_test_harness.py",
        "Block 91 Test Harness",
    )

    print("\n--------------------------------------------------")
    print(" EXECUTING BLOCK 92: PORTFOLIO PERFORMANCE ENGINE")
    print("--------------------------------------------------")
    run_command(
        "docker compose -f docker-compose.production.yml exec -T -e PYTHONPATH=/app api python services/quantitative/block92_test_harness.py",
        "Block 92 Test Harness",
    )

    print("\n==================================================")
    print(" BLOCKS 90, 91, AND 92 VERIFIED SUCCESSFUL")
    print("==================================================")


if __name__ == "__main__":
    main()
