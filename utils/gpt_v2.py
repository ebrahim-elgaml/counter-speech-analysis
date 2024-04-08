import openai
from typing import Dict, Optional
from retry import retry

SYSTEM_MESSAGE = """
    Assume you are a bot that helps reduce hate on the internet. Your job to figure out if a speech can be considered as a hate speech, counter hate speech  to another speech or neutral speech based on the provided definitions.
    Here are the definitions::
        * Hate: Content that insults, expresses, incites, or promotes hate, violence or serious harm based on race, gender, ethnicity, religion, nationality, sexual orientation, disability status, or caste.
        * Counter-hate: Content that is responding to hate speech with empathy and challenging the hate narratives or asking for clarification, rather than responding with more hate speech directed in the opposite direction.
        * Neutral speech: is a speech that can't be considered as a hate speech nor a counter hate speech.

I will share with you first a parent speech and you have to evaluate if the provided speech is a hate speech or a neutral speech. After that I will ask you about the counter speech.
If the parent speech is a hate speech, your job will be to evaluate if the provided speech is a hate speech, counter hate speech for the parent speech or neutral speech. 
If the parent speech is a neutral speech, your job will be to evaluate if the provided speech is a hate speech or neutral speech based 
"""
@retry(tries=3, delay=2)
def process_record_v2(parent_speech: str, counter_speech: str, record: Dict):
    hate_prompt = get_hate_prompt(parent_speech)
    parent_response = send_gpt_request(
        [{"role": "user", "content": hate_prompt}],
        SYSTEM_MESSAGE,
    )

    parent_speech_classification = parse_response(parent_response)
    counter_response = None
    if parent_speech_classification == "neutral speech":
        counter_response = send_gpt_request(
            [
                {"role": "user", "content": hate_prompt},
                {"role": "assistant", "content": parent_response},
                {"role": "user", "content": get_hate_prompt(counter_speech)},
            ],
            SYSTEM_MESSAGE,
        )
        # counter_speech_classification = parse_response(counter_response)
    elif parent_speech_classification == "hate speech":
        counter_response = get_counter_hate_speech_response(hate_prompt, parent_response, counter_speech)

    counter_speech_classification = parse_response(counter_response)
    # Construct the output record
    output_record = {
        'parent_speech': parent_speech_classification,
        'counter_speech': counter_speech_classification,
        "response": f"{parent_response}--{counter_response}",
        **{f"original_{k}": v for k, v in record.items()}
    }

    return output_record


def get_hate_prompt(speech: str) -> str:
    return f"""
    Is this speech '{speech}' a hate speech or a neutral speech based on the mentioned definitions?
    Please reply with the following format

    (your evaluation), because (your explanation)
    
    Please note that your evaluation can be one of the following: hate speech or neutral speech. The explanation should be a short explanation of your answer that consists of 1-2 sentences.
    """


def send_gpt_request(prompts, system_message="Counter Hate speech detection"):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo-0125",  # "gpt-4-0125-preview",  #  gpt-3.5-turbo-0125",  # "gpt-3.5-turbo",
        temperature=0.1,
        messages=[
            {"role": "system", "content": system_message},
        ] + prompts
    )
    return response.choices[0].message["content"]


def parse_response(response):
    if response.lower().strip().startswith("hate speech"):
        return "hate speech"
    elif response.lower().strip().startswith("neutral speech"):
        return "neutral speech"
    elif response.lower().strip().startswith("counter hate speech"):
        return "counter hate speech"
    else:
        return None
    # pattern = r"(.+ speech),?\s?\.? .*"    
    # matches = re.findall(pattern, response)
    # if matches:
    #     return matches[0].lower()
    # else:
    #     return None


def get_hate_speech_response(speech: str):
    hate_prompt = get_hate_prompt(speech)
    parent_response = send_gpt_request(
        [{"role": "user", "content": hate_prompt}],
        SYSTEM_MESSAGE,
    )

    return parent_response


def is_hate_speech(speech: str):
    return parse_response(get_hate_speech_response(speech)) == "hate speech"



def get_counter_hate_speech_response(hate_speech: str, hate_response: str, counter_speech: str) -> bool:
    counter_prompt = f"""
        Is this speech '{counter_speech}' a hate speech or neutral speech or counter hate speech to the previous hate speech based on the mentioned definitions?
        Please reply with the following format
        (your evaluation), because (your explanation)
        Please note that your evaluation can be one of the following: counter hate speech, hate speech or neutral speech. The explanation should be a short explanation of your answer that consists of 1-2 sentences.
        """
    return send_gpt_request(
        [
            {"role": "user", "content": get_hate_prompt(hate_speech)},
            {"role": "assistant", "content": hate_response},
            {"role": "user", "content": counter_prompt},
        ],
        SYSTEM_MESSAGE,
    )


def get_counter_hate_speech_response_gemini(hate_speech: str, counter_speech: str) -> bool:
    counter_prompt = f"""
        Is this speech '{counter_speech}' a hate speech or neutral speech or counter hate speech to this hate speech '{hate_speech}' based on the mentioned definitions?
        Please reply with the following format
        (your evaluation), because (your explanation)
        Please note that your evaluation can be one of the following: counter hate speech, hate speech or neutral speech. The explanation should be a short explanation of your answer that consists of 1-2 sentences.
        """
    return send_gpt_request(
        [
            {"role": "user", "content": get_hate_prompt(hate_speech)},
            {"role": "user", "content": counter_prompt},
        ],
        SYSTEM_MESSAGE,
    )


def get_counter_speech_category(parent_speech: str, counter_speech: str) -> Optional[str]:
    parent_response = get_counter_hate_speech_response_gemini(parent_speech, counter_speech)
    return parse_response(parent_response)
