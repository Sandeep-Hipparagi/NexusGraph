"""FastMCP Server exposing NexusGraph tools over Model Context Protocol (MCP).

Allows Claude Desktop, Cursor, and external AI agents to query FalkorDB multi-tenant graphs
with explainable graph traces. Also exports functions for direct in-process Python invocation.
"""

from typing import Any, Dict
from mcp.server.fastmcp import FastMCP
from backend.mcp_server.tool_registry import (
    analyze_blast_radius_and_commits as _analyze_blast_radius_and_commits,
    run_graph_criticality_and_path as _run_graph_criticality_and_path,
    recall_episodic_and_procedural_memory as _recall_episodic_and_procedural_memory,
    query_company_brain_context as _query_company_brain_context,
    record_agent_handoff as _record_agent_handoff,
    commit_new_episode_memory as _commit_new_episode_memory,
)

# Initialize FastMCP application
mcp = FastMCP(
    name="NexusGraph-FalkorDB",
    instructions="NexusGraph FastMCP Server for FalkorDB Graph Hacks (Tracks 1, 2, and 3).",
)


@mcp.tool()
def analyze_blast_radius_and_commits(
    tenant_id: str = "acme_corp",
    service_name: str = "checkout-service",
    max_hops: int = 3,
) -> Dict[str, Any]:
    """Traverse upstream/downstream dependency blast radius and join recent commits and authors (Track 1)."""
    return _analyze_blast_radius_and_commits(
        tenant_id=tenant_id,
        service_name=service_name,
        max_hops=max_hops,
    )


@mcp.tool()
def run_graph_criticality_and_path(
    tenant_id: str = "acme_corp",
    source_service: str = "api-gateway",
    target_service: str = "ledger-db",
) -> Dict[str, Any]:
    """Execute native PageRank centrality and compute shortest failure propagation path (Track 1)."""
    return _run_graph_criticality_and_path(
        tenant_id=tenant_id,
        source_service=source_service,
        target_service=target_service,
    )


@mcp.tool()
def recall_episodic_and_procedural_memory(
    tenant_id: str = "acme_corp",
    service_name: str = "payment-worker",
    symptom_keyword: str = "",
) -> Dict[str, Any]:
    """Recall past incidents and ranked procedural runbooks by symptom similarity and success rate (Track 2)."""
    return _recall_episodic_and_procedural_memory(
        tenant_id=tenant_id,
        service_name=service_name,
        symptom_keyword=symptom_keyword,
    )


@mcp.tool()
def query_company_brain_context(
    tenant_id: str = "acme_corp",
    service_name: str = "payment-worker",
) -> Dict[str, Any]:
    """Query team ownership, online vs PTO experts, and governing ADR/RFC documentation (Track 3)."""
    return _query_company_brain_context(
        tenant_id=tenant_id,
        service_name=service_name,
    )


@mcp.tool()
def record_agent_handoff(
    tenant_id: str = "acme_corp",
    session_id: str = "sess-default",
    from_agent: str = "TriageAgent",
    to_agent: str = "RemediationAgent",
    summary: str = "Investigating elevated error rate",
    target_service: str = "payment-worker",
) -> Dict[str, Any]:
    """Mutate graph to record state transition and handoff between autonomous agents (Track 2)."""
    return _record_agent_handoff(
        tenant_id=tenant_id,
        session_id=session_id,
        from_agent=from_agent,
        to_agent=to_agent,
        summary=summary,
        target_service=target_service,
    )


@mcp.tool()
def commit_new_episode_memory(
    tenant_id: str = "acme_corp",
    session_id: str = "sess-default",
    service_name: str = "payment-worker",
    symptom: str = "Elevated latency on checkout flow",
    root_cause: str = "Gunicorn worker connection pool exhaustion",
    procedure_name: str = "Database Pool Resizing & Connection Drain",
    action_steps: str = "1. Scale worker connections; 2. Reload pool",
) -> Dict[str, Any]:
    """Persist resolved incident learning, linking new Episode and reinforcing Procedure (Track 2)."""
    return _commit_new_episode_memory(
        tenant_id=tenant_id,
        session_id=session_id,
        service_name=service_name,
        symptom=symptom,
        root_cause=root_cause,
        procedure_name=procedure_name,
        action_steps=action_steps,
    )


if __name__ == "__main__":
    # Run the FastMCP server over standard stdio transport for MCP clients
    mcp.run()
