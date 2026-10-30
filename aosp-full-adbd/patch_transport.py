#!/usr/bin/env python3
"""Fail-closed patch of AOSP android-4.4.4_r2 system/core/adb/transport_local.c.

Only modify the server_socket_thread handler. Never touch other ADB modules.
"""
from pathlib import Path
import difflib
import sys

if len(sys.argv) != 2:
    raise SystemExit('Usage: patch_transport.py PATH_TO_AOSP_SYSTEM_CORE')
root = Path(sys.argv[1])
source = root / 'adb/transport_local.c'
mk = root / 'adb/Android.mk'
original = source.read_text()
makefile = mk.read_text()

for name in ('adb_auth_client.c', 'jdwp_service.c', 'usb_linux_client.c',
             'backup_service.c', 'file_sync_service.c', 'services.c'):
    if name not in makefile:
        raise SystemExit(f'ABORT: missing full adbd component {name}')

begin = 'static void *server_socket_thread(void * arg)'
end = '    D("transport: server_socket_thread() exiting\\n");'
if original.count(begin) != 1 or original.count(end) != 1:
    raise SystemExit('ABORT: unexpected transport_local.c function boundaries')
a, b = original.index(begin), original.index(end)
if not a < b:
    raise SystemExit('ABORT: unexpected function boundary ordering')
portion = original[a:b]
old_decl = '    int serverfd, fd;\n'
old_call = '            register_socket_transport(fd, "host", port, 1);'
if portion.count(old_decl) != 1 or portion.count(old_call) != 1:
    raise SystemExit('ABORT: expected KitKat TCP registration code not found once')
portion = portion.replace(old_decl, '    int serverfd, fd;\n    char serial[32];\n', 1)
portion = portion.replace(old_call, '''            /* B55U: avoid collisions between concurrent accepted TCP connections. */
            snprintf(serial, sizeof(serial), "host-%d", fd);
            if (register_socket_transport(fd, serial, port, 1) < 0) {
                /* The caller still owns fd when registration fails. */
                adb_close(fd);
            }''', 1)
modified = original[:a] + portion + original[b:]
if modified == original:
    raise SystemExit('ABORT: patch had no effect')
source.write_text(modified)
print('Patched: adb/transport_local.c (one function only)')
print('Preserved full AOSP device-side services and build definitions.')
print(''.join(difflib.unified_diff(original.splitlines(True),
                                  modified.splitlines(True),
                                  fromfile='AOSP-original/transport_local.c',
                                  tofile='B55U-fixed/transport_local.c')))
