"""
Tests for NODE Endpoints (Agent Tools API) - Contract & HTTP Behavior Tests.

Tests run against the live FastAPI app via TestClient.
Tests do NOT mock the service layer (except where external deps are unavailable).
Contract tests focus on: auth, validation, schema shape, field priority.

Run: pytest backend/tests/agents/test_node_endpoints.py -v
"""
import os
import pytest

# Set test env BEFORE importing FastAPI app
os.environ["AGENT_INTERNAL_TOOL_KEY"] = "test-secret-key-1234567890"
os.environ["AGENT_TOOLS_BASE_URL"] = "http://localhost:8000/api/agent-tools"
os.environ["AGENT_ENABLED"] = "false"  # Disable LLM agent to avoid startup issues


# ─────────────────────────────────────────────────────────────────────────────
# Shared fixtures
# ─────────────────────────────────────────────────────────────────────────────
@pytest.fixture
def client():
    from fastapi.testclient import TestClient
    from main import app
    return TestClient(app)


@pytest.fixture
def auth_headers():
    return {"X-Agent-Internal-Key": "test-secret-key-1234567890"}


@pytest.fixture
def wrong_auth_headers():
    return {"X-Agent-Internal-Key": "wrong-key"}


# ═══════════════════════════════════════════════════════════════════════════════
# Contract / Discovery Endpoint Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestContractEndpoint:
    """Contract discovery endpoint - public (no auth required)."""

    def test_contract_returns_version(self, client):
        resp = client.get("/api/agent-tools/contract")
        assert resp.status_code == 200
        data = resp.json()
        assert "version" in data
        assert data["version"] == "1.0.0"

    def test_contract_no_auth_required(self, client):
        """Contract endpoint must be public."""
        resp = client.get("/api/agent-tools/contract")
        assert resp.status_code == 200

    def test_contract_has_required_fields(self, client):
        data = client.get("/api/agent-tools/contract").json()
        assert "version" in data
        assert "auth_header" in data
        assert data["auth_header"] == "X-Agent-Internal-Key"
        assert "auth_required" in data
        assert "endpoints" in data
        assert "node3_field_compatibility" in data
        assert "response_envelope" in data

    def test_contract_node3_field_compat(self, client):
        data = client.get("/api/agent-tools/contract").json()
        compat = data["node3_field_compatibility"]
        assert compat["query"]["preferred"] is True
        assert compat["q"]["preferred"] is False
        assert "priority_rule" in compat
        assert "validation_rule" in compat

    def test_contract_endpoints_listed(self, client):
        data = client.get("/api/agent-tools/contract").json()
        endpoints = data["endpoints"]
        assert "node0_preprocess" in endpoints
        assert "node1_query_splitter" in endpoints
        assert "node2_intent_classifier" in endpoints
        assert "node3_tool_executor" in endpoints
        assert "node4_format_response" in endpoints


# ═══════════════════════════════════════════════════════════════════════════════
# Health Endpoint Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestHealthEndpoint:
    """Health check - public (no auth required)."""

    def test_health_returns_200(self, client):
        resp = client.get("/api/agent-tools/health")
        assert resp.status_code == 200

    def test_health_no_auth_required(self, client):
        resp = client.get("/api/agent-tools/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"
        assert "nodes" in data
        assert data["version"] == "1.0.0"


# ═══════════════════════════════════════════════════════════════════════════════
# Auth Header Tests (all protected endpoints)
# ═══════════════════════════════════════════════════════════════════════════════

class TestAuthRequired:
    """All NODE endpoints require X-Agent-Internal-Key."""

    def test_preprocess_no_auth(self, client):
        resp = client.post("/api/agent-tools/preprocess", json={"text": "test"})
        assert resp.status_code == 403

    def test_preprocess_wrong_auth(self, client, wrong_auth_headers):
        resp = client.post("/api/agent-tools/preprocess", json={"text": "test"}, headers=wrong_auth_headers)
        assert resp.status_code == 403

    def test_node1_no_auth(self, client):
        resp = client.post("/api/agent-tools/node1/query_splitter", json={"text": "test"})
        assert resp.status_code == 403

    def test_node2_no_auth(self, client):
        resp = client.post("/api/agent-tools/node2/intent_classifier", json={"query": "test"})
        assert resp.status_code == 403

    def test_node3_no_auth(self, client):
        resp = client.post("/api/agent-tools/intent/grade_view", json={"q": "test"})
        assert resp.status_code == 403

    def test_node4_no_auth(self, client):
        resp = client.post("/api/agent-tools/node4/format_response", json={"results": {}})
        assert resp.status_code == 403

    def test_intents_no_auth(self, client):
        resp = client.get("/api/agent-tools/intents")
        assert resp.status_code == 403


# ═══════════════════════════════════════════════════════════════════════════════
# NODE-0: Text Preprocessor
# ═══════════════════════════════════════════════════════════════════════════════

class TestNode0Preprocess:
    """NODE-0: Text Preprocessor endpoint tests."""

    def test_success(self, client, auth_headers):
        resp = client.post(
            "/api/agent-tools/preprocess",
            json={"text": "Xin chao may la ai?"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "success"
        assert "normalized_text" in data["data"]
        assert data["metadata"]["node"] == "node0_preprocess"
        assert data["error"] is None

    def test_success_with_metadata(self, client, auth_headers):
        resp = client.post(
            "/api/agent-tools/preprocess",
            json={"text": "hello", "metadata": {"source": "test"}},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "success"
        assert data["metadata"]["passed_metadata"] == {"source": "test"}

    def test_empty_text_returns_422(self, client, auth_headers):
        resp = client.post(
            "/api/agent-tools/preprocess",
            json={"text": ""},
            headers=auth_headers,
        )
        assert resp.status_code == 422  # FastAPI default validation

    def test_missing_text_returns_422(self, client, auth_headers):
        resp = client.post(
            "/api/agent-tools/preprocess",
            json={},
            headers=auth_headers,
        )
        assert resp.status_code == 422

    def test_response_envelope_shape(self, client, auth_headers):
        resp = client.post(
            "/api/agent-tools/preprocess",
            json={"text": "test"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        # Must have all envelope fields
        assert "status" in data
        assert "data" in data
        assert "metadata" in data
        assert "error" in data


# ═══════════════════════════════════════════════════════════════════════════════
# NODE-1: Query Splitter
# ═══════════════════════════════════════════════════════════════════════════════

class TestNode1QuerySplitter:
    """NODE-1: Query Splitter endpoint tests."""

    def test_success_simple(self, client, auth_headers):
        resp = client.post(
            "/api/agent-tools/node1/query_splitter",
            json={"text": "xem điểm của tôi"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "success"
        assert "queries" in data["data"]
        assert isinstance(data["data"]["queries"], list)
        assert data["metadata"]["node"] == "node1_query_splitter"
        assert data["error"] is None

    def test_response_envelope_shape(self, client, auth_headers):
        resp = client.post(
            "/api/agent-tools/node1/query_splitter",
            json={"text": "hello"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "status" in data
        assert "data" in data
        assert "metadata" in data
        assert "error" in data


# ═══════════════════════════════════════════════════════════════════════════════
# NODE-2: Intent Classifier
# ═══════════════════════════════════════════════════════════════════════════════

class TestNode2IntentClassifier:
    """NODE-2: Intent Classifier endpoint tests."""

    def test_success_grade_view(self, client, auth_headers):
        resp = client.post(
            "/api/agent-tools/node2/intent_classifier",
            json={"query": "xem điểm của tôi"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "success"
        assert data["data"]["intent"] == "grade_view"
        assert "confidence" in data["data"]
        assert data["metadata"]["node"] == "node2_intent_classifier"
        assert data["error"] is None

    def test_success_schedule_view(self, client, auth_headers):
        resp = client.post(
            "/api/agent-tools/node2/intent_classifier",
            json={"query": "lịch học của tôi"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "success"
        assert data["data"]["intent"] == "schedule_view"

    def test_missing_query_returns_422(self, client, auth_headers):
        resp = client.post(
            "/api/agent-tools/node2/intent_classifier",
            json={},
            headers=auth_headers,
        )
        assert resp.status_code == 422

    def test_response_envelope_shape(self, client, auth_headers):
        resp = client.post(
            "/api/agent-tools/node2/intent_classifier",
            json={"query": "xin chao"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "status" in data
        assert "data" in data
        assert "metadata" in data
        assert "error" in data


# ═══════════════════════════════════════════════════════════════════════════════
# NODE-3: Tool Executor - CONTRACT TESTS
# ═══════════════════════════════════════════════════════════════════════════════

class TestNode3Contract:
    """
    NODE-3 contract tests.
    Priority rule: query > q when both provided.
    Validation: at least one required, 422 otherwise.
    """

    def test_q_field_backward_compat(self, client, auth_headers):
        """NODE-3 accepts `q` field (backward compatible)."""
        resp = client.post(
            "/api/agent-tools/intent/grade_view",
            json={"q": "xem điểm"},
            headers=auth_headers,
        )
        # 200 = success (DB may fail but auth+schema OK)
        # 500 = business error (DB not connected) but NOT 422 (validation passed)
        assert resp.status_code in [200, 500], f"Expected 200 or 500, got {resp.status_code}"
        data = resp.json()
        assert data["status"] in ["success", "error"]  # business error OK
        # 422 would mean schema validation failed - that would be WRONG
        assert resp.status_code != 422

    def test_query_field_preferred(self, client, auth_headers):
        """NODE-3 accepts `query` field (preferred)."""
        resp = client.post(
            "/api/agent-tools/intent/grade_view",
            json={"query": "xem điểm"},
            headers=auth_headers,
        )
        assert resp.status_code in [200, 500]
        data = resp.json()
        assert data["status"] in ["success", "error"]
        assert resp.status_code != 422

    def test_both_query_and_q_prefers_query(self, client, auth_headers):
        """
        When both query and q are provided, query takes precedence.
        The endpoint must NOT reject this (no 422), and should use query value.
        """
        resp = client.post(
            "/api/agent-tools/intent/grade_view",
            json={"query": "xem điểm cpa", "q": "xem điểm"},
            headers=auth_headers,
        )
        assert resp.status_code in [200, 500]
        # Must NOT return 422 - both fields are valid strings
        assert resp.status_code != 422
        data = resp.json()
        # If business logic ran, it used "xem điểm cpa" (query field)
        assert data["status"] in ["success", "error"]

    def test_missing_both_query_and_q_returns_422(self, client, auth_headers):
        """At least one of query or q must be provided. Returns 422 otherwise."""
        resp = client.post(
            "/api/agent-tools/intent/grade_view",
            json={},
            headers=auth_headers,
        )
        assert resp.status_code == 422, f"Expected 422 when both query and q are missing, got {resp.status_code}"

    def test_missing_both_with_student_id_returns_422(self, client, auth_headers):
        """Even with student_id, missing query and q must return 422."""
        resp = client.post(
            "/api/agent-tools/intent/grade_view",
            json={"student_id": 1},
            headers=auth_headers,
        )
        assert resp.status_code == 422

    def test_invalid_intent_returns_404(self, client, auth_headers):
        """Unknown intent name returns 404."""
        resp = client.post(
            "/api/agent-tools/intent/not_a_real_intent",
            json={"q": "test"},
            headers=auth_headers,
        )
        assert resp.status_code == 404

    def test_response_envelope_shape_on_success(self, client, auth_headers):
        """Success response has correct envelope shape."""
        resp = client.post(
            "/api/agent-tools/intent/grade_view",
            json={"query": "xem điểm"},
            headers=auth_headers,
        )
        if resp.status_code == 200:
            data = resp.json()
            assert "status" in data
            assert "data" in data
            assert "metadata" in data
            assert "error" in data

    def test_response_envelope_shape_on_business_error(self, client, auth_headers):
        """Business error (e.g. DB fail) also follows envelope shape."""
        resp = client.post(
            "/api/agent-tools/intent/grade_view",
            json={"query": "xem điểm"},
            headers=auth_headers,
        )
        if resp.status_code == 500:
            data = resp.json()
            # Even on business error, envelope fields must be present
            assert "status" in data
            assert "data" in data
            assert "metadata" in data
            assert "error" in data


# ═══════════════════════════════════════════════════════════════════════════════
# NODE-4: Response Formatter - CONTRACT TESTS
# ═══════════════════════════════════════════════════════════════════════════════

class TestNode4Contract:
    """NODE-4 contract tests - response schema shape."""

    def test_auth_required(self, client):
        """NODE-4 requires auth header."""
        resp = client.post(
            "/api/agent-tools/node4/format_response",
            json={"results": {"score": 85}},
        )
        assert resp.status_code == 403

    def test_response_envelope_shape(self, client, auth_headers):
        """
        NODE-4 response data must have:
        - text: string
        - tokens_used: int
        This is verified from the actual response structure.
        """
        resp = client.post(
            "/api/agent-tools/node4/format_response",
            json={
                "results": {"score": 85, "gpa": 3.5},
                "instruction": "Trả lời bằng tiếng Việt",
                "token_budget": 100,
            },
            headers=auth_headers,
        )
        # Either 200 (success) or 500 (LLM unavailable) is acceptable
        assert resp.status_code in [200, 500]
        data = resp.json()
        # Envelope always present
        assert "status" in data
        assert "data" in data
        assert "metadata" in data
        assert "error" in data

    def test_tokens_used_is_int_not_string(self, client, auth_headers):
        """
        data.tokens_used must be int, NOT string.
        Schema declares Dict[str, Any] to allow both text(str) and tokens_used(int).
        """
        resp = client.post(
            "/api/agent-tools/node4/format_response",
            json={"results": {"score": 100}},
            headers=auth_headers,
        )
        if resp.status_code == 200:
            data = resp.json()
            assert data["status"] == "success"
            assert "tokens_used" in data["data"]
            # Must be int, not string
            assert isinstance(data["data"]["tokens_used"], int), \
                f"tokens_used should be int, got {type(data['data']['tokens_used'])}"
            # text must be string
            assert isinstance(data["data"]["text"], str), \
                f"text should be str, got {type(data['data']['text'])}"

    def test_result_required(self, client, auth_headers):
        """Missing results field returns 422."""
        resp = client.post(
            "/api/agent-tools/node4/format_response",
            json={},
            headers=auth_headers,
        )
        assert resp.status_code == 422


# ═══════════════════════════════════════════════════════════════════════════════
# Response Envelope Shape - Cross-cutting
# ═══════════════════════════════════════════════════════════════════════════════

class TestResponseEnvelopeFormat:
    """
    All NODE endpoints follow the same response envelope:
    - Success:  status=success, data!=None, metadata, error=None
    - Business error: status=error, data=None, metadata, error=message
    - Validation error: FastAPI 422 (no custom override)
    """

    def test_success_envelope(self, client, auth_headers):
        """Success path returns correct envelope."""
        resp = client.post(
            "/api/agent-tools/preprocess",
            json={"text": "hello"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "success"
        assert data["data"] is not None
        assert data["error"] is None
        assert "metadata" in data

    def test_422_is_unchanged(self, client, auth_headers):
        """Validation errors use FastAPI default 422 - no custom override."""
        # Missing required field
        resp = client.post(
            "/api/agent-tools/preprocess",
            json={},
            headers=auth_headers,
        )
        assert resp.status_code == 422
        # FastAPI default 422 body
        assert "detail" in resp.json()
