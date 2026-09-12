import os
import subprocess
import sys

ROOT = r"D:\Users\User\Desktop\AI_STOCK_ANALYZER"
COMPOSE = "docker compose -f docker-compose.production.yml"


def run_command(command, description):
    print(f"\n[RUNNING] {description}...")
    result = subprocess.run(command, shell=True, capture_output=True, text=True)

    if result.stdout:
        print(result.stdout)

    if result.stderr:
        print(result.stderr, file=sys.stderr)

    if result.returncode != 0:
        print(f"[FAILED] {description} exited with code " f"{result.returncode}")
        sys.exit(result.returncode)

    print(f"[PASSED] {description}")
    return result.stdout


def main():
    os.chdir(ROOT)

    print("==================================================")
    print(" EROS GATES 104-113 BATCH VERIFICATION SUITE")
    print("==================================================")

    # ------------------------------------------------
    # CONTAINER CHECK
    # ------------------------------------------------
    container_cmd = f"{COMPOSE} ps -q api"

    api_container = subprocess.run(
        container_cmd, shell=True, capture_output=True, text=True
    ).stdout.strip()

    if not api_container:
        print("[ERROR] Could not determine active API container")
        sys.exit(1)

    print(f"API_CONTAINER={api_container}")

    # ------------------------------------------------
    # VERIFY API IS RUNNING
    # ------------------------------------------------
    run_command(f"{COMPOSE} ps", "Docker Compose health check")

    # ------------------------------------------------
    # GATES 104-113
    # ------------------------------------------------
    gates = [
        (104, "services.quantitative.block104_test_harness", "Block 104 Test Harness"),
        (105, "services.quantitative.block105_test_harness", "Block 105 Test Harness"),
        (106, "services.quantitative.block106_test_harness", "Block 106 Test Harness"),
        (107, "services.quantitative.block107_test_harness", "Block 107 Test Harness"),
        (108, "services.quantitative.block108_test_harness", "Block 108 Test Harness"),
        (109, "services.quantitative.block109_test_harness", "Block 109 Test Harness"),
        (110, "services.quantitative.block110_test_harness", "Block 110 Test Harness"),
        (111, "services.quantitative.block111_test_harness", "Block 111 Test Harness"),
        (112, "services.quantitative.block112_test_harness", "Block 112 Test Harness"),
        (113, "services.quantitative.block113_test_harness", "Block 113 Test Harness"),
    ]

    for gate_no, module, description in gates:
        print("\n--------------------------------------------------")
        print(f" EXECUTING BLOCK {gate_no}")
        print("--------------------------------------------------")

        run_command(
            f"{COMPOSE} exec -T " f"-e PYTHONPATH=/app " f"api python -m {module}", description
        )

    print("\n==================================================")
    print(" BLOCKS 104-113 VERIFIED SUCCESSFUL")
    print("==================================================")


if __name__ == "__main__":
    main()
