# ChartAJ and ChartUIE-8K: Rich AI Feedback for Chart Generation

![ChartAJ and ChartUIE-8K](chartaj.png)

## Contents 
- [Project Site](#project-site)
- [Requirements](#requirements)
- [ChartUIE](#chartuie)
- [ChartAJ](#chartagent)

## Project Site

Demonstration of the pre and post feedback of our ChartAJ is provided in our site [our project site](https://chartaj.github.io/).

## Requirements

This project requires several Python packages to be installed. The dependencies are listed in the `requirements.txt` file. Follow the instructions below to set up the environment:

### Installation Instructions

1. **Clone the Repository**:

   ```bash
   git clone https://github.com/chartaj/ChartAJ-and-ChartUIE-8K.git
   cd ChartAJ-and-ChartUIE-8K

2. **Create a Virtual Environment**:
    You can create a virtual environment to avoid conflicts with other projects.

    Activate the virtual environment:

    ```bash
    python -m venv venv

3. **Install Dependencies**:

    Use pip to install the required packages listed in the requirements.txt file:

    ```bash
    pip install -r requirements.txt

4. **Updating Dependencies**:

    To update the dependencies in `requirements.txt`, you can manually add or modify the package versions. Alternatively, you can use the following command to generate an updated list based on your currently installed packages:

    ```bash
    pip freeze > requirements.txt
    ```

5. **API KEY**:

    For the full functionality of this project, you might need to set up API keys for certain services. We use `OpenAI`, `Anthropic`, `Groq`, and `Deepinfra` API providers.



## ChartUIE

The ChartUIE-8k (Chart User Instruction Emulator) data set can be found in the `ChartUIE_8K/UIE_data` folder. The dataset used to generate ChartUIE-8k is located in the `ChartUIE_8K/data` folder. It includes .csv and .json files from a range of categories, such as Business, Health, and more. The license for each data is attached as `{index}_info.yaml` for each data index.
<!-- 
## ChartAgent

ChartAgent is responsible for handling data-to-chart (d2c) generation tasks. We utilized two closed-source models (GPT-4o and Claude 3.5 Sonnet) and two open-source models (Llama 3.1 70B and Gemma 2 27B). The code for ChartAgent is in `ChartAgent.py`.

ChartAgent performs two d2c tasks in the workflow. The first task is the initial d2c generation, where it creates chart code based on the user’s query (including initial instructions and further instructions in a Q&A format). The second task is the post-feedback d2c generation, which incorporates feedback from ChartAJ. -->

## ChartAJ

ChartAJ provides automated, rich feedback on the initial chart. We use GPT-4o and Claude 3.5 Sonnet as the models for ChartAJ. The code for ChartAJ is in `autojudge.py`, and the overall workflow can be run in the `main.ipynb` file.[here]

The feedback process follows three key steps:

1. Criteria Establishment: Specific criteria are set based on the chart’s task, purpose, and audience, derived semantically from the user query, along with general data visualization principles. We provide two prompts for this: `prompts/AJ_SD.txt` for TPA (Task, Purpose, Audience) derivation, and `prompts/AJ_criteria_establishment.txt` for establishing specialized criteria.

2. Criteria Binarization: The established criteria are transformed into multiple binary (Yes or No) questions for detailed scoring and feedback. We provide the prompts in `prompts/AJ_create_eval_q.txt`

3. Visual Evaluation and Code Feedback: The chart is assessed against the multiple binary evaluation questions, with each QA set categorized into four actions—RETAIN, EDIT, ADD, or DISCARD. These evaluations are then converted into actionable code feedback to refine the initial d2c code. We provide two prompts for this: `prompts/AJ_execute_eval.txt` for evaluation question assessment with an attached target chart plot, and `prompts/AJ_generate_feedback.txt` for generating code centric feedback.
