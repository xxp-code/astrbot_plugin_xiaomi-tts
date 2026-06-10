import base64
import time
import os
import aiohttp

from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from astrbot.api import logger
from astrbot.api import AstrBotConfig

# 预置音色信息
PRESET_VOICES = {
    "mimo_default": "MiMo 默认音色（中国集群默认：冰糖）",
    "冰糖": "中文女声 - 冰糖 (Bingtang)",
    "茉莉": "中文女声 - 茉莉 (Moli)",
    "苏打": "中文男声 - 苏打 (Suda)",
    "白桦": "中文男声 - 白桦 (Baihua)",
    "Mia": "英文女声 - Mia",
    "Chloe": "英文女声 - Chloe",
    "Milo": "英文男声 - Milo",
    "Dean": "英文男声 - Dean",
    "default_zh": "中文女声 (仅 V2 模型)",
    "default_en": "英文女声 (仅 V2 模型)",
}

# 可用风格列表
AVAILABLE_STYLES = [
    "开心", "悲伤", "愤怒", "恐惧", "惊讶", "兴奋", "委屈", "平静", "冷漠",
    "怅然", "欣慰", "无奈", "愧疚", "释然", "嫉妒", "厌倦", "忐忑", "动情",
    "温柔", "高冷", "活泼", "严肃", "慵懒", "俏皮", "深沉", "干练", "凌厉",
    "磁性", "醇厚", "清亮", "空灵", "稚嫩", "苍老", "甜美", "沙哑", "醇雅",
    "夹子音", "御姐音", "正太音", "大叔音", "台湾腔",
    "东北话", "四川话", "河南话", "粤语",
    "孙悟空", "林黛玉",
    "唱歌",
    "变快", "变慢",
    "悄悄话", "角色扮演",
]

# MiMo API 端点
MIMO_API_URL = "https://api.xiaomimimo.com/v1/chat/completions"


@register("xiaomi_tts", "YourName", "小米语音大模型 TTS 音色设置插件，支持多种预置音色与风格控制", "1.0.0")
class XiaomiTTS(Star):
    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        self.config = config

    async def initialize(self):
        """插件初始化"""
        logger.info("小米 TTS 插件已加载！使用 /tts 查看帮助。")

    async def _call_mimo_tts(self, text: str, voice: str = None, style: str = None, model: str = None) -> bytes:
        """调用小米 MiMo TTS API 合成语音，返回音频字节数据"""
        # 从配置获取参数
        if voice is None:
            voice = self.config.get("voice", "mimo_default")
        if model is None:
            model = self.config.get("tts_model", "mimo-v2.5-tts")

        api_key = self.config.get("api_key", "")
        if not api_key:
            raise ValueError("未配置 API Key，请在 WebUI 插件配置中设置 api_key")

        audio_format = self.config.get("audio_format", "wav")

        # 构建 assistant 消息内容
        style_prefix = ""
        if style:
            style_prefix = f"({style})"

        # 构建 user 消息的辅助风格描述
        user_content = ""
        config_speed = self.config.get("speed", "").strip()
        if config_speed:
            user_content = f"请用{config_speed}的语速朗读以下文本。"

        payload = {
            "model": model,
            "messages": [
                {"role": "user", "content": user_content},
                {"role": "assistant", "content": f"{style_prefix}{text}"},
            ],
            "audio": {
                "format": audio_format,
                "voice": voice,
            },
        }

        headers = {
            "api-key": api_key,
            "Content-Type": "application/json",
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(MIMO_API_URL, json=payload, headers=headers, timeout=aiohttp.ClientTimeout(total=60)) as resp:
                if resp.status != 200:
                    error_text = await resp.text()
                    raise Exception(f"API 请求失败 (HTTP {resp.status}): {error_text}")

                result = await resp.json()
                audio_b64 = result.get("choices", [{}])[0].get("message", {}).get("audio", {}).get("data", "")
                if not audio_b64:
                    raise Exception("API 未返回音频数据")

                audio_bytes = base64.b64decode(audio_b64)
                return audio_bytes

    @filter.command_group("tts")
    def tts(self):
        pass

    @tts.command("help")
    async def tts_help(self, event: AstrMessageEvent):
        """显示 TTS 插件帮助信息"""
        help_text = """🎵 **小米 TTS 插件帮助**

**可用指令：**
• `/tts speak <文本>` - 将文本合成为语音并发送
• `/tts speak style:<风格> <文本>` - 指定风格合成语音
• `/tts voice <音色>` - 设置/切换默认音色
• `/tts voice` - 查看当前默认音色
• `/tts voices` - 查看所有可用音色列表
• `/tts style <风格>` - 设置/切换默认风格
• `/tts style` - 查看当前默认风格
• `/tts styles` - 查看可用风格列表  
• `/tts config` - 查看当前配置信息
• `/tts help` - 显示本帮助

**使用示例：**
• `/tts speak 你好世界` - 用默认音色朗读
• `/tts speak style:开心 变快 今天天气真好！` - 用开心+快速风格朗读
• `/tts voice 冰糖` - 切换到"冰糖"音色"""
        yield event.plain_result(help_text)

    @tts.command("speak")
    async def tts_speak(self, event: AstrMessageEvent, message: str = ""):
        """将文本合成为语音并发送文件"""
        if not message:
            yield event.plain_result("请提供要合成的文本。用法: /tts speak <文本>")
            return

        api_key = self.config.get("api_key", "")
        if not api_key:
            yield event.plain_result("❌ 未配置 API Key。请在 WebUI 插件配置中设置 MiMo 开放平台的 api_key，然后重载插件。")
            return

        # 解析 style 前缀：style:开心 变快 文本内容
        text_to_speak = message
        style_override = None
        if message.startswith("style:"):
            # 语法: /tts speak style:<风格的剩余部分都在message中>
            # 实际上，由于 AstrBot 的 command 会将第一个空格后的所有内容作为 message 参数
            # 所以 message = "style:开心 变快 今天是好日子"
            rest = message[6:]  # 去掉 "style:"
            # 找到第一个文本开始的位置 - 实际上我们不知道哪里是风格哪里是文本
            # 简化处理: 用户用 /tts speak style:开心 变快|今天的文本 格式
            if "|" in rest:
                style_part, text_part = rest.split("|", 1)
                style_override = style_part.strip()
                text_to_speak = text_part.strip()
            else:
                # 尝试智能拆分: 取最后一段作为文本
                parts = rest.rsplit(" ", 1)
                if len(parts) > 1:
                    # 倒数第一个可能是文本开头
                    text_to_speak = parts[-1]
                    style_override = parts[0]
                else:
                    text_to_speak = rest

        if not text_to_speak:
            yield event.plain_result("请提供要合成的文本。")
            return

        voice = self.config.get("voice", "mimo_default")
        model = self.config.get("tts_model", "mimo-v2.5-tts")

        # 默认风格
        default_style = self.config.get("style", "").strip()
        effective_style = style_override if style_override else default_style

        yield event.plain_result(f"🔊 正在合成语音...\n音色：{voice}\n风格：{effective_style or '默认'}\n文本：{text_to_speak[:50]}{'...' if len(text_to_speak) > 50 else ''}")

        try:
            audio_bytes = await self._call_mimo_tts(text_to_speak, voice=voice, style=effective_style, model=model)

            # 保存为临时文件
            temp_dir = os.path.join("data", "temp")
            os.makedirs(temp_dir, exist_ok=True)
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"tts_{timestamp}.wav"
            filepath = os.path.join(temp_dir, filename)
            with open(filepath, "wb") as f:
                f.write(audio_bytes)

            # 发送音频文件
            yield event.file_result(filepath)

        except ValueError as e:
            yield event.plain_result(f"❌ {e}")
        except Exception as e:
            logger.error(f"TTS 合成失败: {e}")
            yield event.plain_result(f"❌ 语音合成失败: {e}")

    @tts.command("voice")
    async def tts_set_voice(self, event: AstrMessageEvent, message: str = ""):
        """设置或查看当前默认音色"""
        if not message:
            current = self.config.get("voice", "mimo_default")
            current_desc = PRESET_VOICES.get(current, "未知音色")
            yield event.plain_result(f"🎤 当前默认音色：**{current}** ({current_desc})\n使用 `/tts voice <音色名>` 切换音色\n使用 `/tts voices` 查看所有可用音色")
            return

        voice_name = message.strip()
        if voice_name in PRESET_VOICES:
            self.config["voice"] = voice_name
            self.config.save_config()
            yield event.plain_result(f"✅ 默认音色已设置为：**{voice_name}** ({PRESET_VOICES[voice_name]})")
        else:
            available = "、".join(PRESET_VOICES.keys())
            yield event.plain_result(f"❌ 未知音色：{voice_name}\n可用音色：{available}")

    @tts.command("voices")
    async def tts_list_voices(self, event: AstrMessageEvent):
        """列出所有可用音色"""
        current = self.config.get("voice", "mimo_default")
        model = self.config.get("tts_model", "mimo-v2.5-tts")

        text = f"🎤 **可用音色列表** (当前模型: {model})\n\n"
        for vid, desc in PRESET_VOICES.items():
            marker = " ✅ (当前)" if vid == current else ""
            text += f"• **{vid}**{marker} - {desc}\n"

        text += "\n使用 `/tts voice <音色名>` 切换音色"
        yield event.plain_result(text)

    @tts.command("style")
    async def tts_set_style(self, event: AstrMessageEvent, message: str = ""):
        """设置或查看当前默认发音风格"""
        if not message:
            current = self.config.get("style", "").strip()
            current_speed = self.config.get("speed", "").strip()
            if current or current_speed:
                parts = []
                if current:
                    parts.append(f"风格：{current}")
                if current_speed:
                    parts.append(f"语速：{current_speed}")
                yield event.plain_result(f"🎭 当前默认设置：{', '.join(parts)}\n使用 `/tts style <风格>` 设置风格\n使用 `/tts styles` 查看可用风格")
            else:
                yield event.plain_result("🎭 当前未设置默认风格（使用 API 默认风格）\n使用 `/tts style <风格>` 设置风格\n使用 `/tts styles` 查看可用风格")
            return

        style_text = message.strip()

        # 检查语速关键词
        speed_keywords = ["变快", "变慢", "正常", "较慢", "较快", "非常快", "极慢", "极快"]
        found_speed = None
        for kw in speed_keywords:
            if kw in style_text:
                found_speed = kw
                break

        if found_speed:
            # 语速单独存储
            self.config["speed"] = found_speed
            # 剩下的作为风格
            remaining = style_text.replace(found_speed, "").strip()
            self.config["style"] = remaining
            self.config.save_config()
            parts = []
            if remaining:
                parts.append(f"风格：{remaining}")
            parts.append(f"语速：{found_speed}")
            yield event.plain_result(f"✅ 默认设置已更新：{', '.join(parts)}")
        else:
            self.config["style"] = style_text
            self.config["speed"] = ""
            self.config.save_config()
            yield event.plain_result(f"✅ 默认风格已设置为：**{style_text}**\n使用 `/tts speak <文本>` 测试效果")

    @tts.command("styles")
    async def tts_list_styles(self, event: AstrMessageEvent):
        """列出所有可用的发音风格"""
        text = "🎭 **可用发音风格**\n\n"
        text += "**基础情绪**: 开心、悲伤、愤怒、恐惧、惊讶、兴奋、委屈、平静、冷漠\n"
        text += "**复合情绪**: 怅然、欣慰、无奈、愧疚、释然、嫉妒、厌倦、忐忑、动情\n"
        text += "**整体语调**: 温柔、高冷、活泼、严肃、慵懒、俏皮、深沉、干练、凌厉\n"
        text += "**音色定位**: 磁性、醇厚、清亮、空灵、稚嫩、苍老、甜美、沙哑、醇雅\n"
        text += "**人设腔调**: 夹子音、御姐音、正太音、大叔音、台湾腔\n"
        text += "**方言**: 东北话、四川话、河南话、粤语\n"
        text += "**角色扮演**: 孙悟空、林黛玉\n"
        text += "**特殊**: 唱歌（单独使用）、悄悄话、角色扮演\n"
        text += "**语速**: 变快、变慢、正常\n"
        text += "\n多个风格可同时使用，用空格分隔。示例：`/tts style 开心 变快`\n"
        text += "或在 speak 时指定：`/tts speak style:悲伤|今天心情不好`"

        yield event.plain_result(text)

    @tts.command("config")
    async def tts_config(self, event: AstrMessageEvent):
        """查看当前配置"""
        api_key = self.config.get("api_key", "")
        api_key_masked = api_key[:8] + "****" + api_key[-4:] if len(api_key) > 12 else "未设置"

        text = f"""⚙️ **当前 TTS 配置**
• API Key: {api_key_masked}
• TTS 模型: {self.config.get('tts_model', 'mimo-v2.5-tts')}
• 默认音色: {self.config.get('voice', 'mimo_default')} ({PRESET_VOICES.get(self.config.get('voice', 'mimo_default'), '')})
• 默认风格: {self.config.get('style', '') or '未设置'}
• 默认语速: {self.config.get('speed', '') or '未设置'}
• 音频格式: {self.config.get('audio_format', 'wav')}
"""
        yield event.plain_result(text)

    async def terminate(self):
        """插件销毁时的清理工作"""
        logger.info("小米 TTS 插件已卸载。")
