from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from astrbot.api import logger
from astrbot.api import AstrBotConfig
from astrbot.api.message_components import Record

# 预置音色信息（供用户参考，实际音色由 AstrBot 中配置的 MiMo TTS 提供商决定）
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
}


@register("xiaomi_tts", "YourName", "小米语音大模型 TTS 音色设置插件，基于 AstrBot 已配置的 MiMo TTS 提供商", "1.0.0")
class XiaomiTTS(Star):
    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        self.config = config

    async def initialize(self):
        """插件初始化"""
        logger.info("小米 TTS 插件已加载！使用 /tts 查看帮助。")

    # ======================== 指令组 ========================

    @filter.command_group("tts")
    def tts(self):
        pass

    @tts.command("help")
    async def tts_help(self, event: AstrMessageEvent):
        """显示 TTS 插件帮助信息"""
        help_text = """🎵 **小米 TTS 插件帮助**

本插件基于 AstrBot 已配置的 MiMo TTS 提供商进行语音合成。

**可用指令：**
• `/tts speak <文本>` - 将文本合成为语音并发送
• `/tts voice` - 查看当前设置的音色
• `/tts voice <音色>` - 设置/切换默认音色
• `/tts voices` - 查看所有可用音色列表
• `/tts style <描述>` - 设置发音风格（如: 开心、温柔、东北话等）
• `/tts style` - 查看当前风格设置
• `/tts styles` - 查看可用风格列表
• `/tts config` - 查看当前配置
• `/tts help` - 显示本帮助

**使用示例：**
• `/tts speak 你好世界` - 用当前设置朗读
• `/tts voice 冰糖` - 切换到"冰糖"音色
• `/tts style 开心 变快` - 设置开心+快速风格"""
        yield event.plain_result(help_text)

    @tts.command("speak")
    async def tts_speak(self, event: AstrMessageEvent, message: str = ""):
        """将文本合成为语音并发送"""
        if not message:
            yield event.plain_result("请提供要合成的文本。用法: /tts speak <文本>")
            return

        # 解析 style: 前缀（如 /tts speak style:开心|你好世界）
        text_to_speak = message
        style_override = None
        if message.startswith("style:"):
            rest = message[6:]
            if "|" in rest:
                style_part, text_part = rest.split("|", 1)
                style_override = style_part.strip()
                text_to_speak = text_part.strip()
            else:
                # 没有 | 分隔符，整个作为文本
                text_to_speak = rest

        if not text_to_speak:
            yield event.plain_result("请提供要合成的文本。")
            return

        voice = self.config.get("voice", "mimo_default")
        effective_style = style_override if style_override else self.config.get("style", "").strip()

        style_info = f"\n风格：{effective_style}" if effective_style else ""
        yield event.plain_result(f"🔊 正在合成语音...\n音色：{voice}{style_info}\n文本：{text_to_speak[:50]}{'...' if len(text_to_speak) > 50 else ''}")

        try:
            # 使用 AstrBot 已配置的 TTS 提供商
            tts_provider = self.context.get_using_tts_provider(umo=event.unified_msg_origin)
            if not tts_provider:
                yield event.plain_result(
                    "❌ 未配置 TTS 提供商。\n"
                    "请在 AstrBot WebUI → 配置 → TTS 提供商 中配置小米 MiMo TTS 提供商。"
                )
                return

            audio_path = await tts_provider.get_audio(text_to_speak)
            if audio_path:
                yield event.chain_result([Record(file=audio_path)])
            else:
                yield event.plain_result("❌ TTS 提供商未返回音频文件路径，请检查提供商配置。")

        except Exception as e:
            logger.error(f"TTS 合成失败: {e}")
            yield event.plain_result(f"❌ 语音合成失败: {e}")

    @tts.command("voice")
    async def tts_set_voice(self, event: AstrMessageEvent, message: str = ""):
        """设置或查看当前默认音色"""
        if not message:
            current = self.config.get("voice", "mimo_default")
            current_desc = PRESET_VOICES.get(current, "未知音色")
            yield event.plain_result(
                f"🎤 当前音色：**{current}** ({current_desc})\n"
                f"使用 `/tts voice <音色名>` 切换音色\n"
                f"使用 `/tts voices` 查看所有可用音色\n\n"
                f"💡 提示：本设置记录在插件配置中。实际合成效果取决于 AstrBot 中配置的 TTS 提供商是否支持该音色。"
            )
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

        text = "🎤 **可用音色列表**\n"
        text += "（以下为 MiMo TTS 支持的预置音色，请在 AstrBot 提供商配置中匹配对应音色）\n\n"
        for vid, desc in PRESET_VOICES.items():
            marker = " ✅ (当前)" if vid == current else ""
            text += f"• **{vid}**{marker} - {desc}\n"

        text += "\n使用 `/tts voice <音色名>` 切换音色"
        yield event.plain_result(text)

    @tts.command("style")
    async def tts_set_style(self, event: AstrMessageEvent, message: str = ""):
        """设置或查看当前默认发音风格"""
        if not message:
            current_style = self.config.get("style", "").strip()
            if current_style:
                yield event.plain_result(
                    f"🎭 当前默认风格：**{current_style}**\n"
                    f"使用 `/tts style <风格>` 设置风格\n"
                    f"使用 `/tts styles` 查看可用风格\n\n"
                    f"💡 提示：风格控制取决于 TTS 提供商的能力。MiMo 支持自然语言风格描述。"
                )
            else:
                yield event.plain_result(
                    "🎭 当前未设置默认风格（使用 API 默认风格）\n"
                    "使用 `/tts style <风格描述>` 设置风格\n"
                    "使用 `/tts styles` 查看可用风格"
                )
            return

        self.config["style"] = message.strip()
        self.config.save_config()
        yield event.plain_result(f"✅ 默认风格已设置为：**{message.strip()}**\n使用 `/tts speak <文本>` 测试效果")

    @tts.command("styles")
    async def tts_list_styles(self, event: AstrMessageEvent):
        """列出所有可用的发音风格"""
        text = "🎭 **可用发音风格**\n"
        text += "MiMo TTS 支持通过自然语言描述控制语音风格。\n\n"
        text += "**基础情绪**: 开心、悲伤、愤怒、恐惧、惊讶、兴奋、委屈、平静、冷漠\n"
        text += "**复合情绪**: 怅然、欣慰、无奈、愧疚、释然、嫉妒、厌倦、忐忑、动情\n"
        text += "**整体语调**: 温柔、高冷、活泼、严肃、慵懒、俏皮、深沉、干练、凌厉\n"
        text += "**音色定位**: 磁性、醇厚、清亮、空灵、稚嫩、苍老、甜美、沙哑、醇雅\n"
        text += "**人设腔调**: 夹子音、御姐音、正太音、大叔音、台湾腔\n"
        text += "**方言**: 东北话、四川话、河南话、粤语\n"
        text += "**角色扮演**: 孙悟空、林黛玉\n"
        text += "**特殊**: 唱歌、悄悄话、角色扮演\n"
        text += "**语速**: 变快、变慢、正常\n"
        text += "\n多个风格可同时使用，用空格分隔。\n"
        text += "示例：`/tts style 开心 变快`"
        yield event.plain_result(text)

    @tts.command("config")
    async def tts_config(self, event: AstrMessageEvent):
        """查看当前配置"""
        text = f"""⚙️ **当前 TTS 插件配置**

• 默认音色: {self.config.get('voice', 'mimo_default')} ({PRESET_VOICES.get(self.config.get('voice', 'mimo_default'), '')})
• 默认风格: {self.config.get('style', '') or '未设置'}
• 当前 TTS 提供商: {self._get_tts_provider_name(event)}

💡 **提示**：
• 实际音色效果取决于 AstrBot 中配置的 MiMo TTS 提供商
• 请在 WebUI → 配置 → TTS 提供商 中确认 MiMo 已正确配置
• 音色选项需与提供商支持的声音列表匹配
"""
        yield event.plain_result(text)

    def _get_tts_provider_name(self, event: AstrMessageEvent) -> str:
        """获取当前会话的 TTS 提供商名称"""
        try:
            tts_provider = self.context.get_using_tts_provider(umo=event.unified_msg_origin)
            if tts_provider:
                return type(tts_provider).__name__
        except Exception:
            pass
        return "未获取到"

    async def terminate(self):
        """插件销毁时的清理工作"""
        logger.info("小米 TTS 插件已卸载。")
