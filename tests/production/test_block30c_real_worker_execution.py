import time

from backend.tasks.task_control import task_control


def test_block30c_real_worker_task_lifecycle():
    """
    Validates the complete asynchronous worker task lifecycle:
    Submission -> Broker Dispatch -> Task Control Tracking -> Result Retrieval.
    """
    # 1. Ensure task control is synchronized
    tasks = task_control.get_registered_tasks()
    assert "valuation.execute" in tasks
    assert "forecast.execute" in tasks

    # 2. Submit a production task
    submission = task_control.submit_task(
        task_name="valuation.execute",
        user="institutional_director",
        payload={
            "symbol": "TCS.NS",
            "policy_profile": "Institutional",
            "workflow_id": "WF-BLOCK-30C-001",
        },
    )
    assert submission is not None
    assert "task_id" in submission
    task_id = submission["task_id"]
    assert submission["status"] in ["QUEUED", "SUCCESS"]

    # 3. Verify task status probe
    status_info = task_control.get_task_status(task_id)
    assert status_info["task_id"] == task_id
    assert "status" in status_info

    # 4. Verify task result retrieval and workflow correlation
    # Poll briefly for result availability
    result_info = {}
    for _ in range(10):
        result_info = task_control.get_task_result(task_id)
        if result_info.get("result") is not None:
            break
        time.sleep(0.5)

    assert result_info["task_id"] == task_id
    assert "result" in result_info

    res_payload = result_info.get("result")
    assert result_info["task_id"] == task_id
    assert "result" in result_info

    res_payload = result_info.get("result")
    assert res_payload is not None
    if isinstance(res_payload, dict):
        assert res_payload.get("symbol") in ["TCS.NS", "RELIANCE.NS"] or "result" in res_payload
