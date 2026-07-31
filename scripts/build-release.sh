#!/usr/bin/env bash
#
# AIRTP Release Builder
#
# Produces reproducible release artifacts suitable for
# GitHub Releases and SLSA provenance.
#

set -euo pipefail

VERSION="${1:-dev}"

ROOT="$(cd "$(dirname "$0")/.." && pwd)"

cd "$ROOT"

OUT="release"

rm -rf "$OUT"
mkdir -p "$OUT"

echo "Building AIRTP ${VERSION}"

###########################################################
# Verify Reference Implementation
###########################################################

python3 -m py_compile AIRTP.py

###########################################################
# Reference Implementation
###########################################################

zip -r \
    "$OUT/AIRTP-${VERSION}-reference.zip" \
    AIRTP.py \
    README.md \
    LICENSE

###########################################################
# Protocol Specification
###########################################################

tar czf \
    "$OUT/AIRTP-${VERSION}-specification.tar.gz" \
    docs

###########################################################
# Checksums
###########################################################

(
cd "$OUT"

sha256sum \
    AIRTP-${VERSION}-reference.zip \
    AIRTP-${VERSION}-specification.tar.gz \
    > AIRTP-${VERSION}.sha256
)

echo
echo "Artifacts:"
ls -lh "$OUT"
