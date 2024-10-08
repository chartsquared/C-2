import base64
import importlib
import re
import subprocess
import requests
import pprint
import sys
import json  # Required for encoding data for API calls
from LLM import LLM


class ChartAgent:
    def __init__(self, api_key, d2c_model):
        self.api_key = api_key
        self.d2c_model = d2c_model
        self.llm = LLM(model_name=d2c_model, api_key=api_key)  # Initialize the LLM instance
        self.run_d2c = self._select_d2c_model()
        self.ca_memory = []

    def _select_d2c_model(self):
        """Select the D2C model to use based on the input string."""
        # Define the lambda function to run the LLM instance and save past memory
        def run_model(prompt, past_memory):
            return self.llm.run(prompt=prompt, past_messages=past_memory)
        return run_model

    def parse_code_blocks(self, text):
        # Regular expression to find Python and R code blocks enclosed within triple backticks or custom delimiters
        regex = r"```(?:python|Python|r|R|html|HTML)?\n(.*?)```|<start of Python code format>(.*?)<end of Python code format>"
        matches = re.findall(regex, text, re.DOTALL | re.IGNORECASE)  # DOTALL to allow dot to match newlines, IGNORECASE for case insensitivity
        
        # Combine matches from both groups into one list
        combined_matches = [match[0].strip() if match[0] else match[1].strip() for match in matches]
        return combined_matches

    def parse_modules(self, text):
        # Extract import statements with regular expressions and save them as is
        regex = r"^\s*(import\s+[\w\.]+(?:\s+as\s+\w+)?|from\s+[\w\.]+\s+import\s+[\w\.\*, ]+(?:\s+as\s+\w+)?)"
        modules = re.findall(regex, text, re.MULTILINE)
        import_commands = []
        for match in modules:
            import_commands.append(match.strip())
            # Extract module names from the import statements
            module = match.split(" ")[1]
            spec = importlib.util.find_spec(module)
            if spec is None:
                subprocess.check_call([sys.executable, "-m", "pip", "install", module])
                print(f"Module {module} installed.")
        return import_commands

    @staticmethod
    def write_memory_to_file(memory, file_name="memory.json"):
        """Write the memory object to a JSON file."""
        with open(file_name, "w", encoding="utf-8") as json_file:
            json.dump(memory, json_file, indent=4)
        print(f"Memory updated and written to {file_name}")

    def run_d2c_task(self, data, data_path, file_index, memory):
        self.ca_memory = []
        """Run the D2C task with the specified model."""
        with open("prompts/ca_d2c.txt", "r", encoding="utf-8") as file:
            d2c_prompt = file.read()

        d2c_prompt = d2c_prompt.format(
            data=data, data_path=data_path, file_index=file_index,
            initial_instruction=memory['initial_prompt'],
            Q=memory['questions'], A=memory['answers']
        )
        memory['d2c_prompt'] = d2c_prompt
        # Run the D2C model and update memory
        memory['d2c_before_feedback'] = self.run_d2c(d2c_prompt, self.ca_memory)
        # Write to file after every update
        self.write_memory_to_file(memory)
        self.ca_memory.append({"role": "user", "content": d2c_prompt})
        self.ca_memory.append({"role": "assistant", "content": memory['d2c_before_feedback']})
        
        memory['result_code'] = self.parse_code_blocks(memory['d2c_before_feedback'])[0]
        memory['imported_modules'] = self.parse_modules(memory['result_code'])

        # Write to file after every update
        self.write_memory_to_file(memory)
        self.write_memory_to_file(self.ca_memory, "ca_memory.json")

        return memory
    
    def run_d2c_task_with_feedback(self, feedback_gpt_classified, feedback_claude_classified, feedback_gpt_code, feedback_claude_code, file_index, memory, use_claude=True):
        ######################
        # D2C after feedback #
        ######################

        # D2C Task post feedback (feedback from gpt4o)
        d2c_prompt_icl_gpt = None
        with open("prompts/ca_d2c_after_feedback.txt", "r", encoding="utf-8") as file:
            d2c_prompt_icl_gpt = file.read()
        d2c_prompt_icl_gpt = d2c_prompt_icl_gpt.format(
            initial_instruction=memory['initial_prompt'],
            retain= feedback_gpt_classified['RETAIN'], modification=feedback_gpt_code,
            file_index=f"autojudge_{file_index}(gpt_feedback)"
            )
        memory['16_asking_chartagent_to_improve_visualization(gpt4o)'] = d2c_prompt_icl_gpt
        memory['d2c_icl(gpt4o)'] = self.run_d2c(d2c_prompt_icl_gpt, self.ca_memory)
        memory['result_code_icl(gpt4o)'] = self.parse_code_blocks(memory['d2c_icl(gpt4o)'])

        if use_claude:
            # D2C Task post feedback (feedback from claude)
            d2c_prompt_icl_claude = None
            with open("prompts/ca_d2c_after_feedback.txt", "r", encoding="utf-8") as file:
                d2c_prompt_icl_claude = file.read()
            d2c_prompt_icl_claude = d2c_prompt_icl_claude.format(
                initial_instruction=memory['initial_prompt'],
                retain=feedback_claude_classified['RETAIN'], modification=feedback_claude_code,
                file_index=f"autojudge_{file_index}(claude_feedback)"
                )
            memory['16_asking_chartagent_to_improve_visualization(claude)'] = d2c_prompt_icl_claude
            memory['d2c_icl(claude)'] = self.run_d2c(d2c_prompt_icl_claude, self.ca_memory)
            memory['result_code_icl(claude)'] = self.parse_code_blocks(memory['d2c_icl(claude)'])
            self.write_memory_to_file(memory)

            return memory['result_code_icl(gpt4o)'], memory['result_code_icl(claude)']
        
        else:
            return memory['result_code_icl(gpt4o)']
        