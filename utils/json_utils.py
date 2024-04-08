import json
from os import path
from typing import List, Dict
SLEEP_LIMIT = 30


def read_jsonl(input_file):
    with open(input_file, 'r', encoding='utf-8') as file:
        input_data = [json.loads(line) for line in file]
    return input_data


def read_json(input_file):
    with open(input_file, 'r') as json_file:
        input_data = json.load(json_file)
    return input_data


def write_checkpoint_index(checkpoint_file_path: str, index: int) -> None:
    with open(checkpoint_file_path, 'w') as f:
        f.write(str(index))


def read_checkpoint_index(checkpoint_file_path) -> int:
    if path.exists(checkpoint_file_path):
        with open(checkpoint_file_path, 'r') as f:
            return int(f.read().strip())
    else:
        return -1


# Function to save data to JSONL file
def append_to_jsonl(data: List[Dict], filename: str) -> None:
    with open(filename, 'a', encoding='utf-8') as f:
        for item in data:
            f.write(json.dumps(item) + '\n')
