<h1 align="center">
  <img src="https://readme-typing-svg.demolab.com?font=Chakra+Petch&weight=600&size=38&duration=1&pause=1000&color=000000&background=CCFF00&center=true&vCenter=true&repeat=false&width=1200&lines=Klaudia+%E2%80%94+End-to-End+Agentic+Finance+AI+Platform" alt="Title" />
</h1>

<div align="center">
  <img src="https://github.com/Laoode/agentic-data-entry/blob/development/docs/Klaudia-Cozy-Workspace.png" alt="Klaudia Workspace">
</div>

<p align="center">
  <b>Zero Error is the Baseline. Absolute Balance is the Goal.</b>
</p>

<p align="center">
  <img src="https://readme-typing-svg.demolab.com?font=Chakra+Petch&pause=1800&color=CCFF00&center=true&vCenter=true&width=1000&lines=Multi-Agent+Finance+Accountant+AI;Receipt+Extraction+to+Spreadsheet+Automation;LangGraph+%2B+MCP+%2B+LLMOps+Architecture;Fine-Tuned+Qwen+3.5+for+Financial+Documents;Built+for+Production-Ready+Financial+Workflows" />
</p>

<p align="center">
  <img src="https://img.shields.io/badge/FastAPI-Backend-green" />
  <img src="https://img.shields.io/badge/LangGraph-Agentic%20Workflow-blue" />
  <img src="https://img.shields.io/badge/LangChain-Orchestration-blueviolet" />
  <img src="https://img.shields.io/badge/Qwen3.5-4B-orange" />
  <img src="https://img.shields.io/badge/Gemini3.5-flash-red" />
  <img src="https://img.shields.io/badge/MCP-Protocol-black" />
  <img src="https://img.shields.io/badge/Redis-Queue-red" />
  <img src="https://img.shields.io/badge/Taskiq-Workers-yellow" />
  <img src="https://img.shields.io/badge/vLLM-Model%20Serving-1f4b99" />
  <img src="https://img.shields.io/badge/Vertex%20AI-Google%20Cloud-4285F4" />
  <img src="https://img.shields.io/badge/SQLite-Database-lightblue" />
  <img src="https://img.shields.io/badge/Google%20Sheets-Automation-green" />
  <img src="https://img.shields.io/badge/MinIO-Object%20Storage-darkred" />
  <img src="https://img.shields.io/badge/Langfuse-Observability-purple" />
  <img src="https://img.shields.io/badge/React%20Native-Mobile%20App-cyan" />
  <img src="https://img.shields.io/badge/Expo-Cross%20Platform-black" />
  <img src="https://img.shields.io/badge/Docker-OrbStack-blue" />
</p>

---

## 🏵 Overview

Klaudia is an end-to-end agentic finance accountant AI platform designed to automate financial document processing, receipt extraction, data entry operations, and spreadsheet workflows.

Unlike traditional OCR systems, Klaudia combines document intelligence, multi-agent orchestration, human-in-the-loop validation, and production-grade LLMOps into a single architecture.

### Core Capabilities

- Receipt & invoice extraction
- Multi-page PDF processing
- Human-in-the-loop correction workflow
- Google Sheets automation
- SQLite financial document registry
- LangGraph multi-agent orchestration
- MCP-based tool execution boundary
- Fine-tuned Qwen 3.5 financial document understanding
- Async document processing pipeline
- Langfuse observability & tracing
- Mobile-first conversational interface

---

## 🐸 System Architecture

<div align="center">
  <img src="https://github.com/Laoode/agentic-data-entry/blob/development/docs/LLMOps.png" alt="LLM Ops Pipeline">
</div>

### Agentic Flow

```text
User
 │
 ▼
Guardrails
 │
 ▼
Extraction Agent
 │
 ▼
Supervisor Agent (Klaudia)
 │
 ├── SQL Agent
 │      ▼
 │   MCP SQLite
 │
 └── Data Entry Team
        ▼
    MCP Google Sheets

````

---

## 🐝 Training Pipeline

<div align="center">
  <img src="https://github.com/Laoode/agentic-data-entry/blob/development/docs/FineTuning.png" alt="Fine Tuning Pipeline">
</div>

### Fine-Tuning Strategy

* Base Model: Qwen 3.5 4B
* PEFT LoRA Fine-Tuning
* Hyperparameter Search
* Experiment Tracking with Weights & Biases
* KIEVal Evaluation Suite
* ANLS*, Digit Accuracy, and JSON Validity Assessment

---

## 🍀ྀི Benchmark Results

The Klaudia model (Qwen 3.5 4B fine-tuned on our financial receipt dataset) was evaluated using KIEVal, ANLS*, Digit Accuracy, and JSON Validity benchmarks.

Across all evaluation metrics, Klaudia consistently outperformed the base Qwen 3.5 and Gemma 4 models, demonstrating superior entity extraction, document structure understanding, numerical accuracy, and reduced human correction effort.

<div align="center">
  <img src="https://github.com/Laoode/agentic-data-entry/blob/development/docs/Benchmarks.png" alt="Benchmark Results">
</div>

### Evaluation Summary

| Model | Entity F1 | Group F1 | Aligned | ANLS* | Digit Accuracy | JSON Validity |
|--------|----------:|----------:|----------:|----------:|----------:|----------:|
| Gemma 4 E2B-it | 49.29 | 11.04 | 39.72 | 36.22 | 50.83 | 99 |
| Gemma 4 E4B-it | 58.61 | 18.46 | 51.17 | 73.49 | 60.38 | 100 |
| Qwen 3.5 2B | 58.88 | 18.40 | 50.36 | 68.96 | 71.15 | 98 |
| Qwen 3.5 4B | 69.93 | 28.17 | 63.05 | 77.22 | 77.87 | 100 |
| **Klaudia (Qwen 3.5 4B Fine-Tuned)** | **87.30** | **70.26** | **84.82** | **93.38** | **93.78** | **100** |

### Key Improvements Over Base Qwen 3.5 4B

- **+17.37%** KIEVal Entity F1
- **+41.99%** KIEVal Group F1
- **+21.77%** KIEVal Aligned
- **+16.16%** ANLS*
- **+15.91%** Digit Accuracy
- Maintained **100% JSON Validity**

---

## 🎞️ Dataset & Models

> [!WARNING]
> The dataset and fine-tuned model will be released after the research paper is published. They are currently archived in a private Oxen.ai repository.

<div align="center">
  <img src="https://github.com/Laoode/agentic-data-entry/blob/development/docs/DatasetsModel.png" alt="Datasets and Models">
</div>

### Dataset Sources

* Hugging Face
* Kaggle
* Roboflow
* Pinterest
* X (Twitter)
* Custom Collected Receipts
* Human Verified Labels

---

## 🏞️ Mobile Application

<div align="center">
  <img src="https://github.com/Laoode/agentic-data-entry/blob/development/docs/UIApp.png" alt="Mobile Application">
</div>

### Mobile Stack

* React Native
* Expo
* TypeScript
* Session Management
* Conversational Finance Assistant
* Receipt Upload Workflow
* Spreadsheet Operations

---

## 🍏 Tech Stack

| Layer                   | Technologies         |
| ----------------------- | -------------------- |
| Backend                 | FastAPI              |
| Agent Framework         | LangGraph            |
| LLM Framework           | LangChain            |
| Models                  | Gemini 3.5, Qwen 3.5 |
| Fine-Tuning             | LoRA, PEFT           |
| Inference               | vLLM                 |
| Queue                   | Redis, Taskiq        |
| Storage                 | SQLite, MinIO        |
| Tool Layer              | MCP                  |
| Spreadsheet Integration | Google Sheets        |
| Observability           | Langfuse             |
| Containerization        | Docker, OrbStack     |
| Frontend                | React Native, Expo   |
| Experiment Tracking     | Weights & Biases     |

---

## 🪲 Key Features

### Financial Document Intelligence

* Receipt Extraction
* Invoice Extraction
* OCR + KIE Pipeline
* Multi-page PDF Support
* Structured JSON Generation

### Agentic AI System

* Supervisor Architecture
* Multi-Agent Collaboration
* MCP Tool Execution
* Human-in-the-Loop Workflow
* Session-Aware Context Management

### Production Infrastructure

* Async Processing
* Queue-Based Execution
* Observability & Tracing
* Object Storage
* Deduplication Pipeline
* Fault-Tolerant Processing

---

## 🗂️ Repository Structure

```text
app/
├── routes/
├── services/
├── extraction/
├── guardrails/
└── core/

klaudia/
├── supervisor/
├── sql_agent/
├── data_entry_team/
└── tools/

mcp-sqlite/
mcp-gsheets/

docs/
tests/
sample-data/
```

---

## 🍀 Mission

> Where financial records lose balance, Klaudia restores order.

Klaudia is designed around a simple philosophy:

**Inputting financial data is not merely typing numbers. It is preserving the financial truth of an organization.**

---

## 📗 Research

This project is part of an undergraduate research thesis focused on:

* Agentic AI Systems
* Financial Document Intelligence
* LLMOps Pipelines
* Human-in-the-Loop Data Entry Automation
* Domain Adaptation for Financial OCR

Dataset and model release will follow publication.

---

## 🔰 Author

**Yudhy Prayitno**

Building agentic systems for real-world financial automation.