"""
Antigravity Second Brain — Telegram AI Agent Companion
======================================================
Remote 24/7 mobile copilot with full terminal execution, dynamic memory,
proactive check-ins, and anti-procrastination micro-sprints.

Features:
- Powered by Google Gemini (gemini-2.5-flash / gemini-flash-latest) with Tool Calling
- Remote Terminal Command Execution (PowerShell / Bash)
- Direct Obsidian File Management (reads, writes, daily logs, todo lists)
- Self-Evolving Persistent Memory (Letta-style core memory updates)
- Proactive Check-in Engine (every 3.5 - 4 hours accountability)
- 15-Minute Micro-Sprints (Jarvis-style anti-procrastination timer)
- Voice Note & Audio Transcription
"""

import os
import sys
import json
import logging
import asyncio
import subprocess
import re
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Ensure UTF-8 output on consoles
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Telegram
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# Gemini API
from google import genai
from google.genai import types

VAULT_ROOT = Path(__file__).resolve().parent.parent.parent
ENV_PATH = VAULT_ROOT / "_system" / ".env"
load_dotenv(dotenv_path=ENV_PATH)

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ALLOWED_USER_ID = int(os.getenv("TELEGRAM_USER_ID", "0"))
GEMINI_KEY = os.getenv("GEMINI_API_KEY")

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger("AntigravityBot")

ACTIVE_APPLICATION = None
client = genai.Client(api_key=GEMINI_KEY) if GEMINI_KEY else genai.Client()

def get_system_prompt() -> str:
    agents_file = VAULT_ROOT / ".agents" / "AGENTS.md"
    profile_file = VAULT_ROOT / "_context" / "PROFILE.md"
    rules_file = VAULT_ROOT / "_context" / "RULES.md"
    parts = []
    if profile_file.exists():
        parts.append(profile_file.read_text(encoding="utf-8"))
    if rules_file.exists():
        parts.append(rules_file.read_text(encoding="utf-8"))
    if agents_file.exists():
        parts.append(agents_file.read_text(encoding="utf-8"))
        
    base = "\n\n".join(parts) or "You are an AI Executive Assistant and Second Brain partner."
    instructions = f"""
{base}

---
CORE CAPABILITIES:
1. AUTO-CAPTURE: When user shares an update, completed item, or new action:
   - Call `log_daily_activity(activity, details)`
   - If they completed a task, call `update_todo_status(task_keyword, True)`
2. DESTROY PROCRASTINATION: When user feels stuck, overwhelmed, or inactive, initiate `start_micro_sprint(task_name, minutes)`.
3. EVOLVE MEMORY: When user establishes a new habit, principle, or permanent rule, call `update_core_memory(category, detail)`.
4. NEXT ACTION: Always conclude progress updates by asking: "What are you working on right now?" or "What is the next micro-step?"
"""
    return instructions

# ============================================================
# Tool Implementations
# ============================================================

def run_shell_command(command: str, cwd: str = None) -> str:
    work_dir = Path(cwd) if cwd else VAULT_ROOT
    try:
        proc = subprocess.run(
            command,
            shell=True,
            cwd=work_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=120,
            encoding="utf-8",
            errors="replace"
        )
        out = (proc.stdout or "").strip()
        err = (proc.stderr or "").strip()
        if proc.returncode != 0:
            return f"[Exit code {proc.returncode}]\nSTDOUT:\n{out}\nSTDERR:\n{err}"
        return out if out else "(Command completed with no output)"
    except subprocess.TimeoutExpired:
        return "Error: Command timed out after 120 seconds."
    except Exception as e:
        return f"Error executing command: {str(e)}"

def read_file(relative_or_abs_path: str) -> str:
    p = Path(relative_or_abs_path)
    if not p.is_absolute():
        p = VAULT_ROOT / relative_or_abs_path
    if not p.exists():
        return f"File not found: {p}"
    try:
        return p.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        return f"Error reading file: {str(e)}"

def write_file(relative_or_abs_path: str, content: str) -> str:
    p = Path(relative_or_abs_path)
    if not p.is_absolute():
        p = VAULT_ROOT / relative_or_abs_path
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        return f"File successfully written: {p}"
    except Exception as e:
        return f"Error writing file: {str(e)}"

def log_daily_activity(activity: str, details: str = "") -> str:
    today_str = datetime.now().strftime("%Y-%m-%d")
    daily_dir = VAULT_ROOT / "_daily"
    daily_dir.mkdir(parents=True, exist_ok=True)
    daily_file = daily_dir / f"{today_str}.md"

    time_str = datetime.now().strftime("%H:%M")
    entry = f"- `{time_str}` — {activity}"
    if details:
        entry += f" ({details})"

    if not daily_file.exists():
        content = f"""---
summary: "Daily Chronicle for {today_str}"
tags: [daily, log]
date: {today_str}
---

# Daily Chronicle: {today_str}

## 🎯 Top Priorities
- [ ] Priority 1
- [ ] Priority 2
- [ ] Priority 3

## 📝 Activity Chronicle
{entry}

## 🌙 Evening Shutdown
- [ ] Review pending tasks
- [ ] Tomorrow focus ready
"""
        daily_file.write_text(content, encoding="utf-8")
        return f"Created {today_str}.md and logged: {entry}"
    else:
        content = daily_file.read_text(encoding="utf-8")
        marker = "## 📝 Activity Chronicle"
        if marker in content:
            content = content.replace(marker, f"{marker}\n{entry}", 1)
        else:
            content += f"\n\n{marker}\n{entry}"
        daily_file.write_text(content, encoding="utf-8")
        return f"Logged into {today_str}.md: {entry}"

def update_todo_status(task_keyword: str, completed: bool = True) -> str:
    todo_file = VAULT_ROOT / "_pool" / "todo.md"
    if not todo_file.exists():
        return f"File not found: {todo_file}"
    content = todo_file.read_text(encoding="utf-8")
    lines = content.splitlines()
    found = False
    new_lines = []
    mark = "[x]" if completed else "[ ]"
    for line in lines:
        if task_keyword.lower() in line.lower() and ("- [ ]" in line or "- [x]" in line):
            line = re.sub(r"- \[[ xX]\]", f"- {mark}", line, count=1)
            found = True
        new_lines.append(line)
    if found:
        todo_file.write_text("\n".join(new_lines), encoding="utf-8")
        status_txt = "completed [x]" if completed else "reopened [ ]"
        return f"✅ Task '{task_keyword}' marked as {status_txt}"
    return f"Task containing '{task_keyword}' not found in todo.md."

async def _async_sprint_timer(chat_id: int, task: str, mins: int):
    await asyncio.sleep(mins * 60)
    if ACTIVE_APPLICATION:
        try:
            await ACTIVE_APPLICATION.bot.send_message(
                chat_id=chat_id,
                text=f"⏰ **Micro-Sprint ({mins} min) Completed!**\n\nHow is progress on: **«{task}»**?\nDid you get past the starting friction? Send a quick text or voice update!",
                parse_mode="Markdown"
            )
        except Exception as e:
            logger.error(f"Error sending sprint timer message: {e}")

def start_micro_sprint(task_name: str, minutes: int = 15) -> str:
    mins = max(1, min(60, int(minutes)))
    if ACTIVE_APPLICATION and ALLOWED_USER_ID != 0:
        asyncio.create_task(_async_sprint_timer(ALLOWED_USER_ID, task_name, mins))
    return f"⏱️ Focus sprint started for {mins} minutes: «{task_name}»! Countdown active. I will ping you in {mins} minutes. Shut down distractions and take the first micro-step!"

def update_core_memory(category: str, detail: str) -> str:
    p = VAULT_ROOT / "_context" / "PROFILE.md"
    if not p.exists():
        return f"File not found: {p}"
    content = p.read_text(encoding="utf-8")
    date_str = datetime.now().strftime("%Y-%m-%d")
    entry = f"- [{date_str}] **{category}:** {detail}\n"
    marker = "## 🧠 Core Memory & Evolving Facts"
    if marker in content:
        content = content.replace(marker, marker + "\n" + entry, 1)
    else:
        content += f"\n\n{marker}\n{entry}"
    p.write_text(content, encoding="utf-8")
    return f"🧠 Core memory updated in {p.name}:\n• [{category}]: {detail}"

TOOL_FUNCS = {
    "run_shell_command": run_shell_command,
    "read_file": read_file,
    "write_file": write_file,
    "log_daily_activity": log_daily_activity,
    "update_todo_status": update_todo_status,
    "start_micro_sprint": start_micro_sprint,
    "update_core_memory": update_core_memory,
}

# ============================================================
# Gemini Agent Execution Loop
# ============================================================

CHAT_SESSIONS = {}

def get_or_create_chat(user_id: int):
    if user_id not in CHAT_SESSIONS:
        CHAT_SESSIONS[user_id] = []
    return CHAT_SESSIONS[user_id]

async def process_with_ai(user_id: int, user_message: str) -> str:
    history = get_or_create_chat(user_id)
    history.append({"role": "user", "parts": [{"text": user_message}]})

    tools = [
        types.Tool(function_declarations=[
            types.FunctionDeclaration(
                name="run_shell_command",
                description="Run a terminal command (PowerShell / Bash) on the host computer.",
                parameters=types.Schema(
                    type=types.Type.OBJECT,
                    properties={
                        "command": types.Schema(type=types.Type.STRING, description="Command to execute"),
                        "cwd": types.Schema(type=types.Type.STRING, description="Working directory (optional)")
                    },
                    required=["command"]
                )
            ),
            types.FunctionDeclaration(
                name="read_file",
                description="Read a file from the vault or filesystem.",
                parameters=types.Schema(
                    type=types.Type.OBJECT,
                    properties={
                        "relative_or_abs_path": types.Schema(type=types.Type.STRING, description="Relative or absolute path")
                    },
                    required=["relative_or_abs_path"]
                )
            ),
            types.FunctionDeclaration(
                name="write_file",
                description="Write or overwrite a file in the vault.",
                parameters=types.Schema(
                    type=types.Type.OBJECT,
                    properties={
                        "relative_or_abs_path": types.Schema(type=types.Type.STRING, description="Path to file"),
                        "content": types.Schema(type=types.Type.STRING, description="Content to write")
                    },
                    required=["relative_or_abs_path", "content"]
                )
            ),
            types.FunctionDeclaration(
                name="log_daily_activity",
                description="Record what was done or what the user is working on into today's daily log (_daily/YYYY-MM-DD.md).",
                parameters=types.Schema(
                    type=types.Type.OBJECT,
                    properties={
                        "activity": types.Schema(type=types.Type.STRING, description="Activity description"),
                        "details": types.Schema(type=types.Type.STRING, description="Optional extra details")
                    },
                    required=["activity"]
                )
            ),
            types.FunctionDeclaration(
                name="update_todo_status",
                description="Mark a task as completed [x] or pending [ ] in _pool/todo.md.",
                parameters=types.Schema(
                    type=types.Type.OBJECT,
                    properties={
                        "task_keyword": types.Schema(type=types.Type.STRING, description="Keyword identifying the task"),
                        "completed": types.Schema(type=types.Type.BOOLEAN, description="True for completed, False for pending")
                    },
                    required=["task_keyword"]
                )
            ),
            types.FunctionDeclaration(
                name="start_micro_sprint",
                description="Launch a 15-minute micro sprint to crush procrastination. Schedules a Telegram ping after the duration.",
                parameters=types.Schema(
                    type=types.Type.OBJECT,
                    properties={
                        "task_name": types.Schema(type=types.Type.STRING, description="Specific micro task"),
                        "minutes": types.Schema(type=types.Type.INTEGER, description="Duration in minutes (default 15)")
                    },
                    required=["task_name"]
                )
            ),
            types.FunctionDeclaration(
                name="update_core_memory",
                description="Permanently record a core preference, habit, or life fact into PROFILE.md.",
                parameters=types.Schema(
                    type=types.Type.OBJECT,
                    properties={
                        "category": types.Schema(type=types.Type.STRING, description="Category (e.g. Focus, Routine, Projects)"),
                        "detail": types.Schema(type=types.Type.STRING, description="The concrete fact or rule")
                    },
                    required=["category", "detail"]
                )
            )
        ])
    ]

    candidate_models = ["gemini-2.5-flash", "gemini-flash-latest", "gemini-2.0-flash"]
    max_turns = 6

    for _ in range(max_turns):
        try:
            resp = None
            last_err = None
            for model_name in candidate_models:
                try:
                    contents = []
                    for h in history[-10:]:
                        contents.append(types.Content(
                            role=h["role"],
                            parts=[types.Part.from_text(text=p["text"]) for p in h["parts"] if "text" in p]
                        ))
                    resp = client.models.generate_content(
                        model=model_name,
                        contents=contents,
                        config=types.GenerateContentConfig(
                            system_instruction=get_system_prompt(),
                            tools=tools,
                            temperature=0.4
                        )
                    )
                    if resp:
                        break
                except Exception as e:
                    last_err = e
                    await asyncio.sleep(1)

            if not resp:
                return f"⚠️ Execution error: {str(last_err)}"

            function_calls = resp.function_calls
            if function_calls:
                for call in function_calls:
                    fn_name = call.name
                    fn_args = dict(call.args) if call.args else {}
                    logger.info(f"Tool call: {fn_name}({fn_args})")
                    if fn_name in TOOL_FUNCS:
                        tool_result = TOOL_FUNCS[fn_name](**fn_args)
                    else:
                        tool_result = f"Error: Tool {fn_name} not recognized."

                    history.append({
                        "role": "model",
                        "parts": [{"text": f"[Called tool {fn_name} with args {json.dumps(fn_args)}]"}]
                    })
                    history.append({
                        "role": "user",
                        "parts": [{"text": f"Tool '{fn_name}' execution result:\n{tool_result}\nNow fulfill original request."}]
                    })
            else:
                reply_text = resp.text or "Done!"
                history.append({"role": "model", "parts": [{"text": reply_text}]})
                return reply_text

        except Exception as e:
            logger.error(f"Error in process_with_ai: {e}")
            return f"⚠️ Error: {str(e)}"

    return "Commands executed successfully!"

# ============================================================
# Proactive Check-in Engine
# ============================================================

LAST_SENT_CHECKINS = set()
LAST_CHECKIN_TIMESTAMP = datetime.now()

async def proactive_scheduler_loop(app: Application) -> None:
    global LAST_CHECKIN_TIMESTAMP
    while True:
        try:
            now = datetime.now()
            today_str = now.strftime("%Y-%m-%d")
            checkpoints = [
                (8, 30), (10, 30), (12, 30), (14, 30),
                (16, 30), (18, 30), (20, 30), (22, 30)
            ]
            should_trigger = False

            for ch_hour, ch_min in checkpoints:
                key = f"{today_str}_{ch_hour:02d}:{ch_min:02d}"
                if now.hour == ch_hour and abs(now.minute - ch_min) <= 2 and key not in LAST_SENT_CHECKINS:
                    LAST_SENT_CHECKINS.add(key)
                    should_trigger = True
                    break

            if not should_trigger and (8 <= now.hour <= 23):
                elapsed_sec = (now - LAST_CHECKIN_TIMESTAMP).total_seconds()
                if elapsed_sec >= 2.0 * 3600:
                    should_trigger = True

            if should_trigger and ALLOWED_USER_ID != 0:
                LAST_CHECKIN_TIMESTAMP = now
                msg = (
                    f"🔔 **Accountability Check-in ({now.strftime('%H:%M')})**\n\n"
                    "Quick checkpoint (every 2 hours):\n"
                    "1. What did you finish over the last 2 hours?\n"
                    "2. What are you working on right now?\n"
                    "_Send a quick note or tap to record a voice message!_"
                )
                await app.bot.send_message(chat_id=ALLOWED_USER_ID, text=msg, parse_mode="Markdown")

        except Exception as e:
            logger.error(f"Error in proactive scheduler: {e}")

        await asyncio.sleep(60)

async def post_init(application: Application) -> None:
    global ACTIVE_APPLICATION
    ACTIVE_APPLICATION = application
    asyncio.create_task(proactive_scheduler_loop(application))

# ============================================================
# Telegram Command Handlers
# ============================================================

def is_authorized(update: Update) -> bool:
    if ALLOWED_USER_ID == 0:
        return True
    return update.effective_user.id == ALLOWED_USER_ID

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_authorized(update):
        await update.message.reply_text(f"Access restricted. Your Telegram ID: `{update.effective_user.id}`.")
        return
    welcome_text = (
        "🤖 **Antigravity AI Agent Companion is Online!**\n\n"
        "I am connected directly to your local computer and Second Brain vault.\n\n"
        "**Available Commands:**\n"
        "• `/sprint [minutes] [task]` — Launch 15-minute anti-procrastination sprint\n"
        "• `/recap` — Generate evening summary of completed work\n"
        "• `/focus` — Show current priorities and pending tasks\n"
        "• `/exec <command>` — Run terminal command on your PC\n"
        "• `/file <path>` — Send file from your PC to Telegram\n\n"
        "You can chat naturally or send **voice messages** — I transcribe and log everything automatically!"
    )
    await update.message.reply_text(welcome_text, parse_mode="Markdown")

async def cmd_sprint(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_authorized(update): return
    args = context.args or []
    mins = 15
    task = "Focus Sprint"
    if args:
        if args[0].isdigit():
            mins = int(args[0])
            task = " ".join(args[1:]) if len(args) > 1 else "Focus Sprint"
        else:
            task = " ".join(args)
    res = start_micro_sprint(task, mins)
    await update.message.reply_text(res, parse_mode="Markdown")

async def cmd_recap(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_authorized(update): return
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    today_str = datetime.now().strftime("%Y-%m-%d")
    daily_file = VAULT_ROOT / "_daily" / f"{today_str}.md"
    daily_content = daily_file.read_text(encoding="utf-8") if daily_file.exists() else "No log file found for today."
    
    prompt = f"""
Summarize today's activities ({today_str}) based on this daily log:
{daily_content}

Format:
📊 **DAILY RECAP ({today_str})**
✅ **Closed Today:**
⚡ **Key Breakthroughs:**
📌 **Carry Forward:**
🔥 **Coach Note:**
"""
    try:
        resp = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
        text = resp.text.strip()
    except Exception as e:
        text = f"Could not generate recap: {e}"
    await update.message.reply_text(text, parse_mode="Markdown")

async def cmd_focus(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_authorized(update): return
    todo_file = VAULT_ROOT / "_pool" / "todo.md"
    lines = []
    if todo_file.exists():
        for line in todo_file.read_text(encoding="utf-8").splitlines():
            if line.strip().startswith("- [ ]"):
                lines.append(line.strip())
                if len(lines) >= 5: break
    msg = "🎯 **ACTIVE FOCUS**\n\n" + ("\n".join(lines) if lines else "No pending tasks in todo.md!")
    await update.message.reply_text(msg, parse_mode="Markdown")

async def cmd_exec(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_authorized(update): return
    if not context.args:
        await update.message.reply_text("Usage: `/exec <terminal command>`", parse_mode="Markdown")
        return
    cmd = " ".join(context.args)
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    res = run_shell_command(cmd)
    if len(res) > 4000:
        res = res[:3900] + "\n\n...[Truncated]"
    await update.message.reply_text(f"```\n{res}\n```", parse_mode="Markdown")

async def cmd_sendfile(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_authorized(update): return
    if not context.args:
        await update.message.reply_text("Usage: `/file <path>`")
        return
    p = Path(" ".join(context.args))
    if not p.is_absolute():
        p = VAULT_ROOT / p
    if not p.exists():
        await update.message.reply_text(f"File not found: `{p}`")
        return
    await update.message.reply_document(document=p.open("rb"), filename=p.name)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_authorized(update): return
    text = update.message.text
    if not text: return
    global LAST_CHECKIN_TIMESTAMP
    LAST_CHECKIN_TIMESTAMP = datetime.now()
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    reply = await process_with_ai(update.effective_user.id, text)
    if len(reply) > 4000:
        for chunk in [reply[i:i+4000] for i in range(0, len(reply), 4000)]:
            await update.message.reply_text(chunk)
    else:
        await update.message.reply_text(reply)

async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_authorized(update): return
    voice = update.message.voice
    if not voice: return
    global LAST_CHECKIN_TIMESTAMP
    LAST_CHECKIN_TIMESTAMP = datetime.now()
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    try:
        vf = await context.bot.get_file(voice.file_id)
        audio_bytes = await vf.download_as_bytearray()
        audio_part = types.Part.from_bytes(data=bytes(audio_bytes), mime_type="audio/ogg")
        trans = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[audio_part, "Transcribe this voice message accurately into the spoken language. Return ONLY the transcribed text."]
        ).text.strip()

        reply = await process_with_ai(update.effective_user.id, trans)
        full_msg = f"🎤 *«{trans}»*\n\n{reply}"
        if len(full_msg) > 4000:
            for chunk in [full_msg[i:i+4000] for i in range(0, len(full_msg), 4000)]:
                await update.message.reply_text(chunk)
        else:
            await update.message.reply_text(full_msg, parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Error handling voice: {e}")
        await update.message.reply_text(f"⚠️ Error processing voice: {e}")

def main():
    if not BOT_TOKEN:
        print("[!] Please configure TELEGRAM_BOT_TOKEN in _system/.env")
        sys.exit(1)

    print("==================================================")
    print(">>> Antigravity Second Brain AI Agent Bot Online")
    print(f"[*] Vault Path: {VAULT_ROOT}")
    print("==================================================")

    app = Application.builder().token(BOT_TOKEN).post_init(post_init).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("sprint", cmd_sprint))
    app.add_handler(CommandHandler("recap", cmd_recap))
    app.add_handler(CommandHandler("focus", cmd_focus))
    app.add_handler(CommandHandler("exec", cmd_exec))
    app.add_handler(CommandHandler("file", cmd_sendfile))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.VOICE, handle_voice))

    app.run_polling()

if __name__ == "__main__":
    main()
