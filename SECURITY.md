# Security Policy

## Reporting Security Issues

The Silvirica AI team takes defensive security and developer credential privacy extremely seriously.

If you discover a security vulnerability or sensitive information exposure risk within Silvirica AI:
1. Please do **NOT** open a public GitHub issue.
2. Email your findings and reproduction steps to `security@silvirica.ai` or submit a private security advisory on GitHub.
3. We will acknowledge receipt within 24 hours and provide a timeline for remediation.

---

## Silvirica AI Defensive Design Principles

1. **Local-First Processing**: Silvirica indexes AST symbols, knowledge graphs, and memory vaults entirely locally on your machine using SQLite and deterministic regex/AST parsers.
2. **Automated Secret Redaction**: All compiled prompt contexts are passed through the `SecretRedactor` to strip API keys, private keys, passwords, and tokens before any external model request.
3. **Non-Destructive Initialization**: `silvirica init` strictly creates `.silvirica/` metadata and will never alter, overwrite, or mutate application business logic.
4. **Strict Guardrails**: Prohibits automatic destructive database alterations (`DROP TABLE`, `TRUNCATE`), unauthorized migration editing, and direct modification of secret credential files (`.env`, `credentials.json`).
