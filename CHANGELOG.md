# Changelog

## 0.2.0 - Developer Experience Preview

- Added `jinguzhou init` to generate starter runtime config and local rule packs.
- Added `jinguzhou validate-config` to verify config, policy files, and gateway wiring before startup.
- Added Dockerfile and Docker quick start for local gateway runs.
- Added Docker Compose gateway startup.
- Added a developer quickstart example.
- Added text output mode for local CLI checks and config validation.
- Added friendlier config validation error payloads.
- Added optional Postgres audit backend.
- Added npm launcher package scaffold.
- Added PyPI release workflow using GitHub trusted publishing.
- Added starter Helm chart.
- Added local dashboard and pending approval extension endpoints.
- Added optional admin API key guard for control-plane endpoints.
- Added developer setup documentation and a 0.2 release plan.
- Improved README onboarding for install, initialization, validation, and gateway startup.
- Updated release validation to cover initialization and config validation.

## 0.1.0 - First Preview

- Added OpenAI-compatible gateway for chat completions.
- Added YAML policy loading, merging, deterministic matching, and decision ranking.
- Added input, output, and tool-stage policy enforcement.
- Added configurable tool adapter registry for OpenAI, MCP/content-block, LangChain, and custom tool protocols.
- Added nested JSONPath-like field extraction for tool payloads.
- Added structured JSONL audit logging, query, and replay CLI.
- Added signed human approval tokens for `require_human_review` decisions.
- Added starter rule packs for human safety, prompt injection, privacy, and tool use.
- Added runtime configuration, example config, tests, and release documentation.
