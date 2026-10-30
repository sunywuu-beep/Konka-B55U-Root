#!/bin/bash
# Execute inside historical KitKat build container, with /aosp mounted as repo root.
set -exo pipefail
cd /aosp
printf '\n=== Build environment ===\n'
uname -a
command -v java || true
java -version || true
command -v make
make --version | head -2
printf '\n=== Complete AOSP source check ===\n'
test -f build/envsetup.sh
test -f system/core/adb/Android.mk
test -f bionic/libc/Android.mk
grep -q 'host-%d' system/core/adb/transport_local.c
printf '\n=== Select AOSP ARM engineering target ===\n'
source build/envsetup.sh
lunch aosp_arm-eng
printf '\n=== Build only the full device-side adbd target ===\n'
make -j2 adbd
printf '\n=== Candidate paths ===\n'
find out/target/product -type f -name adbd -print | head -30
