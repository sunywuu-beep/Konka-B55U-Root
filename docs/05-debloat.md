# 五、系统精简：分批停用、先试后删

## 起点

本机有不少康佳厂商和第三方平台包。先执行 `pm list packages -f` 建立 APK 路径清单，再用 `pm list packages -d` 查看停用项，并用 `ps`、`df -h /data`、`cat /proc/meminfo` 记录进程、存储和内存。

**本机第一次采集时已有 6 个包处于 disabled，不能算成此次工具刚刚停掉的数量。**

## 实验分组

### 第一组：不用的推广/功能入口

- `com.konka.gameassistant` — 游戏助手
- `com.konka.hotelmenu` — 酒店模式
- `com.konka.apkhall.edu` — 教育入口
- `com.konka.tv.pay` — 付费入口

这四项是本次第一批相对清晰的候选包。是否“无用”仍取决于用户功能需求和特定固件。

### 第二组：不使用的内容平台

- `com.yunos.tv.yingshi.boutique`
- `com.lz.smart.music`
- `com.gitvdemokonka.video`
- `com.cibn.tv`

本次脚本记录这四项被处理。有关云视听、CIBN、智能音乐进程退出的观察需与实际进程快照结合判断。

### 之前已经停用的其他包

`com.konka.cloudsearch`、`com.konka.message`、`com.konka.fourkshow`、`huan.tv.strongtv`、`com.konka.familycontrolcenter` 及 **`com.konka.systemadvert`** 在开始阶段已有 disabled 记录。

**重要：`com.konka.systemadvert` 必须作为保护对象。** 虽然它的名字包含 `advert`，但本机停用后曾出现遥控器功能问题；最新的 2026-10-27 停用清单仍含该包。用户曾报告后来恢复成功，不过该时点之后的包管理器新快照未在这里验证，所以不能断言最新状态已经 enabled。若发现遥控器异常，并且仍可使用 Root ADB，可尝试：

```powershell
.\adb.exe shell pm enable com.konka.systemadvert
```

恢复后现场测试并重新采集停用包清单，不要仅以命令打印成功为依据。

## 改动方法

**推荐：一次只改一个包。**

```powershell
.\adb.exe shell pm disable com.konka.gameassistant
.\adb.exe shell pm list packages -d
```

撤销：

```powershell
.\adb.exe shell pm enable com.konka.gameassistant
```

Android 4.4 的 `pm` 参数与新版 Android 不完全一致，不要在未经确认的情况下直接套用 `pm uninstall --user 0` 等新系统教程。

## 何谓“效果”

- 包处于 disabled：是包管理器状态变化，**不等于进程已立即退出**。
- 进程数下降：说明当时进程快照变化，**不等于长期提速已被证明**。
- `MemFree` 变化：受到页缓存、内存回收与系统活动影响，**单独比较不够**。
- `/system` 已只读的原厂 APK 只是停用时，通常**不会直接释放 `/data` 的安装空间**。
- 真正删除 `/data/app` 的程序可能回收空间，但必须先备份安装包与数据并完成稳定性验证；**本仓库没有一键删除流程**。

## 永久保护/暂不处理对象

`com.konka.systemadvert`、`/applications/bin/tvos`、`com.konka.smartengine`、`com.konka.livelauncher`、`com.konka.applist`、`com.konka.kksystemui`、`com.android.systemui`、`com.konka.tvsettings`、`com.mstar.tv.service`、遥控器和 MStar 视频音频/CEC 服务等。语音输入法、应用商店和更新服务先不混在第一轮修改中。
