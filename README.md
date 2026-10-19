
## 🧩 Models & Adapters (Hugging Face)

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
