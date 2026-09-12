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
    print(" EROS GATES 96-99 BATCH VERIFICATION SUITE")
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
    print(" EXECUTING BLOCK 96: STRESS DECISION GATE")
    print("--------------------------------------------------")
    run_command(
        "docker compose -f docker-compose.production.yml exec -T -e PYTHONPATH=/app api python -m services.quantitative.block96_test_harness",
        "Block 96 Test Harness",
    )

    print("\n--------------------------------------------------")
    print(" EXECUTING BLOCK 97: STRESS READINESS GATE")
    print("--------------------------------------------------")
    run_command(
        "docker compose -f docker-compose.production.yml exec -T -e PYTHONPATH=/app api python -m services.quantitative.block97_test_harness",
        "Block 97 Test Harness",
    )

    print("\n--------------------------------------------------")
    print(" EXECUTING BLOCK 98: EXECUTION GOVERNANCE BRIDGE")
    print("--------------------------------------------------")
    run_command(
        "docker compose -f docker-compose.production.yml exec -T -e PYTHONPATH=/app api python -m services.quantitative.block98_test_harness",
        "Block 98 Test Harness",
    )

    print("\n--------------------------------------------------")
    print(" EXECUTING BLOCK 99: EXECUTION INTENT AUTHORIZATION GATE")
    print("--------------------------------------------------")
    run_command(
        "docker compose -f docker-compose.production.yml exec -T -e PYTHONPATH=/app api python -m services.quantitative.block99_test_harness",
        "Block 99 Test Harness",
    )

    print("\n==================================================")
    print(" BLOCKS 96, 97, 98, AND 99 VERIFIED SUCCESSFUL")
    print("==================================================")


if __name__ == "__main__":
    main()
