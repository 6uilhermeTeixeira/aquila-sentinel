#!/usr/bin/env bash
set -euo pipefail
if [[ $# -ne 2 ]]; then
  printf 'Usage: %s DATASTREAM.xml OUTPUT_DIRECTORY\n' "$0" >&2
  exit 2
fi
datastream=$1
output_dir=$2
if [[ ! -f "$datastream" ]]; then
  printf 'OpenSCAP datastream not found: %s\n' "$datastream" >&2
  exit 2
fi
mkdir -p "$output_dir"
chmod 700 "$output_dir"
oscap xccdf eval \
  --profile xccdf_org.ssgproject.content_profile_cis_level1_server \
  --results "$output_dir/results.xml" \
  --report "$output_dir/report.html" \
  "$datastream" || status=$?
if [[ ${status:-0} -ne 0 && ${status:-0} -ne 2 ]]; then
  exit "$status"
fi
printf 'Results: %s/results.xml\nReport: %s/report.html\n' "$output_dir" "$output_dir"
