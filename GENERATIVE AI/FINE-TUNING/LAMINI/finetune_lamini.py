Doc= "https://docs.lamini.ai/inference/quick_start/"

def get_data():
    data = [
        {"input": "What is Google ADK?", 
         "output": "Google Agent Development Kit (ADK) is a framework for building, testing, and deploying AI agents using Google's ecosystem."},

        {"input": "Explain the purpose of ADK Agents.", 
         "output": "ADK Agents automate workflows by connecting LLMs with tools, APIs, and contextual memory."},

        {"input": "How do you create a new ADK Agent?", 
         "output": "Use the ADK CLI command `adk create agent <name>` to scaffold a new agent with default configuration."},

        {"input": "What file defines an agent's behavior in ADK?", 
         "output": "The `agent.yaml` file defines the agent’s personality, tools, goals, and memory configuration."},

        {"input": "Describe the role of 'memory' in Google ADK agents.", 
         "output": "Memory stores conversation history and context, enabling agents to maintain continuity across sessions."},

        {"input": "What is a 'tool' in ADK?", 
         "output": "A tool in ADK is an external API, function, or service that agents can call to perform real actions or retrieve data."},

        {"input": "Example of connecting ADK to a REST API.", 
         "output": "You can register an HTTP tool in `tools.yaml` using the endpoint URL and method type (GET, POST, etc.)."},

        {"input": "How can an agent trigger another agent in ADK?", 
         "output": "Agents can invoke other agents through inter-agent messaging defined in the orchestration layer."},

        {"input": "List benefits of using ADK over manual agent wiring.", 
         "output": "ADK provides modularity, reusability, monitoring, and integrated lifecycle management for AI agents."},

        {"input": "Explain 'prompt orchestration' in ADK.", 
         "output": "Prompt orchestration combines templates, context, and goals to produce optimized prompts for each task."},

        {"input": "What command is used to deploy ADK agents?", 
         "output": "Use `adk deploy` to push the agent configuration and code to the ADK runtime environment."},

        {"input": "How does ADK handle agent failures?", 
         "output": "ADK provides retry policies, logging, and fallback mechanisms in the runtime configuration."},

        {"input": "Differentiate between 'runtime' and 'sandbox' modes in ADK.", 
         "output": "'Sandbox' is for local testing, while 'runtime' is for deployed production agents."},

        {"input": "How do you fine-tune agent behavior in ADK?", 
         "output": "Adjust the prompt templates and system instructions in the `agent.yaml` to control response tone and depth."},

        {"input": "How to monitor agent performance in ADK?", 
         "output": "Use the ADK dashboard or API to track usage metrics, response latency, and success rates."},

        {"input": "Add a new tool named 'calendar' to ADK.", 
         "output": "Define the tool in `tools.yaml` with type `calendar`, specify API endpoints, and link it in the agent config."},

        {"input": "What is an 'intent handler' in ADK?", 
         "output": "Intent handlers process user inputs and route them to appropriate tools or sub-agents based on detected goals."},

        {"input": "How does ADK support multi-agent systems?", 
         "output": "ADK allows multiple agents to collaborate via message passing, shared memory, and task delegation."},

        {"input": "Can ADK integrate with LangChain?", 
         "output": "Yes, ADK can use LangChain components for retrieval, embeddings, and chain-based reasoning."},

        {"input": "What’s the typical folder structure of an ADK project?", 
         "output": "`agents/`, `tools/`, `memory/`, and `config/` folders contain core definitions and runtime scripts."}
    ]
    return data


import lamini
from lamini import Lamini

lamini.api_key="<LAMINI_API_KEY>"

llm=Lamini(model_name="meta-llama/Meta-Llama-3-8B-Instruct")

data=get_data()

llm.tune(data_or_dataset=data)

'''
The common hyperparameters you can tune when fine-tuning models on Lamini (or any LLM fine-tuning framework):

| **Parameter**                 | **Description**                                   | **Typical Range / Default**                   |
| ----------------------------- | ------------------------------------------------- | --------------------------------------------- |
| `learning_rate`               | Step size for gradient updates during fine-tuning | `1e-6` → `5e-5`                               |
| `batch_size`                  | Number of samples per gradient step               | `4`, `8`, `16`                                |
| `num_epochs`                  | Number of passes over entire dataset              | `3` → `10`                                    |
| `max_steps`                   | Total number of training steps (overrides epochs) | `200` → `20,000`                              |
| `warmup_ratio`                | % of steps to linearly increase LR before decay   | `0.03` → `0.1`                                |
| `weight_decay`                | Regularization to prevent overfitting             | `0.01`                                        |
| `max_seq_length`              | Max token length per sample                       | `512`, `1024`, `2048`                         |
| `gradient_accumulation_steps` | Virtual batch size increase                       | `1` → `8`                                     |
| `lr_scheduler_type`           | Learning rate decay strategy                      | `linear`, `cosine`, `constant`                |
| `optimizer` / `optim`         | Optimization algorithm used for training          | `adamw_torch`, `adamw_hf`, `adafactor`, `sgd` |
| `logging_steps`               | Steps between logging metrics                     | `10` → `100`                                  |
| `save_steps`                  | Steps between checkpoint saves                    | `500` → `1000`                                |
| `eval_steps`                  | Steps between evaluations                         | `100` → `500`                                 |
| `early_stopping_patience`     | Stop when eval loss stops improving               | `2` → `3` epochs                              |
| `dropout_rate`                | Random deactivation rate in layers                | `0.1` → `0.3`                                 |
| `fp16`                        | Use mixed precision training (saves memory)       | `True` / `False`                              |
'''

llm.tune(data_or_dataset_id=data,
         finetune_args={
             'learning_rate':1.0e-4
         })