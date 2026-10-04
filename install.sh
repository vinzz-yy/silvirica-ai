#!/usr/bin/env bash
# Silvirica AI Installer for Linux & macOS
# Usage: curl -fsSL https://raw.githubusercontent.com/vinzz-yy/silvirica-ai/main/install.sh | bash

set -euo pipefail

echo ""
echo "================================================================="
echo "                SILVIRICA AI POSIX INSTALLER                    "
echo "     Universal AI Intelligence Enhancement Runtime (V0.1.0)     "
echo "================================================================="
echo ""

INSTALL_DIR="${HOME}/.local/share/silvirica"
BIN_DIR="${HOME}/.local/bin"
VENV_DIR="${INSTALL_DIR}/venv"

mkdir -p "${INSTALL_DIR}" "${BIN_DIR}"

PYTHON_BIN=""
if command -v python3 >/dev/null 2>&1; then
    PYTHON_BIN="python3"
elif command -v python >/dev/null 2>&1; then
    PYTHON_BIN="python"
else
    echo "Error: Python 3.9+ is required but not found on PATH." >&2
    exit 1
fi

echo ">> Using Python: $(${PYTHON_BIN} --version)"

if [ ! -d "${VENV_DIR}" ]; then
    echo ">> Creating virtual environment at ${VENV_DIR}..."
    "${PYTHON_BIN}" -m venv "${VENV_DIR}"
fi

echo ">> Installing Silvirica AI package..."
"${VENV_DIR}/bin/pip" install --upgrade pip --quiet
"${VENV_DIR}/bin/pip" install git+https://github.com/vinzz-yy/silvirica-ai.git --quiet

ln -sf "${VENV_DIR}/bin/silvirica" "${BIN_DIR}/silvirica"

echo ">> Linked executable to ${BIN_DIR}/silvirica"

if [[ ":$PATH:" != *":${BIN_DIR}:"* ]]; then
    echo ">> NOTE: Add ~/.local/bin to your PATH by adding this line to ~/.bashrc or ~/.zshrc:"
    echo "   export PATH=\"\$HOME/.local/bin:\$PATH\""
fi

echo ""
echo "================================================================="
echo "       SILVIRICA AI SUCCESSFULLY INSTALLED & READY!             "
echo "================================================================="
echo ""
echo "Try running:"
echo "  silvirica init"
echo "  silvirica doctor"
echo "  silvirica ask \"Where is ProjectBrain?\""
echo "  silvirica benchmark"
echo "  silvirica dashboard"
echo ""
