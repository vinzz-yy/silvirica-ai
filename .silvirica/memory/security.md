# Security

## Redaction & Protection Guidelines

### Automatic Secret Redaction
Silvirica automatically redacts sensitive credentials prior to transmitting prompts to external LLMs:
- **API Keys**: OpenAI (`sk-...`), Anthropic (`sk-ant-...`), Google AI (`AIza...`), GitHub tokens (`ghp_...`, `github_pat_...`), AWS Access Keys (`AKIA...`).
- **Private Keys**: RSA/DSA/EC private key blocks (`BEGIN PRIVATE KEY`).
- **Database Connection Strings**: PostgreSQL, MySQL, MongoDB, Redis connection URIs with embedded passwords (`postgresql://user:pass@host/db`).
- **Authentication Headers**: `Bearer <token>`, `Basic <base64>`, JWT signatures (`eyJ...`).
- **Environment Secrets**: High-entropy strings assigned to `SECRET_KEY`, `PASSWORD`, `API_TOKEN` in `.env` files.

### Vulnerability Guardrails
- **Destructive Queries**: Intercepts unconstrained `DROP TABLE`, `TRUNCATE`, `rm -rf /` commands in generated code.
- **SQL Injection**: Enforces parameterized queries across database adapters.
- **Path Traversal**: Validates file paths stay within the active project workspace.
