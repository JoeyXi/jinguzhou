# Jinguzhou Development Plan

Jinguzhou is an open-source, model-agnostic safety gateway for LLM applications.
Its first goal is to give developers a practical way to define, enforce, and
audit human safety boundaries around model input, model output, tool calls, and
real-world actions.

The project should start as a small but serious system:

- LLM safety proxy gateway
- Policy and rule engine
- Audit trail and replay foundation

It should not depend on any single model provider, and it should not rely on
prompting alone as the safety mechanism.

## Product Positioning

Jinguzhou is the "tightening hoop" outside the model.

The model can become more powerful, change vendors, run locally, or be composed
inside agent frameworks. Jinguzhou remains an external enforcement layer that
checks requests, responses, and actions against human-defined safety policies.

## Core Principles

1. Model-agnostic by default
2. External enforcement instead of model self-restraint
3. Human-defined policy as the source of truth
4. Default-deny for high-risk tool use and real-world actions
5. Every decision should be explainable and auditable
6. Rules should be versioned, testable, and community-extensible
7. The system should degrade safely when classifiers or providers fail

## MVP Scope

The MVP should answer one question well:

Can a developer put Jinguzhou in front of an LLM app and reliably control what
requests, outputs, and tool actions are allowed?

### Included In MVP

- HTTP proxy gateway for chat completion style requests
- Provider adapter for OpenAI-compatible APIs
- Policy file loaded from YAML
- Rule engine with deterministic checks
- Optional classifier hook for semantic risk detection
- Input guard
- Output guard
- Tool/action guard
- Audit event logging to JSONL
- CLI for local checks and gateway startup
- Minimal SDK for Python integration
- Baseline safety rules
- Test suite for rule decisions

### Excluded From MVP

- Full UI dashboard
- Enterprise RBAC
- Distributed policy sync
- Advanced machine-learning risk scoring
- Browser extension
- Kubernetes operator
- Multi-tenant SaaS features

These can come after the gateway, policy engine, and audit foundation are stable.

## Target Users

- Developers building LLM apps
- AI agent framework users
- Open-source model deployers
- Security engineers evaluating AI behavior
- Teams that need auditability before letting AI use tools

## System Architecture

```text
Client / App
    |
    v
Jinguzhou Gateway
    |
    |-- Input Guard
    |     |-- Policy Engine
    |     |-- Risk Detectors
    |
    |-- LLM Provider Adapter
    |     |-- OpenAI-compatible API
    |     |-- Future: Anthropic, Gemini, Ollama, vLLM
    |
    |-- Output Guard
    |     |-- Policy Engine
    |     |-- Risk Detectors
    |
    |-- Tool Guard
    |     |-- Permission Rules
    |     |-- Human Approval Hooks
    |
    |-- Audit Logger
          |-- JSONL Events
          |-- Future: SQLite/Postgres/exporters
```

## Main Components

### 1. Gateway

The gateway receives app requests, applies policy, forwards allowed requests to
the underlying model provider, checks responses, and returns a final decision.

Responsibilities:

- Expose OpenAI-compatible endpoints where possible
- Normalize requests into internal event objects
- Run input checks before provider calls
- Run output checks after provider calls
- Intercept tool calls before execution
- Emit audit events for every decision
- Return structured safety errors when blocked

Initial endpoint targets:

- `POST /v1/chat/completions`
- `GET /health`
- `GET /version`

### 2. Policy Engine

The policy engine evaluates rules against normalized context.

Policy inputs:

- User prompt
- System prompt
- Conversation metadata
- Model name
- Provider name
- Requested tools
- Model output
- Proposed tool call
- Runtime environment metadata

Policy outputs:

- `allow`
- `warn`
- `block`
- `redact`
- `require_human_review`

Every decision should include:

- Decision type
- Matching rule IDs
- Human-readable reason
- Risk category
- Severity
- Optional remediation message

### 3. Rule Format

Rules should be readable, versionable, and easy to test.

Example:

```yaml
version: 1
name: baseline-human-safety
rules:
  - id: human_harm.instructions.block
    stage: input
    category: human_harm
    severity: critical
    action: block
    match:
      any_keywords:
        - "how to kill"
        - "make a bomb"
        - "poison someone"
    reason: "Request appears to ask for instructions that could harm people."

  - id: tool.shell.require_review
    stage: tool
    category: tool_use
    severity: high
    action: require_human_review
    match:
      tool_name: "shell"
      command_contains:
        - "rm"
        - "curl"
        - "chmod"
    reason: "Shell command may modify system state or fetch remote code."
```

MVP match operators:

- `any_keywords`
- `all_keywords`
- `regex`
- `tool_name`
- `command_contains`
- `metadata_equals`
- `model_in`
- `provider_in`

Later match operators:

- semantic classifier score
- embedding similarity
- code AST analysis
- file path sensitivity
- PII detection
- organization-specific allowlists

### 4. Risk Detectors

Risk detectors enrich policy evaluation. They should be optional and replaceable.

MVP detectors:

- Keyword detector
- Regex detector
- Prompt injection detector
- PII pattern detector
- Tool danger detector

Future detectors:

- LLM-based policy classifier
- Local small model classifier
- Malware/code risk detector
- Financial/legal/medical domain risk detector
- Jailbreak intent detector

### 5. Tool Guard

The tool guard controls actions, not just text.

This is one of the most important parts of Jinguzhou because real harm often
happens when models can execute tools.

MVP tool categories:

- `filesystem.read`
- `filesystem.write`
- `network.request`
- `shell.execute`
- `email.send`
- `database.query`
- `payment.execute`
- `browser.operate`

Default stance:

- Read-only actions can be allowed with logging
- Write actions require explicit policy
- Destructive actions require review
- External side effects require review
- Payment, identity, account, and production actions are blocked by default

### 6. Human Approval

The MVP can implement human approval as a structured pending decision rather than
a full UI workflow.

Initial behavior:

- Gateway returns `require_human_review`
- Audit event includes the requested action
- Caller can decide whether to retry with an approval token

Future behavior:

- Web approval console
- Slack/Discord/email approval
- Signed approval tokens
- Approval expiration
- Per-user approval authority

### 7. Audit System

Audit logs are part of the core product, not an add-on.

MVP storage:

- JSONL file

Each event should include:

- Event ID
- Timestamp
- Request ID
- Stage: input, output, tool, provider, system
- Policy version
- Rule IDs matched
- Decision
- Risk category
- Severity
- Provider/model
- Redacted prompt or output excerpt
- Tool call summary
- Latency
- Error details if any

Privacy stance:

- Logs should support redaction by default
- Full prompt logging should be explicitly configurable
- Secrets should never be logged

Future storage:

- SQLite
- Postgres
- OpenTelemetry
- SIEM export
- Audit replay UI

## Proposed Repository Structure

```text
jinguzhou/
  pyproject.toml
  README.md
  jinguzhou.txt
  docs/
    DEVELOPMENT_PLAN.md
    POLICY_SPEC.md
    AUDIT_SPEC.md
    ROADMAP.md
  src/
    jinguzhou/
      __init__.py
      cli.py
      gateway/
        app.py
        middleware.py
        schemas.py
      policy/
        engine.py
        loader.py
        models.py
        matchers.py
      guards/
        input_guard.py
        output_guard.py
        tool_guard.py
      detectors/
        keywords.py
        regex.py
        pii.py
        prompt_injection.py
      providers/
        base.py
        openai_compatible.py
      audit/
        events.py
        logger.py
        redaction.py
      approvals/
        tokens.py
        pending.py
  rules/
    baseline.yaml
    prompt_injection.yaml
    privacy.yaml
    tool_use.yaml
  examples/
    openai_proxy/
    local_agent_tool_guard/
  tests/
    test_policy_engine.py
    test_gateway.py
    test_audit_logger.py
    test_tool_guard.py
```

## Technology Choices

Recommended MVP stack:

- Python 3.11+
- FastAPI for the gateway
- Pydantic for schemas
- PyYAML or ruamel.yaml for policy files
- httpx for provider forwarding
- Typer for CLI
- pytest for tests
- JSONL for audit logs

Why Python first:

- Fastest path for AI developers
- Strong ecosystem for LLM integrations
- Easy CLI and HTTP gateway implementation
- Later SDKs can wrap the gateway from other languages

## CLI Design

Initial commands:

```bash
jinguzhou gateway --policy rules/baseline.yaml --target https://api.openai.com
jinguzhou check-input --policy rules/baseline.yaml --text "..."
jinguzhou check-output --policy rules/baseline.yaml --text "..."
jinguzhou check-tool --policy rules/tool_use.yaml --tool shell --payload '{"command":"rm -rf tmp"}'
jinguzhou audit tail --file .jinguzhou/audit.jsonl
```

## Configuration

Example project config:

```yaml
gateway:
  listen: "127.0.0.1:8787"
  target_provider: "openai-compatible"
  target_base_url: "https://api.openai.com"

policy:
  files:
    - "rules/baseline.yaml"
    - "rules/tool_use.yaml"
  default_action: "allow"
  high_risk_default_action: "require_human_review"

audit:
  enabled: true
  path: ".jinguzhou/audit.jsonl"
  log_full_prompts: false
  redact_secrets: true
```

## Milestones

### Milestone 0: Project Foundation

Deliverables:

- Repository structure
- README
- Development plan
- Python package setup
- Basic CLI skeleton
- Test setup

Exit criteria:

- `pytest` runs
- `jinguzhou --help` works

### Milestone 1: Policy Engine

Deliverables:

- Policy schema
- YAML loader
- Matchers
- Decision model
- Baseline rule pack
- Unit tests

Exit criteria:

- Can evaluate text and tool payloads against YAML rules
- Every decision includes matched rule IDs and reasons

### Milestone 2: Audit Logger

Deliverables:

- Audit event schema
- JSONL logger
- Redaction utilities
- CLI audit tail command
- Tests

Exit criteria:

- Every policy decision can be written as a structured audit event
- Sensitive values are redacted in default mode

### Milestone 3: Gateway MVP

Deliverables:

- FastAPI app
- OpenAI-compatible chat completions proxy
- Input guard before provider call
- Output guard after provider call
- Structured block response
- Request IDs and audit logging

Exit criteria:

- Existing OpenAI-compatible clients can point to Jinguzhou as base URL
- Unsafe input is blocked before provider call
- Unsafe output is blocked or redacted before response

### Milestone 4: Tool Guard

Deliverables:

- Tool call schema
- Tool policy evaluation
- Require-review decision flow
- Example guarded agent
- Tests for destructive and external side-effect actions

Exit criteria:

- Shell/network/filesystem-like actions can be allowed, blocked, or marked for review
- Tool decisions are audited

### Milestone 5: Developer Experience

Deliverables:

- Python SDK helpers
- Example apps
- Policy authoring docs
- Audit docs
- GitHub Actions CI

Exit criteria:

- A developer can add Jinguzhou to a sample app in under 10 minutes
- Rule authors can add tests for new rules

## Rule Packs

Initial built-in packs:

- `baseline`: general harmful content and unsafe assistance
- `prompt_injection`: instruction override, secret exfiltration, policy bypass
- `privacy`: PII, secrets, credentials, personal data leakage
- `tool_use`: filesystem, shell, network, database, payment, email actions

Future packs:

- `medical`
- `legal`
- `financial`
- `child_safety`
- `cybersecurity`
- `enterprise_data`
- `autonomous_agents`

## Testing Strategy

Policy tests:

- Rule match/no-match cases
- Precedence and conflict resolution
- Action selection
- Explanation quality

Gateway tests:

- Safe request forwarded
- Unsafe request blocked
- Provider error handling
- Output filtering
- Audit event emitted

Tool tests:

- Read-only action allowed
- Destructive action requires review
- External side effect blocked or reviewed
- Approval token path works after implementation

Security tests:

- Prompt injection examples
- Secret leakage examples
- Log redaction examples
- Malformed policy files
- Malformed provider responses

## Policy Conflict Resolution

Suggested order:

1. `block`
2. `require_human_review`
3. `redact`
4. `warn`
5. `allow`

The strictest matching decision wins unless a rule explicitly overrides this with
priority.

## Open Design Questions

- Should the first public API be only a gateway, or gateway plus SDK?
- Should semantic risk classification be local-only in MVP, provider-based, or postponed?
- How strict should the default baseline rules be?
- Should policy rules use a custom DSL later, or stay YAML-first?
- What should count as a "real-world action" in v1?
- How should approval tokens be signed and expired?

## First Implementation Order

1. Create Python package skeleton
2. Implement policy models and YAML loader
3. Implement deterministic matchers
4. Add baseline rules
5. Implement audit event model and JSONL logger
6. Add CLI check commands
7. Add FastAPI gateway
8. Add OpenAI-compatible provider forwarding
9. Add input/output guard integration
10. Add tool guard and example agent

## Definition Of Done For First Public Preview

- Installable with `pip`
- Runs as local HTTP gateway
- Loads custom YAML policies
- Provides baseline rule packs
- Blocks unsafe input
- Checks unsafe output
- Controls tool/action requests
- Writes structured audit logs
- Has tests for core behavior
- Has examples and policy documentation

