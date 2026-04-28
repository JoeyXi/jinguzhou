# Roadmap

## Phase 1

- package skeleton
- policy schema and loader
- audit logger
- CLI checks

## Phase 2

- FastAPI gateway
- OpenAI-compatible forwarding
- input/output guards

## Phase 3

- tool guard
- approval flow
- example integrations

## Phase 4

- richer detectors
- better rule packs
- stronger replay and audit tooling

## Completed In 0.1.0 Preview

- Gateway main flow
- Policy engine
- Audit logging
- Audit query and replay CLI
- Tool guard
- Tool adapter registry
- Nested field extraction
- Human approval tokens

## 0.2.0 Developer Experience

Goal: make Jinguzhou easy to install, initialize, validate, and run as a local
developer gateway.

- Versioned `0.2.0` release with changelog notes
- `jinguzhou init` starter config generation
- `jinguzhou validate-config` runtime and policy validation
- Dockerfile and documented container quick start
- clearer README onboarding path
- developer setup guide
- release validation updated for 0.2
- tests for new developer-facing commands

See [0.2 release plan](V0.2_RELEASE_PLAN.md).
