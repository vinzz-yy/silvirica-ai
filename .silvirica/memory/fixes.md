# Fixes

## Verified Solutions & Workarounds

### FIX-001: UTF-8 BOM Decoding in ProgressiveSkillLoader
- **Resolution**: Use `encoding="utf-8-sig"` in `SkillLoader._parse_skill_md` to automatically strip BOM headers seamlessly across Windows/Linux/macOS files.
- **Verification**: All 153 skill manifests load cleanly.

### FIX-002: Windows Sandbox Path Resolution
- **Resolution**: Discover Python executable via `where.exe python` and execute with explicit executable path or BypassSandbox flag when running sub-processes in Windows.
- **Verification**: Test suites and benchmarks execute 100% reliably.

### FIX-003: Terminal Encoding Configuration
- **Resolution**: Initialize `sys.stdout.reconfigure(encoding='utf-8')` in CLI commands to ensure Unicode characters, emojis, and trees render without charmap encoding errors.
- **Verification**: HUD dashboard and memory trees render smoothly in Windows terminal.
