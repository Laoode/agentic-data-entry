<h1 align="center"><img src="https://readme-typing-svg.demolab.com?font=Chakra+Petch&weight=500&size=29&duration=1&pause=1000&color=000000&background=CCFF00&vCenter=true&repeat=false&width=928&lines=Klaudia+Agentic+AI+for+Processing+Receipt+and+Data+Entry+Automation" alt="Typing SVG" /></h1>

<div align="center">
  <img src="https://github.com/Laoode/agentic-data-entry/blob/development/docs/LLMOps.png" alt="LLM Ops Pipeline">
</div>

```
yudhypr@MacBook-Air-La Big-Thesis-S1 % lt
 .
├──  app
│   ├──  __init__.py
│   ├──  exceptions.py
│   ├──  helpers
│   │   ├──  __init__.py
│   │   └──  auth.py
│   ├──  main.py
│   ├──  models
│   │   ├──  __init__.py
│   │   ├──  attachment.py
│   │   ├──  chat.py
│   │   └──  message.py
│   ├──  routes
│   │   ├──  __init__.py
│   │   └──  v1
│   │       ├──  __init__.py
│   │       ├──  chat.py
│   │       ├──  health.py
│   │       ├──  sessions.py
│   │       └──  sheets.py
│   └──  services
│       ├──  __init__.py
│       ├──  core
│       │   ├──  __init__.py
│       │   ├──  container.py
│       │   ├──  llm_client.py
│       │   ├──  observability.py
│       │   ├──  orchestrator.py
│       │   └──  prompts.py
│       ├──  extraction
│       │   ├──  __init__.py
│       │   ├──  agents
│       │   │   ├──  __init__.py
│       │   │   ├──  base.py
│       │   │   ├──  config.py
│       │   │   ├──  parser.py
│       │   │   ├──  prompt.py
│       │   │   └──  schema.py
│       │   ├──  infra
│       │   │   ├──  __init__.py
│       │   │   ├──  db_client.py
│       │   │   ├──  dedup_cache.py
│       │   │   ├──  filename.py
│       │   │   ├──  gemini_kie.py
│       │   │   ├──  hasher.py
│       │   │   ├──  kie_client.py
│       │   │   ├──  magic.py
│       │   │   ├──  normalizer.py
│       │   │   ├──  object_store.py
│       │   │   ├──  pdf_splitter.py
│       │   │   └──  text_ocr.py
│       │   ├──  ingest.py
│       │   └──  queue
│       │       ├──  __init__.py
│       │       ├──  broker.py
│       │       ├──  progress.py
│       │       ├──  state.py
│       │       └──  tasks.py
│       └──  guardrails
│           ├──  __init__.py
│           ├──  agent.py
│           ├──  base.py
│           ├──  config.py
│           ├──  output.py
│           ├──  prompts.py
│           └──  scope.py
├──  app_dev.db-shm
├──  app_dev.db-wal
├──  config
│   ├──  __init__.py
│   └──  settings.py
├──  docs
│   ├──  FRONT_END.md
│   ├──  GLMOCR_DOC.md
│   ├──  HAT.md
│   ├──  LANGCHAIN.md
│   ├──  LLMOps.md
│   ├──  METRICS.md
│   ├──  OPERATIONS.md
│   ├──  paper
│   │   └──  metrics
│   │       ├──  ANSL*.md
│   │       └──  KIEval.md
│   ├──  PLAN.md
│   ├──  PRD.md
│   ├──  PROMPT.md
│   ├──  RECIPE-DB.md
│   └──  THESIS.md
├──  dump.rdb
├──  klaudia
│   ├──  __init__.py
│   ├──  core
│   │   ├──  __init__.py
│   │   └──  supervisor
│   │       ├──  __init__.py
│   │       ├──  _content.py
│   │       ├──  agent.py
│   │       ├──  agents
│   │       │   ├──  data_entry_team
│   │       │   │   ├──  __init__.py
│   │       │   │   ├──  agents.py
│   │       │   │   └──  prompts.py
│   │       │   └──  sql_agent
│   │       │       ├──  __init__.py
│   │       │       ├──  agent.py
│   │       │       └──  prompts.py
│   │       ├──  llm.py
│   │       ├──  prompts.py
│   │       ├──  router.py
│   │       ├──  state.py
│   │       └──  tools
│   │           ├──  __init__.py
│   │           ├──  context.py
│   │           └──  wrappers.py
│   ├──  interfaces
│   │   ├──  __init__.py
│   │   ├──  agent.py
│   │   └──  tool_registry.py
│   ├──  models
│   │   ├──  __init__.py
│   │   ├──  message.py
│   │   └──  state.py
│   ├──  pyproject.toml
│   └── 󰂺 README.md
├──  mcp-config-stdio.json
├──  mcp-config.json
├──  mcp-gsheets
│   ├──  app
│   │   ├──  __init__.py
│   │   ├──  infra
│   │   │   ├──  __init__.py
│   │   │   └──  gsheet_client.py
│   │   ├──  server.py
│   │   ├──  tools
│   │   │   ├──  __init__.py
│   │   │   ├──  read_ops.py
│   │   │   ├──  sheet_ops.py
│   │   │   └──  write_ops.py
│   │   └──  utils
│   │       ├──  __init__.py
│   │       └──  logger.py
│   ├──  main.py
│   ├──  pyproject.toml
│   ├── 󰂺 README.md
│   └──  service_account.json
├──  mcp-sqlite
│   ├──  app
│   │   ├──  __init__.py
│   │   ├──  engines
│   │   │   ├──  __init__.py
│   │   │   └──  config.py
│   │   ├──  infra
│   │   │   ├──  __init__.py
│   │   │   └──  db_client.py
│   │   ├──  server.py
│   │   ├──  tools
│   │   │   ├──  __init__.py
│   │   │   ├──  document_ops.py
│   │   │   ├──  extraction_ops.py
│   │   │   └──  page_ops.py
│   │   └──  utils
│   │       ├──  __init__.py
│   │       ├──  exceptions.py
│   │       └──  logger.py
│   ├──  main.py
│   ├──  mcp_sqlite.egg-info
│   │   ├──  dependency_links.txt
│   │   ├── 󰡯 PKG-INFO
│   │   ├──  requires.txt
│   │   ├──  SOURCES.txt
│   │   └──  top_level.txt
│   ├──  pyproject.toml
│   └── 󰂺 README.md
├──  pyproject.toml
├── 󰂺 README.md
├──  sample-data
│   ├──  labels
│   │   ├──  images
│   │   │   ├──  1000-receipt.json
│   │   │   └──  1001-receipt.json
│   │   └──  pdf
│   │       └──  001-receipt
│   │           ├──  1.json
│   │           ├──  2.json
│   │           ├──  3.json
│   │           ├──  4.json
│   │           ├──  5.json
│   │           └──  6.json
│   ├──  pdf
│   │   └──  001-receipt.pdf
│   └──  receipt
│       ├──  1000-receipt.jpg
│       └──  1001-receipt.jpg
├──  scripts
│   └──  run_worker.sh
├──  setup.sh
├──  shutdown.sh
├──  startup.sh
├──  tests
│   ├──  api
│   ├──  data
│   │   └──  receipt-indomaret-test.jpg
│   ├──  e2e
│   │   ├──  __init__.py
│   │   └──  postman_collection.json
│   ├──  integration
│   │   ├──  agent
│   │   │   ├──  __init__.py
│   │   │   ├──  test_data_entry_team.py
│   │   │   ├──  test_guardrails.py
│   │   │   ├──  test_hitl_and_idempotency.py
│   │   │   ├──  test_llm_client.py
│   │   │   ├──  test_sql_agent.py
│   │   │   └──  test_streaming.py
│   │   ├──  database
│   │   │   ├──  __init__.py
│   │   │   └──  test_db_client.py
│   │   ├──  extraction
│   │   │   ├──  __init__.py
│   │   │   ├──  test_async_pipeline.py
│   │   │   ├──  test_gemini_kie.py
│   │   │   └──  test_ingest_pipeline.py
│   │   ├──  mcp-gsheets
│   │   │   ├──  test_gsheets_tools.py
│   │   │   └──  test_mcp_gsheets.py
│   │   ├──  mcp-sqlite
│   │   │   ├──  test_mcp_sqlite.py
│   │   │   └──  test_sqlite_tools.py
│   │   ├──  observability
│   │   │   ├──  __init__.py
│   │   │   └──  test_langfuse.py
│   │   └──  ocr
│   │       └──  test_ocr_mock.py
│   └──  unit
│       ├──  __init__.py
│       ├──  test_filename_and_magic.py
│       ├──  test_hasher.py
│       ├──  test_normalizer.py
│       ├──  test_observability.py
│       ├──  test_pdf_splitter.py
│       ├──  test_schema_and_parser.py
│       └──  test_supervisor_resolve.py
└──  uv.lock
```

```
redis-server
redis-cli shutdown
```

```
minio server /Users/yudhypr/Codex/minio/data
```