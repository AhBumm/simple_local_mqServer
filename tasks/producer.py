import json
import os
from typing import Dict


def enqueue_task(task: Dict, queue_file: str = 'tasks/queue.jsonl') -> None:
    """
    Persist a single task as a JSON line into tasks/queue.jsonl.

    The function will create the tasks directory if it does not exist.
    """
    dirpath = os.path.dirname(queue_file)
    if dirpath and not os.path.exists(dirpath):
        os.makedirs(dirpath, exist_ok=True)

    # Append a single JSON object per line
    with open(queue_file, 'a', encoding='utf-8') as f:
        f.write(json.dumps(task, ensure_ascii=False) + '\n')


if __name__ == '__main__':
    # simple smoke test
    sample = {
        'prompt': json.dumps({'op': 'echo', 'value': 'hello'}),
        'priority': 1,
        'metadata': {'prompt_id': 'test', 'create_time': '2020-01-01T00:00:00Z'}
    }
    enqueue_task(sample)
    print('Wrote sample task to tasks/queue.jsonl')
