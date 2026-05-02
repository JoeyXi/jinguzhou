# Changelog

## 0.3.0 - Agent Ecosystem

- Added LlamaIndex adapter helper module and runnable policy example.
- Added OpenAI Agents adapter helper module and runnable policy example.
- Completed v0.3 release validation across MCP, LangChain, LlamaIndex, and OpenAI Agents examples.
- Updated public docs, release notes, package metadata, Docker, npm, and Helm versions for 0.3.0.

## 0.3.0-beta - MCP And LangChain Integrations

- Added MCP adapter helper module for JSON-RPC `tools/call` payloads.
- Added LangChain-style pre-execution tool middleware.
- Added MCP tool security and LangChain tool policy runnable examples.
- Added tests for MCP normalization and LangChain guarded tool execution.
- Expanded release validation to cover the new integration examples.

## 0.3.0-alpha - Agent Ecosystem Foundation

- Added public adapter foundation imports under `jinguzhou.adapters`.
- Added normalized tool-call handling for direct adapter usage.
- Added extraction support for MCP JSON-RPC `tools/call`, LlamaIndex-style top-level tool calls, and OpenAI Agents-style `function_call` output items.
- Expanded JSONPath-like extractor support for bracket notation, wildcards, indexes, negative indexes, and recursive key lookup.
- Added `domain_regex` policy matching for network target controls.
- Added first-pass file, network, and database tool policy packs.
- Added tests and release validation for the new adapter, extractor, and policy-pack behavior.

## 0.2.1 - Developer Infrastructure

- Added Docker Compose gateway startup.
- Added a developer quickstart example.
- Added text output mode for local CLI checks and config validation.
- Added config validation error payloads with stable hints.
- Added optional Postgres audit backend.
- Added npm launcher package scaffold.
- Added PyPI release workflow using GitHub trusted publishing.
- Added starter Helm chart.
- Added local dashboard and pending approval extension endpoints.
- Added optional admin API key guard for control-plane endpoints.
- Revised public docs for a more direct engineering tone.
- Expanded release validation to cover text output, quickstart, and distribution files.

## 0.2.0 - Developer Experience Preview

- Added `jinguzhou init` to generate starter runtime config and local rule packs.
- Added `jinguzhou validate-config` to verify config, policy files, and gateway wiring before startup.
- Added Dockerfile and Docker quick start for local gateway runs.
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
