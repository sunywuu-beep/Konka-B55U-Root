# Konka B55U adbd: isolated build and smoke-test

## What this package is

GitHub Actions build recipe for **experimental** ARM32 Android API19 static `adbd`, built from a pinned KitKat-derived standalone test daemon (`ajiang17/android-adbd-for-linux`, commit `ba0f0fd06acaa28d6d264818a1703e462b8bfbbc`). The `adbd-build/prepare.py` script:

- Fixes connection identifiers (`host-%d`) and closes accepted TCP sockets on registration failure.
- Uses TCP **5556**, not the stock 5555.
- Removes the standalone daemon's local 5037 listener and USB initialization from this build; its upstream already does not use JDWP.
- Restricts TCP peers to maintenance computer `192.168.0.131` (hard-coded IP).

**This is NOT yet a compatible replacement for the factory `/sbin/adbd`.** It is a cross-compiled proof-of-concept to validate the repair and ARM API19 execution, after which a full AOSP-compatible daemon needs to be produced and tested. This standalone mini daemon does not implement all original services, RSA auth or JDWP. It will run as the user that launches it, not automatically become root.

## Creating the GitHub branch by hand

GitHub connector tried to create `adbd-fix` in `sunywuu-beep/Konka-B55U-Root` and received `403 Resource not accessible by integration`, so the repository was NOT modified. Create branch `adbd-fix` from main in GitHub's web UI yourself. Then choose **Add file -> Upload files**, select the individual files in this package while preserving paths. GitHub web Upload files with files selected from file picker may flatten directories; check that the workflow actually appears at `.github/workflows/build-b55u-adbd-test.yml` and script at `adbd-build/prepare.py`. The most reliable alternative is to open GitHub's file editor with a new path and paste file content. Commit on `adbd-fix`, NOT main.

Once both files exist on `adbd-fix`, the push trigger should run. Go to Actions and the job 'B55U Android 4.4 adbd ARM32 (isolated test candidate)'. Download artifact `B55U-adbd-ARM32-TEST-ONLY`. Inspect build logs if it fails; this third-party standalone implementation has not yet been successfully cross-built and run on your specific TV.

## Safety and testing

Do NOT replace `/sbin/adbd`, stop the original service, change `init.rc`, edit the root persistence hook, or add startup automation for the new daemon. If build passes, first provide the artifact and compile logs for verification; then use the already-working Root ADB on port 5555 to stage it under `/data/local/tmp/`. Run only during supervised test from `192.168.0.131`. The test daemon has **no RSA authentication** and grants commands at whatever privileges it starts with. Do not leave port 5556 exposed permanently. Confirm TV has an independent fallback before deploying any long-term changes.

## Source / licenses

AOSP Android 4.4.4 platform/system/core/adb; Apache-2.0 components. Standalone fork: https://github.com/ajiang17/android-adbd-for-linux . Verify licenses and author attribution before distributing modified binaries. `adbd-build/aosp44-connection-fix.patch` is the original patch for *full AOSP* (it is not what the isolated-mini-daemon workflow applies).
