import json
from LLM import LLM
import re
import yaml

class AutoJudge:
    def __init__(self, gpt_api_key, claude_api_key, rendered_img, memory, data, run_only_gpt = False):
        self.memory = memory.copy()
        self.aj_gpt = LLM(model_name='gpt-4o', api_key=gpt_api_key)
        self.aj_claude = LLM(model_name='claude', api_key=claude_api_key)
        self.aj_memory_gpt = []
        self.aj_memory_claude = []
        self.initial_instruction: str = self.memory["02_initial_prompt"]
        self.data_attributes: str = self.memory["05_data_attributes"]
        self.run_only_gpt: bool = run_only_gpt
        self.semantic_decompose(data)
        self.gpt_task: str = self.memory['05_task(gpt4o)']
        self.gpt_purpose: str = self.memory['05_purpose(gpt4o)']
        self.gpt_audience: str = self.memory['05_audience(gpt4o)']
        self.claude_task: str = self.memory["05_task(claude)"]
        self.claude_purpose: str = self.memory["05_purpose(claude)"]
        self.claude_audience: str = self.memory["05_audience(claude)"]
        self.questions: str = self.memory['07_questions']
        self.answers: str = self.memory['09_answers']
        self.code: str = self.memory['result_code']
        self.rendered_img:list = rendered_img
        self.basic_criteria: str = """
        Chart Type
        - Choose a chart type that aligns with the given purpose, task, and audience. The chart type should effectively convey the intended message; for example, bar charts are ideal for comparing quantities for limited number of categorical data, while line charts show trends over time. The choice must consider the inherent spacing requirements and the context in which the chart will be used, ensuring clarity and comprehension.

        Visual Embellishment
        - Use embellishments to enhance understanding without overwhelming the data. Visual embellishments, like icons, patterns, or textures, should be used sparingly and purposefully to make the chart memorable and engaging while maintaining a balance that does not distract from the core data.
        
        Text
        - Prioritize legibility and adhere to consistent textual criteria. Text elements, such as legends, titles, and labels, should be legible and easy to read, with sufficient contrast against the background. Consistent font size, style, and placement should be maintained to create a cohesive visual narrative that guides the audience's understanding.

        Color
        - Use color purposefully and sparingly to convey meaning. Choose a limited palette that enhances readability and highlights key data points, considering color statistics and opponent processing principles (contrasting colors for clarity). This helps ensure accessibility for viewers with color vision deficiencies.

        Annotation
        - Emphasize critical data while minimizing irrelevant details. Use annotations strategically to draw attention to important insights, trends, or outliers, and smooth over or de-emphasize less significant data points, ensuring the chart communicates its key message effectively.

        Aesthetics
        - Tailor aesthetics to the chart's purpose, audience, and context. Consider the chart’s purpose, the target audience, and the presentation environment when designing aesthetics, including compact spacing and visual hierarchy. This ensures the chart is both functional and appealing, maximizing its impact and effectiveness

        Visual Clutter
        - Optimize the chart size to fit its content and context, balancing data and available space to prevent clutter or excessive white space while maintaining readability. Manage visual elements by minimizing overcrowding and overlapping, adequately spacing text, data points, and annotations, removing unnecessary details, and maintaining a clean layout to enhance clarity. Segmentation of complex charts or data visualizations can also be employed if the visual complexity is high, breaking down the data into smaller, more manageable parts for easier interpretation. It is important to emphasize key data by using size, color, and opacity to highlight critical insights while downplaying less relevant information for a focused presentation.
        """
        self.feedback_gpt: str = None
        self.feedback_gpt_classified: dict = None
        self.feedback_claude: str = None
        self.feedback_claude_classified: dict = None
        self.feedback_gpt_code = ""
        self.feedback_claude_code = ""

    # def default_judge(self):
    #     self.judge()

    def judge(self):     
        self.aj_memory_gpt = []
        self.aj_memory_claude = []
        print("###### Establishing Criteria ...")
        # 1. Establish Criteria
        # Input: initial_instruction, task, purpose, Q, A
        #<GPT4o>
        with open("prompts/AJ_criteria_establishment.txt", mode="r", encoding="utf-8") as file:
            establishment_prompt_template = file.read()
        establishment_prompt_gpt = establishment_prompt_template.format(
            basic_criteria = self.basic_criteria, initial_instruction= self.initial_instruction, Q=self.questions, A=self.answers, tasks = self.gpt_task, purpose= self.gpt_purpose,\
            audience = self.gpt_audience
        )
        self.memory['10_asking_autojudge_to_establish_criteria(gpt4o)'] = establishment_prompt_gpt
        self.memory['11_criteria(gpt4o)']=self.aj_gpt.run(establishment_prompt_gpt, [], self.aj_memory_gpt)
        self.aj_memory_gpt.append({"role": "user","content": establishment_prompt_gpt})
        self.aj_memory_gpt.append({"role": "assistant","content": self.memory['11_criteria(gpt4o)']})

        if not self.run_only_gpt:
            #<Claude>
            establishment_prompt_claude = establishment_prompt_template.format(
                basic_criteria = self.basic_criteria, initial_instruction=self.initial_instruction, Q=self.questions, A=self.answers, tasks=self.claude_task, purpose=self.claude_purpose, \
                audience = self.claude_audience
            )
            self.memory['10_asking_autojudge_to_establish_criteria(claude)'] = establishment_prompt_claude
            self.memory['11_criteria(claude)'] = self.aj_claude.run(establishment_prompt_claude, [], self.aj_memory_claude)
            self.aj_memory_claude.append({"role": "user","content": establishment_prompt_claude})
            self.aj_memory_claude.append({"role": "assistant","content": self.memory['11_criteria(claude)']})

        print("###### Creating Evaluation Questions ...")
        # 2. Create Evaluation Questions
        # Input: image, task, purpose, criteria
        #<GPT4o>
        with open("prompts/AJ_create_eval_q.txt", mode="r", encoding="utf-8") as file:
            question_generation_prompt_template = file.read()
        question_generation_prompt_gpt = question_generation_prompt_template.format(
            task=self.gpt_task, purpose=self.gpt_purpose, criteria=self.memory['11_criteria(gpt4o)'], audience=self.gpt_audience
            )
        self.memory['12_asking_autojudge_to_create_eval_questions(gpt4o)'] = question_generation_prompt_gpt
        self.memory['13_evaluation_questions(gpt4o)'] = self.aj_gpt.run(question_generation_prompt_gpt, [], self.aj_memory_gpt)
        self.aj_memory_gpt.append({"role": "user","content": question_generation_prompt_gpt})
        self.aj_memory_gpt.append({"role": "assistant","content": self.memory['13_evaluation_questions(gpt4o)']})

        #<Claude>
        question_generation_prompt_claude = question_generation_prompt_template.format(
            task=self.claude_task, purpose=self.claude_purpose, criteria=self.memory['11_criteria(claude)'], audience=self.claude_audience
            )
        self.memory['12_asking_autojudge_to_create_eval_questions(claude)'] = question_generation_prompt_claude
        self.memory['13_evaluation_questions(claude)'] = self.aj_claude.run(question_generation_prompt_claude, [], self.aj_memory_claude)
        self.aj_memory_claude.append({"role": "user","content": question_generation_prompt_claude})
        self.aj_memory_claude.append({"role": "assistant","content": self.memory['13_evaluation_questions(claude)']})
        print("###### Evaluating ...")
        # 3. Evaluate
        # Input: questions, Image
        #<GPT4o>
        with open("prompts/AJ_execute_eval.txt", mode="r", encoding="utf-8") as file:
            evaluation_prompt_template = file.read()
        evaluation_prompt_gpt = evaluation_prompt_template.format(
            evaluation_questions = self.memory['13_evaluation_questions(gpt4o)'], initial_instruction=self.initial_instruction)
        self.memory['14_asking_autojudge_to_evaluate(gpt4o)'] = evaluation_prompt_gpt
        self.memory['15_evaluation_vfeedback(gpt4o)'] = self.aj_gpt.run(evaluation_prompt_gpt + "Handle this task based on the image provided.", self.rendered_img, self.aj_memory_gpt)
        self.aj_memory_gpt.append({"role":"user","content": evaluation_prompt_gpt})
        self.aj_memory_gpt.append({"role":"assistant","content":self.memory['15_evaluation_vfeedback(gpt4o)']})

        if not self.run_only_gpt:
            #<Claude>
            evaluation_prompt_claude = evaluation_prompt_template.format(
                evaluation_questions=self.memory['13_evaluation_questions(claude)'], initial_instruction=self.initial_instruction)
            self.memory['14_asking_autojudge_to_evaluate(claude)'] = evaluation_prompt_claude
            self.memory['15_evaluation_vfeedback(claude)'] = self.aj_claude.run(evaluation_prompt_claude + "Handle this task based on the image provided.", self.rendered_img, self.aj_memory_claude)
            self.aj_memory_claude.append({"role":"user","content": evaluation_prompt_claude})
            self.aj_memory_claude.append({"role":"assistant","content": self.memory['15_evaluation_vfeedback(claude)']})
        
    def semantic_decompose(self, data):
        task = {}
        with open('./prompts/purpose_self_reflection.json', 'r', encoding="utf-8") as file:
            tasks = json.load(file)
            task["Show External Context"] = tasks["Type"]["Recall"]["Subtype"]["External context"]["description"]
            task["Show Confirmation"] = tasks["Type"]["Recall"]["Subtype"]["Confirmation"]["description"]
            task["Show Contradiction"] = tasks["Type"]["Recall"]["Subtype"]["Contradiction"]["description"]
            task["Focus on Identifying value"] = tasks["Type"]["Detail"]["Subtype"]["Identify value"]["description"]
            task["Focus on Identifying extreme"] = tasks["Type"]["Detail"]["Subtype"]["Identify extreme"]["description"]
            task["Focus on Identifying references"] = tasks["Type"]["Detail"]["Subtype"]["Identify references"]["description"]
            task["Comparison by Time Segmentation"] = tasks["Type"]["Comparison"]["Subtype"]["By time segmentation"]["description"]
            task["Comparison by Multiple services"] = tasks["Type"]["Comparison"]["Subtype"]["Multiple services"]["description"]
            task["Comparison against external data"] = tasks["Type"]["Comparison"]["Subtype"]["Against external data"]["description"]
            task["Comparison By Factor"] = tasks["Type"]["Comparison"]["Subtype"]["By factor"]["description"]
            task["Comparison By Instances"] = tasks["Type"]["Comparison"]["Subtype"]["Instances"]["description"]
            task["Show Trend"] = tasks["Type"]["Trend"]["description"]
            task["Value judgement"] = tasks["Type"]["Value judgement"]["description"]
            task["Distribution with variability"] = tasks["Type"]["Distribution"]["Subtype"]["Variability"]["description"]
            task["Distribution By Category"] = tasks["Type"]["Distribution"]["Subtype"]["By category"]["description"]
            task["Correlation"] = tasks["Type"]["Correlation"]["description"]
            task["Outlier"] = tasks["Type"]["Outlier"]["description"]
            task["Summarization of data"] = tasks["Type"]["Data summary"]["description"]
            task["Prediction/Forecasting"] = tasks["Type"]["Prediction"]["description"]    
        # Ask ChartAgent about the Task, Purpose, and Audience
        query = {"Task": None, "Purpose": None, "Audience": None}
                
        with open("prompts/AJ_SD.txt", "r", encoding="utf-8") as file:
            semantics_decomposition_template = file.read()
        sd_gpt_prompt = semantics_decomposition_template.format(initial_instruction=self.initial_instruction, data=data, task=task, query=query)
        self.memory['05_ask_for_Task_Purpose_Audience(gpt4o)'] = sd_gpt_prompt
        self.memory['04_response_w_attributes_task_purpose(gpt4o)']= self.aj_gpt.run(sd_gpt_prompt, [], self.aj_memory_gpt)
        
        if not self.run_only_gpt:
            sd_claude_prompt = semantics_decomposition_template.format(initial_instruction=self.initial_instruction, data=data, task=task, query=query)
            self.memory['05_ask_for_Task_Purpose_Audience(claude)'] = sd_claude_prompt
            self.memory['04_response_w_attributes_task_purpose(claude)'] = self.aj_claude.run(sd_claude_prompt, [], self.aj_memory_claude)
                
        # EXTRACT ONLY THE DICTIONARY VARIABLE PART FROM THE RESPONSE, EXCLUDING OTHER PARTS
        gpt_query_response = self.memory['04_response_w_attributes_task_purpose(gpt4o)']
        gpt_query_response = gpt_query_response[gpt_query_response.find("{") : gpt_query_response.rfind("}") + 1]

        gpt_query_response = gpt_query_response.replace("'", "\'")
        gpt_query_response = json.loads(gpt_query_response)
        self.memory['05_task(gpt4o)'] = gpt_query_response['Task']
        self.memory['05_purpose(gpt4o)'] = gpt_query_response['Purpose']
        self.memory['05_audience(gpt4o)'] = gpt_query_response['Audience']

        # EXTRACT ONLY THE DICTIONARY VARIABLE PART FROM THE RESPONSE, EXCLUDING OTHER PARTS
        if not self.run_only_gpt:
            claude_query_response = self.memory['04_response_w_attributes_task_purpose(claude)']
            claude_query_response = claude_query_response[claude_query_response.find("{") : claude_query_response.rfind("}") + 1]

            claude_query_response = claude_query_response.replace("'", "\'")
            claude_query_response = json.loads(claude_query_response)
            self.memory['05_task(claude)'] = claude_query_response['Task']
            self.memory['05_purpose(claude)'] = claude_query_response['Purpose']
            self.memory['05_audience(claude)'] = claude_query_response['Audience']

    def feedback(self, additional_tag:str = ""):
        # if aj_memory_gpt and aj_memory_claude are not empty and have more than 6 elements, initialize them with their first 6 indices
        self.aj_memory_gpt = self.aj_memory_gpt[:6]
        self.aj_memory_claude = self.aj_memory_claude[:6]
        
        print("###### Parsing Visual Feedback ...")
        # Feedback parsing
        self.feedback_gpt = self.memory['15_evaluation_vfeedback(gpt4o)']
        if not self.run_only_gpt:
            self.feedback_claude = self.memory['15_evaluation_vfeedback(claude)']

        # Extract the feedback from the ```json``` block
        self.feedback_gpt = self.feedback_gpt[self.feedback_gpt.find("```json") + 7 : self.feedback_gpt.rfind("```")].strip()
        if not self.run_only_gpt:
            self.feedback_claude = self.feedback_claude[self.feedback_claude.find("```json") + 7 : self.feedback_claude.rfind("```")].strip()

        self.feedback_gpt = json.loads(self.feedback_gpt)
        if not self.run_only_gpt:
            self.feedback_claude = json.loads(self.feedback_claude)

        # save each of them to prompts/feedbacks
        if additional_tag != "":
            with open(f"feedbacks/feedback_gpt_visual_{additional_tag}.json", "w", encoding="utf-8") as file:
                json.dump(self.feedback_gpt, file, indent=4)
            if not self.run_only_gpt:
                with open(f"feedbacks/feedback_claude_visual_{additional_tag}.json", "w", encoding="utf-8") as file:
                    json.dump(self.feedback_claude, file, indent=4)
        else:
            with open("feedbacks/feedback_gpt_visual.json", "w", encoding="utf-8") as file:
                json.dump(self.feedback_gpt, file, indent=4)
            if not self.run_only_gpt:
                with open("feedbacks/feedback_claude_visual.json", "w", encoding="utf-8") as file:
                    json.dump(self.feedback_claude, file, indent=4)

        #FILTER the feedback into KEEP, MODIFY, DISCARD, ADD
        #<GPT4o>
        self.feedback_gpt_classified = {
            "RETAIN" : [],
            "EDIT" : [],
            "DISCARD" : [],
            "ADD" : []
        }
        for evaluation in self.feedback_gpt['evaluation']:
            for feedback_cell in evaluation['feedback']:
                self.feedback_gpt_classified[feedback_cell['tag']].append(feedback_cell['improvement'])

        if not self.run_only_gpt:
            #<Claude>
            self.feedback_claude_classified = {
                "RETAIN" : [],
                "EDIT" : [],
                "DISCARD" : [],
                "ADD" : []
            }
            for evaluation in self.feedback_claude['evaluation']:
                for feedback_cell in evaluation['feedback']:
                    self.feedback_claude_classified[feedback_cell['tag']].append(feedback_cell['improvement'])

        print("###### Generating Code Feedback ...")
        # 4. Generate Feedback
        # Input: evaluation_vfeedback, code
        #<GPT4o>
        with open("prompts/AJ_generate_feedback.txt", mode="r", encoding="utf-8") as file:
            feedback_generation_prompt_template = file.read()
        feedback_generation_prompt_gpt = feedback_generation_prompt_template.format(
            initial_instruction=self.initial_instruction, code=self.code, attributes=self.data_attributes,
            retain=self.feedback_gpt_classified["RETAIN"], discard=self.feedback_gpt_classified["DISCARD"], edit=self.feedback_gpt_classified["EDIT"], add=self.feedback_gpt_classified["ADD"]
            )

        self.memory['16_asking_autojudge_to_generate_feedback(gpt4o)'] = feedback_generation_prompt_gpt
        self.memory['17_feedback(gpt4o)'] = self.aj_gpt.run(feedback_generation_prompt_gpt, self.rendered_img, self.aj_memory_gpt)
        self.aj_memory_gpt.append({"role":"user","content": feedback_generation_prompt_gpt})
        self.aj_memory_gpt.append({"role":"assistant","content": self.memory['17_feedback(gpt4o)']})

        if not self.run_only_gpt:
            #<Claude>
            feedback_generation_prompt_claude = feedback_generation_prompt_template.format(
                initial_instruction=self.initial_instruction, code=self.code, attributes=self.data_attributes,
                retain=self.feedback_claude_classified["RETAIN"], discard=self.feedback_claude_classified["DISCARD"], edit=self.feedback_claude_classified["EDIT"], add=self.feedback_claude_classified["ADD"]
                )
            self.memory['16_asking_autojudge_to_generate_feedback(claude)'] = feedback_generation_prompt_claude
            self.memory['17_feedback(claude)'] = self.aj_claude.run(feedback_generation_prompt_claude, self.rendered_img, self.aj_memory_claude)
            self.aj_memory_claude.append({"role":"user","content": feedback_generation_prompt_claude})
            self.aj_memory_claude.append({"role":"assistant","content": self.memory['17_feedback(claude)']})

    def feedback_parse(self, additional_tag: str = ""):
        self.aj_memory_gpt = self.aj_memory_gpt[:8]
        self.aj_memory_claude = self.aj_memory_claude[:8]

        print("###### Parsing Code Feedback ...")
        # Feedback parsing
        self.feedback_gpt = self.memory['17_feedback(gpt4o)']
        if not self.run_only_gpt:
            self.feedback_claude = self.memory['17_feedback(claude)']

        # Extract the feedback from the ```json``` block
        self.feedback_gpt = self.feedback_gpt[self.feedback_gpt.find("```json") + 7 : self.feedback_gpt.rfind("```")].strip()
        if not self.run_only_gpt:
            self.feedback_claude = self.feedback_claude[self.feedback_claude.find("```json") + 7 : self.feedback_claude.rfind("```")].strip()
        else:
            self.feedback_claude = ""

        #remove useless comments
        pattern = r'//.*?(?=\n|$)'
        self.feedback_gpt = re.sub(pattern, '', self.feedback_gpt)
        self.feedback_claude = re.sub(pattern, '', self.feedback_claude)

        self.feedback_gpt = json.loads(self.feedback_gpt)
        if not self.run_only_gpt:
            self.feedback_claude = json.loads(self.feedback_claude)
        else:
            self.feedback_claude = {}

        # save each of them to prompts/feedbacks
        with open("feedbacks/feedback_gpt_code.json", "w", encoding="utf-8") as file:
            json.dump(self.feedback_gpt, file, indent=4)
        if not self.run_only_gpt:
            with open("feedbacks/feedback_claude_code.json", "w", encoding="utf-8") as file:
                json.dump(self.feedback_claude, file, indent=4)

        # Initialize self.feedback_gpt_code as an empty string
        self.feedback_gpt_code = ""
        if not self.run_only_gpt:
            self.feedback_claude_code = ""

        for feedback in self.feedback_gpt["code feedback"]:
            #if feedback['before'] key exists, then make a modification
            if feedback.get('before') is None or feedback['before']==[]:
                self.feedback_gpt_code += f"{feedback['explanation']}\n---\n*Please add [{feedback['after']}\n\n"
            else:
                self.feedback_gpt_code += f"{feedback['explanation']}\n---\n*Please change [{feedback['before']}] to [{feedback['after']}\n\n"
        self.feedback_gpt_code = self.feedback_gpt_code.strip()

        
        if not self.run_only_gpt:
            for feedback in self.feedback_claude["code feedback"]:
                #if feedback['before'] key exists, then make a modification
                if feedback.get('before') is None:
                    self.feedback_claude_code += f"{feedback['explanation']}\n---\n*Please add [{feedback['after']}\n\n"
                else:
                    self.feedback_claude_code += f"{feedback['explanation']}\n---\n*Please change [{feedback['before']}] to [{feedback['after']}\n\n"
            self.feedback_claude_code = self.feedback_claude_code.strip()
        else:
            self.feedback_claude_code = ""
        # save memory in AJ.json
        # if additional_tag == "":
        #     with open("prompts/AJ.json", "w", encoding="utf-8") as file:
        #         json.dump(self.memory, file, indent=4)
        # else:
        #     with open(f"prompts/AJ_{additional_tag}.json", "w", encoding="utf-8") as file:
        #         json.dump(self.memory, file, indent=4)            
        return self.memory, self.feedback_gpt_classified, self.feedback_claude_classified, self.feedback_gpt_code, self.feedback_claude_code