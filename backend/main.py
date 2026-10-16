"""FastAPI Application for NexusGraph.

Exposes REST APIs for:
1. POST /api/investigate: Multi-agent incident triage, memory recall, and ownership attribution
2. GET /api/graph/{tenant_id}: Full graph topology and statistics for live visualizer
3. POST /api/reset-demo: Cleanly reset and re-seed the graphs for repeatable hackathon judging
"""

import logging
from typing import Any, Dict, List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from backend.agents.orchestrator import MultiAgentOrchestrator
from backend.db.client import FalkorDBManager
from backend.db.seed_graph import seed_acme_corp, seed_finserve_io

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("nexus_api")

app = FastAPI(
    title="NexusGraph API",
    description="Multi-Agent Incident Intelligence & Memory Swarm powered by FalkorDB",
    version="1.0.0",
)

# Enable CORS for frontend visualizers (React / Next.js / Vite on port 3000, 5173, etc.)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Shared instances
manager = FalkorDBManager()
orchestrator = MultiAgentOrchestrator(manager=manager)


# =============================================================================
# Request & Response Schemas
# =============================================================================
class InvestigateRequest(BaseModel):
    tenant_id: str = Field(default="acme_corp", description="Multi-tenant graph identifier")
    session_id: str = Field(default="sess-demo-01", description="Unique coordination session ID")
    query: str = Field(
        default="High latency and 504 timeouts on checkout-service",
        description="Incident symptom or natural language query",
    )


class ResetDemoRequest(BaseModel):
    tenant_id: Optional[str] = Field(default=None, description="Optional tenant to reset or None for all")


# =============================================================================
# API Endpoints
# =============================================================================
@app.get("/health")
def health_check():
    """Health check verifying FalkorDB connectivity."""
    is_connected = manager.ping()
    return {
        "status": "HEALTHY" if is_connected else "UNHEALTHY",
        "falkordb_connected": is_connected,
        "falkordb_host": manager.host,
        "falkordb_port": manager.port,
    }


@app.post("/api/investigate")
def run_investigation(payload: InvestigateRequest) -> Dict[str, Any]:
    """
    Execute the 3-Agent Swarm investigation:
    1. SRE_Triage_Agent -> 2. Memory_Coordinator_Agent -> 3. Company_Brain_Agent
    Returns step-by-step reasoning, traversed explainable subgraph, and markdown synthesis.
    """
    try:
        result = orchestrator.investigate(
            tenant_id=payload.tenant_id,
            session_id=payload.session_id,
            query=payload.query,
        )
        return result
    except Exception as e:
        logger.error(f"Error during investigation: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/graph/{tenant_id}")
def get_graph_topology(tenant_id: str) -> Dict[str, Any]:
    """
    Retrieve the full node and edge topology for the selected tenant,
    plus graph statistics for live canvas/network visualization.
    """
    try:
        # Fetch full topology
        cypher = "MATCH (n) OPTIONAL MATCH (n)-[r]->(m) RETURN n, r, m"
        trace_res = manager.query_with_trace(tenant_id, cypher)
        _, trace = trace_res

        # Fetch category stats
        def _get_count(query_str: str) -> int:
            try:
                res = manager.query(tenant_id, query_str)
                return res.result_set[0][0] if res.result_set else 0
            except Exception:
                return 0

        node_cnt = _get_count("MATCH (n) RETURN count(n)")
        edge_cnt = _get_count("MATCH ()-[r]->() RETURN count(r)")
        svc_cnt = _get_count("MATCH (s:Service) RETURN count(s)")
        ep_cnt = _get_count("MATCH (e:Episode) RETURN count(e)")
        team_cnt = _get_count("MATCH (t:Team) RETURN count(t)")
        dec_cnt = _get_count("MATCH (d:Decision) RETURN count(d)")

        clean_tenant = tenant_id.strip()
        graph_name = f"nexus_{clean_tenant}" if not clean_tenant.startswith("nexus_") else clean_tenant

        return {
            "tenant_id": tenant_id,
            "isolated_tenant_name": graph_name,
            "stats": {
                "node_count": node_cnt,
                "edge_count": edge_cnt,
                "service_count": svc_cnt,
                "active_episodes": ep_cnt,
                "teams_count": team_cnt,
                "decisions_count": dec_cnt,
            },
            "nodes": trace.get("nodes", []),
            "edges": trace.get("edges", []),
        }
    except Exception as e:
        logger.error(f"Error retrieving graph for tenant '{tenant_id}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/reset-demo")
def reset_demo(payload: Optional[ResetDemoRequest] = None) -> Dict[str, Any]:
    """
    Reset and re-seed the graphs cleanly for repeatable demo takes.
    """
    try:
        target_tenant = payload.tenant_id if payload else None
        seeded = []

        if target_tenant in ("acme_corp", None):
            res_acme = seed_acme_corp(manager)
            seeded.append(res_acme)

        if target_tenant in ("finserve_io", None):
            res_finserve = seed_finserve_io(manager)
            seeded.append(res_finserve)

        return {
            "status": "SUCCESS",
            "message": "FalkorDB graphs cleanly reset and re-seeded for demo.",
            "seeded_graphs": seeded,
        }
    except Exception as e:
        logger.error(f"Error resetting demo graphs: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
