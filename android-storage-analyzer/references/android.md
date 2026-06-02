# Android 存储参考

分析 Android 设备存储时读这份。目标是把 `adb` 只读扫描结果转成清理决策，而不是盲目删除目录。

## 目录地图

| 路径 | 常见内容 | 默认分级 |
|---|---|---|
| `/sdcard/Download` | 安装包、导出文件、压缩包、临时下载 | 🟡，若明确是旧安装包/临时产物可转 🟢 |
| `/sdcard/DCIM` `/sdcard/Pictures` `/sdcard/Movies` | 相机照片、截图、录屏、视频 | 🟡 |
| `/sdcard/Documents` | 文档、导出备份、项目包 | 🟡 |
| `/sdcard/Android/media/<pkg>` | 应用公开媒体、聊天附件、离线内容 | 🟡 |
| `/sdcard/Android/obb/<pkg>` | 大型游戏资源包、可重下资产 | 🟡 或 🔴 |
| `/sdcard/MIUI` `/sdcard/bugreports` `/sdcard/tencent/QQ_Images` 等厂商日志/导出目录 | 视内容而定，日志或明显临时目录可 🟢 |
| `/data` | 系统和应用私有数据 | 不作为清理目标，归蓝色系统空间 |

## 分级规则

### 🟢 可优先清理

只放这类目标：
- 已确认是旧安装包、导出残留、日志、bugreport、崩溃转储
- 用户明确不再需要的下载临时目录
- 明显可重建的公共缓存目录
- 用户明确接受重新下载代价的 `obb` 资源包

可给的建议命令示例：

```bash
adb -s <serial> shell rm -rf '/sdcard/Download/<old-dir>'
adb -s <serial> shell rm -f '/sdcard/Download/<old.apk>'
```

只展示，不自动运行。

### 🟡 需人工判断

典型目标：
- `DCIM`、截图、录屏、音视频素材
- `Android/media/<pkg>`
- 聊天媒体、离线视频、导出备份
- `Download` 里的文档、压缩包、ROM、刷机包

回答里应写清楚：
- 这里通常装什么
- 为什么不能当缓存直接删
- 更安全的处置路径
  - 在应用内清理
  - 在系统“存储”页检查
  - 在文件管理器人工审查

### 🔴 谨慎处理

典型目标：
- `pm clear <pkg>` 这类会重置应用状态的动作
- 卸载应用以回收 `obb/media` 占用
- 仍在使用的大型游戏资源包
- 任何需要动到系统目录或私有应用数据的建议

对这类目标，重点写：
- 为什么别手删
- 正规释放方式
  - `设置 > 存储 > 应用`
  - 应用内“清缓存/管理下载”
  - 卸载后再删除残留公共目录

## Android 限制

- Android 11+ 上，`adb shell` 往往不能直接遍历 `/sdcard/Android/data`。这是平台限制，不是脚本失败。
- 无 root 不应尝试扫描 `/data/data`、`/data/user/0` 这类私有目录。
- `obb` 目录不一定是缓存，很多游戏会把核心资源放在这里。
- `Android/media/<pkg>` 常常是用户主动下载的内容或聊天附件，删除前必须让用户知道后果。

## 识别技巧

- `Android/media/<pkg>` 和 `Android/obb/<pkg>` 的目录名通常就是包名。
- 可用只读命令核实包归属：

```bash
adb -s <serial> shell pm list packages | grep '<pkg-fragment>'
adb -s <serial> shell dumpsys package <package>
```

- `Download` 或厂商目录里的大文件，优先通过后缀和命名判断：
  - `.apk` `.apks` `.xapk`: 安装包
  - `.zip` `.7z` `.rar`: 压缩包 / ROM / 导出包
  - `.mp4` `.mov`: 视频
  - `.log` `.txt`: 日志或导出文本

## 总结口径

最终摘要优先说：
1. 设备总量 / 已用 / 可用
2. 绿色项估算能回收多少
3. 最该先看的 2-3 个目录
4. 风险最高、不要盲删的是哪一项
