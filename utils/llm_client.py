from typing import List
import openai
import re
from utils.prompts import prompts
from typing import NamedTuple, Optional
import vertexai
from vertexai.preview.generative_models import (
    GenerativeModel,
    GenerationConfig,
    HarmCategory,
    HarmBlockThreshold
)
from retry import retry
import os
from dotenv import load_dotenv

load_dotenv() 
openai.api_key = os.getenv('OPENAI_API_KEY')
vertexai.init(project=os.getenv("VERTEX_AI_PROJECT"), location="us-central1")


class SpeechCategory:
    HATE_SPEECH: str = "hate speech"
    NEUTRAL_SPEECH: str = "neutral speech"
    COUNTER_HATE_SPEECH: str = "counter hate speech"


class ProcessResponse(NamedTuple):
    parent_speech: Optional[str]
    counter_speech: Optional[str]
    responses: List[str]


class LlmClient:
    def __init__(self, parent_speech: str):
        self.parent_speech = parent_speech
        self.responses = []

    def send_request(self, prompt: str):
        raise NotImplementedError

    def get_response_text(self, response) -> str:
        raise NotImplementedError

    def is_hate_speech(self, speech: str) -> bool:
        raise NotImplementedError

    def get_counter_speech_category(self, counter_speech: str) -> Optional[str]:
        raise NotImplementedError
    
    def parse_response(self, response_text):
        raise NotImplementedError
    
    def process(self, counter_speech: str) -> ProcessResponse:
        raise NotImplementedError


class GptSingleClient(LlmClient):
    def __init__(self, **args):
        super().__init__(**args)
        self.system_message = prompts["gpt_single_system_message"]

    def process(self, counter_speech: str) -> ProcessResponse:
        response = self.send_request(
            prompts["gpt_single_prompt"].format(
                parent_speech=self.parent_speech,
                counter_speech=counter_speech
            )
        )
        response_text = self.get_response_text(response)
        parent_speech_category, counter_speech_category = self.parse_response(
            response_text
        )
        return ProcessResponse(
            parent_speech=parent_speech_category,
            counter_speech=counter_speech_category,
            responses=[response_text]
        )

    @retry(
        exceptions=Exception,
        tries=5,
        delay=2,
        backoff=2,
        max_delay=60,
    )
    def send_request(self, prompt: str):
        return openai.ChatCompletion.create(
            model="gpt-3.5-turbo-0125",  # "gpt-4-0125-preview",  #  gpt-3.5-turbo-0125",  # "gpt-3.5-turbo",
            temperature=0.1,
            messages=[
                {"role": "system", "content": self.system_message},
                {"role": "user", "content": prompt},
            ]
        )

    def get_response_text(self, response):
        return response.choices[0].message["content"]
    
    def parse_response(self, response_text):
        pattern = r"Parent speech is a?\s?(.+), Counter speech is a?\s?(.+), because .*"    
        matches = re.findall(pattern, response_text)
        if matches:
            return matches[0]
        else:
            return None, None


class GptSingleMulti(GptSingleClient):
    def __init__(self, **args):
        super().__init__(**args)
        self.system_message = prompts["gpt_multi_system_message"]
        self.messages = [{"role": "system", "content": self.system_message}]

    def process(self, counter_speech: str) -> ProcessResponse:
        hate_prompt = prompts["gpt_multi_hate_prompt"]
        parent_response = self.send_request(hate_prompt.format(
            speech=self.parent_speech
        ))
        parent_response_text = self.get_response_text(parent_response)
        parent_speech_classification = self.parse_response(
            parent_response_text
        )

        counter_response = None
        if parent_speech_classification == SpeechCategory.NEUTRAL_SPEECH:
            counter_response = self.send_request(
                hate_prompt.format(speech=counter_speech)
            )
        elif parent_speech_classification == SpeechCategory.HATE_SPEECH:
            counter_response = self.send_request(
                prompts["gpt_multi_counter_prompt"].format(
                    counter_speech=counter_speech
                )
            )
        counter_response_text = self.get_response_text(counter_response)
        counter_speech_classification = self.parse_response(
            counter_response_text
        )
        return ProcessResponse(
            parent_speech=parent_speech_classification,
            counter_speech=counter_speech_classification,
            responses=[parent_response_text, counter_response_text]
        )

    @retry(
        exceptions=Exception,
        tries=5,
        delay=2,
        backoff=2,
        max_delay=60,
    )
    def send_request(self, prompt: str):
        self.messages.append({"role": "user", "content": prompt})
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo-0125",  # "gpt-4-0125-preview",  #  gpt-3.5-turbo-0125",  # "gpt-3.5-turbo",
            temperature=0.1,
            messages=self.messages,
        )
        self.messages.append(
            {"role": "assistant", "content": self.get_response_text(response)}
        )
        return response

    def parse_response(self, response_text):
        return parse_multi_step_response(response_text)


class GeminiSingleClient(LlmClient):
    def process(self, counter_speech: str) -> ProcessResponse:
        response = self.send_request(
            prompts["gemini_single_prompt"].format(
                parent_speech=self.parent_speech,
                counter_speech=counter_speech
            )
        )
        response_text = self.get_response_text(response)
        parent_speech_category, counter_speech_category = self.parse_response(
            response_text
        )
        return ProcessResponse(
            parent_speech=parent_speech_category,
            counter_speech=counter_speech_category,
            responses=[response_text]
        )

    @retry(
        exceptions=Exception,
        tries=5,
        delay=2,
        backoff=2,
        max_delay=60,
    )
    def send_request(self, prompt: str):
        parameters = {
            "temperature": 0.1,  # Temperature controls the degree of randomness in token selection.
            "max_output_tokens": 2560,  # Token limit determines the maximum amount of text output.
            "top_p": 0.8,  # Tokens are selected from most probable to least until the sum of their probabilities equals the top_p value.
            "top_k": 1,  # A top_k of 1 means the selected token is the most probable among all tokens.
            "candidate_count": 1
        }
        gemini_pro_model = GenerativeModel(
            "gemini-1.0-pro",
            generation_config=GenerationConfig(**parameters)
        )
        block_threshold = HarmBlockThreshold.BLOCK_NONE
        response = gemini_pro_model.generate_content(
            prompt,
            safety_settings={
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: block_threshold,
                HarmCategory.HARM_CATEGORY_HARASSMENT: block_threshold,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: block_threshold,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: block_threshold,
            }
        )
        return response

    def get_response_text(self, response):
        # print("************", response)
        try:
            return response.text
        except Exception:
            if response.candidates[0].finish_reason == 7:
                return "Parent speech is neutral speech, Counter speech neutral speech, because finish_reason 7"
            raise
    
    def parse_response(self, response_text):
        pattern = r"Parent speech is a?\s?(.+), Counter speech is a?\s?(.+), because .*"    
        matches = re.findall(pattern, response_text)
        if matches:
            return matches[0]
        else:
            return None, None
        

class GeminiMultiClient(GeminiSingleClient):
    def __init__(self, **args):
        super().__init__(**args)
        self.system_message = prompts["gemini_multi_system_message"]
        self.responses = []


    def process(self, counter_speech: str) -> ProcessResponse:
        parent_speech_classification = self.get_parent_speech_category(
            self.parent_speech
        )
        counter_speech_classification = None
        if parent_speech_classification == SpeechCategory.NEUTRAL_SPEECH:
            counter_speech_classification = self.get_parent_speech_category(
                counter_speech
            )
        elif parent_speech_classification == SpeechCategory.HATE_SPEECH:
            counter_speech_classification = self.get_counter_speech_category(
                counter_speech
            )
        return ProcessResponse(
            parent_speech=parent_speech_classification,
            counter_speech=counter_speech_classification,
            responses=self.responses
        )

    def get_response_text(self, response):
        # print("**********************", response)
        # print("************2", response.candidates)
        try:
            return response.text
        except Exception:
            try:
                if response.candidates[0].finish_reason == 7:
                    return "Neutral speech, because finish_reason 7"
                raise
            except IndexError:
                return "Neutral speech, because finish_reason 7w"

    def parse_response(self, response_text):
        return parse_multi_step_response(response_text)

    def is_hate_speech(self, speech: str) -> bool:
        cat = self.get_parent_speech_category(speech)
        return cat == SpeechCategory.HATE_SPEECH

    def get_parent_speech_category(self, speech: str) -> Optional[str]:
        hate_prompt = prompts["gemini_multi_hate_prompt"]
        parent_response = self.send_request(
            hate_prompt.format(
                system_message=self.system_message,
                speech=speech
            )
        )
        parent_response_text = self.get_response_text(parent_response)
        self.responses.append(parent_response_text)
        return self.parse_response(parent_response_text)
    
    def get_counter_speech_category(self, counter_speech: str) -> Optional[str]:
        counter_response = self.send_request(
            prompts["gemini_multi_counter_prompt"].format(
                system_message=self.system_message,
                counter_speech=counter_speech,
                parent_speech=self.parent_speech
            )
        )
        counter_response_text = self.get_response_text(counter_response)
        self.responses.append(counter_response_text)
        return self.parse_response(counter_response_text)


def parse_multi_step_response(response_text):
    if response_text.lower().strip().startswith("hate speech"):
        return SpeechCategory.HATE_SPEECH
    elif response_text.lower().strip().startswith("neutral speech"):
        return SpeechCategory.NEUTRAL_SPEECH
    elif response_text.lower().strip().startswith("counter hate speech"):
        return SpeechCategory.COUNTER_HATE_SPEECH
    else:
        return None