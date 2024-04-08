import json
import csv


def jsonl_to_csv(jsonl_file, csv_file):
    with open(jsonl_file, 'r', encoding='utf-8') as json_file:
        data = [json.loads(line) for line in json_file]

    # Assuming the keys are the same in all JSON objects
    keys = data[0].keys()

    with open(csv_file, 'w', newline='', encoding='utf-8') as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=keys)
        writer.writeheader()
        writer.writerows(data)
