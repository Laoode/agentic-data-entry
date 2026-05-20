# 📄 PRODUCT REQUIREMENT DOCUMENT
## Agentic Receipt Processing & Data Entry System

```
Version: 1.1
Audience: Senior AI Engineer / Senior Software Engineer
Status: Implementation-ready
Last Updated: 2026-02-16
```

## 1. PRODUCT OVERVIEW

### 1.1 Objective
Membangun sistem AI-assisted data entry untuk receipt/struk pembelian berbasis document OCR + structured extraction, yang:
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
| **Extraction Agent (KIE)** | `gemini-3-flash-preview` (default) or `zai-org/GLM-OCR` (fine-tune, future) | Google Generative AI / vLLM | **Image → structured receipt JSON** |
| **Text OCR (optional)** | `zai-org/GLM-OCR` base | vLLM endpoint | Plain-text recognition when `OCR_MODE=true` |
| **Supervisor Agent (Klaudia)** | `gemini-3.1-pro-preview` | Google Generative AI | Orchestration & conversation |
| **Guardrails Agent** | `gemini-2.5-flash` | Google Generative AI | Input validation |
| **SQL Agent** | `gemini-3-flash-preview` | Google Generative AI | Database operations |
| **Data Entry Team** | `gemini-3-flash-preview` | Google Generative AI | Google Sheets operations |

#### KIE Routing Modes

Selected via env (`MOCK_KIE`, `OCR_MODE`, `KIE_MODEL`):

| `MOCK_KIE` | `OCR_MODE` | Pipeline                                                         | Use when            |
|------------|------------|------------------------------------------------------------------|---------------------|
| `true`     | (ignored)  | Content-keyed fixture from `sample-data/labels/`                 | Dev / tests offline |
| `false`    | `false`    | Image → `KIE_MODEL` (Gemini) → JSON (single multimodal call)     | Default production  |
| `false`    | `true`     | Image → GLM-OCR (vLLM) text → `KIE_MODEL` → JSON (two-stage)     | After GLM-OCR fine-tune ships or for redundancy testing |

The single seam is `app/services/extraction/infra/kie_client.py::KIEClient`.
IngestService + Taskiq workers never branch on mode themselves; they call
`extract_from_image(jpg_bytes)` and the client picks the path.

### 3.2 Environment Configuration

```bash
# Service Configuration
SERVICE_NAME=Klaudia Chatbot
VERSION=1.1.0
DEBUG=true

# LLM Configuration (Gemini for agents)
LLM_PROVIDER=openai
LLM_ENDPOINT=https://generativelanguage.googleapis.com/v1beta/openai/
LLM_MODEL=gemini-3-flash-preview
LLM_API_KEY=<your-gemini-key>
LLM_TEMPERATURE=0.5

# OCR Configuration (vLLM endpoint - GLM-OCR)
VLLM_BASE_URL=<your-vllm-endpoint>
AUTH_TOKEN=<your-vllm-auth-token>
VLLM_OCR_MODEL=zai-org/GLM-OCR

# Database
SQLITE_DB=app_dev.db

# Logging
LOG_PATH=logs
```

### 3.3 Extraction Pipeline

**Architecture :**
```
PDF/Image → GLM-OCR (vLLM) → Structured JSON (Direct)
```

#### **Implementation: Extraction Agent**

**Location:** `app/services/extraction/agents/extraction_agent.py`

```python
# app/services/extraction/agents/extraction_agent.py
import base64
import requests
import pypdfium2 as pdfium
import io
from typing import Dict, List
import logging

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
    "returned_items": [
        {
            "item_name": "",
            "quantity": "",
            "unit_price": "",
            "total_refund": ""
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

class ExtractionAgent:
    """
    Simplified Extraction Agent using GLM-OCR
    Directly extracts structured JSON from receipt images/PDFs
    """
    
    def __init__(
        self,
        vllm_endpoint: str,
        auth_token: str,
        model: str = "zai-org/GLM-OCR",
        db_client = None
    ):
        self.endpoint = vllm_endpoint
        self.auth_token = auth_token
        self.model = model
        self.db_client = db_client
        self.logger = logging.getLogger("ExtractionAgent")
    
    async def process_document(
        self,
        file_path: str,
        file_type: str,  # 'pdf' | 'image'
        metadata_file_id: int
    ) -> Dict:
        """
        Process document and extract structured data
        
        Flow:
        1. Convert PDF/Image to base64
        2. Send to GLM-OCR with JSON schema prompt
        3. Parse JSON response
        4. Validate against schema
        5. Save to database (pages table)
        """
        try:
            if file_type == 'pdf':
                pages_data = await self._process_pdf(file_path, metadata_file_id)
            else:
                pages_data = await self._process_image(file_path, metadata_file_id)
            
            # Update metadata_file status
            await self._update_file_status(
                metadata_file_id,
                total_pages=len(pages_data),
                pages_extracted=sum(1 for p in pages_data if p['status'] == 'extracted')
            )
            
            return {
                "metadata_file_id": metadata_file_id,
                "pages": pages_data,
                "status": "success"
            }
            
        except Exception as e:
            self.logger.error(f"Document processing failed: {e}")
            await self._update_file_status(
                metadata_file_id,
                status='failed',
                status_message=str(e)
            )
            raise
    
    async def _process_pdf(self, file_path: str, metadata_file_id: int) -> List[Dict]:
        """Process multi-page PDF"""
        pdf = pdfium.PdfDocument(file_path)
        pages_data = []
        
        for page_num, page in enumerate(pdf, start=1):
            try:
                # Render at 200 DPI
                pil_image = page.render(scale=2.77).to_pil()
                
                # Convert to base64
                buffer = io.BytesIO()
                pil_image.save(buffer, format="PNG")
                image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
                
                # Extract JSON
                extracted_json = await self._extract_json(image_base64)
                
                # Validate JSON
                validated_json = self._validate_schema(extracted_json)
                
                # Save to database
                page_id = await self._save_page(
                    metadata_file_id=metadata_file_id,
                    page_number=page_num,
                    extracted_json=validated_json,
                    status='extracted'
                )
                
                pages_data.append({
                    "page_id": page_id,
                    "page_number": page_num,
                    "status": "extracted",
                    "data": validated_json
                })
                
            except Exception as e:
                self.logger.error(f"Page {page_num} extraction failed: {e}")
                pages_data.append({
                    "page_number": page_num,
                    "status": "failed",
                    "error": str(e)
                })
        
        return pages_data
    
    async def _process_image(self, file_path: str, metadata_file_id: int) -> List[Dict]:
        """Process single image"""
        try:
            with open(file_path, 'rb') as f:
                image_base64 = base64.b64encode(f.read()).decode('utf-8')
            
            extracted_json = await self._extract_json(image_base64)
            validated_json = self._validate_schema(extracted_json)
            
            page_id = await self._save_page(
                metadata_file_id=metadata_file_id,
                page_number=1,
                extracted_json=validated_json,
                status='extracted'
            )
            
            return [{
                "page_id": page_id,
                "page_number": 1,
                "status": "extracted",
                "data": validated_json
            }]
            
        except Exception as e:
            self.logger.error(f"Image extraction failed: {e}")
            return [{
                "page_number": 1,
                "status": "failed",
                "error": str(e)
            }]
    
    async def _extract_json(self, image_base64: str) -> Dict:
        """
        Call GLM-OCR with structured prompt
        Returns JSON directly from model
        """
        import json
        
        # Construct prompt with JSON schema
        prompt = f"""请按下列JSON格式输出图中信息:
{json.dumps(EXTRACTION_SCHEMA, ensure_ascii=False, indent=2)}"""
        
        headers = {
            "Authorization": f"Bearer {self.auth_token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": [{
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{image_base64}"}
                    },
                    {
                        "type": "text",
                        "text": prompt
                    }
                ]
            }],
            "max_tokens": 4096,
            "temperature": 0.2,
            "top_p": 0.9,
        }
        
        response = requests.post(self.endpoint, json=payload, headers=headers)
        response.raise_for_status()
        
        content = response.json()['choices'][0]['message']['content']
        
        # Parse JSON from response
        # GLM-OCR might wrap JSON in markdown code blocks
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
        
        return json.loads(content)
    
    def _validate_schema(self, data: Dict) -> Dict:
        """
        Validate and fill missing fields with defaults
        """
        import copy
        validated = copy.deepcopy(EXTRACTION_SCHEMA)
        
        # Merge extracted data
        if "info" in data:
            validated["info"].update(data["info"])
        
        if "items" in data and isinstance(data["items"], list):
            validated["items"] = data["items"]
        
        if "payment" in data:
            validated["payment"].update(data["payment"])
        
        return validated
    
    async def _save_page(
        self,
        metadata_file_id: int,
        page_number: int,
        extracted_json: Dict,
        status: str
    ) -> int:
        """Save page data to database"""
        import json
        
        result = await self.db_client.execute(
            """
            INSERT INTO pages (metadata_file_id, page, agent_extracted, status, status_message)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                metadata_file_id,
                page_number,
                json.dumps(extracted_json, ensure_ascii=False),
                status,
                "extracted" if status == "extracted" else None
            )
        )
        
        return result.lastrowid
    
    async def _update_file_status(
        self,
        metadata_file_id: int,
        status: str = None,
        status_message: str = None,
        total_pages: int = None,
        pages_extracted: int = None
    ):
        """Update metadata_file status"""
        updates = []
        params = []
        
        if total_pages is not None:
            updates.append("total_pages = ?")
            params.append(total_pages)
        
        if status:
            updates.append("status = ?")
            params.append(status)
        elif total_pages and pages_extracted is not None:
            if pages_extracted == total_pages:
                updates.append("status = 'completed'")
            elif pages_extracted > 0:
                updates.append("status = 'partial'")
            else:
                updates.append("status = 'failed'")
        
        if status_message:
            updates.append("status_message = ?")
            params.append(status_message)
        
        params.append(metadata_file_id)
        
        await self.db_client.execute(
            f"UPDATE metadata_file SET {', '.join(updates)} WHERE id = ?",
            tuple(params)
        )
```

#### **Testing Example**

```python
# tests/integration/extraction/test_extraction_agent.py
import pytest
from app.services.extraction.agents.extraction_agent import ExtractionAgent

@pytest.mark.asyncio
async def test_extract_receipt_image():
    agent = ExtractionAgent(
        vllm_endpoint=os.environ["VLLM_BASE_URL"],
        auth_token=os.environ["AUTH_TOKEN"],
        db_client=mock_db_client
    )
    
    result = await agent.process_document(
        file_path="data/receipt-indomaret-test.jpg",
        file_type="image",
        metadata_file_id=1
    )
    
    assert result["status"] == "success"
    assert len(result["pages"]) == 1
    assert result["pages"][0]["status"] == "extracted"
    
    # Validate JSON structure
    data = result["pages"][0]["data"]
    assert "info" in data
    assert "items" in data
    assert "payment" in data
    assert data["info"]["store_name"] != ""
    assert len(data["items"]) > 0
```

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
    │ • GLM-OCR (vLLM)     │  │ • Klaudia            │
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
    → Extraction Agent (GLM-OCR) → structured JSON
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

### 5.2 Schema: `agent_extracted` JSON

```json
{
  "info": {
    "receipt_id": "INV-2025-001",
    "store_name": "Indomaret",
    "store_location": "Jl. Poros Raha",
    "payment_date": "2025-01-30",
    "payment_time": "14:30:00"
  },
  "items": [
    {
      "item_name": "Indomie Goreng",
      "quantity": 2,
      "unit_price": 3500,
      "total_price": 7000
    }
  ],
  "payment": {
    "subtotal": 10000,
    "tax": 1000,
    "rounding": 0,
    "discount": 0,
    "voucher": 0,
    "grand_total": 11000,
    "payment_method": "QRIS",
    "change": 0
  }
}
```

**Validation Rules:**
- Missing numeric fields → default to `0`
- Missing string fields → default to `""` (empty string)
- All fields MUST be present in output JSON
- Python validation for multi-page PDF extraction

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
| `list_sheets`             | Read | List all sheets                  |
| `get_spreadsheet_info`    | Read | Get spreadsheet metadata         |
| `get_multiple_sheet_data` | Read | Batch read multiple ranges       |

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
    branch = main

[submodule "mcp-sqlite"]
    path = mcp-sqlite
    url = https://github.com/laoode/mcp-sqlite.git
    branch = main

[submodule "mcp-gsheets"]
    path = mcp-gsheets
    url = https://github.com/laoode/mcp-gsheets.git
    branch = main
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

### 9.3 Resource Cleanup

```python
# app/services/core/container.py
class KlaudiaContainer:
    async def shutdown(self):
        """Graceful shutdown"""
        await self.llm_client.shutdown()
        await self.extraction_agent.shutdown()
        await self.mcp_sqlite.shutdown()
        await self.mcp_gsheets.shutdown()
        await self.db_client.close()
```

---

## 10. DEVELOPMENT MODE

**Dynamic Staging:**
- In development mode, use mock OCR KIE responses to avoid vLLM bottlenecks
- Apply to all services with high latency

```python
# config.py
if os.getenv("DEBUG") == "true":
    USE_MOCK_OCR = True
```

# TODO Apply Docker