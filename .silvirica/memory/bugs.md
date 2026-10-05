# Bugs

## Known & Tracked Issues

### BUG-001: UTF-8 BOM Header in SKILL.md Files
- **Symptom**: Skills starting with UTF-8 byte order mark (`\ufeff`) failed frontmatter extraction when opened with standard `utf-8` decoding.
- **Root Cause**: Windows editor files occasionally prepend UTF-8 BOM headers.
- **Reference Fix**: [[Fixes#FIX-001]]

### BUG-002: Windows Sandbox Python Executable Resolution
- **Symptom**: Executing `python` directly inside sandboxes on Windows can fail if the binary resides outside the local workspace.
- **Root Cause**: Virtual environment / user-level AppData path restrictions.
- **Reference Fix**: [[Fixes#FIX-002]]

### BUG-003: Terminal Unicode Output in Windows CP1252 Consoles
- **Symptom**: `print()` crashing with `UnicodeEncodeError: 'charmap'` when outputting UTF-8 characters on Windows cmd.
- **Root Cause**: Windows default code page is often cp1252.
- **Reference Fix**: [[Fixes#FIX-003]]
