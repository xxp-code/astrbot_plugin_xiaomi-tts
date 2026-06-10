from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from astrbot.api import logger
from astrbot.api import AstrBotConfig
from astrbot.api.message_components import Record, Plain

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
}

# 防止 on_decorating_result 重复触发导致语音附加两次
_tts_processed_sessions: set[str] = set()


@register("xiaoxu_tts", "xiaoxu", "小米语音大模型 TTS 音色设置插件，基于 AstrBot 已配置的 MiMo TTS 提供商", "1.0.1")
class XiaomiTTS(Star):
    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        self.config = config

    async def initialize(self):
        """插件初始化"""
        auto_status = "已开启" if self.config.get("auto_tts", True) else "已关闭"
        logger.info(f"小米 TTS 插件已加载！自动语音合成：{auto_status}。使用 /tts 查看帮助。")

    # ======================== 自动语音合成 ========================

    @filter.on_decorating_result()
    async def auto_tts_decorate(self, event: AstrMessageEvent):
        """自动将 LLM 文本回复转为语音并附加到消息链末尾"""
        if not self.config.get("auto_tts", True):
            return

        result = event.get_result()
        if not result or not result.chain:
            return

        text_parts = []
        for comp in result.chain:
            if isinstance(comp, Plain) and comp.text:
                text_parts.append(comp.text)

        full_text = "".join(text_parts).strip()
        if len(full_text) < 4:
            return
        # 过滤 TTS 插件自己的回复
        for prefix in ("🔊", "🎤", "🎭", "⚙️", "✅", "❌", "🤖"):
            if full_text.startswith(prefix):
                return

        # 去重：同一会话+同一文本只附加一次语音
        dedup_key = f"{event.unified_msg_origin}:{full_text}"
        if dedup_key in _tts_processed_sessions:
            return
        if len(_tts_processed_sessions) > 200:
            _tts_processed_sessions.clear()
        _tts_processed_sessions.add(dedup_key)

        tts_provider = self.context.get_using_tts_provider(umo=event.unified_msg_origin)
        if not tts_provider:
            return

        try:
            audio_path = await tts_provider.get_audio(full_text)
            if audio_path:
                result.chain = list(result.chain) + [Record(file=audio_path)]
        except Exception as e:
            logger.warning(f"自动 TTS 合成失败（消息不受影响）: {e}")

    # ======================== 指令组 ========================

    @filter.command_group("tts")
    def tts(self):
        pass

    @tts.command("help")
    async def tts_help(self, event: AstrMessageEvent):
        """显示 TTS 插件帮助信息"""
        help_text = """🎵 **小米 TTS 插件帮助**

本插件基于 AstrBot 已配置的 MiMo TTS 提供商进行语音合成。

**核心功能：**
• 自动语音合成：开启后，机器人的所有文本回复自动附带语音
• 音色切换：支持冰糖、茉莉、苏打、白桦等 9 种预置音色
• 风格控制：支持情绪、语调、方言、语速等多种风格设置

**可用指令：**
• `/tts speak <文本>` - 手动将文本合成为语音并发送
• `/tts auto` - 查看自动语音状态
• `/tts auto on` - 开启自动语音合成
• `/tts auto off` - 关闭自动语音合成
• `/tts voice` - 查看当前音色
• `/tts voice <音色>` - 切换音色
• `/tts voices` - 查看所有可用音色
• `/tts style <描述>` - 设置发音风格
• `/tts style` - 查看当前风格
• `/tts styles` - 查看可用风格列表
• `/tts config` - 查看当前配置
• `/tts help` - 显示本帮助

**使用示例：**
• `/tts voice 冰糖` — 切换到冰糖音色
• `/tts style 开心 东北话` — 设置风格
• `/tts auto on` — 开启自动语音（机器人回复自动带语音）"""
        yield event.plain_result(help_text)

    @tts.command("auto")
    async def tts_auto(self, event: AstrMessageEvent, message: str = ""):
        """查看/切换自动语音合成状态"""
        if not message:
            status = "✅ 已开启" if self.config.get("auto_tts", True) else "❌ 已关闭"
            yield event.plain_result(
                f"🤖 自动语音合成：{status}\n"
                f"使用 `/tts auto on` 开启\n"
                f"使用 `/tts auto off` 关闭"
            )
            return

        cmd = message.strip().lower()
        if cmd == "on":
            self.config["auto_tts"] = True
            self.config.save_config()
            yield event.plain_result("✅ 自动语音合成已**开启**！机器人的文本回复将自动附带语音。")
        elif cmd == "off":
            self.config["auto_tts"] = False
            self.config.save_config()
            yield event.plain_result("❌ 自动语音合成已**关闭**。可继续使用 `/tts speak` 手动合成。")
        else:
            yield event.plain_result(f"用法: `/tts auto on` 或 `/tts auto off`")

    @tts.command("speak")
    async def tts_speak(self, event: AstrMessageEvent, message: str = ""):
        """手动将文本合成为语音并发送"""
        if not message:
            yield event.plain_result("请提供要合成的文本。用法: /tts speak <文本>")
            return

        text_to_speak = message
        if message.startswith("style:"):
            rest = message[6:]
            if "|" in rest:
                _, text_part = rest.split("|", 1)
                text_to_speak = text_part.strip()
            else:
                text_to_speak = rest

        if not text_to_speak:
            yield event.plain_result("请提供要合成的文本。")
            return

        voice = self.config.get("voice", "mimo_default")
        style = self.config.get("style", "").strip()
        style_info = f"\n风格：{style}" if style else ""

        yield event.plain_result(f"🔊 正在合成语音...\n音色：{voice}{style_info}\n文本：{text_to_speak[:50]}{'...' if len(text_to_speak) > 50 else ''}")

        try:
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
                f"💡 切换后，机器人的自动语音回复也会使用新音色。"
            )
            return

        voice_name = message.strip()
        if voice_name in PRESET_VOICES:
            self.config["voice"] = voice_name
            self.config.save_config()
            yield event.plain_result(f"✅ 默认音色已设置为：**{voice_name}** ({PRESET_VOICES[voice_name]})\n后续自动语音将使用此音色。")
        else:
            available = "、".join(PRESET_VOICES.keys())
            yield event.plain_result(f"❌ 未知音色：{voice_name}\n可用音色：{available}")

    @tts.command("voices")
    async def tts_list_voices(self, event: AstrMessageEvent):
        """列出所有可用音色"""
        current = self.config.get("voice", "mimo_default")

        text = "🎤 **可用音色列表**\n"
        text += "（以下为 MiMo TTS 支持的预置音色）\n\n"
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
                    f"使用 `/tts styles` 查看可用风格"
                )
            else:
                yield event.plain_result(
                    "🎭 当前未设置默认风格\n"
                    "使用 `/tts style <风格描述>` 设置风格\n"
                    "使用 `/tts styles` 查看可用风格"
                )
            return

        self.config["style"] = message.strip()
        self.config.save_config()
        yield event.plain_result(f"✅ 默认风格已设置为：**{message.strip()}**\n后续自动语音将使用此风格。")

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
        auto_status = "✅ 已开启" if self.config.get("auto_tts", True) else "❌ 已关闭"

        text = f"""⚙️ **当前 TTS 插件配置**

• 自动语音：{auto_status}
• 默认音色：{self.config.get('voice', 'mimo_default')} ({PRESET_VOICES.get(self.config.get('voice', 'mimo_default'), '')})
• 默认风格：{self.config.get('style', '') or '未设置'}
• TTS 提供商：{self._get_tts_provider_name(event)}

💡 使用 `/tts auto on/off` 切换自动语音
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
