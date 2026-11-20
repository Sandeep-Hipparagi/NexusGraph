"""Security regression tests for the NexusGraph API hardening.

Covers CORS credential policy and the Cypher/graph-name injection guards.
"""

import pytest
from fastapi.middleware.cors import CORSMiddleware

from backend.db.client import FalkorDBManager
from backend.main import app


def _cors_middleware_kwargs() -> dict:
    middlewares = [
        m.kwargs for m in app.user_middleware if m.cls is CORSMiddleware
    ]
    assert middlewares, "CORSMiddleware must be registered on the API app"
    return middlewares[0]


class TestCorsHardening:
    def test_allow_credentials_disabled_with_wildcard(self):
        kwargs = _cors_middleware_kwargs()
        if kwargs.get("allow_origins") == ["*"]:
            assert kwargs["allow_credentials"] is False

    def test_all_methods_allowed_for_demo_visualizers(self):
        kwargs = _cors_middleware_kwargs()
        assert kwargs.get("allow_methods") == ["*"]


class TestCypherAndGraphNameInjectionGuards:
    """create_index interpolates identifiers into Cypher; tenant ids become
    graph names. Both must be strictly validated."""

    @pytest.fixture
    def manager(self) -> FalkorDBManager:
        mgr = FalkorDBManager.__new__(FalkorDBManager)
        return mgr

    def test_valid_tenant_ids_accepted(self, manager):
        assert manager.graph_name_for("acme_corp") == "nexus_acme_corp"
        assert manager.graph_name_for("default") == "nexus_default"

    def test_malicious_tenant_ids_rejected(self, manager):
        for bad in [
            "acme_corp DETACH DELETE n",
            "acme'; MATCH (n) DELETE n; --",
            "tenant-1",  # hyphens are not part of the tenant alphabet
            "../../etc/passwd",
            "x" * 65,
        ]:
            with pytest.raises(ValueError):
                manager.graph_name_for(bad)

    def test_blank_tenant_falls_back_to_default(self, manager):
        assert manager.graph_name_for("") == "nexus_default"
        assert manager.graph_name_for(None) == "nexus_default"

    def test_malicious_index_identifiers_rejected(self, manager):
        for bad in [
            "Service) ON (n.x) DETACH DELETE n",
            "Service; DROP",
            "x y",
            "",
        ]:
            with pytest.raises(ValueError):
                manager._validate_identifier(bad, "label")

    def test_valid_index_identifiers_accepted(self, manager):
        assert manager._validate_identifier("Service", "label") == "Service"
        assert manager._validate_identifier("service_name", "property_name") == "service_name"
