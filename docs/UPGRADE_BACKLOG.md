# Upgrade Backlog

This file tracks work after the current gateway, policy, audit, tool-guard, and
adapter-registry baseline.

## High Priority

- Policy pack version pinning and migration checks
- Tool action simulation mode for dry-run enforcement
- Policy decision explainability with matched fact snapshots
- Provider retry policy and circuit breaker behavior
- Streaming response guardrails for incremental output checking

## Security Hardening

- Signed audit records or tamper-evident audit chains
- Secret scanning for nested payloads and binary-safe logging redaction
- Tenant or environment scoping for policies
- Stronger prompt injection detectors beyond keyword rules
- Safer defaults for shell, network, and browser tools

## Platform Extensibility

- Formal adapter packages for OpenAI tools, LangChain, MCP, and local runtimes
- Nested JSONPath-style field extractors instead of top-level-only extraction
- Per-tool schema hints to enrich extractor normalization
- Rule authoring linter and policy test fixture generator
- Rule packs for medical, legal, enterprise data, and cyber abuse domains

## Operations

- Metrics and tracing integration
- Structured health endpoint with provider and policy readiness
- Config validation CLI
- Docker image and containerized quick start
- CI matrix for Python versions and linting

## Developer Experience

- End-to-end sample app with guarded tool execution
- Cookbook for writing custom tool adapters
- More readable CLI output for policy decisions
- Example policy packs for sandboxed agents and enterprise bots
