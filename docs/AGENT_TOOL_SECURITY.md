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
- MCP-style content blocks
- LangChain tool payloads
- custom tool adapters declared in config

## Related Docs

- [Policy spec](POLICY_SPEC.md)
- [MCP tool security guide](MCP_TOOL_SECURITY.md)
- [Developer setup](DEVELOPER_SETUP.md)
