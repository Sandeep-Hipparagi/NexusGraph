# NexusGraph

**Multi-agent incident intelligence on a connected graph brain: deterministic tenant isolation, Cypher-level execution traces, and MCP tooling on FalkorDB.**

[![CI](https://github.com/Sandeep-Hipparagi/NexusGraph/actions/workflows/ci.yml/badge.svg)](https://github.com/Sandeep-Hipparagi/NexusGraph/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-blue.svg)](backend/requirements.txt)

NexusGraph turns incident triage into a **deterministic graph operation**: a multi-agent swarm (SRE triage, memory coordination, company brain) queries per-tenant FalkorDB graphs with PageRank and shortest-path algorithms, persists every handoff as episodic memory, and exposes the whole loop as MCP tools with explainable subgraph traces for every answer.

## Product Walkthrough & Architecture Demo

https://github.com/Sandeep-Hipparagi/NexusGraph/releases/download/media-v1/brag.mp4

[![NexusGraph demo](assets/media/preview.webp)](https://github.com/Sandeep-Hipparagi/NexusGraph/releases/tag/media-v1)

---

## Quickstart (3 commands)

```bash
docker compose up -d falkordb          # start the graph engine
pip install -r backend/requirements.txt pytest httpx
FALKORDB_HOST=localhost FALKORDB_PORT=6379 pytest backend/tests
```

## Security & verification posture

- **38/38 tests green**: DB-free unit tests, live-FalkorDB integration tests (API, MCP tools, multi-tenant isolation, memory workflows), and security regression tests.
- **CI on a digest-pinned FalkorDB image** — the integration tier cannot silently drift with `:latest`.
- **Injection-hardened**: tenant identifiers and Cypher index identifiers are strictly validated (`DETACH DELETE` payloads are provably neutralized); all tool queries are parameterized.
- **Non-root containers** for backend and frontend; frontend builds with deterministic `npm ci`.
- CORS runs credential-free; zero secrets in the tree.

## Ecosystem

NexusGraph's graph-memory contract is exercised by the portfolio's unified evaluation harness — see [`agent-benchmark-suite`](https://github.com/Sandeep-Hipparagi/agent-benchmark-suite).

---

## Models & Adapters (Hugging Face)

NexusGraph can be used with local or cloud LLM backends to produce explainable traversal-aware responses. The following Hugging Face model releases and adapters are compatible with our inference pipelines and served as GGUF / adapter artifacts for low-latency inference.

| Model | Type | Hugging Face | Notes |
| :--- | :--- | :--- | :--- |
| **llama3-2-lora-wisdom** | LoRA / GGUF | https://huggingface.co/Sandeep4235/llama3-2-lora-wisdom | Fine-tuned Llama-3 2B LoRA weights for concise, citation-first reasoning. Useful for short-context graph trace summarization and low-latency on-device runs via Ollama or llama.cpp. |
| **qwen2.5-7b-adapter** | Adapter | https://huggingface.co/Sandeep4235/qwen2.5-7b-adapter | Adapter weights for Qwen 2.5 7B which injects compliance-aware templates and token-level suppression for hallucination control. Use with Qwen base models and the adapter loader in your inference stack. |

### Integration example (FastMCP → Model)

This snippet shows how to resolve a model call from a FastMCP tool and run it through the local inference client while preserving the NexusGraph verification pipeline.

```python
from backend.inference import get_local_client  # hypothetical helper
from backend.mcp_server.tools import analyze_blast_radius_and_commits

client = get_local_client(model_name="Sandeep4235/llama3-2-lora-wisdom")

def run_model_with_trace(prompt, trace_metadata):
    # attach the deterministic traversal trace as structured context
    context = {
        "trace_id": trace_metadata["trace_id"],
        "graph_hops": trace_metadata["hops"],
        "verifiable_citations": trace_metadata["citations"],
    }

    response = client.generate(
        prompt=prompt,
        context=context,
        max_tokens=300,
    )

    # Post-check: ensure no unauthorized data or internal endpoints leaked
    sanitized = backend.guardrails.post_check(response)
    return sanitized
```

### Where to find the model artifacts
- Model weights & adapters are published on Hugging Face:
  - https://huggingface.co/Sandeep4235/llama3-2-lora-wisdom
  - https://huggingface.co/Sandeep4235/qwen2.5-7b-adapter

---
