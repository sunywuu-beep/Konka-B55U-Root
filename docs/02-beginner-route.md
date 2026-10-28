# 二、给新手的操作路线

## 术语先读

- **ADB**：Android Debug Bridge，电脑上通过 `adb.exe` 管理 Android 设备。
- **Shell**：命令行环境；普通 Shell 常显示 `uid=2000(shell)`，Root Shell 显示 `uid=0(root)`。
- **Root**：最高系统权限。使用不当可导致电视无法启动；务必区分“短暂 Root 命令入口”和“开机后的 Root ADB”。
- **停用 / 恢复**：`pm disable <包名>` / `pm enable <包名>`，通常保留 APK，可恢复；不能把它与永久删除混为一谈。

## 操作前准备

1. 确认电视为 B55U，先记录 Android 版本、固件标识、电视 IP、RAM 和剩余空间。其他机型先停手。
2. Windows 安装 Android Platform Tools（Google 官方 ADB）。打开 PowerShell，先运行 `./adb.exe version`（在 PowerShell 通常写 `.\adb.exe version`）。
3. 确保电脑、电视在同一可信局域网；电视有可用的遥控器及 USB 键盘等本地输入手段。
4. 记录电视能否正常显示、遥控器是否正常、声音是否正常、HDMI 是否正常；把这些作为修改后测试清单。
5. **不要把 GitHub 中保存的开机参考脚本直接放进 `/system`。** 必须先验证目标机自己的启动入口和回滚条件。

## 情况 A：电视已有可用 Root ADB（本次实机已达到）

在 `adb.exe` 所在文件夹的 PowerShell 中：

```powershell
.\adb.exe connect <电视IP>:5555
.\adb.exe shell id
.\adb.exe shell getprop ro.build.type
.\adb.exe shell pm list packages -d
```

如果 `id` 返回 `uid=0(root)`，可继续审计。使用本仓库只读快照脚本：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\Audit-B55U.ps1 -TvIp <电视IP> -AdbPath .\adb.exe
```

`Audit-B55U.ps1` 生成的日志放在本地 `audit-output` 中；上传分享前请检查有无可识别设备信息。

若出现 `unauthorized`：说明 ADB 身份授权未成功，与“是否有 Root 能力”不是同一个问题；先处理电视本地授权问题。若 `uid=2000(shell)`：说明连接成立，但当前不是 Root Shell，**不要运行需要 Root 的操作**。

## 情况 B：电视尚未 Root

本仓库不能在当前版本提供已复核的“首次 Root 一条命令”。原实验曾通过 TVOS 服务侧执行拿到 `uid=0`，但缺失当时使用的精确参数和可发布的调用程序。请阅读 [Root 探索](03-root-discovery.md) 和 [待补证据](09-open-items.md)；**不能把下面的开机脚本当成首次提权方式**。

## 第一次精简实验怎么做

先备份和观察：

```powershell
.\adb.exe shell pm list packages -d
.\adb.exe shell df -h /data
.\adb.exe shell cat /proc/meminfo
```

只在不使用某个附加入口且已经验证其非关键依赖时，尝试**单包**停用。本项目的交互式脚本没有“全部停用”选项：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\Toggle-OptionalPackage.ps1 -TvIp <电视IP> -AdbPath .\adb.exe -Mode Disable -Package com.konka.gameassistant
```

检查遥控器、主页、声音、画面、HDMI、播放器，确认没有问题后再研究下一项。如果某一步引起异常，立即恢复：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\Toggle-OptionalPackage.ps1 -TvIp <电视IP> -AdbPath .\adb.exe -Mode Restore -Package com.konka.gameassistant
```

**注意**：上面的命令只允许尝试在本次实机出现过且有候选价值的包；也不保证该包对你的固件必定安全。电视若无法正常启动，ADB 也可能失效，所以永远先准备本地恢复手段。
