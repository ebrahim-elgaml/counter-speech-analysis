from utils.gpt import GptFileWriter
from utils.json_utils import read_jsonl


if __name__ == "__main__":
    name = "train"
    output_name = "train_multi"
    color = "silver"
    input_file_path = f'./conversational_context_paper/counter_context-main/data/{color}/{name}.jsonl'
    output_file_path = f'./conversational_context_paper/counter_context-main/data/{color}/{output_name}_gpt.jsonl'
    checkpoint_file_path = f'./conversational_context_paper/counter_context-main/data/{color}/{output_name}_checkpoint.txt'
    csv_file_path = f'./conversational_context_paper/counter_context-main/data/{color}/{output_name}_gpt.csv'

    gpt_file_writer = GptFileWriter(
        read_jsonl(input_file_path),
        output_file_path,
        checkpoint_file_path,
        csv_file_path,
        version="v2"
    )
    gpt_file_writer.process(
        parent_speech_key="context", counter_speech_key="target"
    )
