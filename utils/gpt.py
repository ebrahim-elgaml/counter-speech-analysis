from os import path
import openai
import json
import re
import time
from typing import Dict, List
from utils.csv_utils import jsonl_to_csv
from retry import retry
from utils.gpt_v2 import process_record_v2
import os
from dotenv import load_dotenv


load_dotenv()
openai.api_key = os.getenv('OPENAI_API_KEY')


class GptFileWriter:
    def __init__(
        self,
        input_data: List[Dict],
        output_file: str,
        checkpoint_file: str,
        output_csv_file: str,
        version: str = "v1"
    ):
        self.input_data = input_data
        self.output_file = output_file
        self.checkpoint_file = checkpoint_file
        self.sleep_limit = 30
        self.output_csv_file = output_csv_file
        self.version = version
   
    def process(self, parent_speech_key: str, counter_speech_key: str):
        last_processed_index = self.read_checkpoint()
        start = last_processed_index + 1
        input_data = self.input_data[start:]
        sleep_count = 0
        with open(self.output_file, 'a') as outfile:
            for index, record in enumerate(input_data, start=start):
                try:
                    print(f"Processing record {index}")
                    # print(record["idx"])
                    processed_record = process_record(
                        parent_speech=record[parent_speech_key],
                        counter_speech=record[counter_speech_key],
                        record=record,
                    ) if self.version == "v1" else process_record_v2(
                        parent_speech=record[parent_speech_key],
                        counter_speech=record[counter_speech_key],
                        record=record,
                    )
                    
                    print(f"Done processing record {index}")
                    outfile.write(json.dumps(processed_record) + '\n')
                    self.write_checkpoint(index)
                    sleep_count += 1
                
                    if sleep_count % self.sleep_limit == 0:
                        print("Sleeping for 10 seconds")
                        time.sleep(10)
                except Exception as e:
                    print(f"Error processing record at index {index}: {e}")
                    # Break out of the loop in case of error to avoid processing further
                    break
        jsonl_to_csv(self.output_file, self.output_csv_file)
            
    def write_checkpoint(self, index):
        with open(self.checkpoint_file, 'w') as f:
            f.write(str(index))

    def read_checkpoint(self):
        if path.exists(self.checkpoint_file):
            with open(self.checkpoint_file, 'r') as f:
                return int(f.read().strip())
        else:
            return -1


@retry(tries=3, delay=2)
def process_record(parent_speech: str, counter_speech: str, record: Dict):
    system_message = """
        Assume you are a bot that helps reduce hate on the internet. Your job to figure out if a speech can be considered as a hate speech, counter hate speech  to another speech or neutral speech based on the provided definitions.
        Here are the definitions::
            * Hate: Content that insults, expresses, incites, or promotes hate, violence or serious harm based on race, gender, ethnicity, religion, nationality, sexual orientation, disability status, or caste.
            * Counter-hate: Content that is responding to hate speech with empathy and challenging the hate narratives or asking for clarification, rather than responding with more hate speech directed in the opposite direction.
            * Neutral speech: is a speech that can't be considered as a hate speech nor a counter hate speech.
        
        The input will be a parent speech and a counter speech to the parent speech with the following format:
    Parent speech: {parent speech}
    Counter speech: {respond speech}

    You have to do the following
    1. Determine if parent speech is a hate speech or a neutral speech given the mentioned definitions
    2. Determine if the counter speech is counter hate speech, hate speech or neutral speech based on the mentioned definition before for each one.
    ----------------------------------
    Example scenarios to consider for illustration and learn how to determine the type of speech:
    Scenario 1:
    Parent speech: This is the type of thinking that make people afraid to come out about sexual assault. It's how people rationalize assault by a close peer. You weren't raped honey, you just regret it. Are you sure you didn't flirt with him? How can you be sure you didn't lead him on? It's all a way to cover up what happened.   False accusations are a heinous thing, as someone who would rather let criminals walk than see an innocent be jailed. But encouraging the suppression of sexual assault reporting by supporting the "regret doesn't equal rape" narrative is fucked up. 
    Counter speech: So regret *does* equal rape?
    
    Response: Parent speech is neutral speech, Counter speech is hate speech

    Scenario 2:
    Parent speech: The girl should be put in jail and given the same punishment a rapist would get
    Counter speech: But that would discourage other women from lying about rape.

    Response: Parent speech is hate speech, Counter speech is counter hate speech

    Scenario 3:
    Parent speech: just think how great a place to work it will be? cheaters, liars, narcissist and huge twats all working together.  i hope she is successful and creates her own personal hell on earth 
    Counter speech: > cheaters, liars, narcissist and huge twats all working together.  A perfect synopsis of /r/politics 
    
    Response: Parent speech is hate speech, Counter speech is hate speech


    Scenario 4:
    Parent speech: A great friend of mine trained  her husband to piss sitting down.  I visited and got up to piss at night.  Got read the Riot Act in the morning because she fell in.  It came out he had to piss sitting, and I couldn't  help just [hee hawing.](https://www.youtube.com/watch?v=FopyRHHlt3M)  Now I feel sad.
    Counter speech: My solution to this: piss in the sink, only use toilet to number 2.

    Response: Parent speech is neutral speech, Counter speech is neutral speech
    ----------------------------------
    
    Please reply with the following format:
    Parent speech is {your evaluation}, Counter speech is {your evaluation}, because {your explanation}
    

    Please note that your evaluation can be one of the following: hate speech, counter hate speech, neutral speech. The explanation should be a short explanation of your answer that consists of 1-2 sentences.
    """
    prompt = f"""
    Parent speech: {parent_speech}
    Counter speech: {counter_speech}
    """

    # Send request to GPT-3.5 API
    gpt_response = send_gpt_request(prompt, system_message)

    # Process GPT-3.5 response to determine if it's a counter hate speech
    # This is a simplified example, you may need to adapt it based on actual responses from GPT-3.5
    # is_counter_hate_speech = gpt_response.lower().startswith("yes") # 'counter-hate' in gpt_response.lower()
    parent_speech_classification, counter_speech_classification = parse_gpt_response(gpt_response)

    # Construct the output record
    output_record = {
        'parent_speech': parent_speech_classification,
        'counter_speech': counter_speech_classification,
        "response": gpt_response,
        **{f"original_{k}": v for k, v in record.items()}
    }

    return output_record


def send_gpt_request(prompt, system_message="Counter Hate speech detection"):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo-0125",  # "gpt-4-0125-preview",  #  gpt-3.5-turbo-0125",  # "gpt-3.5-turbo",
        temperature=0.1,
        messages=[
            {"role": "system", "content": system_message},
            {"role": "user", "content": prompt},
        ]
    )
    return response.choices[0].message["content"]


def clean_text(text):
    if text.startswith('"'):
        return text.replace('"', "")
    return text 


def parse_gpt_response(response):
    pattern = r"Parent speech is a?\s?(.+), Counter speech is a?\s?(.+), because .*"    
    matches = re.findall(pattern, response)
    if matches:
        return matches[0]
    else:
        return None, None
