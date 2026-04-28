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

Goal: reduce the steps required to install, initialize, validate, and run a
local gateway.

- Versioned `0.2.0` release with changelog notes
- `jinguzhou init` starter config generation
- `jinguzhou validate-config` runtime and policy validation
- Dockerfile and documented container quick start
- Docker Compose gateway quick start
- developer quickstart example
- clearer README setup path
- developer setup guide
- release validation updated for 0.2
- tests for new developer-facing commands
- CLI text output for local checks and config validation
- optional Postgres audit backend
- npm launcher package scaffold
- PyPI release workflow
- starter Helm chart
- local dashboard status page

See [0.2 release plan](V0.2_RELEASE_PLAN.md).

## External Release Tasks

These require registry, cluster, or organization configuration outside the
repository:

- publish `jinguzhou` to PyPI
- publish `@jinguzhou/cli` to npm
- configure GitHub trusted publishing environment `pypi`
- render and test the Helm chart in a Kubernetes cluster
- build and push a container image
- choose the approval inbox provider for Slack or Teams
- choose the identity provider for OIDC or SSO
