import openai
from dotenv import load_dotenv
import os

load_dotenv()

openai.api_key = os.getenv('OPENAI_API_KEY')


def generate_hate_speech_prompt(speech):
    return f"""
        Please label the following speech as (Hate speech, Not a hate speech, Depends on the situations).
        
        "{speech}"
    """


def generate_counter_hate_speech_prompt(hate_speech, potential_counter_speech):
    return f"""
        Can this speech '{potential_counter_speech}' be considered a counter hate speech to this hate speech {hate_speech}? Please reply only with yes or no then your explanation.
        In case of no please also explain if the speech can be considered as a hate speech
    """


def send_hate_speech(speech):
    prompt = generate_hate_speech_prompt(speech)
    print(f"Asking: {prompt}")
    return openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        temperature=0.1,
        messages=[
            {"role": "system", "content": "Hate speech detection"},
            {"role": "user", "content": prompt},
        ]
    )

def get_response_message(response) -> str:
    return response["choices"][0]["message"]["content"]


def is_hate_speech_response(response):
    return get_response_message(response).lower().startswith("hate speech")


def send_counter_speech(hate_speech, hate_speech_response, potential_counter):
    hs_prompt = generate_hate_speech_prompt(hate_speech)
    counter_prompt = generate_counter_hate_speech_prompt(hate_speech, potential_counter)
    msg = [
            {"role": "system", "content": "Hate speech detection"},
            {"role": "user", "content": hs_prompt},
            {"role": "assistant", "content": get_response_message(hate_speech_response)},
            {"role": "user", "content": counter_prompt},
        ]
    print(f"sending {msg}")
    return openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        temperature=0.1,
        messages=msg
    )


def process():
    print("Please enter the hate speech")
    potential_hate_speech = input().strip()
    res = send_hate_speech(potential_hate_speech)
    print(f"Hate speech response : {res}")

    if not is_hate_speech_response(res):
        print("Stopping because it is not a hate speech")
        return

    print("Please enter the counter hate speech")
    potential_counter_hate_speech = input().strip()
    print(
        send_counter_speech(
            hate_speech=potential_hate_speech,
            hate_speech_response=res,
            potential_counter=potential_counter_hate_speech
        )
    )


if __name__ == "__main__":
    process()
