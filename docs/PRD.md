# 📄 PRODUCT REQUIREMENT DOCUMENT
## Agentic Receipt Processing & Finance Accountant Data Entry

```
Version: 1.2
Audience: Senior AI Engineer / Senior Software Engineer
Status: Implementation-ready
Last Updated: 2026-06-05
```

## 1. PRODUCT OVERVIEW

### 1.1 Objective
Membangun sistem AI-assisted finance accountant data entry dengan fitur upload receipt/struk pembelian menjadi structured extraction, yang:
- Mendukung multi-page PDF / image
- Menggunakan single source of truth (SQLite)
- Memungkinkan multi-turn conversational input
- Aman dari silent data corruption
- Terintegrasi dengan Google Sheets
- Menggunakan Langgraph Hierarchical Agent Teams pattern
- Menggunakan MCP (Model Context Protocol) sebagai boundary tool execution
- Conversational interface dengan persona "Klaudia"

### 1.2 User Interaction Modes

**Mode 1: Document Processing**
- User uploads PDF/image attachment
- System processes through: User → Guardrails → Extraction Agent → Supervisor (Klaudia)

**Mode 2: Conversational Chat**
- User sends text-only message
- System processes through: User → Guardrails → Supervisor (Klaudia)

---

## 2. CORE PRINCIPLES (NON-NEGOTIABLE)

### 2.1 Architectural Principles
- **Separation of Concerns**: Each component has single responsibility
- **Explicit State > Implicit Context**: State managed in database, not memory
- **Agent = Reasoning, Tool = Execution**: Agents decide, tools execute
- **No Raw SQL from LLM**: All database operations through MCP tools
- **Single Writer Principle**: One source writes to each resource
- **Deterministic Side Effects**: Predictable outcomes from operations
- **Human-in-the-Loop for Ambiguity**: Confirm before critical actions

---

## 3. INFRASTRUCTURE CONFIGURATION

### 3.1 LLM Model Assignment

| Component | Model | Endpoint | Purpose |
|-----------|-------|----------|---------|
| **Extraction Agent (KIE)** | `gemini-3-flash-preview` (default) or `Qwen/Qwen3.5-4B` (fine-tune, future) | Google Generative AI / vLLM | **Image → structured receipt JSON** |
| **Text OCR (optional)** | `Qwen/Qwen3.5-4B` base | vLLM endpoint | Plain-text recognition when `OCR_MODE=true` |
| **Supervisor Agent (Klaudia)** | `gemini-3-flash-preview` | Google Generative AI | Orchestration & conversation |
| **Guardrails Agent** | `gemini-3.1-flash-lite` | Google Generative AI | Input validation |
| **SQL Agent** | `gemini-3-flash-preview` | Google Generative AI | Database operations |
| **Data Entry Team** | `gemini-3-flash-preview` | Google Generative AI | Google Sheets operations |

#### KIE Routing Modes

Selected via env (`MOCK_KIE`, `OCR_MODE`, `KIE_MODEL`):

| `MOCK_KIE` | `OCR_MODE` | Pipeline                                                         | Use when            |
|------------|------------|------------------------------------------------------------------|---------------------|
| `true`     | (ignored)  | Content-keyed fixture from `sample-data/labels/`                 | Dev / tests offline |
| `false`    | `false`    | Image → `KIE_MODEL` (Gemini) → JSON (single multimodal call)     | Default production  |
| `false`    | `true`     | Image → Qwen3.5-4B (vLLM) text → `KIE_MODEL` → JSON (two-stage)  | After Qwen3.5-4B fine-tune ships or for redundancy testing |

The single seam is `app/services/extraction/infra/kie_client.py::KIEClient`.
IngestService + Taskiq workers never branch on mode themselves; they call
`extract_from_image(jpg_bytes)` and the client picks the path.

### 3.2 Environment Configuration

```bash
# Service Configuration
HOST=0.0.0.0
PORT=8000
SERVICE_NAME=Klaudia Chatbot
VERSION=1.0.0
DEBUG=true

# LLM Configuration (Google Gemini via native google-genai SDK | Vertex AI) 
LLM_MODEL=gemini-3-flash-preview
LLM_API_KEY=
LLM_TEMPERATURE=0.5
LLM_THINKING_LEVEL_ROUTING=minimal
LLM_THINKING_LEVEL_WORKER=minimal

# Vertex AI
GOOGLE_CLOUD_PROJECT=
GOOGLE_CLOUD_LOCATION=global
GOOGLE_GENAI_USE_VERTEXAI=True
GOOGLE_APPLICATION_CREDENTIALS=gcp_service_account.json

# OCR Configuration (vLLM endpoint - Qwen3.5-4B)
VLLM_BASE_URL=<your-vllm-endpoint>
AUTH_TOKEN=<your-vllm-auth-token>
VLLM_OCR_MODEL=Qwen/Qwen3.5-4B

# Database
SQLITE_DB=app_dev.db

# Logging
LOG_PATH=logs
```

### 3.3 Extraction Pipeline

**Architecture :**
```
PDF/Image → Qwen3.5-4B (vLLM) → Structured JSON (Direct)
```

#### **Implementation: Extraction Agent**

```python
EXTRACTION_SCHEMA = {
    "info": {
        "store_name": "",
        "store_location": "",
        "store_contacts": [
            {"type": "", "value": ""}
        ],
        "tax_id": "",
        "receipt_id": "",
        "payment_date": "",
        "payment_time": "",
        "time_unit": ""
    },
    "items": [
        {
            "item_name": "",
            "quantity": "",
            "unit_price": "",
            "discount_label": "",
            "discount_price": "",
            "tax_label": "",
            "total_price": ""
        }
    ],
    "payment": {
        "total_items": "",
        "currency": "",
        "subtotal_price": "",
        "discounts": [
            {"discount_name": "", "amount": ""}
        ],
        "taxes": [
            {"tax_name": "", "amount": ""}
        ],
        "additional_charges": [
            {"charge_name": "", "amount": ""}
        ],
        "grand_total": "",
        "rounding": "",
        "payment_method": "",
        "tendered": "",
        "change": ""
    }
}

---

## 4. AGENT HIERARCHY & FLOW

### 4.1 Conditional Routing Logic

```python
if user_message.has_attachment():
    route = "User → Guardrails → Extraction Agent → Supervisor"
else:
    route = "User → Guardrails → Supervisor"
```

### 4.2 Layer Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      USER REQUEST                           │
│                 (Text or PDF/Image)                         │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│              [1] FASTAPI ROUTE LAYER                        │
│  • app/routes/v1/chat.py                                    │
│  • Request validation (Pydantic)                            │
│  • Response formatting                                      │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│              [2] GUARDRAILS LAYER                           │
│  • Prompt injection detection (parallel)                    │
│  • Topic blacklist (parallel)                               │
│  ❌ REJECT → Return formatted response                      │
│  ✅ PASS → Continue to orchestrator                         │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│          [3] ORCHESTRATOR LAYER                             │
│  • Inject Klaudia persona                                   │
│  • Get conversation context                                 │
│  • Route to appropriate agent                               │
└─────────────────────────────────────────────────────────────┘
                            ↓
                   ┌────────┴────────┐
                   │                 │
        Has Attachment?         Text Only?
                   │                 │
                   ↓                 ↓
    ┌──────────────────────┐  ┌──────────────────────┐
    │ [4A] EXTRACTION      │  │ [4B] SUPERVISOR      │
    │      AGENT           │  │      AGENT           │
    │                      │  │                      │
    │ • Qwen3.5-4B (vLLM)     │ • Klaudia            │
    │ • Direct JSON output │  │ • Conversational AI  │
    │ • Schema validation  │  │ • Task routing       │
    └──────────────────────┘  └──────────────────────┘
                   │                 │
                   └────────┬────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│           [5] SUPERVISOR AGENT LAYER                        │
│  • LangGraph state management                               │
│  • Tool selection logic                                     │
│  • Sub-agent coordination                                   │
│  • LLM response generation                                  │
└─────────────────────────────────────────────────────────────┘
                            ↓
                   ┌────────┴────────┐
                   │                 │
            Need DB?           Need Sheets?
                   │                 │
                   ↓                 ↓
    ┌──────────────────────┐  ┌──────────────────────┐
    │ [6A] SQL AGENT       │  │ [6B] DATA ENTRY TEAM │
    │ • MCP-SQLite tools   │  │ • Read/Sheet/Write   │
    └──────────────────────┘  └──────────────────────┘
                   │                 │
                   └────────┬────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│              [7] MCP SERVER LAYER                           │
│  ┌──────────────────┐         ┌──────────────────┐          │
│  │ mcp-sqlite       │         │ mcp-gsheets      │          │
│  │ (Port 8001)      │         │ (Port 8002)      │          │
│  └──────────────────┘         └──────────────────┘          │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│              [8] STORAGE LAYER                              │
│  ┌──────────────────┐         ┌──────────────────┐          │
│  │ SQLite Database  │         │ Google Sheets    │          │
│  └──────────────────┘         └──────────────────┘          │
└─────────────────────────────────────────────────────────────┘
```

### 4.3 Data Flow Summary

```
WITH attachment:
User Request (PDF/Image)
  → Guardrails (validation)
    → Extraction Agent (Qwen3.5-4B) → structured JSON
      → Supervisor Agent "Klaudia" (orchestration)
        ├→ Data Entry Team (Google Sheets via MCP)
        └→ SQL Agent (SQLite via MCP)

WITHOUT attachment:
User Request (Text only)
  → Guardrails (validation)
    → Supervisor Agent "Klaudia" (orchestration)
      ├→ Data Entry Team (Google Sheets via MCP)
      └→ SQL Agent (SQLite via MCP)
```

---

## 5. DATA MODEL (SINGLE SOURCE OF TRUTH)

### 5.1 Database: SQLite

**Table: `user`**
```sql
CREATE TABLE user (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);
```

**Table: `session`**
```sql
CREATE TABLE session (
    session_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    session_name TEXT,  -- auto-generated
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES user(user_id)
);
```

**Table: `conversation`**
```sql
CREATE TABLE conversation (
    message_id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    sender TEXT NOT NULL,  -- 'user' | 'assistant' | 'system'
    message_text TEXT NOT NULL,
    file_id INTEGER,  -- FK to metadata_file (nullable)
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES session(session_id),
    FOREIGN KEY (user_id) REFERENCES user(user_id),
    FOREIGN KEY (file_id) REFERENCES metadata_file(id)
);
```

**Table: `metadata_file`**
```sql
CREATE TABLE metadata_file (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    type TEXT NOT NULL,  -- 'pdf' | 'image'
    total_pages INTEGER,
    file_name TEXT NOT NULL,
    status TEXT NOT NULL,  -- 'completed' | 'partial' | 'failed'
    status_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES session(session_id),
    FOREIGN KEY (user_id) REFERENCES user(user_id)
);
```

**Table: `pages`**
```sql
CREATE TABLE pages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    metadata_file_id INTEGER NOT NULL,
    page INTEGER NOT NULL,
    agent_extracted TEXT,  -- JSON string
    status TEXT NOT NULL,  -- 'extracted' | 'failed'
    status_message TEXT,
    FOREIGN KEY (metadata_file_id) REFERENCES metadata_file(id)
);
```

---

## 6. MCP TOOL CONTRACTS

### 6.1 MCP-SQL Tools (SQL Agent)

| Tool             | Type | Description           |
|------------------|------|-----------------------|
| `get_document`   | Read | Fetch document        |
| `list_pages`     | Read | List pages            |
| `get_page`       | Read | Fetch page            |
| `get_extraction` | Read | Get extraction data   |

### 6.2 MCP-GSheets Tools (Data Entry Team)

#### Read Agent Tools
| Tool Name                 | Type | Description                      |
|---------------------------|------|----------------------------------|
| `get_sheet_formulas`      | Read | Fetch formulas                   |
| `get_sheet_data`          | Read | Read specific sheetndata         |
| `get_multiple_sheet_data` | Read | Batch read multiple sheets       |

#### Sheet Agent Tools
| Tool Name      | Type  | Description                 |
|----------------|-------|-----------------------------|
| `create_sheet` | Write | Create new sheet tab        |
| `rename_sheet` | Write | Rename existing sheet       |
| `copy_sheet`   | Write | Copy sheet                  |
| `delete_sheet` | Write | Delete sheet tab            |
| `batch_update` | Write | Execute batchUpdate requests|

#### Write Agent Tools
| Tool Name            | Type  | Description              |
|----------------------|-------|--------------------------|
| `update_cells`       | Write | Update specific range    |
| `batch_update_cells` | Write | Update multiple ranges   |
| `append_rows`        | Write | Append rows              |
| `add_rows`           | Write | Insert empty rows        |
| `add_columns`        | Write | Insert empty columns     |
| `clear_range`        | Write | Clear values             |

---

## 7. CONTEXT ENRICHMENT

**Purpose:** Enable supervisor to be aware of all files in session

**Implementation:**
```python
# On every conversation turn, fetch ALL files in session
# Inject file context into system prompt

Example context:
"""
Files in current session:
1. receipt_jan.pdf
   - Type: pdf
   - Status: completed
   - Pages: 1/1 extracted
   - File ID: 1

2. invoice_feb.pdf
   - Type: pdf
   - Status: partial
   - Pages: 3/4 extracted
   - File ID: 2
"""
```

**Benefits:**
- Supervisor knows what files exist
- Can reference files by name or number
- Prevents asking "which file?" repeatedly
- Enables complex multi-file workflows

---

## 8. RUNNING & DEPLOYMENT

### 8.1 Startup Script (`startup.sh`)

```bash
#!/bin/bash
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

FASTAPI_PORT=${PORT:-8000}
MCP_SQLITE_PORT=8001
MCP_GSHEETS_PORT=8002

# Start MCP servers
python mcp-sqlite/server.py --port $MCP_SQLITE_PORT &
python mcp-gsheets/server.py --port $MCP_GSHEETS_PORT &

# Start FastAPI
uvicorn app.main:app --port $FASTAPI_PORT --reload
```

### 8.2 Git Submodules

```
[submodule "klaudia"]
    path = klaudia
    url = https://github.com/laoode/klaudia.git
    branch = development

[submodule "mcp-sqlite"]
    path = mcp-sqlite
    url = https://github.com/laoode/mcp-sqlite.git
    branch = development

[submodule "mcp-gsheets"]
    path = mcp-gsheets
    url = https://github.com/laoode/mcp-gsheets.git
    branch = development
```

### 8.3 Dependency Management (`setup.sh`)

Centralized installation for:
- `pyproject.toml` (main)
- `klaudia/pyproject.toml`
- `mcp-sqlite/pyproject.toml`
- `mcp-gsheets/pyproject.toml`

---

## 9. LOGGING & ERROR HANDLING

### 9.1 Centralized Logging
```bash
LOG_PATH=logs
```

### 9.2 Error Categories

| Category          | Handler            | Response                    |
|-------------------|--------------------|-----------------------------|
| Validation Error  | Guardrails         | 400 + Error message         |
| Extraction Failure| Extraction Agent   | Partial result + warning    |
| Tool Timeout      | Sub-agent          | Retry 3x, then fallback     |
| LLM Error         | Orchestrator       | Generic error message       |


---

## 10. DEVELOPMENT MODE

**Dynamic Staging:**
- In development mode, use mock OCR KIE responses to avoid vLLM bottlenecks
- Apply to all services with high latency

# TODO Apply Docker + OrbStack
