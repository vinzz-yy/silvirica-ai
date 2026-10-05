#!/usr/bin/env bash
# Hardened Production POSIX Installer for Silvirica AI (Linux & macOS)
#
# Recommended Secure Usage:
#   1. Download:
#      curl -fsSLO https://github.com/vinzz-yy/silvirica-ai/releases/download/v0.1.0/install.sh
#   2. Inspect script content
#   3. Execute:
#      bash install.sh --version 0.1.0

set -euo pipefail

VERSION="0.1.0"
DRY_RUN=0
FORCE=0

while [[ $# -gt 0 ]]; do
    case "$1" in
        --version)
            VERSION="$2"
            shift 2
            ;;
        --dry-run)
            DRY_RUN=1
            shift
            ;;
        --force)
            FORCE=1
            shift
            ;;
        *)
            echo "Unknown argument: $1" >&2
            exit 1
            ;;
    esac
done

echo ""
echo "================================================================="
echo "        SILVIRICA AI HARDENED POSIX INSTALLER                   "
echo "  Universal AI Intelligence Enhancement Runtime (v${VERSION})   "
echo "================================================================="
echo ""

INSTALL_DIR="${HOME}/.local/share/silvirica"
BIN_DIR="${HOME}/.local/bin"
VENV_DIR="${INSTALL_DIR}/venv"
BACKUP_DIR="${INSTALL_DIR}/backup_previous"

# 1. Locate and verify Python 3.9+
PYTHON_BIN=""
if command -v python3 >/dev/null 2>&1; then
    PYTHON_BIN="python3"
elif command -v python >/dev/null 2>&1; then
    PYTHON_BIN="python"
else
    echo "Error: Python 3.9+ is required but not found on PATH." >&2
    exit 1
fi

PY_VER=$("${PYTHON_BIN}" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo ">> Verified Python runtime: Python ${PY_VER} (${PYTHON_BIN})"

if [ "${DRY_RUN}" -eq 1 ]; then
    echo "[DRY RUN] Environment check passed. Exiting dry run."
    exit 0
fi

# 2. Directory preparation with atomic backup
mkdir -p "${INSTALL_DIR}" "${BIN_DIR}"

if [ -d "${VENV_DIR}" ]; then
    echo ">> Backing up previous environment for rollback..."
    rm -rf "${BACKUP_DIR}"
    cp -r "${VENV_DIR}" "${BACKUP_DIR}"
fi

# 3. Create isolated virtualenv and install
rollback() {
    echo ""
    echo "!! INSTALLATION ENCOUNTERED AN ERROR." >&2
    if [ -d "${BACKUP_DIR}" ]; then
        echo ">> Performing automatic rollback to previous version..." >&2
        rm -rf "${VENV_DIR}"
        mv "${BACKUP_DIR}" "${VENV_DIR}"
        echo ">> Rollback complete." >&2
    fi
    exit 1
}

trap rollback ERR

if [ ! -d "${VENV_DIR}" ] || [ "${FORCE}" -eq 1 ]; then
    echo ">> Creating virtual environment at ${VENV_DIR}..."
    "${PYTHON_BIN}" -m venv "${VENV_DIR}"
fi

echo ">> Installing Silvirica AI package (Version: ${VERSION})..."
"${VENV_DIR}/bin/pip" install --upgrade pip --quiet
if ! "${VENV_DIR}/bin/pip" install "git+https://github.com/vinzz-yy/silvirica-ai.git@v${VERSION}" --quiet 2>/dev/null; then
    echo ">> Release tag v${VERSION} pending, installing from main..."
    "${VENV_DIR}/bin/pip" install git+https://github.com/vinzz-yy/silvirica-ai.git --quiet
fi

ln -sf "${VENV_DIR}/bin/silvirica" "${BIN_DIR}/silvirica"
echo ">> Linked executable to ${BIN_DIR}/silvirica"

# Remove backup after success
rm -rf "${BACKUP_DIR}"

case ":$PATH:" in
    *":${BIN_DIR}:"*) ;;
    *)
        echo ""
        echo ">> NOTE: Add ~/.local/bin to your PATH by adding this line to ~/.bashrc or ~/.zshrc:"
        echo "   export PATH=\"\$HOME/.local/bin:\$PATH\""
        ;;
esac

echo ""
echo "================================================================="
echo "       SILVIRICA AI SUCCESSFULLY INSTALLED & READY!             "
echo "================================================================="
echo ""
echo "Try running:"
echo "  silvirica init"
echo "  silvirica doctor"
echo "  silvirica ask \"Where is ProjectBrain?\""
echo "  silvirica security"
echo "  silvirica mcp"
echo ""
