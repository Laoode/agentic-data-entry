# LangChain & LangGraph — Klaudia Project Reference
# Python only | Hierarchical Agent Teams + MCP

## LangGraph Core

- [LangGraph Overview](https://docs.langchain.com/oss/python/langgraph/overview.md): Introduction to LangGraph, a library for building stateful, multi-actor applications with LLMs.
- [Graph API](https://docs.langchain.com/oss/python/langgraph/graph-api.md): Learn how to define state, create nodes, and connect them with edges.
- [Workflows & Agents](https://docs.langchain.com/oss/python/langgraph/workflows-agents.md): Build agents and workflows with LangGraph.
- [Thinking in LangGraph](https://docs.langchain.com/oss/python/langgraph/thinking-in-langgraph.md): Learn how to think about building agents with LangGraph.
- [Choosing between Graph and Functional APIs](https://docs.langchain.com/oss/python/langgraph/choosing-apis.md): Decide which API to use for your use case.
- [Application Structure](https://docs.langchain.com/oss/python/langgraph/application-structure.md): How to structure a LangGraph application.

## LangGraph State & Memory

- [Persistence](https://docs.langchain.com/oss/python/langgraph/persistence.md): Add memory and checkpointing to your graphs.
- [Add Memory](https://docs.langchain.com/oss/python/langgraph/add-memory.md): Implement short-term and long-term memory.
- [Durable Execution](https://docs.langchain.com/oss/python/langgraph/durable-execution.md): Make your graphs resilient to failures.

## LangGraph Multi-Agent

- [Use Subgraphs](https://docs.langchain.com/oss/python/langgraph/use-subgraphs.md): Compose graphs using subgraphs for hierarchical agent teams.
- [Interrupts](https://docs.langchain.com/oss/python/langgraph/interrupts.md): Pause graph execution for human-in-the-loop confirmation.

## LangGraph Streaming

- [Streaming](https://docs.langchain.com/oss/python/langgraph/streaming.md): Stream outputs from your graph for better UX.

## LangGraph Tutorials

- [SQL Agent](https://docs.langchain.com/oss/python/langgraph/sql-agent.md): Create a SQL agent with LangGraph.

## LangGraph Reference

- [Errors](https://docs.langchain.com/oss/python/common-errors.md): Troubleshoot common LangGraph/LangChain errors.
- [LangGraph SDK Reference](https://docs.langchain.com/oss/python/reference/langgraph-python.md): Complete API documentation for LangGraph Python SDK.
- [Checkpointer Integrations](https://docs.langchain.com/oss/python/integrations/checkpointers/index.md): Integrate with checkpointer backends for LangGraph persistence.

## LangChain Agents & Tools

- [Agents](https://docs.langchain.com/oss/python/langchain/agents.md): Build agents with LangChain.
- [Tools](https://docs.langchain.com/oss/python/langchain/tools.md): Define and use tools in LangChain agents.
- [Model Context Protocol (MCP)](https://docs.langchain.com/oss/python/langchain/mcp.md): Connect agents to MCP servers as tool providers.
- [Messages](https://docs.langchain.com/oss/python/langchain/messages.md): Understand message types used in LangChain agents.
- [Structured Output](https://docs.langchain.com/oss/python/langchain/structured-output.md): Get structured responses from LLMs.

## LangChain Multi-Agent

- [Multi-agent](https://docs.langchain.com/oss/python/langchain/multi-agent/index.md): Build multi-agent systems with LangChain.
- [Handoffs](https://docs.langchain.com/oss/python/langchain/multi-agent/handoffs.md): Pass control between agents.
- [Subagents](https://docs.langchain.com/oss/python/langchain/multi-agent/subagents.md): Delegate work to subagents.
- [Build a personal assistant with subagents](https://docs.langchain.com/oss/python/langchain/multi-agent/subagents-personal-assistant.md)

## LangChain Memory

- [Short-term memory](https://docs.langchain.com/oss/python/langchain/short-term-memory.md): Manage conversation history within a session.
- [Long-term memory](https://docs.langchain.com/oss/python/langchain/long-term-memory.md): Store and recall data across conversations.

## LangChain Streaming

- [Streaming](https://docs.langchain.com/oss/python/langchain/streaming.md): Stream real-time updates from agent runs.
- [Streaming Langgraph](https://docs.langchain.com/oss/python/langgraph/streaming.md)

## Langchain Context Engineering

- [Context engineering in agents](https://docs.langchain.com/oss/python/langchain/context-engineering.md)

## LangChain Human-in-the-loop

- [Human-in-the-loop](https://docs.langchain.com/oss/python/langchain/human-in-the-loop.md): Add human approval steps to agent workflows.
- [Guardrails](https://docs.langchain.com/oss/python/langchain/guardrails.md): Implement safety checks and content filtering for agents.

## LangChain Models

- [Models](https://docs.langchain.com/oss/python/langchain/models.md): Configure and use LLMs in LangChain.
- [Google integrations](https://docs.langchain.com/oss/python/integrations/providers/google.md): Integrate with Google (Gemini) using LangChain Python.

## LangChain Reference

- [LangChain SDK Reference](https://docs.langchain.com/oss/python/reference/langchain-python.md): Complete API documentation for LangChain Python SDK.
- [Context overview](https://docs.langchain.com/oss/python/concepts/context.md): Understand context management in LangChain.
- [Memory overview](https://docs.langchain.com/oss/python/concepts/memory.md): Understand memory patterns in LangChain.
- [Providers and models](https://docs.langchain.com/oss/python/concepts/providers-and-models.md): Understand how LangChain uses providers for model access.
- [What's new in LangChain v1](https://docs.langchain.com/oss/python/releases/langchain-v1.md)
- [What's new in LangGraph v1](https://docs.langchain.com/oss/python/releases/langgraph-v1.md)

## Integration

- [Middleware integrations](https://docs.langchain.com/oss/python/integrations/middleware/index.md): Integrate with middleware using LangChain Python.
- [Langfuse Observability](https://docs.langchain.com/oss/python/integrations/providers/langfuse.md)

## ML Flow

- [ML Flow Integrations](https://docs.langchain.com/oss/python/integrations/providers/mlflow_tracking.md)
- [MLflow Tracing for LLM and Agent Observability](https://mlflow.org/docs/latest/genai/tracing.md)
- [MLflow LangChain Flavor](https://mlflow.org/docs/latest/genai/flavors/langchain.md)