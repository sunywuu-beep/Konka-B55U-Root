康佳 B55U：完整版 AOSP 4.4.4 adbd 的 5556 隔离测试构建包
==========================================================

目标：保留已成功构建的完整 adbd 候选版，同时另外构建一个专门的 5556 TEST-ONLY 版。
不会写入或替换电视上的 /sbin/adbd，也不会启动或关闭原厂 5555 服务。

预先验证（Windows PowerShell，当前电脑 ADB 已经授权电视 5555）：
  1. 核对电脑在 192.168.0.x 局域网的当前 IPv4：
     Get-NetIPAddress -AddressFamily IPv4 | Where-Object {$_.IPAddress -like '192.168.0.*'} | Select-Object InterfaceAlias,IPAddress
     之前精简版的维护电脑 IP 为 192.168.0.131；如果 IP 已变化，运行 Actions 时更新 test_peer_ip。
  2. 只检查电视 ADB 公钥文件是否存在，绝不要贴出公钥内容：
     .\adb.exe -s 192.168.0.210:5555 shell 'ls -l /data/misc/adb/adb_keys /adb_keys 2>/dev/null'
     两者至少一个应存在且可读；否则测试版将拒绝启动（安全失败）。

仓库： https://github.com/sunywuu-beep/Konka-B55U-Root
工作分支：adbd-fix

更新仓库（手动，由于当前连接不能写入 GitHub）：
  A. 将 aosp-full-adbd/patch_5556_isolated.py 上传至 adbd-fix 分支同名目录；保留原有 patch_transport.py。
  B. 将 .github/workflows/build-b55u-full-adbd.yml 覆盖 adbd-fix 分支的原有工作流。
  C. 建议也将同一个 YAML 文件更新到 main 分支，以便 Actions 页面显示新的 workflow_dispatch 输入项。不要将补丁文件上传到 main；运行时选择 adbd-fix。

运行 GitHub Actions 时：
   Use workflow from: adbd-fix
   full_build: true
   isolated_test: true
   test_peer_ip: 192.168.0.131（或电脑当前实际 IPv4）

运行完成应当生成两份不同的 artifact：
  - B55U-FULL-AOSP44-adbd-REVIEW-ONLY （不改动的正式候选版）
  - B55U-FULL-AOSP44-5556-ISOLATED-TEST-ONLY （5556 隔离测试版）

隔离版源码改动：
  - 仍使用此前已验证的 host-%d transport registration 修复。
  - Root 模式必须满足 ro.debuggable=1 且 service.adb.root=1；否则拒绝启动。
  - 只有 TCP 5556；不注册设备端 5037、USB 或 JDWP 控制监听。
  - 强制 ro.adb.secure=1 和已批准密钥文件，阻止未认证 Root ADB。
  - 对 TCP 客户端实施源 IPv4 白名单；未列入白名单者立即断开。
  - 已批准的密钥才能通过 RSA 校验；不支持新增密钥审批弹窗。
  - 当前候选尚未在康佳电视上实际运行验证；不能作为永久替换版。

请勿在电视上执行 setprop service.adb.tcp.port、setprop persist.adb.tcp.port、stop adbd、start adbd 或覆盖 /sbin/adbd。

测试脚本和 YAML 已做静态解析和模拟补丁测试，尚未在 GitHub 完成 5556 隔离版编译。
