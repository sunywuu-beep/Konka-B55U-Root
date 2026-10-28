# 三、首次 Root 的探索过程：成功证据与未记录之处

## 从普通 ADB 的限制开始

早期通过 TCP 5555 接入时，曾遇到 `unauthorized`，意味着电脑有连接，但未得到可用 RSA 授权；能连上网络、能执行 `adb connect` 都不能说明拥有 Root。

本机运行的是 Android 4.4.4、`userdebug` 固件。后续确认存在原厂 TVOS 服务 `/applications/bin/tvos`，并发现电视服务层可以执行具备 Root 身份的 Shell 命令。日志 `B55U_service_report.txt`、`B55U_tvos_id.txt` 分别记载 Root 命令执行和 `uid=0(root)`。

## 已知的关键入口

通过对 `/tvservice/applications/autotest_client` 及 TVOS 服务的排查，发现 `mstar.TvManager` 的 `executeShellCmd` 相关机制是重要方向。**现有记录没有保留完整的调用参数、Binder 事务编号的独立验证过程以及首次执行的全部命令。**

特别提醒：`service list` 中的数字编号是 **服务列表序号**，并不是 Binder 事务编号。**不能用“TvManager 在服务列表中序号 93”推导其 `executeShellCmd` 事务号；本项目不会把未经核实的“事务号 83”当作新手可复制命令。**

这台电视确实运行过 Root Shell，和“首次 Root 步骤能被他人完整复现”是两个不同结论。

## 失败与歧路

| 尝试 / 观察 | 实际现象 | 学到的知识 |
|---|---|---|
| 搜索 `eshell` | `/system/xbin/eshell` 与 `/dev/socket/eshell` 均不存在 | 网上其他型号的路径不一定适用 |
| 两次测试调用 | `Segmentation fault` | 崩溃不是 Root 成功；要检查架构与依赖库 |
| 执行/调用 Android 运行时工具 | `app_process` 加载 `libandroid_runtime.so` 等依赖时出现错误，追踪到 `libc.so.6 not found` | Android/Bionic 与 GNU/Linux glibc 的动态链接环境不同，不能想当然直接运行 Linux ARM 程序 |
| 依赖 Root 程序的其他方案 | 未取得本次可复核的正向证明 | 保留日志，不从失败路线直接推导成功 |

`B55U_autotest_client` 经 ELF 文件头检查为 **ARM 32-bit GNU/Linux 动态链接可执行文件**，不是 Android APK。尚无发布授权/完整说明，本仓库**不包含它**。

## 还缺什么

- 最初 Root 调用程序的准确版本、许可证和来源。
- 通过 TVOS 服务执行 `id` 的**完整可复核命令**及参数。
- Windows ADB 公钥授权写入的完整、已验证的命令和原始文件权限。
- 对同型号不同固件的重复测试。

只要这些没有补齐，**首次获取临时 Root 尚不能写成“一键安装”**。已完成 Root 的用户可以从下一章继续学习开机持久化原理。
