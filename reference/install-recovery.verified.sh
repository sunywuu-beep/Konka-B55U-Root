#!/system/bin/sh
# B55U_PERSIST_ROOT_HOOK_V1
# Invoked only if the real TV init scripts define service flash_recovery.
# Uses the TV's original adbd. This is a boot-time service, not an su replacement.
unset LD_LIBRARY_PATH
unset LD_PRELOAD
PATH=/system/bin:/system/xbin:/sbin:/bin
export PATH
# Keep original factory/recovery behavior. Backup exists on the same partition.
/system/bin/sh /system/etc/B55U_original_install-recovery.sh "$@"
# Wait for normal startup before enabling TCP root debugging.
sleep 30
(
 echo B55U_BOOT_ROOT_BEGIN
 date
 id
 echo PERSIST_TCP_BEFORE:
 getprop persist.adb.tcp.port
 echo STATE_BEFORE:
 getprop init.svc.adbd
 setprop persist.adb.tcp.port 5555
 setprop service.adb.tcp.port 5555
 setprop service.adb.root 1
 setprop ctl.stop adbd
 sleep 2
 setprop ctl.start adbd
 sleep 3
 echo STATE_AFTER:
 getprop init.svc.adbd
 echo ADB_ROOT_SETTING:
 getprop service.adb.root
 echo TCP_SETTING:
 getprop service.adb.tcp.port
 echo B55U_BOOT_ROOT_END
) >> /data/local/tmp/B55U_bootroot.log 2>&1
exit 0
