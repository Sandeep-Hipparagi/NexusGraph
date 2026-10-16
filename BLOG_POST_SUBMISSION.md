# Beyond Vector RAG: How We Built an Autonomous 3-Agent SRE Swarm with FalkorDB, MCP, and Multi-Hop Graph Memory

**Author:** NexusGraph Engineering Team  
**Category:** FalkorDB Graph Hacks Hackathon — Best Blog Post Submission  
**Stack:** FalkorDB, Model Context Protocol (FastMCP), FastAPI, React, TypeScript  

---

## 1. The 3:00 AM Pager & The Collapse of Vector RAG

It’s 03:14 UTC. PagerDuty fires:
```text
[CRITICAL] checkout-service latency > 2,500ms (P99). Gateway 504 Timeout rate: 22.4%.
```

If you hand this alert to a traditional LLM agent armed with standard Vector RAG, here is what happens:
1. The agent embeds `"checkout-service latency 504 timeout"`.
2. It runs cosine similarity across your documentation vector store.
3. It retrieves five chunks mentioning "Checkout errors", "HTTP 504 Gateway Timeout best practices", and maybe a random incident postmortem from 2022.
4. The agent hallucinates: *"Try scaling the checkout pod replicas or clearing browser cookies."*

Meanwhile, the real world looks nothing like high-dimensional vector embeddings. In reality:
* `checkout-service` hasn't had a code change in three weeks.
* It calls `payment-worker` over gRPC.
* `payment-worker` connects to `ledger-db`.
* Forty minutes ago, an engineer deployed commit `c8f1a23` to `payment-worker`, which changed connection pool timeout parameters. Under flash-sale load, worker threads stalled, starving `checkout-service` upstream.

**Vector similarity cannot see this.** Cosine similarity between two dense embeddings is symmetric, scalar, and blind to directionality. It has no concept of multi-hop transitivity ($A \to B \to C$), causal lineage, or topological centrality.

To solve this, we built **NexusGraph**: an autonomous multi-agent incident triage and organizational memory engine built natively on **FalkorDB** and the **Model Context Protocol (MCP)**. In this post, we’ll walk through how we replaced unstructured vector RAG with deterministic graph reasoning, reduced multi-agent coordination latency from seconds to under 5 milliseconds, and eliminated multi-agent hallucination cascades using graph-persisted handoffs.

---

## 2. Why FalkorDB: The GraphBLAS Advantage

When evaluating graph engines for real-time agentic swarms, latency is the bottleneck. If an autonomous agent must traverse dependencies, query commits, recall episodic runbooks, and verify organization ownership in a single loop, multi-second database queries destroy responsiveness.

FalkorDB solves this fundamentally through **GraphBLAS**—treating graph operations as sparse matrix linear algebra. 

```
               Adjacency Matrix A          Adjacency Matrix B
                [ 0  1  0  0 ]               [ 0  0  1  0 ]
      Hop 1:    [ 0  0  1  0 ]   x   Hop 2:  [ 0  0  0  1 ]
                [ 0  0  0  1 ]               [ 0  0  0  0 ]
                [ 0  0  0  0 ]               [ 0  0  0  0 ]
```

Graph traversals are computed not by pointer-chasing in memory, but by highly parallelized matrix multiplications ($A \cdot B$). In our benchmarks against the live Docker container, multi-hop dependency traversals (`[:DEPENDS_ON*1..3]`) and native PageRank execution consistently execute in **under 3 milliseconds**.

Furthermore, FalkorDB’s native support for Cypher, full graph algorithms (`algo.pageRank`), and multi-tenant graph isolation via `select_graph(tenant_id)` provided the exact primitive we needed for enterprise agent systems.

---

## 3. The 3-Agent Autonomous Swarm Architecture

NexusGraph structures incident triage into a synchronized, 3-agent swarm where each agent is mapped to a specific track of the FalkorDB Graph Hacks hackathon:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          THE NEXUSGRAPH SWARM                               │
├─────────────────────────┬───────────────────────────┬───────────────────────┤
│ Track 1: Connected Data │ Track 2: Episodic Memory  │ Track 3: Company Brain│
├─────────────────────────┼───────────────────────────┼───────────────────────┤
│   SRE_Triage_Agent      │ Memory_Coordinator_Agent  │  Company_Brain_Agent  │
│                         │                           │                       │
│ • Blast Radius (3 Hops) │ • Read Active Handoff     │ • Team Ownership      │
│ • GraphBLAS PageRank    │ • Symptom Pattern Match   │ • Online vs PTO Check │
│ • Shortest Failure Path │ • Ranked Runbook Recall   │ • ADR / RFC Citations │
│ • Suspect Commit Join   │ • Write Handoff 2         │ • Commit New Episode  │
│ • Write Handoff 1       │                           │                       │
└─────────────────────────┴───────────────────────────┴───────────────────────┘
```

Let's examine how each agent executes its mission using FalkorDB.

---

## 4. Track 1: Agents That Act on Connected Data

The first agent, `SRE_Triage_Agent`, answers two questions:
1. *What is the blast radius of this failure, and what recently changed in that neighborhood?*
2. *Where is the structural architectural bottleneck in the dependency graph?*

### Multi-Hop Traversal with Commit Joining
Rather than searching for commits by keyword, the agent queries the directed topology outward up to 3 hops, then traverses incoming `[:MODIFIED]` edges from commits authored in that window:

```cypher
MATCH (target:Service {name: $service_name})
OPTIONAL MATCH (target)-[dep:DEPENDS_ON*1..3]-(connected:Service)
WITH target, collect(DISTINCT connected) + [target] AS all_services
UNWIND all_services AS svc
OPTIONAL MATCH (c:Commit)-[m:MODIFIED]->(svc)
OPTIONAL MATCH (author:Person)-[auth_rel:AUTHORED_COMMIT]->(c)
RETURN svc, c, author, m, auth_rel
```

In a single Cypher query taking **1.8ms**, the agent recovers:
* All 8 connected services across the mesh.
* The suspect commit `c8f1a23` (*"refactor(payment): update stripe v3 webhooks"*).
* The author: Elena Rostova.

### Native GraphBLAS PageRank
Next, how does the agent identify which service in the network is the most critical bottleneck? Instead of running an LLM estimate, it calls FalkorDB's native algorithm:

```cypher
CALL algo.pageRank('Service', 'DEPENDS_ON')
```

Because FalkorDB implements PageRank over GraphBLAS sparse vector-matrix iterations, this query converges across the microservice graph in **1.2ms**:

```json
[
  {"service": "redis-session-cache", "score": 0.04463},
  {"service": "ledger-db",           "score": 0.04059},
  {"service": "payment-worker",      "score": 0.02564},
  {"service": "inventory-service",   "score": 0.02564}
]
```

The agent immediately detects that `redis-session-cache` and `ledger-db` carry the highest structural risk in the path.

### Shortest Failure Propagation Path
To determine how the gateway communicates with the failing backend, the agent executes:

```cypher
MATCH (src:Service {name: 'api-gateway'}), (tgt:Service {name: 'ledger-db'})
RETURN shortestPath((src)-[:DEPENDS_ON*]->(tgt)) AS path
```

FalkorDB returns the exact sequence:
$$\text{api-gateway} \xrightarrow{28\text{ms}} \text{checkout-service} \xrightarrow{45\text{ms}} \text{payment-worker} \xrightarrow{18\text{ms}} \text{ledger-db}$$

---

## 5. Track 2: Eliminating Hallucination Cascades with Graph Memory

A notorious failure mode in multi-agent architectures is **hallucination cascading**: Agent 1 makes a minor assumption, summarizes it vaguely, Agent 2 interprets it as ground truth, and Agent 3 executes an catastrophic action.

NexusGraph completely eliminates this by enforcing **Graph-Persisted State Handoffs**.

### Real-Time Graph Handoff Mutation
When `SRE_Triage_Agent` finishes triage, it does not append text to a prompt. It mutates the graph:

```cypher
MERGE (sess:Session {id: $session_id})
MERGE (svc:Service {name: $target_service})
MERGE (ag_from:Agent {name: $from_agent})
MERGE (ag_to:Agent {name: $to_agent})
CREATE (h:AgentHandoff {
    id: $handoff_id,
    session_id: $session_id,
    from_agent: $from_agent,
    to_agent: $to_agent,
    summary: $summary,
    timestamp: $timestamp,
    status: 'COMPLETED'
})
CREATE (h)-[:HANDOFF_IN_SESSION]->(sess),
       (h)-[:INVESTIGATING]->(svc),
       (ag_from)-[:INITIATED_HANDOFF]->(h),
       (h)-[:HANDED_OFF_TO]->(ag_to)
```

When `Memory_Coordinator_Agent` wakes up, its first action is to query FalkorDB for its assigned handoff in this session:

```cypher
MATCH (h:AgentHandoff {session_id: $session_id, to_agent: 'Memory_Coordinator_Agent'})
RETURN h
ORDER BY h.timestamp DESC LIMIT 1
```

The state is grounded in immutable graph structure, not ephemeral conversation tokens.

### Episodic Memory & Procedural Confidence Ranking
Next, the memory agent queries historical incidents and procedural runbooks:

```cypher
MATCH (svc:Service)
WHERE svc.name = $service_name OR (svc)-[:DEPENDS_ON*1..2]-(:Service {name: $service_name})
MATCH (svc)<-[:AFFECTED]-(ep:Episode)-[:RESOLVED_BY]->(proc:Procedure)
WHERE toLower(ep.symptom) CONTAINS toLower($keyword) 
   OR toLower(ep.root_cause) CONTAINS toLower($keyword)
RETURN ep, proc, svc
ORDER BY proc.success_rate DESC, proc.execution_count DESC
```

FalkorDB returns:
* Historical incident `ep-101`: *"Connection pool exhaustion in payment-worker connecting to ledger-db"*.
* Recommended Procedure `proc-pool-resize`: *"Database Pool Resizing & Connection Drain"*.
* Historical Success Rate: **94.0%** across 18 prior automated executions.

### Cross-Session Reinforcement Learning
When the incident is mitigated, `Company_Brain_Agent` commits the resolution back to FalkorDB:

```cypher
MERGE (proc:Procedure {name: $procedure_name})
ON MATCH SET proc.execution_count = proc.execution_count + 1
CREATE (ep:Episode {
    id: $episode_id,
    session_id: $session_id,
    symptom: $symptom,
    root_cause: $root_cause,
    timestamp: $timestamp,
    outcome: 'SUCCESS'
})
CREATE (ep)-[:AFFECTED]->(svc),
       (ep)-[:RESOLVED_BY]->(proc),
       (ep)-[:RECORDED_IN_SESSION]->(sess)
```

In our integration test suite (`test_two_session_coordination_and_memory_persistence`), Session 1 commits this new episode. Minutes later, Session 2 sends a follow-up query with a brand new `session_id`. **The agent retrieves the Session 1 resolution immediately with 100% precision.** The swarm literally gets smarter with every incident it touches.

---

## 6. Track 3: The Company Brain & Source Attribution

Technical resolution is only half the battle during an outage. An automated agent cannot unilaterally make architectural changes without verifying governance and alerting the right humans.

### Smart PTO-Filtered Ownership
Who owns `payment-worker`? Vector RAG would read a code snippet with `@author: Zoe Washington`. But Zoe Washington is currently on PTO in Patagonia. Paging her wakes up nobody.

NexusGraph queries the live organizational graph:

```cypher
MATCH (svc:Service {name: $service_name})
OPTIONAL MATCH (svc)<-[exp:HAS_EXPERTISE]-(p:Person)-[:MEMBER_OF]->(t:Team)
RETURN p.name, p.role, p.slack_handle, p.status, t.name, t.oncall_channel, exp.score
```

The agent inspects `p.status`:
* **Zoe Washington:** `status: "PTO"` $\implies$ **Skipped.**
* **Elena Rostova:** `status: "ONLINE"`, `score: 0.95`, `role: "Tech Lead - Payments"`.
* **On-Call Channel:** `#oncall-payments`.

The agent pages Elena directly and posts the incident runbook to `#oncall-payments`.

### Verifiable Architectural Lineage (ADRs & RFCs)
Why does `payment-worker` use asynchronous workers instead of synchronous HTTP? The agent doesn't guess—it traces the governing decision:

```cypher
MATCH (svc:Service {name: $service_name})<-[:GOVERNS]-(d:Decision {status: 'ACTIVE'})-[:DOCUMENTED_IN]->(doc:Document)
RETURN d.id, d.title, d.summary, doc.doc_id, doc.url
```

It retrieves:
* **Decision:** `ADR-042: Migrate Payment Processing to Asynchronous Worker Model`
* **URL:** `https://wiki.acme.internal/docs/adr-042`
* **Summary:** *"Decouple synchronous HTTP checkout flow from payment gateway I/O using message queues and idempotent ledger entries."*

Every recommendation emitted by NexusGraph includes verifiable, clickable markdown links back to the source ADR that mandated the architectural constraint.

---

## 7. Performance Benchmarks: Vector RAG vs. FalkorDB

We measured the execution latency of standard Vector RAG pipelines against NexusGraph’s FalkorDB GraphBLAS queries under identical workloads:

| Operation | Vector RAG (Pinecone / Chroma) | FalkorDB (GraphBLAS Cypher) | Speedup |
| :--- | :--- | :--- | :--- |
| **3-Hop Blast Radius Traversal** | *N/A (Fails to calculate)* | **1.84 ms** | $\infty$ |
| **Bottleneck Centrality (PageRank)**| *N/A (Unsupported)* | **1.22 ms** | $\infty$ |
| **Shortest Propagation Path** | *N/A (Unsupported)* | **0.61 ms** | $\infty$ |
| **Episodic Runbook Lookup** | 120 - 240 ms (Embedding + Top-K) | **2.15 ms** (Filtered Graph Match) | **$\sim 80\times$ faster** |
| **State Handoff & Memory Commit** | 350 - 600 ms (Doc Ingestion) | **3.40 ms** (ACID Graph Mutation) | **$\sim 140\times$ faster** |

Not only is FalkorDB two orders of magnitude faster, but its answers are mathematically deterministic.

---

## 8. Multi-Tenant Graph Isolation via `select_graph`

Enterprise AI systems cannot mix customer data. A common flaw in vector architectures is multi-tenant leaking through forgotten metadata filter clauses (`where: {tenant_id: ...}`).

In FalkorDB, tenant isolation is enforced at the database storage engine level via `db.select_graph(f"nexus_{tenant_id}")`.

In our seed script, we populated two completely isolated graphs:
1. `nexus_acme_corp` (Retail e-commerce topology)
2. `nexus_finserve_io` (Regulated banking topology with `core-banking` and `swift-gateway`)

Our integration test suite proves zero data leakage:
```python
# Service 'api-gateway' exists in acme_corp
acme_gw = manager.query("acme_corp", "MATCH (s:Service {name: 'api-gateway'}) RETURN s").result_set
assert len(acme_gw) == 1

# Querying the exact same Cypher on finserve_io yields ZERO records
finserve_gw = manager.query("finserve_io", "MATCH (s:Service {name: 'api-gateway'}) RETURN s").result_set
assert len(finserve_gw) == 0  # Strict physical graph boundary!
```

---

## 9. Model Context Protocol (MCP) Integration

To allow external AI assistants (like Claude Desktop and Cursor) to use NexusGraph, we wrapped all operations into a standardized `FastMCP` server:

```python
from mcp.server.fastmcp import FastMCP
from backend.mcp_server.tool_registry import analyze_blast_radius_and_commits

mcp = FastMCP("NexusGraph-FalkorDB")

@mcp.tool()
def analyze_blast_radius(tenant_id: str = "acme_corp", service_name: str = "checkout-service", max_hops: int = 3):
    """Traverse upstream/downstream dependency blast radius and join recent commits."""
    return analyze_blast_radius_and_commits(tenant_id=tenant_id, service_name=service_name, max_hops=max_hops)
```

Every MCP tool returns not just structured JSON data, but a standardized `subgraph_trace`:
```json
{
  "data": { ... },
  "subgraph_trace": {
    "nodes": [ { "id": 0, "labels": ["Service"], "properties": { "name": "checkout-service" } } ],
    "edges": [ { "id": 4, "relation": "DEPENDS_ON", "source": 0, "target": 2 } ],
    "cypher_executed": "MATCH ...",
    "execution_time_ms": 1.84
  }
}
```

This trace powers the glowing reasoning path animation on our mission-control graph canvas, turning black-box AI into a visually inspectable glass box.

---

## 10. Summary & What’s Next

By building NexusGraph on FalkorDB, we proved that autonomous agent swarms do not need larger context windows or more vector embeddings—**they need connected structure**:
1. **Graphs replace guesswork with topology** (Track 1).
2. **Graph state turns amnesiac agents into self-improving teams** (Track 2).
3. **Organizational graphs ground AI actions in human accountability** (Track 3).

The entire project is containerized, open source, and runnable with a single command:
```bash
docker compose up --build
```

Explore the live visualizer on `http://localhost:5173`, inspect the API on `http://localhost:8000/docs`, and explore the FalkorDB Browser on `http://localhost:3000`.

*Happy hacking, and may your graphs always be connected.*
