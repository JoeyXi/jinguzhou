# Agent Tool Security

Jinguzhou evaluates tool calls before an agent runtime executes them.

## Scope

- shell commands
- file reads and writes
- network requests
- database queries
- other tool protocols normalized through adapters

## Policy Controls

Tool rules can match:

- tool name
- command fragments
- file paths
- path sensitivity labels
- target domains
- database operation types

## Example Tool Rule

```yaml
- id: tool.database.destructive.block
  stage: tool
  category: database
  severity: critical
  action: block
  reason: Destructive database operations are blocked.
  match:
    tool_name: database.query
    db_operation_in:
      - drop
      - truncate
      - alter
```

## Runtime Integrations

Current adapter coverage includes:

- OpenAI tool calls
- MCP-style content blocks and MCP JSON-RPC `tools/call`
- LangChain tool payloads and pre-execution middleware
- LlamaIndex-style top-level tool call payloads
- OpenAI Agents-style `function_call` output items
- custom tool adapters declared in config

The `jinguzhou.integrations.langchain` middleware raises a
`ToolPolicyViolation` before a blocked or review-required tool is executed.

## v0.3 Policy Packs

The alpha rule packs split agent tool controls by risk area:

- `rules/tool_file_access.yaml`
- `rules/tool_network_access.yaml`
- `rules/tool_database_access.yaml`

These packs evaluate normalized facts from the extractor layer, including file
paths, path sensitivity, target domains, SQL text, and database operation types.

## Related Docs

- [Policy spec](POLICY_SPEC.md)
- [MCP tool security guide](MCP_TOOL_SECURITY.md)
- [Developer setup](DEVELOPER_SETUP.md)
