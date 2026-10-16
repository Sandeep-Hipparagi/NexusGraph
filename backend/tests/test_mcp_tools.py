"""Integration tests for NexusGraph MCP Tools against live FalkorDB instance."""

import json
import uuid
import pytest
from backend.mcp_server.tool_registry import (
    analyze_blast_radius_and_commits,
    run_graph_criticality_and_path,
    recall_episodic_and_procedural_memory,
    query_company_brain_context,
    record_agent_handoff,
    commit_new_episode_memory,
)


def test_tool_1_analyze_blast_radius_and_commits():
    result = analyze_blast_radius_and_commits(
        tenant_id="acme_corp",
        service_name="checkout-service",
        max_hops=3,
    )
    # Valid JSON verification
    json_str = json.dumps(result)
    assert json_str is not None

    data = result["data"]
    trace = result["subgraph_trace"]

    assert data["service_name"] == "checkout-service"
    assert data["connected_services_count"] >= 5
    assert data["recent_commits_count"] >= 1
    assert len(data["impacted_services"]) >= 5
    assert len(data["recent_commits"]) >= 1

    # Non-empty trace verification
    assert len(trace["nodes"]) > 0
    assert len(trace["edges"]) > 0
    assert "DEPENDS_ON" in trace["cypher_executed"]
    assert trace["execution_time_ms"] >= 0


def test_tool_2_run_graph_criticality_and_path():
    result = run_graph_criticality_and_path(
        tenant_id="acme_corp",
        source_service="api-gateway",
        target_service="ledger-db",
    )
    # Valid JSON verification
    json_str = json.dumps(result)
    assert json_str is not None

    data = result["data"]
    trace = result["subgraph_trace"]

    assert data["source_service"] == "api-gateway"
    assert data["target_service"] == "ledger-db"
    assert data["path_found"] is True
    assert len(data["propagation_path"]) >= 3
    assert data["propagation_hops"] >= 2
    assert "api-gateway" in data["propagation_path"]
    assert "ledger-db" in data["propagation_path"]
    assert len(data["pagerank_rankings"]) == 8
    assert len(data["top_bottleneck_services"]) == 3

    # Non-empty trace verification combining PageRank and ShortestPath
    assert len(trace["nodes"]) > 0
    assert len(trace["edges"]) > 0
    assert "algo.pageRank" in trace["cypher_executed"]
    assert "shortestPath" in trace["cypher_executed"]
    assert trace["execution_time_ms"] >= 0


def test_tool_3_recall_episodic_and_procedural_memory():
    result = recall_episodic_and_procedural_memory(
        tenant_id="acme_corp",
        service_name="payment-worker",
        symptom_keyword="latency",
    )
    # Valid JSON verification
    json_str = json.dumps(result)
    assert json_str is not None

    data = result["data"]
    trace = result["subgraph_trace"]

    assert data["service_name"] == "payment-worker"
    assert data["episodes_found"] >= 1
    assert len(data["episodes"]) >= 1

    top_episode = data["episodes"][0]
    assert "episode_id" in top_episode
    assert "symptom" in top_episode
    assert "root_cause" in top_episode
    assert top_episode["resolved_by_procedure"]["success_rate"] > 0

    assert data["recommended_runbook"] is not None
    assert "action_steps" in data["recommended_runbook"]

    # Non-empty trace verification
    assert len(trace["nodes"]) > 0
    assert len(trace["edges"]) > 0
    assert "AFFECTED" in trace["cypher_executed"]
    assert trace["execution_time_ms"] >= 0


def test_tool_4_query_company_brain_context():
    result = query_company_brain_context(
        tenant_id="acme_corp",
        service_name="payment-worker",
    )
    # Valid JSON verification
    json_str = json.dumps(result)
    assert json_str is not None

    data = result["data"]
    trace = result["subgraph_trace"]

    assert data["service_name"] == "payment-worker"
    assert len(data["online_experts"]) >= 1
    assert data["primary_contact"] is not None
    assert data["primary_contact"]["name"] == "Elena Rostova"
    assert data["primary_contact"]["status"] == "ONLINE"
    assert data["primary_contact"]["oncall_channel"] == "#oncall-payments"

    assert len(data["governing_decisions"]) >= 1
    decision = data["governing_decisions"][0]
    assert "decision_id" in decision
    assert "summary" in decision
    assert "document" in decision
    assert decision["document"]["doc_id"] == "ADR-042"
    assert "wiki.acme.internal" in decision["document"]["url"]

    # Non-empty trace verification
    assert len(trace["nodes"]) > 0
    assert len(trace["edges"]) > 0
    assert "HAS_EXPERTISE" in trace["cypher_executed"]
    assert trace["execution_time_ms"] >= 0


def test_tool_5_record_agent_handoff():
    session_id = f"sess-test-{uuid.uuid4().hex[:6]}"
    result = record_agent_handoff(
        tenant_id="acme_corp",
        session_id=session_id,
        from_agent="TriageAgent",
        to_agent="RemediationAgent",
        summary="Verified pool lockout; escalating to remediation",
        target_service="payment-worker",
    )
    # Valid JSON verification
    json_str = json.dumps(result)
    assert json_str is not None

    data = result["data"]
    trace = result["subgraph_trace"]

    assert data["session_id"] == session_id
    assert data["from_agent"] == "TriageAgent"
    assert data["to_agent"] == "RemediationAgent"
    assert data["status"] == "COMPLETED"
    assert data["target_service"] == "payment-worker"

    # Non-empty trace verification
    assert len(trace["nodes"]) >= 4
    assert len(trace["edges"]) >= 3
    assert "HANDOFF_IN_SESSION" in trace["cypher_executed"]


def test_tool_6_commit_and_readback_mutation():
    unique_kw = f"Starvation-{uuid.uuid4().hex[:6]}"
    session_id = f"sess-test-{uuid.uuid4().hex[:6]}"
    procedure_name = f"Recycle-Pool-{unique_kw}"

    # 1. Commit new episode
    commit_res = commit_new_episode_memory(
        tenant_id="acme_corp",
        session_id=session_id,
        service_name="payment-worker",
        symptom=f"Severe queue backup and {unique_kw} on worker",
        root_cause="Leaked thread handles in connection manager",
        procedure_name=procedure_name,
        action_steps="1. Gracefully drain connections; 2. Terminate zombie workers",
    )
    # Valid JSON verification
    assert json.dumps(commit_res) is not None

    data = commit_res["data"]
    trace = commit_res["subgraph_trace"]

    assert data["status"] == "COMMITTED"
    assert data["service_name"] == "payment-worker"
    assert data["procedure"]["name"] == procedure_name
    assert data["procedure"]["execution_count"] >= 1
    assert len(trace["nodes"]) >= 3
    assert len(trace["edges"]) >= 2

    # 2. Read back via Tool 3
    recall_res = recall_episodic_and_procedural_memory(
        tenant_id="acme_corp",
        service_name="payment-worker",
        symptom_keyword=unique_kw,
    )
    assert json.dumps(recall_res) is not None

    recall_data = recall_res["data"]
    assert recall_data["episodes_found"] >= 1
    matched = [ep for ep in recall_data["episodes"] if unique_kw in ep["symptom"]]
    assert len(matched) == 1
    assert matched[0]["resolved_by_procedure"]["name"] == procedure_name


def test_multi_tenant_isolation_in_tools():
    # acme_corp has api-gateway
    acme_res = analyze_blast_radius_and_commits(
        tenant_id="acme_corp",
        service_name="api-gateway",
    )
    assert acme_res["data"]["connected_services_count"] > 0

    # finserve_io does not have api-gateway
    finserve_res = analyze_blast_radius_and_commits(
        tenant_id="finserve_io",
        service_name="api-gateway",
    )
    assert finserve_res["data"]["connected_services_count"] == 0

    # finserve_io has core-banking
    finserve_core = analyze_blast_radius_and_commits(
        tenant_id="finserve_io",
        service_name="core-banking",
    )
    assert finserve_core["data"]["connected_services_count"] > 0


def test_tool_fallback_and_edge_cases():
    """Verify all tools gracefully handle None or edge-case parameters without crashing."""
    # 1. Tool 1 with None and negative hops
    r1 = analyze_blast_radius_and_commits(tenant_id=None, service_name=None, max_hops=-5)
    assert r1 is not None
    assert "data" in r1 and "subgraph_trace" in r1
    assert r1["data"]["max_hops"] == 1

    # 2. Tool 2 with None services
    r2 = run_graph_criticality_and_path(tenant_id=None, source_service=None, target_service=None)
    assert r2 is not None
    assert "data" in r2 and "subgraph_trace" in r2
    assert "top_bottleneck_services" in r2["data"]

    # 3. Tool 3 with empty keyword
    r3 = recall_episodic_and_procedural_memory(tenant_id=None, service_name=None, symptom_keyword=None)
    assert r3 is not None
    assert "data" in r3 and "subgraph_trace" in r3

    # 4. Tool 4 with non-existent service
    r4 = query_company_brain_context(tenant_id="acme_corp", service_name="ghost-service-xyz")
    assert r4 is not None
    assert r4["data"]["service_name"] == "ghost-service-xyz"
    assert r4["data"]["primary_contact"] is None

    # 5. Tool 5 with None parameters
    r5 = record_agent_handoff(tenant_id=None, session_id=None, from_agent=None, to_agent=None, target_service=None)
    assert r5 is not None
    assert r5["data"]["status"] == "COMPLETED"

    # 6. Tool 6 with None parameters
    r6 = commit_new_episode_memory(tenant_id=None, session_id=None, service_name=None)
    assert r6 is not None
    assert r6["data"]["status"] == "COMMITTED"
