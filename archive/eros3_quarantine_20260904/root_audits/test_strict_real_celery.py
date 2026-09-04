import time
import pprint
from backend.tasks.task_control import TaskControlService

print('==================================================')
print('   EROS 3.0 STRICT REAL-CELERY CONTRACT TEST')
print('==================================================')

control = TaskControlService()

target_user = 'institutional_research_user'
payload = {
    'symbol': 'TCS.NS',
    'bull_value': 4500.0,
    'base_value': 3500.0,
    'bear_value': 2500.0,
}

submission = control.submit_task(
    task_name='forecast.execute',
    user=target_user,
    payload=payload,
)

task_id = submission['task_id']
print('Submitted Task ID :', task_id)
print('Submitted User    :', submission.get('user'))
print('')

print('POLLING REAL CELERY WORKER...')
for i in range(20):
    time.sleep(1)
    status = control.get_task_status(task_id)
    print(f'[{i+1:02d}s] status={status.get("status")} ready={status.get("ready")}')
    if status.get('ready'):
        break

result = control.get_task_result(task_id)
print('')
print('FINAL WORKER RESULT:')
pprint.pp(result)

worker_data = result.get('result', {})
if not isinstance(worker_data, dict):
    worker_data = {}

worker_task_id = worker_data.get('task_id')
worker_user = worker_data.get('user')
worker_symbol = worker_data.get('symbol')
worker_bull = worker_data.get('bull_value')
worker_base = worker_data.get('base_value')
worker_bear = worker_data.get('bear_value')

print('')
print('==================================================')
print('EROS 3.0 STRICT CONTRACT COMPARISON MATRIX')
print('==================================================')
print(f'Control Task ID  : {task_id}')
print(f'Worker Task ID   : {worker_task_id}')
print('')
print(f'Requested User   : {target_user}')
print(f'Worker User      : {worker_user}')
print('')
print(f'Requested Symbol : {payload["symbol"]}')
print(f'Worker Symbol    : {worker_symbol}')
print('')
print(f'Requested Bull   : {payload["bull_value"]}')
print(f'Worker Bull      : {worker_bull}')
print(f'Requested Base   : {payload["base_value"]}')
print(f'Worker Base      : {worker_base}')
print(f'Requested Bear   : {payload["bear_value"]}')
print(f'Worker Bear      : {worker_bear}')
print('==================================================')

id_match = (task_id == worker_task_id)
user_match = (target_user == worker_user)
symbol_match = (payload['symbol'] == worker_symbol)
bull_match = (float(payload['bull_value']) == float(worker_bull or 0))
base_match = (float(payload['base_value']) == float(worker_base or 0))
bear_match = (float(payload['bear_value']) == float(worker_bear or 0))

if id_match and user_match and symbol_match and bull_match and base_match and bear_match:
    print('')
    print('*** EROS 3.0 REAL CELERY CONTRACT PASSED ***')
    print('*** UUID + USER + FULL PAYLOAD VERIFIED ***')
else:
    print('')
    print('*** STRICT CONTRACT MISMATCH DETECTED ***')
print('==================================================')