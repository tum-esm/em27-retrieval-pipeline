#!/usr/bin/env bash

set -euo pipefail

repository_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
package_config_dir="${repository_dir}/packaging/em27-metadata"
output_dir="${1:-${repository_dir}/dist/em27-metadata}"
staging_dir="$(mktemp -d)"

cleanup() {
    rm -rf "${staging_dir}"
}
trap cleanup EXIT

cp "${package_config_dir}/pyproject.toml" "${staging_dir}/pyproject.toml"
cp "${package_config_dir}/README.md" "${staging_dir}/README.md"
cp "${package_config_dir}/LICENSE" "${staging_dir}/LICENSE"
cp -R "${repository_dir}/src/em27_metadata" "${staging_dir}/em27_metadata"

uv build --no-sources --out-dir "${output_dir}" "${staging_dir}"
