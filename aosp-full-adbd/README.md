# 康佳 B55U：完整 AOSP 4.4.4 `adbd` 构建实验（仅构建，不安装）

## 与此前的精简版有什么区别？

本工作流从 AOSP 官方 `android-4.4.4_r2` 版本获取**完整平台源码**，调用原版 `system/core/adb/Android.mk` 进行设备端 `adbd` 构建。完整模块包括 `adb_auth_client.c`、`jdwp_service.c`、`usb_linux_client.c`、`file_sync_service.c`、`services.c` 等。脚本只对 `adb/transport_local.c` 的 TCP 连接注册部分进行最小修复，不删改这些模块。

注意：这仍是**AOSP 完整版**，并不是康佳 OEM 出厂构建的逐字节复刻。厂商补丁和运行时配置可能不同。

## 如何使用

1. 在 GitHub 仓库 `sunywuu-beep/Konka-B55U-Root` 中切换至 **`adbd-fix`** 分支。
2. 上传本 ZIP 解压后得到的 `.github/workflows/build-b55u-full-adbd.yml` 和 `aosp-full-adbd/` 目录。**不要覆盖已有的精简版工作流**。
3. 提交到 `adbd-fix` 分支，GitHub Actions 将自动触发 `B55U Full AOSP 4.4 adbd (build only)`。这次同步 Android 4.4 平台源码，需要远大于精简版的空间和时间；可能遇到过时 Java/Make、网络镜像或 Docker 镜像兼容问题。
4. 若成功，下载 `B55U-FULL-AOSP44-adbd-REVIEW-ONLY`，里面包含 `B55U_full_AOSP44_adbd_candidate` 及 ELF 检查报告。
5. 若失败，下载 `B55U-FULL-AOSP44-build-diagnostics` 并提供日志**真正失败处**；工作流已设置即使编译失败也尽量保存日志。

## 技术约束和风险

- KitKat 源码构建依赖旧宿主工具链。本工作流使用曾专门测试过 KitKat 的 `kylemanna/aosp:4.4-kitkat` Docker 镜像，而 GitHub Actions 的 Ubuntu 24.04 只负责拉取代码和容器编排。
- `repo init --depth=1`、`repo sync -c --no-tags` 限制下载历史，但完整源码仍很大；工作流清理 GitHub Runner 的 Android SDK / .NET / Swift 等预装文件以回收空间。
- Docker 镜像较老，来源为第三方，使用前需留意供应链风险；其代码与标签可在 GitHub `kylemanna/docker-aosp` 和 Docker Hub 查看。用户仓库的 token 仅有 `contents: read`，工作流不会执行部署命令。
- **没有在本次对话中完成完整平台编译，也没有实际在 B55U 上运行这份完整版。不能把 CI 配置视为已经验证可替换。**
- 现有 `/sbin/adbd` 和 `/system/etc/install-recovery.sh` 原样保留。不能将这个未经实测的完整版直接覆盖原厂程序。
- 本工作流编译的可执行程序若不经过资源隔离，不能与现有 5555 Root ADB 并行启动（可能争用 5037、USB、JDWP、5555）。要在电视上测试前必须专门准备可回退方案。

## GitHub 页面

- 仓库：`https://github.com/sunywuu-beep/Konka-B55U-Root/tree/adbd-fix`
- KitKat 工具环境：`https://github.com/kylemanna/docker-aosp`
- 完整 Android `adbd` 源码：`https://github.com/aosp-mirror/platform_system_core/blob/android-4.4.4_r2/adb/Android.mk`
