#!/usr/bin/env python3
"""Apply bounded, fail-closed test-only changes to kitkat-derived standalone adbd.

Unlike the stock B55U adbd, this upstream is a reduced GNU/Linux test daemon:
no JDWP, Android init integration, or Android RSA authentication.
Do not use it as a drop-in replacement for /sbin/adbd.
"""
import pathlib
import sys

if len(sys.argv) != 2:
    raise SystemExit('usage: prepare.py PATH_TO_STANDALONE_SOURCE')
root = pathlib.Path(sys.argv[1])
adb = root / 'adb.c'
local = root / 'transport_local.c'

text = adb.read_text()
start = '    if (0) {\n\n    } else {'
end = '    //D("adb_main(): pre init_jdwp()\\n");'
assert text.count(start) == 1 and text.count(end) == 1, 'Unrecognized adb.c; refusing unsafe patch'
i, j = text.index(start), text.index(end)
assert i < j
assert text[i:j].count('install_listener') == 1
assert text[i:j].count('local_init(') >= 1
# Isolate from stock port 5555, local 5037, USB gadget and Android JDWP.
text = text[:i] + '''    /* B55U test daemon: intentionally NO 5037, USB or JDWP listeners.\n     * TCP port 5556 only; peer filter is in transport_local.c.\n     * It provides no RSA authentication: short, supervised testing only. */\n    local_init(5556);\n\n''' + text[j:]
adb.write_text(text)

text = local.read_text()
beg = 'static void *server_socket_thread(void * arg)'
end = '    D("transport: server_socket_thread() exiting\\n");'
assert text.count(beg) == 1 and text.count(end) == 1, 'Unrecognized transport_local.c'
i, j = text.index(beg), text.index(end)
assert i < j
segment = text[i:j]
old_decl = '    int serverfd, fd;\n'
old_reg = '            register_socket_transport(fd, "host", port, 1);'
assert segment.count(old_decl) == 1 and segment.count(old_reg) == 1
peer_anchor = '        if(fd >= 0) {\n            D("server: new connection on fd %d\\n", fd);'
assert segment.count(peer_anchor) == 1, 'Cannot reliably insert peer authorization filter'
segment = segment.replace(old_decl, '    int serverfd, fd;\n    char serial[32];\n', 1)
segment = segment.replace('''        if(fd >= 0) {
            D("server: new connection on fd %d\\n", fd);''', '''        if(fd >= 0) {
            /* No built-in auth in this standalone test server: permit only
             * the known Windows maintenance PC (192.168.0.131). */
            if (addr.sa_family != AF_INET ||
                ((struct sockaddr_in *)&addr)->sin_addr.s_addr != inet_addr("192.168.0.131")) {
                adb_close(fd);
                continue;
            }
            D("server: new connection on fd %d\\n", fd);''', 1)
segment = segment.replace(old_reg, '''            snprintf(serial, sizeof(serial), "host-%d", fd);
            if (register_socket_transport(fd, serial, port, 1) != 0) {
                adb_close(fd);
            }''', 1)
text = text[:i] + segment + text[j:]
assert text.count('#include <arpa/inet.h>') == 0
text = text.replace('#include <stdio.h>', '#include <stdio.h>\n#include <arpa/inet.h>\n#include <netinet/in.h>', 1)

# Fix Android 4.4 shell path for B55U.
services = root / 'services.c'
code = services.read_text()

old = (
    '#else\n'
    '#define SHELL_COMMAND "/bin/sh"\n'
    '#define SHELL_BASH_COMMAND "/bin/bash"\n'
    '#endif'
)

new = old.replace(
    '#define SHELL_COMMAND "/bin/sh"',
    '#define SHELL_COMMAND "/system/bin/sh"'
)

assert code.count(old) == 1, 'Unexpected services.c layout'
services.write_text(code.replace(old, new, 1))

print('OK: Android shell path /system/bin/sh')
local.write_text(text)
print('OK: isolated test port 5556; host-%d serial; close-on-failure; peer 192.168.0.131 only')
