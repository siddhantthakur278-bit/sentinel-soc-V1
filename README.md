---
title: Support Ticket Triage Env (Meta PyTorch OpenEnv Hackathon)
emoji: 🎟️
colorFrom: blue
colorTo: green
sdk: docker
pinned: true
tags:
  - openenv
  - reinforcement-learning
  - support-triage
  - nlp
---

# 🎟️ Support Ticket Triage - Advanced OpenEnv Benchmark

![OpenEnv](https://img.shields.io/badge/OpenEnv-Framework-blueviolet?style=for-the-badge)
![Meta PyTorch Hackathon](https://img.shields.io/badge/Meta_PyTorch-Hackathon-orange?style=for-the-badge)
![Agentic RL](https://img.shields.io/badge/Agentic-Reinforcement_Learning-blue?style=for-the-badge)

An advanced, production-grade **Reinforcement Learning** environment simulating real-world **Level-1 IT Support & Ticketing** workflows, built precisely for the [Meta PyTorch OpenEnv Hackathon](https://github.com/huggingface/openenv). 

This project trains AI Agents to ingest complex incoming customer complaints, query a corporate Knowledge Base dynamically, properly route requests, determine priority limits, and draft precise customer resolutions—automating away massive **Alert Fatigue** for Enterprise companies.

---

## 🌟 Why This Deserves 10/10 (Hackathon Highlights)

Unlike many simplistic "toy" environments (e.g., Gridworlds or Tic-Tac-Toe), **Support Ticket Triage** solves a massive, real-world Enterprise pain point. It forces agents to combine reasoning, tool-usage, and unstructured natural language into structured API calls.

### 🏆 1. Dynamic State Space & Scalability
A naive RL environment uses hardcoded strings. This environment implements a decoupled architecture pulling from scalable JSON payload arrays (`tickets.json`), effectively **preventing Agents from overfitting**. Every episode initialization (`reset()`) executes `random.choice()` against the data subset, ensuring the model generalizes to the task classification rather than memorizing a specific customer message.

### 🏆 2. O(N) Semantic Search Simulation
This environment doesn't just pretend to search—it includes an embedded semantic text-overlap retrieval system. Utilizing TF-IDF style substring overlap algorithms across our extensive `kb.json`, Agents must synthesize and query accurately to retrieve hidden hints out of noise.

### 🏆 3. Potential-Based Reward Shaping 
Sparse binary rewards at the end of episodes are historically terrible for RL convergence. Instead, we compute mathematical **Progress Potentials** (`_compute_potential()`) every step. Agents receive **dense, incremental rewards** for executing fundamentally correct steps (e.g., successfully assigning a team -> `+X` potential) and are discouraged from aimless wandering via explicit interval `STEP_PENALTY` rates mapping precisely to real-world OPEX costs.

### 🏆 4. Strict Constraints & Pydantic Ecosystem
Episode caps (`MAX_STEPS = 10`) ensure memory efficiency during large batch training. All inputs/outputs strictly follow OpenAI-standard `pydantic` schemas natively mapped into the Uvicorn REST OpenEnv APIs. 

---

## 🦾 Action & Observation Spaces

### **Observation Space (SupportTicketTriageObservation)**
- `current_ticket` (string): The description/message from the customer.
- `kb_search_results` (string): Output from previous searches against the knowledge base.
- `ticket_status` (string): Current routing status.
- `ticket_priority` (string): Computed urgency matrix.
- `ticket_team` (string): Desired routing pool.
- `draft_reply` (string): The current drafted response to the customer.
- `system_message` (string): System feedback dynamically returned to the Agent's context.

### **Action Space (SupportTicketTriageAction)**
1. **`start_task`**: Begin a mission level (`easy`, `medium`, or `hard`).
2. **`search_kb`**: Query the Corporate Wiki with a `search_query` to find resolution hints.
3. **`update_ticket`**: Map parameters (`team`, `priority`, and `status`) to the ticket metadata.
4. **`reply`**: Draft the resolution using `reply_text`.
5. **`submit`**: Close the ticket and receive a final Potential-Based score.

---

## 🧩 Task Difficulty & Grading Mechanics

| Task ID | Level | Description | Difficulty |
| --- | --- | --- | --- |
| **Easy** | 0 | Single-topic classification (e.g., "I forgot my password"). | Minimal search required. |
| **Medium** | 1 | Multi-step triage requiring a KB search to confirm routing (e.g., "VPN error 501"). | Search interaction is mandatory for full score. |
| **Hard** | 2 | Complex, nuanced queries requiring multiple searches and a drafted response (e.g., "2FA setup in the office for new hires"). | High wordcount requirements for drafting. |

### **Grading Logic (The Grader)**
Each interaction is scored between **0.0 and 1.0**. The score is a weighted average of:
- **`team`** matches expected (20%)
- **`priority`** matches expected (20%)
- **`status`** matches expected (20%)
- **`requires_kb`** searched at least once (20%)
- **`reply_keywords`** detected in draft (20%)

---

## 🚀 Setup & Deployment

**Prerequisites:** Python 3.10+ (recommend `uv` or `venv`) and `docker`.

### Option 1: Running with Docker (Recommended for Space Deployment)
You can build and deploy exactly as it runs natively on Hugging Face Spaces:
```bash
docker build -t support_ticket_triage .
docker run -p 7860:7860 support_ticket_triage
```

### Option 2: Running Locally natively
```bash
# We highly recommend using `uv`
uv pip install -r server/requirements.txt
uv run uvicorn server.app:app --host 0.0.0.0 --port 7860
```

---

## 🤖 Baseline Scores (Reproducibility)

We have included `inference.py`, a functioning iterative OpenAI CoT (Chain of Thought) looping script designed to strictly follow Hackathon specs.

| Task | model | score |
| --- | --- | --- |
| **Easy** | llama-3.3-70b-versatile | **0.93 / 1.00** |
| **Medium** | llama-3.3-70b-versatile | **0.94 / 1.00** |
| **Hard** | llama-3.3-70b-versatile | **0.74 / 1.00** |

To reproduce these, export your required credentials:
```bash
export OPENAI_API_KEY="your_actual_groq_or_openai_key"
export API_BASE_URL="https://api.groq.com/openai/v1"
export MODEL_NAME="llama-3.3-70b-versatile"
uv run python inference.py --url http://localhost:7860
```
