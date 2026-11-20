"""Security regression tests for the NexusGraph API CORS configuration.

Guards against reintroducing the wildcard-origin + allow-credentials
combination (CSRF-style abuse surface; browsers reject it outright).
"""

from fastapi.middleware.cors import CORSMiddleware

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
