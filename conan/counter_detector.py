from utils.gpt import GptFileWriter
from utils.json_utils import read_json


def get_input_data(input_file: str):
    input_data = [item for item in read_json(input_file)["conan"] if item["cn_id"].startswith("EN")]
    return input_data


if __name__ == "__main__":
    base_path = "./conan/datasets"
    name = "CONAN"
    out_name = "conan_multi"
    input_file_path = f'{base_path}/{name}.json'
    output_file_path = f'{base_path}/{out_name}_gpt.jsonl'
    checkpoint_file_path = f'{base_path}/{out_name}_checkpoint.txt'
    csv_file_path = f'{base_path}/{out_name}_gpt.csv'

    gpt_file_writer = GptFileWriter(
        get_input_data(input_file_path),
        output_file_path,
        checkpoint_file_path,
        csv_file_path,
        version="v2"
    )
    gpt_file_writer.process(
        parent_speech_key="hateSpeech", counter_speech_key="counterSpeech"
    )
