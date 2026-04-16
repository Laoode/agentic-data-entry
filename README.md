```bash tree -I 'venv|__pycache__|*.pyc|*.log|.git|.DS_Store|*.jpg|everything-claude-code'```

```
.
├── app
│   ├── __init__.py
│   ├── exceptions.py
│   ├── helpers
│   │   ├── __init__.py
│   │   └── auth.py
│   ├── main.py
│   ├── models
│   │   ├── __init__.py
│   │   ├── attachment.py
│   │   ├── chat.py
│   │   └── message.py
│   ├── routes
│   │   ├── __init__.py
│   │   └── v1
│   │       ├── __init__.py
│   │       ├── chat.py
│   │       └── health.py
│   └── services
│       ├── __init__.py
│       ├── core
│       │   ├── __init__.py
│       │   ├── container.py
│       │   ├── llm_client.py
│       │   ├── orchestrator.py
│       │   └── prompts.py
│       ├── extraction
│       │   ├── __init__.py
│       │   ├── agents
│       │   │   ├── __init__.py
│       │   │   ├── base.py
│       │   │   ├── config.py
│       │   │   └── prompt.py
│       │   └── infra
│       │       ├── __init__.py
│       │       ├── db_client.py
│       │       └── ocr_client.py
│       └── guardrails
│           ├── __init__.py
│           ├── agent.py
│           ├── base.py
│           ├── config.py
│           ├── output.py
│           ├── prompts.py
│           └── scope.py
├── app_dev.db
├── config
│   ├── __init__.py
│   └── settings.py
├── docs
│   ├── CLAUDE.md
│   ├── DOCS.md
│   ├── FRONT_END.md
│   ├── GLMOCR_DOC.md
│   ├── LLMOps.md
│   ├── METRICS.md
│   ├── paper
│   │   └── metrics
│   │       ├── ANSL*.md
│   │       └── KIEval.md
│   ├── PRD.md
│   ├── RECIPE-DB.md
│   └── THESIS.md
├── everything-claude-code/
├── klaudia
│   ├── __init__.py
│   ├── core
│   │   ├── __init__.py
│   │   └── supervisor
│   │       ├── __init__.py
│   │       ├── agent.py
│   │       ├── agents
│   │       │   ├── data_entry_team
│   │       │   │   ├── __init__.py
│   │       │   │   ├── agents.py
│   │       │   │   └── prompts.py
│   │       │   └── sql_agent
│   │       │       ├── __init__.py
│   │       │       ├── agent.py
│   │       │       └── prompts.py
│   │       ├── prompts.py
│   │       ├── router.py
│   │       ├── state.py
│   │       └── tools
│   │           ├── __init__.py
│   │           ├── context.py
│   │           └── wrappers.py
│   ├── interfaces
│   │   ├── __init__.py
│   │   ├── agent.py
│   │   └── tool_registry.py
│   ├── models
│   │   ├── __init__.py
│   │   ├── message.py
│   │   └── state.py
│   ├── pyproject.toml
│   └── README.md
├── logs
├── mcp-config-stdio.json
├── mcp-config.json
├── mcp-gsheets
│   ├── app
│   │   ├── __init__.py
│   │   ├── infra
│   │   │   ├── __init__.py
│   │   │   └── gsheet_client.py
│   │   ├── server.py
│   │   ├── tools
│   │   │   ├── __init__.py
│   │   │   ├── read_ops.py
│   │   │   ├── sheet_ops.py
│   │   │   └── write_ops.py
│   │   └── utils
│   │       ├── __init__.py
│   │       └── logger.py
│   ├── main.py
│   ├── pyproject.toml
│   ├── README.md
│   └── service_account.json
├── mcp-sqlite
│   ├── app
│   │   ├── __init__.py
│   │   ├── engines
│   │   │   ├── __init__.py
│   │   │   └── config.py
│   │   ├── infra
│   │   │   ├── __init__.py
│   │   │   └── db_client.py
│   │   ├── server.py
│   │   ├── tools
│   │   │   ├── __init__.py
│   │   │   ├── document_ops.py
│   │   │   ├── extraction_ops.py
│   │   │   └── page_ops.py
│   │   └── utils
│   │       ├── __init__.py
│   │       ├── exceptions.py
│   │       └── logger.py
│   ├── main.py
│   ├── mcp_sqlite.egg-info
│   │   ├── dependency_links.txt
│   │   ├── PKG-INFO
│   │   ├── requires.txt
│   │   ├── SOURCES.txt
│   │   └── top_level.txt
│   ├── pyproject.toml
│   ├── README.md
│   └── test
├── pyproject.toml
├── README.md
├── sample-data
│   ├── a.json
│   └── large-receipt-image-dataset-SRD/
│       └── 1000-receipt.jpg
├── setup.sh
├── shutdown.sh
├── startup.sh
├── tests
│   ├── api
│   │   ├── gemini.curl
│   │   └── groq.curl
│   ├── data
│   ├── e2e
│   │   ├── __init__.py
│   │   └── postman_collection.json
│   ├── integration
│   │   ├── agent
│   │   │   ├── __init__.py
│   │   │   ├── test_extraction.py
│   │   │   ├── test_guardrails.py
│   │   │   └── test_llm_client.py
│   │   ├── database
│   │   │   ├── __init__.py
│   │   │   └── test_db_client.py
│   │   ├── mcp-gsheets
│   │   │   └── test_mcp_gsheets.py
│   │   ├── mcp-sqlite
│   │   │   └── test_mcp_sqlite.py
│   │   └── ocr
│   │       ├── test_ocr_client.py
│   │       ├── test-ocr-client.py
│   │       └── test-vllm-endpoint.py
│   └── unit
└── uv.lock
```



