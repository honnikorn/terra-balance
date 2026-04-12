#!/bin/bash
# ─────────────────────────────────────────────────────────────────────────────
# Terra Balance – Keystore Setup Script
# Generates a signing keystore, extracts the SHA256 fingerprint,
# and writes keystore.properties + assetlinks.json automatically.
# Run this once before your first release build.
# ─────────────────────────────────────────────────────────────────────────────
set -e

KEYSTORE_DIR="$(cd "$(dirname "$0")" && pwd)/keystore"
KEYSTORE_FILE="$KEYSTORE_DIR/release.jks"
PROPS_FILE="$(cd "$(dirname "$0")" && pwd)/keystore.properties"
ASSETLINKS_FILE="$(cd "$(dirname "$0")/.." && pwd)/.well-known/assetlinks.json"

KEY_ALIAS="terrabalance"
PACKAGE_NAME="no.terrabalance.app"

mkdir -p "$KEYSTORE_DIR"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Terra Balance – Signing Key Setup"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if [ -f "$KEYSTORE_FILE" ]; then
    echo "✓ Keystore already exists at $KEYSTORE_FILE"
    echo "  Delete it and re-run if you want to generate a new one."
else
    echo "Enter the details for your signing certificate."
    echo "(These are stored in the keystore — keep it safe!)"
    echo ""

    read -s -p "Keystore password (min 6 chars): " STORE_PASS
    echo
    read -s -p "Key password (min 6 chars):       " KEY_PASS
    echo
    read -p "Your name (e.g. Honni Korn):      " DNAME_CN
    read -p "Organisation (or your name):       " DNAME_O
    read -p "Country code (e.g. NO):           " DNAME_C

    DNAME="CN=${DNAME_CN}, O=${DNAME_O}, C=${DNAME_C}"

    keytool -genkeypair \
        -keystore "$KEYSTORE_FILE" \
        -alias "$KEY_ALIAS" \
        -keyalg RSA \
        -keysize 2048 \
        -validity 10000 \
        -storepass "$STORE_PASS" \
        -keypass "$KEY_PASS" \
        -dname "$DNAME"

    echo ""
    echo "✓ Keystore created: $KEYSTORE_FILE"

    # Write keystore.properties (excluded from git)
    cat > "$PROPS_FILE" <<PROPS
storeFile=keystore/release.jks
storePassword=${STORE_PASS}
keyAlias=${KEY_ALIAS}
keyPassword=${KEY_PASS}
PROPS
    echo "✓ Written: keystore.properties"
fi

# Extract SHA256 fingerprint
echo ""
echo "Extracting SHA256 certificate fingerprint…"

if [ -f "$PROPS_FILE" ]; then
    STORE_PASS=$(grep storePassword "$PROPS_FILE" | cut -d= -f2)
fi

SHA256=$(keytool -list -v \
    -keystore "$KEYSTORE_FILE" \
    -alias "$KEY_ALIAS" \
    -storepass "$STORE_PASS" 2>/dev/null \
    | grep "SHA256:" \
    | sed 's/.*SHA256: //' \
    | tr -d ' ')

echo "  SHA256: $SHA256"

# Update assetlinks.json
cat > "$ASSETLINKS_FILE" <<JSON
[
  {
    "relation": ["delegate_permission/common.handle_all_urls"],
    "target": {
      "namespace": "android_app",
      "package_name": "${PACKAGE_NAME}",
      "sha256_cert_fingerprints": [
        "${SHA256}"
      ]
    }
  }
]
JSON

echo "✓ Updated: .well-known/assetlinks.json"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Next steps:"
echo "  1. git add .well-known/assetlinks.json && git commit -m 'chore: add assetlinks' && git push"
echo "  2. cd android && gradle wrapper   (if you haven't already)"
echo "  3. ./gradlew bundleRelease"
echo "  4. Upload android/app/build/outputs/bundle/release/app-release.aab to Play Console"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
