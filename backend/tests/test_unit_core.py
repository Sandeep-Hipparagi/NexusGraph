"""Pure unit tests that run without a live FalkorDB connection.

Covers the DB-facing data contracts (QueryTraceResult, serializers) and the
orchestrator's service-detection heuristics with a mocked graph manager.
"""

from typing import Any, Dict, List
from unittest.mock import MagicMock

import pytest
from falkordb import Edge, Node

from backend.agents.orchestrator import MultiAgentOrchestrator
from backend.db.client import FalkorDBManager, QueryTraceResult


# ---------------------------------------------------------------------------
# QueryTraceResult
# ---------------------------------------------------------------------------


class TestQueryTraceResult:
    ROWS: List[Dict[str, Any]] = [{"name": "api-gateway"}]
    TRACE: Dict[str, Any] = {"nodes": [], "edges": [], "query": "MATCH (n) RETURN n"}

    def test_tuple_unpacking(self):
        rows, trace = QueryTraceResult(self.ROWS, self.TRACE)
        assert rows == self.ROWS
        assert trace == self.TRACE

    def test_attribute_access(self):
        result = QueryTraceResult(self.ROWS, self.TRACE)
        assert result.rows == self.ROWS
        assert result.subgraph_trace == self.TRACE

    def test_string_key_access_aliases(self):
        result = QueryTraceResult(self.ROWS, self.TRACE)
        assert result["rows"] == self.ROWS
        assert result["result_rows"] == self.ROWS
        assert result["subgraph_trace"] == self.TRACE
        assert result["trace"] == self.TRACE

    def test_unknown_string_key_raises(self):
        result = QueryTraceResult(self.ROWS, self.TRACE)
        with pytest.raises(KeyError):
            result["bogus"]

    def test_integer_index_returns_component(self):
        result = QueryTraceResult(self.ROWS, self.TRACE)
        assert result[0] == self.ROWS
        assert result[1] == self.TRACE

    def test_to_dict_roundtrip(self):
        result = QueryTraceResult(self.ROWS, self.TRACE)
        d = result.to_dict()
        assert d == {"rows": self.ROWS, "subgraph_trace": self.TRACE}


# ---------------------------------------------------------------------------
# FalkorDBManager serializers (no connection required)
# ---------------------------------------------------------------------------


class TestSerializers:
    @pytest.fixture
    def manager(self) -> FalkorDBManager:
        mgr = FalkorDBManager.__new__(FalkorDBManager)
        return mgr

    def test_serialize_node(self, manager):
        node = Node(node_id=1, alias="a", labels=["Service"], properties={"name": "api-gateway", "tier": 1})
        out = manager._serialize_node(node)
        assert out["id"] == 1
        assert out["labels"] == ["Service"]
        assert out["properties"] == {"name": "api-gateway", "tier": 1}

    def test_serialize_node_labels_variants(self, manager):
        single = Node(node_id=1, alias="a", labels="Service", properties={})
        none = Node(node_id=2, alias="b", labels=[], properties=None)
        assert manager._serialize_node(single)["labels"] == ["Service"]
        assert manager._serialize_node(none)["labels"] == []
        assert manager._serialize_node(none)["properties"] == {}

    def test_serialize_edge_with_node_objects_and_harvest(self, manager):
        src = Node(node_id=1, alias="a", labels=["Service"], properties={"name": "api-gateway"})
        dst = Node(node_id=2, alias="b", labels=["Service"], properties={"name": "auth-service"})
        edge = Edge(src, "DEPENDS_ON", dst, edge_id=10, properties={"latency_ms": 12})

        nodes_map: Dict[int, Dict[str, Any]] = {}
        out = manager._serialize_edge(edge, nodes_map)

        assert out["id"] == 10
        assert out["relation"] == "DEPENDS_ON"
        assert out["source"] == 1
        assert out["target"] == 2
        assert out["properties"] == {"latency_ms": 12}
        assert set(nodes_map.keys()) == {1, 2}
        assert nodes_map[1]["properties"]["name"] == "api-gateway"

    def test_serialize_edge_with_raw_ids(self, manager):
        edge = Edge(7, "DEPENDS_ON", 9, edge_id=11, properties=None)
        out = manager._serialize_edge(edge)
        assert out["source"] == 7
        assert out["target"] == 9
        assert out["properties"] == {}

    def test_serialize_item_scalar_passthrough(self, manager):
        nodes_map: Dict[int, Dict[str, Any]] = {}
        edges_map: Dict[int, Dict[str, Any]] = {}
        assert manager._serialize_item(42, nodes_map, edges_map) == 42
        assert manager._serialize_item("text", nodes_map, edges_map) == "text"
        assert manager._serialize_item(None, nodes_map, edges_map) is None

    def test_serialize_item_nested_containers(self, manager):
        node = Node(node_id=3, alias="c", labels=["Service"], properties={"name": "ledger-db"})
        nodes_map: Dict[int, Dict[str, Any]] = {}
        edges_map: Dict[int, Dict[str, Any]] = {}
        out = manager._serialize_item([{"svc": node}, [1, 2]], nodes_map, edges_map)
        assert out[0]["svc"]["id"] == 3
        assert out[1] == [1, 2]
        assert nodes_map[3]["properties"]["name"] == "ledger-db"


# ---------------------------------------------------------------------------
# Orchestrator service detection (mocked manager)
# ---------------------------------------------------------------------------


def _orchestrator_with_services(known: List[str]) -> MultiAgentOrchestrator:
    orch = MultiAgentOrchestrator.__new__(MultiAgentOrchestrator)
    orch.manager = MagicMock()
    if known:
        res = MagicMock()
        res.result_set = [[s] for s in known]
        orch.manager.query.return_value = res
    else:
        orch.manager.query.side_effect = RuntimeError("db unavailable")
    return orch


class TestDetectTargetService:
    def test_exact_service_name_in_query(self):
        orch = _orchestrator_with_services(["checkout-service", "auth-service"])
        assert orch._detect_target_service("acme_corp", "504 timeouts on checkout-service") == "checkout-service"

    def test_case_insensitive_match(self):
        orch = _orchestrator_with_services(["payment-worker"])
        assert orch._detect_target_service("acme_corp", "Payment-Worker is down") == "payment-worker"

    def test_regex_heuristic_match(self):
        orch = _orchestrator_with_services(["auth-service", "checkout-service"])
        assert orch._detect_target_service("acme_corp", "auth-service latency spike") == "auth-service"

    def test_fallback_to_default_demo_service(self):
        orch = _orchestrator_with_services(["auth-service", "checkout-service"])
        assert orch._detect_target_service("acme_corp", "mystery incident") == "checkout-service"

    def test_fallback_to_first_service_without_default(self):
        orch = _orchestrator_with_services(["ledger-db", "auth-service"])
        assert orch._detect_target_service("acme_corp", "mystery incident") == "ledger-db"

    def test_fallback_when_graph_unreachable(self):
        orch = _orchestrator_with_services([])
        assert orch._detect_target_service("acme_corp", "mystery incident") == "checkout-service"
