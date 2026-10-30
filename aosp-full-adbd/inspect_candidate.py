#!/usr/bin/env python3
"""Validate full AOSP KitKat adbd built by platform build. Never deploy."""
from pathlib import Path
import hashlib
import subprocess
import sys
import shutil

if len(sys.argv) != 3:
    raise SystemExit('Usage: inspect_candidate.py AOSP_ROOT OUTPUT_DIR')
root = Path(sys.argv[1])
out = Path(sys.argv[2])
choices = list((root / 'out/target/product').rglob('adbd'))
choices = [p for p in choices if p.is_file()]
# Prefer installed ramdisk binary over obj intermediary.
prefer = [p for p in choices if p.as_posix().endswith('/root/sbin/adbd')]
if len(prefer) == 1:
    target = prefer[0]
elif len(choices) == 1:
    target = choices[0]
else:
    raise SystemExit('ABORT: ambiguous output paths: ' + ', '.join(map(str, choices)))

out.mkdir(parents=True, exist_ok=True)
elf = out / 'B55U_full_AOSP44_adbd_candidate'
shutil.copy2(target, elf)
elf.chmod(0o755)

def call(*argv):
    return subprocess.check_output(argv, text=True, stderr=subprocess.STDOUT)

hdr = call('readelf', '-hW', str(elf))
program = call('readelf', '-lW', str(elf))
section = call('readelf', '-SW', str(elf))
file_report = call('file', str(elf))
if not any(line.strip().startswith('Machine:') and line.strip().endswith('ARM') for line in hdr.splitlines()):
    raise SystemExit('ABORT: not an ARM machine')
if not any(line.strip().startswith('Class:') and line.strip().endswith('ELF32') for line in hdr.splitlines()):
    raise SystemExit('ABORT: not ELF32')
if 'INTERP ' in program or 'Requesting program interpreter' in program:
    raise SystemExit('ABORT: program unexpectedly requires dynamic interpreter')
for line in program.splitlines():
    if line.strip().startswith('TLS '):
        align = int(line.split()[-1], 16)
        if align < 32:
            raise SystemExit(f'ABORT: TLS alignment {align} < 32')

raw = elf.read_bytes()
for token in [b'/system/bin/sh', b'service.adb.tcp.port', b'/dev/usb-ffs/adb/ep0']:
    if token not in raw:
        raise SystemExit('ABORT: missing expected AOSP feature marker: ' + repr(token))

(out / 'elf-header.txt').write_text(hdr)
(out / 'elf-program-headers.txt').write_text(program)
(out / 'elf-sections.txt').write_text(section)
(out / 'elf-file.txt').write_text(file_report)
digest = hashlib.sha256(raw).hexdigest()
(out / 'sha256.txt').write_text(f'{digest}  {elf.name}\n')
(out / 'BUILD-STATUS.txt').write_text(
    'FULL AOSP 4.4.4 source candidate; NOT an exact vendor reproduction.\n'
    'DO NOT overwrite /sbin/adbd or use as boot service.\n'
    'Device-side compatibility and feature parity remain untested.\n'
    'Do not start next to existing adbd without isolating TCP, USB, 5037 and JDWP.\n'
    'Original B55U SHA256: a619fc9fe587569f704d23bd5c626629cd94ad3c3f7f5bc99b49af99060512e1\n'
)
print('PASS: candidate ', elf)
print('SHA256:', digest)
print(file_report)
