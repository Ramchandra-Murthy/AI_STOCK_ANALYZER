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
    print(" EROS GATES 100-103 BATCH VERIFICATION SUITE")
    print("==================================================")

    container_cmd = "docker compose -f docker-compose.production.yml ps -q api"
    api_container = subprocess.run(container_cmd, shell=True, capture_output=True, text=True).stdout.strip()
    
    if not api_container:
        print("[ERROR] Could not determine active API container")
        sys.exit(1)
    print(f"API_CONTAINER={api_container}")

    print("\n--------------------------------------------------")
    print(" EXECUTING BLOCK 100: PAPER EXECUTION FILL GATE")
    print("--------------------------------------------------")
    run_command(
        "docker compose -f docker-compose.production.yml exec -T -e PYTHONPATH=/app api python -m services.quantitative.block100_test_harness",
        "Block 100 Test Harness"
    )

    print("\n--------------------------------------------------")
    print(" EXECUTING BLOCK 101: EXECUTION EVIDENCE RECONCILIATION")
    print("--------------------------------------------------")
    run_command(
        "docker compose -f docker-compose.production.yml exec -T -e PYTHONPATH=/app api python -m services.quantitative.block101_test_harness",
        "Block 101 Test Harness"
    )

    print("\n--------------------------------------------------")
    print(" EXECUTING BLOCK 102: FRONTEND CONTRACT")
    print("--------------------------------------------------")
    run_command(
        "docker compose -f docker-compose.production.yml exec -T -e PYTHONPATH=/app api python -m services.quantitative.block102_test_harness",
        "Block 102 Test Harness"
    )

    print("\n--------------------------------------------------")
    print(" EXECUTING BLOCK 103: INSTITUTIONAL FRONTEND READ MODEL")
    print("--------------------------------------------------")
    run_command(
        "docker compose -f docker-compose.production.yml exec -T -e PYTHONPATH=/app api python -m services.quantitative.block103_test_harness",
        "Block 103 Test Harness"
    )

    print("\n==================================================")
    print(" BLOCKS 100, 101, 102, AND 103 VERIFIED SUCCESSFUL")
    print("==================================================")

if __name__ == "__main__":
    main()
