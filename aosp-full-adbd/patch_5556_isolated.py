#!/usr/bin/env python3
"""Fail-closed, full-AOSP-4.4.4-r2 test-only adbd isolation patch.

Requires patch_transport.py to have already applied the production fix.
Does NOT modify original production binary, only the AOSP source tree for
second compilation. Never install resulting binary as /sbin/adbd.
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

paths = {
    'adb.c': root / 'adb/adb.c',
    'transport_local.c': root / 'adb/transport_local.c',
    'services.c': root / 'adb/services.c',
    'sockets.c': root / 'adb/sockets.c',
}
originals = {key: path.read_text() for key, path in paths.items()}
changed = dict(originals)

def replace_exact(source, old, new, label):
    n = source.count(old)
    if n != 1:
        raise SystemExit(f'ABORT: expected exactly one {label}, found {n}')
    return source.replace(old, new, 1)

adb = changed['adb.c']
old = '''    property_get("ro.adb.secure", value, "0");
    auth_enabled = !strcmp(value, "1");
    if (auth_enabled)
        adb_auth_init();
'''
new = '''    /* B55U_5556_ISOLATED: RSA verification required, no new key approvals. */
    property_get("ro.adb.secure", value, "0");
    auth_enabled = !strcmp(value, "1");
    if (!auth_enabled) fatal("B55U test refuses unauthenticated ADB");
    if (access("/data/misc/adb/adb_keys", R_OK) != 0 &&
        access("/adb_keys", R_OK) != 0) {
        fatal("B55U test requires a pre-approved ADB key file");
    }
    /* Do not call adb_auth_init(): init-owned control socket belongs to stock. */
'''
adb = replace_exact(adb, old, new, 'ADB RSA authentication initialization')

start, end = '    if (should_drop_privileges()) {\n', '    int usb = 0;\n'
if adb.count(start) != 1 or adb.count(end) != 1:
    raise SystemExit('ABORT: unexpected KitKat privilege section')
a, b = adb.index(start), adb.index(end)
if a >= b:
    raise SystemExit('ABORT: privilege-section markers out of order')
block = adb[a:b]
for required in ('install_listener(local_name, "*smartsocket*", NULL, 0)',
                 'setuid(AID_SHELL)', 'setgid(AID_SHELL)'):
    if required not in block:
        raise SystemExit('ABORT: missing expected privilege code: ' + required)
adb = adb[:a] + '''    /* B55U_5556_ISOLATED: root only; do not claim 5037/smartsocket. */
    if (should_drop_privileges()) {
        fatal("B55U test requires ro.debuggable=1 and service.adb.root=1");
    }

''' + adb[b:]

start = '    int usb = 0;\n'
end = '    D("adb_main(): post init_jdwp()\\n");\n'
if adb.count(start) != 1 or adb.count(end) != 1:
    raise SystemExit('ABORT: unexpected KitKat USB/TCP/JDWP section')
a, b = adb.index(start), adb.index(end) + len(end)
part = adb[a:b]
for required in ('usb_init();', 'local_init(port);', 'init_jdwp();', 'service.adb.tcp.port'):
    if required not in part:
        raise SystemExit('ABORT: missing expected service init: ' + required)
adb = adb[:a] + '''    /* B55U_5556_ISOLATED: TCP 5556 only, no USB/JDWP binding. */
    local_init(5556);
''' + adb[b:]
changed['adb.c'] = adb

loc = changed['transport_local.c']
start = 'static void *server_socket_thread(void * arg)'
end = '    D("transport: server_socket_thread() exiting\\n");'
if loc.count(start) != 1 or loc.count(end) != 1:
    raise SystemExit('ABORT: unexpected transport loop anchors')
a, b = loc.index(start), loc.index(end)
section = loc[a:b]
if section.count('snprintf(serial, sizeof(serial), "host-%d", fd);') != 1:
    raise SystemExit('ABORT: production transport collision fix not present')
old = '''        if(fd >= 0) {
            D("server: new connection on fd %d\\n", fd);'''
new = '''        if(fd >= 0) {
            /* B55U_5556_ISOLATED: reject all peers except the maintenance PC. */
            if (addr.sa_family != AF_INET ||
                ((struct sockaddr_in *)&addr)->sin_addr.s_addr != inet_addr("''' + str(ip) + '''")) {
                adb_close(fd);
                continue;
            }
            D("server: new connection on fd %d\\n", fd);'''
section = replace_exact(section, old, new, 'TCP peer admission point')
loc = loc[:a] + section + loc[b:]
loc = replace_exact(loc, '#include <stdio.h>\n',
                    '#include <stdio.h>\n#include <arpa/inet.h>\n#include <netinet/in.h>\n',
                    'network header')
changed['transport_local.c'] = loc

# JDWP global lists are initialized by init_jdwp(). The isolated daemon MUST
# NOT bind its abstract socket, so reject these entrypoints to avoid null list
# dereferences when an ADB host issues `adb jdwp` or `track-jdwp`.
sockets = changed['sockets.c']
old = '''#if !ADB_HOST
    if (!strcmp(name,"jdwp")) {
        return create_jdwp_service_socket();
    }
    if (!strcmp(name,"track-jdwp")) {
        return create_jdwp_tracker_service_socket();
    }
#endif
'''
new = '''#if !ADB_HOST
    /* B55U_5556_ISOLATED: JDWP global lists were never initialized. */
    if (!strcmp(name,"jdwp") || !strcmp(name,"track-jdwp")) {
        return NULL;
    }
#endif
'''
sockets = replace_exact(sockets, old, new, 'JDWP service socket dispatch')
changed['sockets.c'] = sockets

# Prevent the isolated daemon from changing global ADB mode, rebooting the TV,
# remounting system, or invoking JDWP PID dispatch (also needs init_jdwp).
services = changed['services.c']
old = '''int service_to_fd(const char *name)
{
    int ret = -1;
'''
new = '''int service_to_fd(const char *name)
{
    int ret = -1;
#if !ADB_HOST
    /* B55U_5556_ISOLATED: these services affect the stock daemon/TV or
       need JDWP initialization. Shell, sync, log and file services remain. */
    if (!strncmp(name, "jdwp:", 5) || !strncmp(name, "reboot:", 7) ||
        !strncmp(name, "remount:", 8) || !strncmp(name, "root:", 5) ||
        !strncmp(name, "tcpip:", 6) || !strncmp(name, "usb:", 4) ||
        !strncmp(name, "backup:", 7) || !strncmp(name, "restore:", 8)) {
        return -1;
    }
#endif
'''
services = replace_exact(services, old, new, 'service dispatch guard')
changed['services.c'] = services

# Fail closed: do not partially patch a source tree if an anchor fails.
for key, file in paths.items():
    file.write_text(changed[key])

print('B55U_5556_ISOLATION_PATCH_PASS')
print('Allowed maintenance host IPv4:', ip)
print('Root+RSA key checks enabled; no ADB auth/USB/JDWP/5037 init')
print('JDWP and global-state-changing ADB services rejected in test mode')
for key in paths:
    prev, now = originals[key], changed[key]
    print(''.join(difflib.unified_diff(prev.splitlines(True), now.splitlines(True),
                                      fromfile=f'AOSP-original/{key}',
                                      tofile=f'B55U-5556-test/{key}')))
