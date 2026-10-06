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
RELEASE=""
CHANNEL="release"
EXPECTED_SHA256=""
DRY_RUN=0
FORCE=0

while [[ $# -gt 0 ]]; do
    case "$1" in
        --version)
            VERSION="$2"
            shift 2
            ;;
        --release)
            RELEASE="$2"
            shift 2
            ;;
        --channel)
            CHANNEL="$2"
            shift 2
            ;;
        --expected-sha256)
            EXPECTED_SHA256="$2"
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

TARGET_VERSION="${RELEASE:-$VERSION}"
TARGET_VERSION="${TARGET_VERSION#v}"
RELEASE_TAG="v${TARGET_VERSION}"

echo ""
echo "================================================================="
echo "        SILVIRICA AI HARDENED POSIX INSTALLER                   "
echo "  Universal AI Intelligence Enhancement Runtime (v${TARGET_VERSION})   "
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

"${PYTHON_BIN}" -c "import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)" || {
    echo "Error: Python 3.9+ is required." >&2
    exit 1
}

PY_VER=$("${PYTHON_BIN}" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}')")
echo ">> Verified Python runtime: Python ${PY_VER} (${PYTHON_BIN})"

if [ -n "${EXPECTED_SHA256}" ]; then
    EXPECTED_SHA256=$(echo "${EXPECTED_SHA256}" | tr '[:upper:]' '[:lower:]' | tr -d '[:space:]')
    if [ ${#EXPECTED_SHA256} -ne 64 ]; then
        echo "Error: --expected-sha256 must be a 64-character SHA-256 hash string." >&2
        exit 1
    fi
fi

if [ "${DRY_RUN}" -eq 1 ]; then
    echo "[DRY RUN] Environment check passed. Installation target: ${VENV_DIR}"
    echo "[DRY RUN] Exiting dry run."
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
    elif [ -d "${VENV_DIR}" ]; then
        rm -rf "${VENV_DIR}"
    fi
    exit 1
}

trap rollback ERR

if [ ! -d "${VENV_DIR}" ] || [ "${FORCE}" -eq 1 ]; then
    echo ">> Creating virtual environment at ${VENV_DIR}..."
    "${PYTHON_BIN}" -m venv "${VENV_DIR}"
fi

VENV_PY="${VENV_DIR}/bin/python"

echo ">> Upgrading pip inside virtual environment..."
"${VENV_PY}" -m pip install --upgrade pip --quiet || true

if [ -n "${EXPECTED_SHA256}" ]; then
    echo ">> Downloading and verifying package artifact with SHA-256..."
    TEMP_PKG="${INSTALL_DIR}/silvirica-pkg.tar.gz"
    DOWNLOAD_URL="https://github.com/vinzz-yy/silvirica-ai/archive/refs/tags/${RELEASE_TAG}.tar.gz"
    curl -fsSL "${DOWNLOAD_URL}" -o "${TEMP_PKG}"
    
    if command -v sha256sum >/dev/null 2>&1; then
        ACTUAL_HASH=$(sha256sum "${TEMP_PKG}" | awk '{print $1}')
    elif command -v shasum >/dev/null 2>&1; then
        ACTUAL_HASH=$(shasum -a 256 "${TEMP_PKG}" | awk '{print $1}')
    else
        ACTUAL_HASH=$("${VENV_PY}" -c "import hashlib; print(hashlib.sha256(open('${TEMP_PKG}','rb').read()).hexdigest())")
    fi
    ACTUAL_HASH=$(echo "${ACTUAL_HASH}" | tr '[:upper:]' '[:lower:]' | tr -d '[:space:]')

    if [ "${ACTUAL_HASH}" != "${EXPECTED_SHA256}" ]; then
        rm -f "${TEMP_PKG}"
        echo "Error: SHA-256 checksum mismatch! Expected ${EXPECTED_SHA256}, got ${ACTUAL_HASH}." >&2
        exit 1
    fi
    echo ">> SHA-256 checksum verified successfully."
    "${VENV_PY}" -m pip install "${TEMP_PKG}" --quiet
    rm -f "${TEMP_PKG}"
elif [ "${CHANNEL}" = "main" ] || [ "${CHANNEL}" = "dev" ]; then
    echo ">> Installing Silvirica AI from main branch (development channel)..."
    "${VENV_PY}" -m pip install "git+https://github.com/vinzz-yy/silvirica-ai.git" --quiet
else
    echo ">> Installing Silvirica AI package (Pinned Release: ${RELEASE_TAG})..."
    if ! "${VENV_PY}" -m pip install "git+https://github.com/vinzz-yy/silvirica-ai.git@${RELEASE_TAG}" --quiet; then
        echo "Error: Failed to install release tag '${RELEASE_TAG}'. To install from the development branch explicitly, rerun with '--channel main'." >&2
        exit 1
    fi
fi

ln -sf "${VENV_DIR}/bin/silvirica" "${BIN_DIR}/silvirica"
echo ">> Linked executable to ${BIN_DIR}/silvirica"

# Verify CLI
"${VENV_PY}" -m silvirica.cli.main --help >/dev/null 2>&1 || {
    echo "Error: Silvirica CLI verification failed." >&2
    exit 1
}

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
echo "  silvirica ask \"What functions exist in app.py?\""
echo "  silvirica security"
echo "  silvirica mcp"
echo ""

