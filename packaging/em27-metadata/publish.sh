#!/usr/bin/env bash

set -euo pipefail

set -a
[[ -f "$(dirname "$0")/.env" ]] && source "$(dirname "$0")/.env"
set +a

package_config_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
dist_dir="${package_config_dir}/../dist"
package_version="$(sed -n 's/^version = "\(.*\)"/\1/p' "${package_config_dir}/pyproject.toml")"

"${package_config_dir}/build.sh" "${dist_dir}"

artifacts=(
    "${dist_dir}/em27_metadata-${package_version}.tar.gz"
    "${dist_dir}/em27_metadata-${package_version}-py3-none-any.whl"
)
for artifact in "${artifacts[@]}"; do
    if [[ ! -f "${artifact}" ]]; then
        echo "Expected build artifact not found: ${artifact}" >&2
        exit 1
    fi
done

uv publish "$@" "${artifacts[@]}"
