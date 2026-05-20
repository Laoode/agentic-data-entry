```markdown
# An End-to-End LLMOps Pipeline for Receipt Data Entry Automation — Klaudia Agentic AI

---

## 1. DATA ANNOTATION PIPELINE

### 1.1 Digital Data Sources
- HuggingFace
- Kaggle
- Roboflow
- Oxen.ai
- Pinterest

### 1.2 Image Selection
#### Sumber Data
| Dataset | Jumlah Total | Digunakan | Bahasa | Mata Uang |
|---|---|---|---|---|
| CORD-V2 | 999 | 50 | Indo, Eng | Rp |
| E-Receipt | 53 | 53 (full) | Indo, Eng | Rp, $ |
| Express Expense | 200 | 50 | Eng | € |
| Nanonets | 987 | 50 | Malay, Eng | RM |
| Roboflow | 1.746 | 50 | Indo, Malay, Eng | Rp, RM, €, $ |
| Pinterest | 502 | 502 (full) | Indo, Eng | Rp, €, $ |
| SROIE | 973 | 50 | Malay, Eng | RM |
| Unique Data | 20 | 20 (full) | Eng | € |
| **TOTAL** | **5.480** | **~825** | | |

#### Train/Test Split Strategy
- **Per-source split:** Setiap dataset berkontribusi 5% ke test set
- **Deterministic:** Sort gambar alphabetically → ambil N% terakhir sebagai test
- **Alasan:** Menghindari distribusi skew; setiap sumber terwakili di test

#### Naming Convention
Format: `{prefix}_{original_stem}.jpg`

| Prefix | Dataset |
|---|---|
| `cord_` | CORD-V2 |
| `erec_` | E-Receipt |
| `expr_` | Express Expense |
| `nano_` | Nanonets |
| `robo_` | Roboflow |
| `pint_` | Pinterest |
| `sroe_` | SROIE |
| `uniq_` | Unique Data |

Contoh: `pint_GAMBAR_0042.jpg`, `cord_GAMBAR_0001.jpg`

### 1.3 OCR Stage
- Input: Selected receipt images
- Process: Raw OCR extraction → produces `Image + Raw OCR` output
- Model: GLM-OCR 0.9b

### 1.4 Structured Extraction
- Model: **Gemini 3.1 Pro**
- Input: Image + Raw OCR text
- Rules: Scheme Rules applied
- Output: **JSON**

### 1.5 Human Correction Loop
- Platform: **Label Studio** (annotation & review UI)
- Approval: Human reviewer accepts ✓ or rejects ✗ extracted JSON
- Storage: **Oxen.ai** (versioned dataset storage)
- Sharing: **ShareGPT** (data sharing/export)

---

## 2. TRAINING PIPELINE

### 2.1 Fine-Tuning Framework
- Framework: **LLaMA-Factory** (Easy and Efficient LLM Fine-Tuning)
- Base Architecture: **GLM-OCR + LoRA**
  - Techniques: Adapter layers, Add & Norm, Feed Forward, Multi-Head Attention
  - PEFT Method: LoRA (Low-Rank Adaptation)
  - Additional: Prompt Tuning, DPO support

### 2.2 Experiment Tracking
- Tool: **MLflow**
- Metrics tracked:
  - `ANLS*` (Average Normalized Levenshtein Similarity)
  - `KIEval` (Key Information Extraction Evaluation)
  - `Digit Accuracy` (Normalize price value, Exatch Match)

### 2.3 Hyperparameter Tuning
- Method: Search Heuristic
- Rule of thumb: lora_rank = [8, 16, 32, 64], lora_alpha = r*2

### 2.4 Output
- Best Model selected → registered to **Model Registry**

---

## 3. INFERENCE PIPELINE

### 3.1 Containerization
- Runtime: **Docker**
- Services:
  - `Klaudia Server` — agentic orchestration layer
  - `GLM-OCR Server` — fine-tuned OCR inference model (running on vLLM)

### 3.2 Queue
- Async job queue between servers and API layer
- Tool: Redis
```
REST API
↓
Queue
↓
OCR worker

Ini menyelesaikan masalah:
- PDF multi page & multi docs
- High latency OCR
- blocking API

Queue membuat:
- API responsive
- OCR async
```

### 3.3 API Layer
- Interface: **REST API/Fast API**
- Input: `"Input the receipt..."` (user submits receipt)
- Output: `"Generated output..."` (output generated)

---

## 4. KLAUDIA PIPELINE (Agentic Orchestration)

### 4.1 Entry Point
- **User** submits unstructured receipt data

### 4.2 Guardrails Layer
- Validates and filters user input before routing to agents

### 4.3 Data Sources
- Unstructured Docs
- Single Source Database

### 4.4 Extraction Agent
- Extracts raw fields from receipt documents

### 4.5 Supervisor Agent
- Orchestrates all downstream agents
- Manages **Human in the Loop** checkpoint
- Routes tasks to specialized agents

### 4.6 Specialized Agents

| Agent | Responsibility |
|---|---|
| **SQL Agent** | Queries/writes structured database (SQLite) |
| **Read Agent** | Reads from data sources |
| **Write Agent** | Writes processed records |
| **Sheet Agent** | Interfaces with Google Sheets via MCP |
| **Data Entry Team** | Coordinates multi-agent data entry tasks |

### 4.7 MCP Server Integrations
- **MCP Server (top)** — connected to SQL Agent + SQLite
- **MCP Server (bottom)** — connected to Sheet Agent + Google Sheets

### 4.8 Human in the Loop
- Supervisor Agent has a dedicated human review checkpoint before finalizing writes

---

## 5. OBSERVABILITY & STORAGE

### 5.1 Observability Agents
- Tool: **Lanfuse** (LLM observability & tracing)
- Monitors agent calls, latency, token usage, errors

### 5.2 Model Registry
- Stores versioned fine-tuned models
- Tools: HuggingFace 🤗 + vLLM

### 5.3 Object Storage
- Tool: **MinIO**
- Stores raw images, OCR outputs, model artifacts

---

## 6. SYSTEM FLOW SUMMARY

```
[User Input: Receipt Image]
        ↓
[Data Annotation Pipeline: GLM-OCR → Gemini 3.1 Pro → JSON → Human Correction]
        ↓
[Training Pipeline: LLaMA-Factory + GLM-OCR+LoRA → Best Model]
        ↓
[Model Registry → Inference Pipeline: Docker (Klaudia + GLM-OCR Servers) → Queue → REST API]
        ↓
[Klaudia Agentic Pipeline: User → Guardrails → Extraction Agent → Supervisor Agent]
        ↓
[Supervisor routes to: SQL Agent / Read Agent / Write Agent / Sheet Agent]
        ↓
[MCP Servers → SQLite / Google Sheets]
        ↓
[Observability: Lanfuse | Storage: MinIO]
        ↓
[Output: Structured Receipt Data]
```

---

## 7. KEY TECHNOLOGY STACK

| Category | Tools |
|---|---|
| Data Sources | HuggingFace, Kaggle, Roboflow, Oxen.ai, Pinterest |
| OCR & Extraction | GLM-OCR 0.9b, Gemini 3.1 Pro |
| Annotation | Label Studio, ShareGPT |
| Fine-Tuning | LLaMA-Factory, GLM-OCR, LoRA |
| Experiment Tracking | MLflow |
| Serving | Docker, Fast API |
| Orchestration | Klaudia Server (custom agentic framework) |
| Agent Tools | MCP Server, SQLite, Google Sheets |
| Observability | Lanfuse |
| Model Registry | HuggingFace, vLLM |
| Object Storage | MinIO |
```