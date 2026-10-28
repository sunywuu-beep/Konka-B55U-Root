# 开机脚本：只供理解，不是安装器

`install-recovery.verified.sh` 来自本机实际运行脚本的用户备份。它依赖该固件特有的开机调用链、`/system/etc/B55U_original_install-recovery.sh` 和已有的 Root 执行能力与 RSA 授权。

它不能直接拷贝到尚未 Root 或其他型号的设备；执行前应先检查 `flash_recovery` 配置、备份原始脚本、验证可以恢复。**不要将它称为无需准备的“一键 Root”。**
