# 四、Root ADB 固化：这次确实重启验收成功的部分

## 什么叫“固化”

我们实现的是：**开机脚本自动设置 ADB Root 与 TCP 端口，使用原厂 `adbd`**，不是把所有第三方 App 变成 Root，也不是把 Root 永久写进内核。

## 环境先决条件

**需要先取得 `uid=0` 的本地命令执行能力**。本章节不能用于尚无 Root 的设备。

实机日志 `B55U_PERSIST_RESULT.txt` 显示：

- `/init.rc:545` 存在 `service flash_recovery /system/etc/install-recovery.sh`。
- 先前 `/system` 是只读；临时挂为可写后保存原始脚本，再安装 `/system/etc/install-recovery.sh`。
- 原始脚本保存在 `/system/etc/B55U_original_install-recovery.sh`，安装后 `/system` 恢复只读。
- 设备已有 ADB 授权公钥文件；没有发布其内容。

这意味着**该固件具有真实的启动脚本入口**。不能假定所有 Android 4.4 设备或所有康佳 TVOS 固件都存在它。

## 真实启动脚本的逻辑

参考 [`reference/install-recovery.verified.sh`](../reference/install-recovery.verified.sh)。要点：

1. 保留并调用原先的 `/system/etc/B55U_original_install-recovery.sh`；
2. 等待 30 秒；
3. 设置 `persist.adb.tcp.port=5555`、`service.adb.tcp.port=5555`、`service.adb.root=1`；
4. 停止并重新启动 `adbd`；
5. 将执行日志写到 `/data/local/tmp/B55U_bootroot.log`。

**这是原机脚本样本，不是安装器。** 因为首次 Root 入口和回滚程序的完整调用链未在本项目内，禁止不经检查地复制到其他电视。

## 重启后的验证（实测通过）

Windows 端运行：

```powershell
.\adb.exe kill-server
.\adb.exe start-server
.\adb.exe connect <电视IP>:5555
.\adb.exe shell id
.\adb.exe shell cat /data/local/tmp/B55U_bootroot.log
```

实测第一条关键返回是：

```text
uid=0(root) gid=0(root)
```

开机日志关键段：

```text
B55U_BOOT_ROOT_BEGIN
uid=0(root) gid=0(root)
STATE_AFTER:
running
ADB_ROOT_SETTING:
1
TCP_SETTING:
5555
B55U_BOOT_ROOT_END
```

只有**实际断电/正常重启后**仍出现上述 Root 身份，并确认日志中的开机标记，才能判定开机恢复成功。只见到 `BOOT_HOOK_INSTALLED` 是安装完成，并不能代替重启验证。

## 特别的 1970 年时间戳

开机日志曾显示 `Thu Jan 1 ... 1970`，原因可以是系统在网络授时前读取了初始时间。它不能单独证明失败，也不能用作实测日期。应同时观察 `id`、开机标记和实际重启过程。

## 如何回退

原机保存了 `/system/etc/B55U_original_install-recovery.sh`。**恢复操作必须由已经取得的 Root 入口执行，并须确认文件真实存在且可读**；不能简单删除整个 `/system/etc/install-recovery.sh`，更不能误删原厂启动链。

本仓库暂不提供未经实机单独验收的一键回滚脚本。若 5555 失联，需要先使用电视本地终端或已验证的 TVOS 入口重新确认 Root，再据原始备份恢复启动脚本。没有这些途径时不要盲目修改 `/system`。

## 安全边界

TCP 5555 + Root ADB 意味着可信的已授权 ADB 主机能取得系统最高权限。请勿将端口暴露公网、跨不可信 Wi-Fi 使用，也不要上传任何 `adbkey` 私钥或 `/data/misc/adb/adb_keys`。
