#!/usr/bin/env bash

set -euo pipefail

package_config_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repository_dir="$(cd "${package_config_dir}/../.." && pwd)"
output_dir="${1:-${repository_dir}/packaging/dist}"
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
