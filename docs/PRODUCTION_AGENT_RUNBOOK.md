# Production Agent Runbook (learnbuild.dev)

## 1. Required Env Before Deploy
- `AGENT_ENABLED=true`
- `LLM_SPACE_URL` set to production model endpoint
- `LLM_API_TOKEN` set for private model endpoint
- `AGENT_INTERNAL_TOOL_KEY` strong secret (>= 24 chars, non-default)
- `METRICS_INTERNAL_KEY` set and rotated
- Optional override: `AGENT_TOOLS_CONFIG_JSON`

## 2. Security Rules
- Block public access to `/api/agent-tools/*` at reverse proxy.
- Allow only backend internal calls with `X-Agent-Internal-Key`.
- Restrict `/internal/metrics/orchestration` and `/internal/alerts/orchestration` with `X-Internal-Metrics-Key`.

## 3. Health and Readiness
- `GET /health/live`: process liveness
- `GET /health/ready`: DB + Redis + LLM/circuit readiness
- Deployment should gate traffic on readiness, not root endpoint.

## 4. Alert Baseline
- `ALERT_LLM_TIMEOUT_MIN=5`
- `ALERT_NODE4_FALLBACK_MIN=5`
- `ALERT_TOOLS_FAILURE_MIN=5`
- `ALERT_CIRCUIT_OPEN_MIN=3`

Trigger checks using:
- `GET /internal/alerts/orchestration` with `X-Internal-Metrics-Key` header

## 5. Canary Checklist
1. Enable canary traffic only for internal users first.
2. Run single-query chatbot scenarios (grade, schedule, student info).
3. Run compound-query scenarios (grade + schedule).
4. Run multi-turn class suggestion flow.
5. Simulate LLM down (invalid URL or network block) and verify fallback behavior.
6. Watch metrics and alerts for 24-48h before full rollout.

## 6. Rollback Procedure
1. Set `AGENT_ENABLED=false`.
2. Redeploy backend service.
3. Confirm `/health/ready` is `ready`.
4. Run smoke chat checks from UI.

## 7. CI Test Command Standard
From repo root in backend container/workspace:

```bash
python -m pytest \
  tests/test_api_call.py \
  tests/agents/test_agent_orchestrator.py \
  tests/agents/test_orchestration_integration.py \
  -v --tb=short
```
