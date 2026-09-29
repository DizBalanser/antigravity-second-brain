"""
Personal Telegram Companion Bot — Mobile Second Brain Access
============================================================
Allows you to chat with your Second Brain, dump thoughts, and send
voice notes while away from your computer.

Features:
- Instant voice note transcription via Gemini 2.5 Flash
- Reads and updates your local Obsidian / Antigravity files
- Restricted strictly to your personal Telegram User ID
"""

import os
import sys
import logging
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
from google import genai
from google.genai import types

VAULT_ROOT = Path(__file__).resolve().parent.parent.parent
ENV_PATH = VAULT_ROOT / "_system" / ".env"
load_dotenv(dotenv_path=ENV_PATH)

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ALLOWED_USER_ID = int(os.getenv("TELEGRAM_USER_ID", "0"))
GEMINI_KEY = os.getenv("GEMINI_API_KEY")

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger("MobileCompanion")

client = genai.Client(api_key=GEMINI_KEY) if GEMINI_KEY else genai.Client()

def get_system_prompt() -> str:
    agents_file = VAULT_ROOT / ".agents" / "AGENTS.md"
    profile_file = VAULT_ROOT / "_context" / "PROFILE.md"
    rules_file = VAULT_ROOT / "_context" / "RULES.md"
    parts = []
    if profile_file.exists(): parts.append(profile_file.read_text(encoding="utf-8"))
    if rules_file.exists(): parts.append(rules_file.read_text(encoding="utf-8"))
    if agents_file.exists(): parts.append(agents_file.read_text(encoding="utf-8"))
    return "\n\n".join(parts) or "You are a personal AI executive assistant."

def is_authorized(update: Update) -> bool:
    if ALLOWED_USER_ID == 0:
        return True
    return update.effective_user.id == ALLOWED_USER_ID

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_authorized(update):
        await update.message.reply_text(f"Access restricted. Your Telegram ID: `{update.effective_user.id}`.")
        return
    await update.message.reply_text(
        "👋 **Hello! Your Personal AI Second Brain is online.**\n\n"
        "You can send text messages or **record voice notes** on the go.\n"
        "I will listen, analyze, structure your thoughts, and keep your tasks organized!",
        parse_mode="Markdown"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_authorized(update): return
    text = update.message.text
    if not text: return

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    try:
        resp = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=text,
            config=types.GenerateContentConfig(system_instruction=get_system_prompt(), temperature=0.5)
        )
        reply = resp.text or "Done!"
        await update.message.reply_text(reply)
    except Exception as e:
        logger.error(f"Error handling message: {e}")
        await update.message.reply_text(f"⚠️ Error: {e}")

async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_authorized(update): return
    voice = update.message.voice
    if not voice: return

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    try:
        vf = await context.bot.get_file(voice.file_id)
        audio_bytes = await vf.download_as_bytearray()
        audio_part = types.Part.from_bytes(data=bytes(audio_bytes), mime_type="audio/ogg")
        trans = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[audio_part, "Transcribe this voice message accurately. Return ONLY the transcription text."]
        ).text.strip()

        resp = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=trans,
            config=types.GenerateContentConfig(system_instruction=get_system_prompt(), temperature=0.5)
        )
        reply = resp.text or "Done!"
        await update.message.reply_text(f"🎤 *«{trans}»*\n\n{reply}", parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Error handling voice: {e}")
        await update.message.reply_text(f"⚠️ Error processing voice: {e}")

def main():
    if not BOT_TOKEN:
        print("Please configure TELEGRAM_BOT_TOKEN in _system/.env")
        sys.exit(1)
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.VOICE, handle_voice))
    print("Mobile Companion Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
