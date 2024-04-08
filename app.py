import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import openai

load_dotenv()
app = Flask(__name__)
cors = CORS(app, resources={r"/*": {"origins": "*"}})


@app.route('/detect_hate_speech', methods=['POST'])
def detect_hate_speech():
    data = request.get_json()
    message = data.get('message')
    show_explanation = data.get('show_explanation', False)
    gpt_response = get_response_message(send_hate_speech(message))

    response = {
        'is_hate_speech': gpt_response.lower().startswith("yes"),  # Replace with your actual result
        'explanation': gpt_response if show_explanation else None,
        'prompt': generate_hate_speech_prompt(message),
    }
    
    return jsonify(response)


@app.route('/detect_counter_hate_speech', methods=['POST'])
def detect_counter_hate_speech():
    data = request.get_json()
    hate_speech = data.get('hate_speech')
    hate_speech_response = data.get('hate_speech_response')
    potential_counter = data.get('potential_counter')
    
    gpt_response = get_response_message(
        send_counter_speech(hate_speech=hate_speech, hate_speech_response=hate_speech_response, potential_counter=potential_counter)
    )
    response = {
        'explanation': gpt_response, # Replace with your actual result
        'prompt': generate_counter_hate_speech_prompt(hate_speech, potential_counter),
    }
    
    return jsonify(response)


def get_response_message(response) -> str:
    return response["choices"][0]["message"]["content"]


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

def send_counter_speech(hate_speech, hate_speech_response, potential_counter):
    hs_prompt = generate_hate_speech_prompt(hate_speech)
    counter_prompt = generate_counter_hate_speech_prompt(hate_speech, potential_counter)
    msg = [
            {"role": "system", "content": "Hate speech detection"},
            {"role": "user", "content": hs_prompt},
            {"role": "assistant", "content": hate_speech_response},
            {"role": "user", "content": counter_prompt},
        ]
    print(f"sending {msg}")
    return openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        temperature=0.1,
        messages=msg
    )


def generate_hate_speech_prompt(speech):
    return f"""
        Is this a hate speech 
        "{speech}"?
    """

def generate_counter_hate_speech_prompt(hate_speech, potential_counter_speech):
    return f"""
        Can this speech '{potential_counter_speech}' be considered a counter hate speech to this hate speech {hate_speech}? Please reply only with yes or no then your explanation.
        In case of no please also explain if the speech can be considered as a hate speech
    """

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)

