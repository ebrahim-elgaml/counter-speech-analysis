from utils.csv_utils import jsonl_to_csv


if __name__ == "__main__":
    # Example usage:
    name = "test_gpt"
    jsonl_file_path = f'./conversational_context_paper/counter_context-main/data/gold/{name}.jsonl'
    csv_file_path = f'./conversational_context_paper/counter_context-main/data/gold/{name}.csv'

    jsonl_to_csv(jsonl_file_path, csv_file_path)