#!/usr/bin/env python3
"""Fail-closed isolation patch for the already transport-patched AOSP 4.4.4_r2 adbd.

This creates a TEST-only build with TCP:5556, a single allowed maintenance-PC IP,
existing-key RSA auth (ro.adb.secure=1), and no init-owned USB/JDWP/5037 sockets.
The unmodified production candidate must be built/packaged BEFORE this runs.
"""
from pathlib import Path
import ipaddress
import sys
import difflib

if len(sys.argv) != 3:
    raise SystemExit('Usage: patch_5556_isolated.py PATH_TO_AOSP_SYSTEM_CORE ALLOWED_IPV4')
root = Path(sys.argv[1])
ip = ipaddress.IPv4Address(sys.argv[2])
if not ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_multicast or ip.is_unspecified:
    raise SystemExit('ABORT: test client must be a private, non-loopback IPv4 address')

adb_file = root / 'adb/adb.c'
local_file = root / 'adb/transport_local.c'
orig_adb = adb_file.read_text()
orig_local = local_file.read_text()
adb = orig_adb
loc = orig_local

def replace_exact(source, old, new, label):
    if source.count(old) != 1:
        raise SystemExit(f'ABORT: expected exactly one {label}, got {source.count(old)}')
    return source.replace(old, new, 1)

# 1. Require secure authentication, only already-approved ADB public keys.
# No framework/auth control socket registration by second daemon; approval of a
# NEW key is deliberately unavailable in test mode (fail closed).
old = '''    property_get("ro.adb.secure", value, "0");
    auth_enabled = !strcmp(value, "1");
    if (auth_enabled)
        adb_auth_init();
'''
new = '''    /* B55U_5556_ISOLATED: RSA must remain enabled. No new key approvals. */
    property_get("ro.adb.secure", value, "0");
    auth_enabled = !strcmp(value, "1");
    if (!auth_enabled) fatal("B55U test refuses unauthenticated ADB");
    if (access("/data/misc/adb/adb_keys", R_OK) != 0 &&
        access("/adb_keys", R_OK) != 0) {
        fatal("B55U test requires a pre-approved ADB key file");
    }
    /* Do not call adb_auth_init(): its Android init socket belongs to stock adbd. */
'''
adb = replace_exact(adb, old, new, 'ro.adb.secure authentication initialization')

# 2. Do not drop privileges or register local smartsocket/5037; retain the
# standard AOSP should_drop_privileges decision to verify expected TV settings.
start = '    if (should_drop_privileges()) {\n'
end = '    int usb = 0;\n'
if adb.count(start) != 1 or adb.count(end) != 1:
    raise SystemExit('ABORT: expected AOSP adbd privilege/USB anchors not found')
a, b = adb.index(start), adb.index(end)
if a >= b:
    raise SystemExit('ABORT: incorrect privilege block ordering')
block = adb[a:b]
for required in ('install_listener(local_name, "*smartsocket*", NULL, 0)', 'setuid(AID_SHELL)', 'setgid(AID_SHELL)'):
    if required not in block:
        raise SystemExit(f'ABORT: missing expected privilege-block marker: {required}')
adb = adb[:a] + '''    /* B55U_5556_ISOLATED: require the already-established Root ADB setting. */
    if (should_drop_privileges()) {
        fatal("B55U test requires ro.debuggable=1 and service.adb.root=1");
    }
    /* No smartsocket/5037 listener; it remains owned by the stock daemon. */

''' + adb[b:]

# 3. No USB claim, no JDWP-control bind, do not read global TCP properties 5555.
start = '    int usb = 0;\n'
end = '    D("adb_main(): post init_jdwp()\\n");\n'
if adb.count(start) != 1 or adb.count(end) != 1:
    raise SystemExit('ABORT: cannot safely isolate USB/TCP/JDWP initialization')
a, b = adb.index(start), adb.index(end) + len(end)
part = adb[a:b]
for mark in ('usb_init();', 'local_init(port);', 'init_jdwp();', 'service.adb.tcp.port'):
    if mark not in part:
        raise SystemExit(f'ABORT: missing expected device initialization: {mark}')
adb = adb[:a] + '''    /* B55U_5556_ISOLATED: only TCP 5556, no USB / JDWP control. */
    local_init(5556);
''' + adb[b:]

# 4. Source-IP allowlist in the TCP accept loop; keep existing host-fd collision fix.
start = 'static void *server_socket_thread(void * arg)'
end = '    D("transport: server_socket_thread() exiting\\n");'
if loc.count(start) != 1 or loc.count(end) != 1:
    raise SystemExit('ABORT: unexpected transport socket thread anchors')
a, b = loc.index(start), loc.index(end)
section = loc[a:b]
if section.count('snprintf(serial, sizeof(serial), "host-%d", fd);') != 1:
    raise SystemExit('ABORT: transport collision fix missing')
old = '''        if(fd >= 0) {
            D("server: new connection on fd %d\\n", fd);'''
new = '''        if(fd >= 0) {
            /* B55U_5556_ISOLATED: reject every host except the maintenance PC. */
            if (addr.sa_family != AF_INET ||
                ((struct sockaddr_in *)&addr)->sin_addr.s_addr != inet_addr("''' + str(ip) + '''")) {
                adb_close(fd);
                continue;
            }
            D("server: new connection on fd %d\\n", fd);'''
section = replace_exact(section, old, new, 'peer-IP admission point')
loc = loc[:a] + section + loc[b:]
loc = replace_exact(loc, '#include <stdio.h>\n', '#include <stdio.h>\n#include <arpa/inet.h>\n#include <netinet/in.h>\n', 'network include')

# No writes until all anchors are checked.
adb_file.write_text(adb)
local_file.write_text(loc)
print('B55U_5556_ISOLATION_PATCH_PASS')
print('Allowed maintenance-PC IPv4:', ip)
print('Root and ro.adb.secure=1 enforced; existing ADB key required.')
print('TCP 5556 only; 5037/USB/JDWP init suppressed; 5555 stock untouched.')
for path, prev, now in [('adb.c', orig_adb, adb), ('transport_local.c', orig_local, loc)]:
    print(''.join(difflib.unified_diff(prev.splitlines(True), now.splitlines(True),
                                     fromfile=f'AOSP-original/{path}',
                                     tofile=f'B55U-5556-test/{path}')))
