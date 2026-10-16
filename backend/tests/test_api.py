"""Integration tests for FastAPI endpoints and 2-session multi-agent memory workflows."""

import uuid
import pytest
from fastapi.testclient import TestClient
from backend.main import app, manager


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        yield test_client


def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "HEALTHY"
    assert data["falkordb_connected"] is True


def test_reset_demo(client):
    response = client.post("/api/reset-demo")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "SUCCESS"
    assert len(data["seeded_graphs"]) == 2


def test_get_graph_topology(client):
    response = client.get("/api/graph/acme_corp")
    assert response.status_code == 200
    data = response.json()
    assert data["tenant_id"] == "acme_corp"
    assert data["isolated_tenant_name"] == "nexus_acme_corp"
    assert data["stats"]["node_count"] >= 40
    assert data["stats"]["edge_count"] >= 50
    assert len(data["nodes"]) >= 40
    assert len(data["edges"]) >= 50


def test_two_session_coordination_and_memory_persistence(client):
    # -------------------------------------------------------------------------
    # SESSION 1: Triage incident, generate handoffs, and persist new Episode
    # -------------------------------------------------------------------------
    session_1_id = f"sess-test-alpha-{uuid.uuid4().hex[:6]}"
    query_1 = "Incident alert: Severe latency spike and 504 timeouts on checkout-service"

    response_1 = client.post(
        "/api/investigate",
        json={
            "tenant_id": "acme_corp",
            "session_id": session_1_id,
            "query": query_1,
        },
    )
    assert response_1.status_code == 200
    res1_data = response_1.json()

    # 1. Verify 3-Agent Swarm execution steps
    agent_steps = res1_data["agent_steps"]
    assert len(agent_steps) == 3

    agent_names = [s["agent_name"] for s in agent_steps]
    assert agent_names == [
        "SRE_Triage_Agent",
        "Memory_Coordinator_Agent",
        "Company_Brain_Agent",
    ]

    for step in agent_steps:
        assert len(step["reasoning"]) > 0
        assert len(step["tool_calls"]) > 0
        assert step["execution_time_ms"] >= 0

    # 2. Verify explainable subgraph trace
    subgraph = res1_data["subgraph"]
    assert len(subgraph["nodes"]) > 0
    assert len(subgraph["edges"]) > 0

    # 3. Verify final markdown synthesis report
    final_synthesis = res1_data["final_synthesis"]
    assert "# NexusGraph Autonomous Incident Synthesis" in final_synthesis
    assert "checkout-service" in final_synthesis
    assert "Applied Runbook" in final_synthesis
    assert "Assigned On-Call Engineer" in final_synthesis

    # 4. Verify FalkorDB persistence for Session 1: Handoffs written
    handoff_check = manager.query(
        "acme_corp",
        "MATCH (h:AgentHandoff {session_id: $sess_id}) RETURN count(h) AS cnt",
        {"sess_id": session_1_id},
    )
    assert handoff_check.result_set[0][0] >= 2

    # 5. Verify FalkorDB persistence for Session 1: Episode written
    episode_check = manager.query(
        "acme_corp",
        "MATCH (ep:Episode {session_id: $sess_id}) RETURN ep.id AS id, ep.symptom AS symptom",
        {"sess_id": session_1_id},
    )
    assert len(episode_check.result_set) >= 1
    session_1_episode_id = episode_check.result_set[0][0]
    assert session_1_episode_id is not None

    # -------------------------------------------------------------------------
    # SESSION 2: Follow-up query in a NEW session - Recall Session 1 Episode!
    # -------------------------------------------------------------------------
    session_2_id = f"sess-test-beta-{uuid.uuid4().hex[:6]}"
    query_2 = "Recurring latency spike on checkout-service after deployment"

    response_2 = client.post(
        "/api/investigate",
        json={
            "tenant_id": "acme_corp",
            "session_id": session_2_id,
            "query": query_2,
        },
    )
    assert response_2.status_code == 200
    res2_data = response_2.json()

    # Verify Agent 2 in Session 2 retrieved historical memory
    agent_2_step = res2_data["agent_steps"][1]
    assert agent_2_step["agent_name"] == "Memory_Coordinator_Agent"
    assert "Memory recall successful" in agent_2_step["reasoning"] or "Selected Runbook" in agent_2_step["reasoning"]

    # Verify query on checkout-service returned past episodes in FalkorDB
    verify_episodes = manager.query(
        "acme_corp",
        "MATCH (ep:Episode)-[:AFFECTED]->(s:Service {name: 'checkout-service'}) RETURN count(ep) AS cnt",
    )
    # Both initial seeded episode and Session 1 episode exist!
    assert verify_episodes.result_set[0][0] >= 2


def test_tenant_isolation_via_api(client):
    # Acme corp investigation
    acme_resp = client.post(
        "/api/investigate",
        json={
            "tenant_id": "acme_corp",
            "session_id": "sess-iso-acme",
            "query": "api-gateway routing issue",
        },
    )
    assert acme_resp.status_code == 200
    assert acme_resp.json()["target_service"] == "api-gateway"

    # FinServe investigation (isolated banking graph)
    finserve_resp = client.post(
        "/api/investigate",
        json={
            "tenant_id": "finserve_io",
            "session_id": "sess-iso-finserve",
            "query": "wire-transfer clearing delays",
        },
    )
    assert finserve_resp.status_code == 200
    assert finserve_resp.json()["target_service"] == "wire-transfer"

    # Topology of FinServe has core-banking, not api-gateway
    fs_graph = client.get("/api/graph/finserve_io").json()
    fs_node_names = [
        n.get("properties", {}).get("name")
        for n in fs_graph["nodes"]
        if "name" in n.get("properties", {})
    ]
    assert "wire-transfer" in fs_node_names
    assert "core-banking" in fs_node_names
    assert "api-gateway" not in fs_node_names
