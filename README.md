# 小米 TTS 语音合成插件

基于 [小米 MiMo 语音大模型](https://platform.xiaomimimo.com) 的 AstrBot TTS 插件，支持多种预置音色设置与风格控制。

## 功能特性

- 🎤 **多音色支持**：支持冰糖、茉莉、苏打、白桦、Mia、Chloe 等 9 种预置音色
- 🎭 **丰富风格控制**：支持情绪、语速、方言、角色扮演等多种发音风格
- ⚙️ **WebUI 配置**：在 AstrBot 管理面板中可视化配置 API Key、默认音色等
- 🔊 **语音合成**：将文本实时合成为 WAV 音频文件并发送

## 前置条件

1. 前往 [小米 MiMo 开放平台](https://platform.xiaomimimo.com) 注册并获取 API Key
2. 当前 TTS 功能限时免费

## 安装方法

在 AstrBot 的 `data/plugins` 目录下克隆本仓库：

```bash
cd AstrBot/data/plugins
git clone https://github.com/xiaomi/astrbot_plugin_xiaomi-tts
```

然后在 WebUI 的插件管理页面启用本插件，并填写 API Key 等配置。

## 指令说明

| 指令 | 说明 |
|------|------|
| `/tts help` | 显示帮助信息 |
| `/tts speak <文本>` | 将文本合成为语音并发送 |
| `/tts speak style:<风格>\|<文本>` | 指定风格合成语音 |
| `/tts voice <音色>` | 设置默认音色 |
| `/tts voice` | 查看当前音色 |
| `/tts voices` | 列出所有可用音色 |
| `/tts style <风格>` | 设置默认发音风格 |
| `/tts style` | 查看当前风格设置 |
| `/tts styles` | 列出所有可用风格 |
| `/tts config` | 查看当前配置 |

## 使用示例

```
/tts speak 你好世界，这是小米TTS插件生成的语音！
/tts speak style:开心 变快|今天天气真好呀！
/tts voice 冰糖
/tts style 温柔 磁性
/tts config
```

## 配置说明

在 WebUI 插件配置页面可设置：

- **api_key**: 小米 MiMo 开放平台 API Key（必填）
- **tts_model**: TTS 模型选择（默认 `mimo-v2.5-tts`）
- **voice**: 默认音色（默认 `mimo_default`）
- **style**: 默认发音风格（可选）
- **speed**: 默认语速控制（可选）
- **audio_format**: 输出音频格式（默认 `wav`）

## 注意事项

- 本插件使用异步网络请求（aiohttp），不会阻塞 Bot 主进程
- TTS 生成的音频临时保存在 `data/temp/` 目录
- 如遇到 API 错误，请检查 API Key 是否正确配置，以及 MiMo 平台账户状态
