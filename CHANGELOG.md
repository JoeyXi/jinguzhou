# Changelog

## 0.1.0 - First Preview

- Added OpenAI-compatible safety gateway for chat completions.
- Added YAML policy loading, merging, deterministic matching, and decision ranking.
- Added input, output, and tool-stage policy enforcement.
- Added configurable tool adapter registry for OpenAI, MCP/content-block, LangChain, and custom tool protocols.
- Added nested JSONPath-like field extraction for tool payloads.
- Added structured JSONL audit logging, query, and replay CLI.
- Added signed human approval tokens for `require_human_review` decisions.
- Added starter rule packs for human safety, prompt injection, privacy, and tool use.
- Added runtime configuration, example config, tests, and release documentation.
