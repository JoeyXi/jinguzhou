# Security Policy

Jinguzhou is an early-stage safety gateway. Treat it as a defense layer, not a
complete safety guarantee.

## Reporting Issues

Please open a private security advisory or contact the maintainers before
publishing details about vulnerabilities that could weaken policy enforcement,
approval tokens, audit integrity, or tool-call controls.

## Safety Notes

- Keep approval secrets private.
- Use short approval token TTLs.
- Do not log full prompts in production unless you have a privacy review.
- Run destructive tools behind human review or explicit policy allowlists.
