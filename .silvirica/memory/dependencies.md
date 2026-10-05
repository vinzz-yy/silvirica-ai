# Dependencies

## Runtime Dependencies
- **Python**: `>=3.9` (Tested on 3.9, 3.10, 3.11, 3.12, 3.14)
- **PyYAML**: `>=6.0` (YAML frontmatter parsing for skills and configuration)
- **Requests**: `>=2.31.0` (HTTP client for external model providers and MCP daemon)

## Development Dependencies
- **pytest**: `>=7.0.0` (Optional test runner; fully compatible with stdlib `unittest`)

## Storage & Internal Engines
- **SQLite 3**: Built into Python standard library; used for Knowledge Graph (`graph.db`), Symbols index (`symbols.db`), and Telemetry (`telemetry.db`).
- **File System Cache**: Plain JSON / hashed binary format under `.silvirica/cache/`.
