# 六、弯路、失败与避坑经验

## 坑 1：网络 ADB 不等于 Root

`adb connect` 可以成功而 `adb shell` 没有权限；`unauthorized` 说明需要 ADB RSA 认证。正确顺序是分别验证**连接、授权、身份**，而不是连接上就声称 Root。

## 坑 2：网上的路径不一定存在

测试中 `/system/xbin/eshell`、`/dev/socket/eshell` 都不存在。不要照搬别的固件的路径、服务编号或 Root 方法。

## 坑 3：ARM 二进制不等于 Android 可执行程序

本次测试见到 `Segmentation fault` 与 `libc.so.6 not found`。Android 4.4 使用 Bionic 等特定环境，而 GNU/Linux ARM 程序可能依赖 glibc。架构一致也可能无法运行。要同时检查 ELF 架构、解释器、ABI 和依赖库。

## 坑 4：服务列表编号 ≠ Binder 事务号

`service list` 中 `mstar.TvManager` 的数字仅为枚举序号；不能拿它当 `service call` 的事务码。未经查证的“83 号事务”不能写成已验证操作命令。

## 坑 5：写入 Root 脚本 ≠ 开机 Root 成功

必须检查真实 `/init*.rc` 启动链，再备份、谨慎安装、重启、核对日志与 `adb shell id`。本机确实完成这一步，但不代表其他固件都可以。

## 坑 6：名字带 advert 的包可能管其他功能

`com.konka.systemadvert` 曾在本机停用后导致遥控器异常。**包名只能提供线索，不能确定依赖关系。** 这也是不采用网上“一键删广告包清单”的重要原因。

## 坑 7：批量一次删完，无法定位是谁造成故障

第一批应少量、单项测试；保存改动前 disabled 清单；只恢复本轮新停用的包；严格记录电视基础功能的测试结果。

## 坑 8：禁用进程不能立刻等于释放 RAM 和空间

本机禁用后仍看到 `com.konka.message`、`huan.tv.strongtv` 进程，必须考虑已驻留服务、进程延迟退出及重启状态。两次 `/data` 空闲空间都约为 344.2 MiB，不能宣称“删除了十几个包就省了很多存储”。

## 坑 9：1970 年日志时间误判

开机初期没有校准 RTC/NTP 可能显示 1970-01-01。按日志标记与真实重启后的命令结果判断，不以这个时间戳单独下结论。

## 坑 10：公网 Root ADB 风险

端口 5555 不要映射公网，ADB 私钥和公钥授权名单不要放 GitHub。发布原始日志前要检查局域网 IP、设备序列号、用户信息。
