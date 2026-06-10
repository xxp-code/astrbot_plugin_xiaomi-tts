# 小米 TTS 语音合成插件

基于 AstrBot 已配置的 MiMo TTS 提供商进行语音合成，支持音色与风格设置。

## 功能特性

- 🎤 **音色管理**：支持冰糖、茉莉、苏打、白桦、Mia、Chloe 等 9 种预置音色的选择与切换
- 🎭 **风格控制**：支持情绪、语调、方言、角色扮演等多种发音风格设置
- 🔌 **即插即用**：直接调用 AstrBot 中已配置的 TTS 提供商，无需单独配置 API Key
- ⚙️ **WebUI 配置**：在 AstrBot 管理面板中可视化配置默认音色和风格

## 前置条件

1. 在 AstrBot WebUI → 配置 → TTS 提供商中配置好 MiMo TTS（或其他兼容的 TTS 提供商）
2. 确保 TTS 提供商工作正常

## 安装方法

在 AstrBot 的 `data/plugins` 目录下克隆本仓库：

```bash
cd AstrBot/data/plugins
git clone https://github.com/xiaomi/astrbot_plugin_xiaomi-tts
```

然后在 WebUI 的插件管理页面启用本插件。

## 指令说明

| 指令 | 说明 |
|------|------|
| `/tts help` | 显示帮助信息 |
| `/tts speak <文本>` | 将文本合成为语音并发送 |
| `/tts speak style:<风格>\|<文本>` | 临时指定风格合成语音 |
| `/tts voice` | 查看当前音色 |
| `/tts voice <音色>` | 设置默认音色 |
| `/tts voices` | 列出所有可用音色 |
| `/tts style` | 查看当前风格 |
| `/tts style <描述>` | 设置默认风格 |
| `/tts styles` | 列出可用风格参考 |
| `/tts config` | 查看当前配置 |

## 使用示例

```
/tts speak 你好世界
/tts speak style:开心|今天天气真好呀！
/tts voice 冰糖
/tts style 温柔 磁性
/tts config
```

## 配置说明

在 WebUI 插件配置页面可设置：

- **voice**: 默认音色（默认 `mimo_default`）
- **style**: 默认发音风格描述（可选）

实际音色效果取决于 AstrBot 中配置的 TTS 提供商的支持能力。
