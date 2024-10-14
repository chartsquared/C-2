import re
import json
import base64
import openai
import requests
import pprint
import anthropic
from groq import Groq

class LLM:
    def __init__(self, model_name, api_key):
        self.model_name = model_name.lower()
        self.api_key = api_key
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

        if "gpt-4o" in self.model_name:
            self.client = None  # OpenAI client will use requests
        elif "claude" in self.model_name:
            self.client = anthropic.Anthropic(api_key=self.api_key)
        elif "llama" in self.model_name:
            self.client = Groq(api_key=self.api_key)
        elif "gemma" in self.model_name:
            self.client = openai.OpenAI(api_key=self.api_key, base_url="https://api.deepinfra.com/v1/openai")
        else:
            raise ValueError("Unsupported model name.")

    def encode_image(self, image_path):
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')

    def safe_execute(self, code_string):
        result_dict = {'success': False, 'error': None}
        try:
            exec(code_string)
            result_dict['success'] = True
        except Exception as e:
            result_dict['success'] = False
            result_dict['error'] = str(e)
        return result_dict['success'], result_dict['error']

    def run(self, prompt, imgs=None, past_messages=None):
        if imgs is None:
            imgs = []
        if past_messages is None:
            past_messages = []

        if "gpt-4o" in self.model_name:
            return self.run_gpt4o(prompt, imgs, past_messages)
        elif "claude" in self.model_name:
            return self.run_claude(prompt, imgs, past_messages)
        elif "llama" in self.model_name:
            return self.run_llama(prompt, past_messages)
        elif "gemma" in self.model_name:
            return self.run_gemma2(prompt, past_messages)
        else:
            raise ValueError("Unsupported model name.")

    def run_gpt4o(self, prompt, imgs, past_messages):
        messages = past_messages.copy()
        messages.append({
            "role": "user",
            "content": [
                {"type": "text", "text": prompt}
            ]
        })

        for base64_image in imgs:
            messages[-1]["content"].append({
                "type": "image_url",
                "image_url": {"url": f"data:image/png;base64,{base64_image}"}
            })

        payload = {"model": "gpt-4o", "messages": messages}
        response = requests.post("https://api.openai.com/v1/chat/completions", headers=self.headers, json=payload)
        # print(response.json())
        usage = response.json()['usage']
        return response.json()['choices'][0].get('message', {}).get('content', '')#, usage.get('total_tokens', -1), usage.get('prompt_tokens', -1), usage.get('completion_tokens', -1)

    def run_claude(self, prompt, imgs, past_messages):
        messages = past_messages.copy()
        content = [{"type": "text", "text": prompt}]
        for base64_image in imgs:
            content.append({
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/png",
                    "data": base64_image,
                }
            })

        messages.append({"role": "user", "content": content})
        response = self.client.messages.create(
            model="claude-3-5-sonnet-20240620",
            max_tokens=4096,
            messages=messages
        )
        usage = response.model_dump()['usage']
        return response.content[0].text#, usage.get('input_tokens', -1) + usage.get('output_tokens', -1), usage.get('input_tokens', -1), usage.get('output_tokens', -1)

    def run_llama(self, prompt, past_messages):
        llama_messages = past_messages.copy()
        llama_messages.append({"role": "user", "content": prompt})

        response = self.client.chat.completions.create(
            messages=llama_messages,
            model="llama-3.1-70b-versatile",
        )
        usage = response.usage
        return response.choices[0].message.content#, usage.total_tokens, usage.prompt_tokens, usage.completion_tokens

    def run_gemma2(self, prompt, past_messages):
        gemma_messages = past_messages.copy()
        gemma_messages.append({
            "role": "user",
            "content": prompt
        })

        chat_completion = self.client.chat.completions.create(
            model="google/gemma-2-27b-it",
            messages=gemma_messages,
            max_tokens=2048
        )

        usage = chat_completion.usage
        return chat_completion.choices[0].message.content#, usage.total_tokens, usage.prompt_tokens, usage.completion_tokens