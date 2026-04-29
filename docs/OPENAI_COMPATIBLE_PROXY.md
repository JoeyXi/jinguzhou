# OpenAI-Compatible Proxy

Jinguzhou can sit in front of clients that already speak the OpenAI chat
completions API.

## What This Covers

- request and response policy checks
- OpenAI-compatible request forwarding
- audit logging for model and tool decisions
- approval flow for blocked or review-required actions

## Endpoint

Current gateway endpoint:

```text
POST /v1/chat/completions
```

This lets an existing OpenAI-compatible client point to Jinguzhou as its base
URL while keeping the rest of the request shape unchanged.

## Example Runtime Config

```yaml
provider:
  type: "openai-compatible"
  base_url: "https://api.openai.com"
  api_key_env: "OPENAI_API_KEY"
```

## Typical Uses

- add policy checks in front of an existing OpenAI-compatible application
- audit prompt, output, and tool-call decisions without changing model code
- require human approval before a risky tool call is executed

## Related Docs

- [README](../README.md)
- [Policy spec](POLICY_SPEC.md)
- [Approval flow](APPROVALS.md)
