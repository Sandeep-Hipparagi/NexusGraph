"""Unit & integration tests for FalkorDBManager client."""

import pytest
from backend.db.client import FalkorDBManager, QueryTraceResult


@pytest.fixture
def manager():
    mgr = FalkorDBManager()
    yield mgr
    mgr.delete_tenant_graph("test_unit")


def test_tenant_isolation(manager):
    # Setup test tenant 1
    manager.delete_tenant_graph("tenant_1")
    manager.delete_tenant_graph("tenant_2")

    g1 = manager.get_graph("tenant_1")
    g2 = manager.get_graph("tenant_2")

    assert g1.name == "nexus_tenant_1"
    assert g2.name == "nexus_tenant_2"

    g1.query("CREATE (:Service {name: 'service-in-tenant-1'})")
    g2.query("CREATE (:Service {name: 'service-in-tenant-2'})")

    res1 = g1.query("MATCH (s:Service) RETURN s.name AS name")
    res2 = g2.query("MATCH (s:Service) RETURN s.name AS name")

    assert len(res1.result_set) == 1
    assert res1.result_set[0][0] == "service-in-tenant-1"

    assert len(res2.result_set) == 1
    assert res2.result_set[0][0] == "service-in-tenant-2"

    manager.delete_tenant_graph("tenant_1")
    manager.delete_tenant_graph("tenant_2")


def test_query_with_trace(manager):
    tenant = "test_unit"
    manager.delete_tenant_graph(tenant)
    g = manager.get_graph(tenant)

    g.query("CREATE (a:Service {name: 'api-gateway', tier: 1})-[r:DEPENDS_ON {latency_ms: 20}]->(b:Service {name: 'auth-service', tier: 2})")

    cypher = "MATCH (a:Service {name: 'api-gateway'})-[r:DEPENDS_ON]->(b:Service) RETURN a, r, b"
    result = manager.query_with_trace(tenant, cypher)

    # Test unpacking
    rows, trace = result
    assert isinstance(result, QueryTraceResult)
    assert len(rows) == 1

    # Verify structured row
    row = rows[0]
    assert "a" in row and "r" in row and "b" in row
    assert row["a"]["properties"]["name"] == "api-gateway"
    assert row["b"]["properties"]["name"] == "auth-service"
    assert row["r"]["relation"] == "DEPENDS_ON"
    assert row["r"]["properties"]["latency_ms"] == 20

    # Verify subgraph_trace
    assert "nodes" in trace
    assert "edges" in trace
    assert "cypher_executed" in trace
    assert "execution_time_ms" in trace

    assert len(trace["nodes"]) == 2
    assert len(trace["edges"]) == 1
    assert trace["cypher_executed"] == cypher
    assert trace["execution_time_ms"] >= 0

    # Test attribute & dict access
    assert result.rows == rows
    assert result.subgraph_trace == trace
    assert result["rows"] == rows
    assert result["subgraph_trace"] == trace
