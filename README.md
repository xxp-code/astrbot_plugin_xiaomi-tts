# 小米 TTS 语音合成插件

基于 AstrBot 已配置的 MiMo TTS 提供商进行语音合成，支持音色与风格设置。**开启自动语音后，机器人的所有文本回复自动附带语音。**

## 功能特性

- 🤖 **自动语音合成**：开启后，机器人每条文本回复自动附带对应语音（默认开启）
- 🎤 **音色管理**：支持冰糖、茉莉、苏打、白桦、Mia、Chloe 等 9 种预置音色
- 🎭 **风格控制**：支持情绪、语调、方言、角色扮演、语速等多种风格
- 🔌 **即插即用**：直接调用 AstrBot 中已配置的 TTS 提供商，无需额外配置 API Key
- ⚙️ **WebUI 配置**：在 AstrBot 管理面板中可视化配置默认音色、风格和自动语音开关

## 前置条件

1. 在 AstrBot WebUI → 配置 → TTS 提供商中配置好 MiMo TTS 提供商
2. 确保 TTS 提供商工作正常

## 安装方法

将插件文件夹放入 AstrBot 的 `data/plugins` 目录，然后在 WebUI 插件管理中启用即可：

```bash
cd AstrBot/data/plugins
git clone https://github.com/你的用户名/astrbot_plugin_xiaomi-tts
```

## 指令说明

| 指令 | 说明 |
|------|------|
| `/tts help` | 显示帮助信息 |
| `/tts auto` | 查看自动语音合成状态 |
| `/tts auto on` | 开启自动语音（机器人回复自动附带语音） |
| `/tts auto off` | 关闭自动语音 |
| `/tts speak <文本>` | 手动将文本合成为语音并发送 |
| `/tts voice` | 查看当前音色 |
| `/tts voice <音色>` | 切换默认音色 |
| `/tts voices` | 列出所有可用音色 |
| `/tts style` | 查看当前风格 |
| `/tts style <描述>` | 设置默认发音风格 |
| `/tts styles` | 查看可用风格参考列表 |
| `/tts config` | 查看当前配置 |

> **注意**：`/tts styles` 仅查看列表（无参数），`/tts style` 是设置风格（带参数）。

## 使用示例

```
/tts auto on                   # 开启自动语音
/tts voice Dean                # 切换到 Dean 音色
/tts style 东北话 开心           # 设置风格
/tts speak 你好世界              # 手动合成语音
/tts config                    # 查看配置
```

设置好音色和风格后，直接跟机器人聊天即可自动收到语音回复。

## 配置说明

在 WebUI 插件配置页面可设置：

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `auto_tts` | 自动语音合成开关 | `true` |
| `voice` | 默认音色 | `mimo_default` |
| `style` | 默认发音风格描述 | 空 |

## 可用音色

| 音色 | 说明 |
|------|------|
| `mimo_default` | 默认识别（中国集群默认：冰糖） |
| `冰糖` | 中文女声 |
| `茉莉` | 中文女声 |
| `苏打` | 中文男声 |
| `白桦` | 中文男声 |
| `Mia` | 英文女声 |
| `Chloe` | 英文女声 |
| `Milo` | 英文男声 |
| `Dean` | 英文男声 |
