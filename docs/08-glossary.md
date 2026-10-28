# 八、基础知识点

| 名词 | 新手理解 | 本次应用 |
|---|---|---|
| ADB | 从电脑给 Android 发送调试指令 | Windows 连接 5555 |
| `adbd` | 电视上负责接收 ADB 的后台服务 | 脚本重启它使属性生效 |
| `uid=0` | Linux 系统的 Root 身份 | 通过 `id` 验证 |
| `userdebug` | Android 可调试构建类型 | 此固件可结合相关属性提供 Root ADB |
| `setprop/getprop` | 设置/读取 Android 系统属性 | 控制 ADB 端口与 Root 开关 |
| `init.rc` | Android 开机服务定义文件 | 确认 `flash_recovery` 实际存在 |
| `/system` | 系统分区 | 修改前只读，短暂可写，修改后只读 |
| `/data` | 用户程序与数据分区 | 只停用系统包不会必然增加空闲空间 |
| `pm` | Android 包管理命令 | 查询、停用、恢复应用 |
| Binder | Android 进程间通信机制 | 排查 TVOS 服务侧命令执行入口 |
| RSS | 进程驻留内存指标，含可共享内存 | 不应逐进程 RSS 相加当作节省内存 |
| ABI/Bionic/glibc | 可执行程序的系统调用和动态库兼容环境 | 解释 ARM Linux 程序在 Android 崩溃 |
| RSA 授权 | 电视允许哪些 ADB 客户端连接 | `unauthorized` 不等于没有 Root |
