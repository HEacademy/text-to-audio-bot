import io
import json
import logging
import os
import re
from pathlib import Path
from typing import Optional

import httpx
from dotenv import load_dotenv
from telegram import Update
from telegram.constants import ChatAction, ChatType
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

load_dotenv()

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
)
# Hide httpx request URLs, which include the Telegram bot token.
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger("text_to_audio_bot")

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "").strip()
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "").strip()
ELEVENLABS_MODEL_ID = os.getenv("ELEVENLABS_MODEL_ID", "eleven_v3").strip()
LANGUAGE_CODE = os.getenv("LANGUAGE_CODE", "hy").strip()
ALLOWED_USER_IDS = {
    item.strip()
    for item in os.getenv("ALLOWED_TELEGRAM_USER_IDS", "").split(",")
    if item.strip()
}
MAX_TEXT_LENGTH = int(os.getenv("MAX_TEXT_LENGTH", "4500"))
RECIPIENTS_FILE = Path(__file__).with_name("recipients.json")
SELECTED_TARGET_FILE = Path(__file__).with_name("selected_target.txt")


def user_is_allowed(update: Update) -> bool:
    user = update.effective_user
    return bool(user and str(user.id) in ALLOWED_USER_IDS)


def load_recipients() -> dict[str, int]:
    try:
        data = json.loads(RECIPIENTS_FILE.read_text(encoding="utf-8"))
        return {str(name).lower(): int(chat_id) for name, chat_id in data.items()}
    except (OSError, json.JSONDecodeError, TypeError, ValueError):
        return {}


def save_recipients(recipients: dict[str, int]) -> None:
    temporary = RECIPIENTS_FILE.with_suffix(".tmp")
    temporary.write_text(
        json.dumps(recipients, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    temporary.replace(RECIPIENTS_FILE)


def load_selected_target() -> Optional[str]:
    try:
        value = SELECTED_TARGET_FILE.read_text(encoding="utf-8").strip().lower()
        return value or None
    except OSError:
        return None


def save_selected_target(username: Optional[str]) -> None:
    if username:
        SELECTED_TARGET_FILE.write_text(username.lower(), encoding="utf-8")
    else:
        try:
            SELECTED_TARGET_FILE.unlink()
        except FileNotFoundError:
            pass


def register_recipient(update: Update) -> Optional[str]:
    chat = update.effective_chat
    user = update.effective_user
    if not chat or not user or chat.type != ChatType.PRIVATE:
        return None
    if not user.username:
        return None

    username = user.username.lower()
    recipients = load_recipients()
    recipients[username] = int(chat.id)
    save_recipients(recipients)
    return username


async def send_text(update: Update, text: str) -> None:
    if update.effective_message:
        await update.effective_message.reply_text(text)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if user_is_allowed(update):
        await send_text(
            update,
            "Բարև։ Ուղարկիր տեքստ՝ ձայն ստեղծելու համար։\n\n"
            "Ստացող ընտրելու համար գրիր՝ /to @username\n"
            "Ինքդ ստանալու համար՝ /to off\n"
            "Օգնություն՝ /help",
        )
        return

    username = register_recipient(update)
    if username:
        await send_text(
            update,
            f"Գրանցվեցիր որպես @{username}։ Բոտի տերը կարող է ընտրել քեզ՝ "
            f"գրելով /to @{username}։ Դու կարող ես բոտը օգտագործել միայն որպես ստացող։",
        )
    else:
        await send_text(
            update,
            "Ստացող գրանցվելու համար բացիր բոտի անձնական չաթը և սեղմիր Start։ "
            "Քո Telegram-ի Settings-ում պետք է նաև ունենաս username։",
        )


async def id_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if user:
        await send_text(update, f"Քո Telegram ID-ն է՝ {user.id}")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not user_is_allowed(update):
        await send_text(update, "Բոտի ձայն ստեղծելու գործառույթից կարող է օգտվել միայն տերը։")
        return

    await send_text(
        update,
        "Ուղարկիր տեքստային հաղորդագրություն՝ MP3 ստանալու կամ ընտրված մարդուն ուղարկելու համար։\n\n"
        "/to @username — ընտրել ստացողին\n"
        "/to off — աուդիոն ուղարկել քեզ\n"
        "/to — տեսնել ընտրված ստացողին\n"
        "/id — ցույց տալ քո Telegram ID-ն\n\n"
        "Ստացողը պետք է նախ բացի բոտը և սեղմի Start։",
    )


async def to_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not user_is_allowed(update):
        await send_text(update, "Այս հրամանից կարող է օգտվել միայն բոտի տերը։")
        return

    if not context.args:
        current = load_selected_target()
        if current:
            await send_text(update, f"Ընտրված ստացողը՝ @{current}։ Փոխելու համար գրիր /to @username։")
        else:
            await send_text(update, "Ստացող դեռ ընտրված չէ․ աուդիոն կուղարկվի քեզ։ Գրիր /to @username՝ ընտրելու համար։")
        return

    requested = context.args[0].strip()
    if requested.lower() in {"off", "me", "self"}:
        save_selected_target(None)
        await send_text(update, "Պատրաստ է․ հաջորդ աուդիոն կուղարկվի քեզ։")
        return

    username = requested.lstrip("@").lower()
    if not re.fullmatch(r"[a-z0-9_]{5,32}", username):
        await send_text(update, "Գրիր ստացողի Telegram username-ը, օրինակ՝ /to @harut123։")
        return

    recipients = load_recipients()
    if username not in recipients:
        await send_text(
            update,
            f"@{username}-ը դեռ գրանցված չէ։ Թող նա բացի քո բոտը, սեղմի Start և նորից փորձիր։",
        )
        return

    save_selected_target(username)
    await send_text(
        update,
        f"Ընտրված է @{username}։ Հաջորդ ուղարկած տեքստերիդ աուդիոն կուղարկվի նրան։\n"
        "Քեզ ուղարկելու համար գրիր /to off։",
    )


async def create_audio(text: str) -> bytes:
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVENLABS_VOICE_ID}"
    params = {"output_format": "mp3_44100_128"}
    headers = {
        "xi-api-key": ELEVENLABS_API_KEY,
        "Content-Type": "application/json",
        "Accept": "audio/mpeg",
    }
    payload = {
        "text": text,
        "model_id": ELEVENLABS_MODEL_ID,
        "language_code": LANGUAGE_CODE,
    }

    timeout = httpx.Timeout(120.0, connect=20.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.post(url, params=params, headers=headers, json=payload)
        if response.is_error:
            # Log the provider response so the real cause is visible in the console.
            # Do not log request headers, which contain API credentials.
            logger.error(
                "ElevenLabs returned HTTP %s: %s",
                response.status_code,
                response.text[:500],
            )
            raise RuntimeError(f"ElevenLabs returned HTTP {response.status_code}")
        return response.content


async def text_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.effective_message
    if not message or not message.text:
        return

    if not user_is_allowed(update):
        await send_text(update, "Բոտի ձայն ստեղծելու գործառույթից կարող է օգտվել միայն տերը։")
        return

    text = message.text.strip()
    if not text:
        return
    if len(text) > MAX_TEXT_LENGTH:
        await send_text(update, f"Տեքստը շատ երկար է։ Ուղարկիր առավելագույնը {MAX_TEXT_LENGTH} նիշ։")
        return

    target_username = load_selected_target()
    if target_username:
        recipients = load_recipients()
        recipient_chat_id = recipients.get(target_username)
        if not recipient_chat_id:
            save_selected_target(None)
            await send_text(update, f"@{target_username}-ի գրանցումը չի գտնվել։ Թող նա նորից սեղմի Start։")
            return
    else:
        recipient_chat_id = message.chat_id

    await context.bot.send_chat_action(
        chat_id=message.chat_id,
        action=ChatAction.UPLOAD_VOICE,
    )
    status = await message.reply_text("Ստեղծում եմ աուդիոն…")

    try:
        audio_bytes = await create_audio(text)
        audio_file = io.BytesIO(audio_bytes)
        audio_file.name = "generated-speech.mp3"
        await context.bot.send_audio(
            chat_id=recipient_chat_id,
            audio=audio_file,
            filename="generated-speech.mp3",
            title="Generated speech",
            caption="Աուդիոն ստեղծվել է ուղարկված տեքստից։",
        )
        if target_username:
            await status.edit_text(f"✅ Աուդիոն ուղարկվեց @{target_username} օգտատիրոջը։")
        else:
            await status.delete()
    except httpx.TimeoutException:
        logger.exception("ElevenLabs request timed out")
        await status.edit_text("Ձայնի ստեղծումը երկար տևեց։ Փորձիր նորից՝ ավելի կարճ տեքստով։")
    except Exception:
        logger.exception("Audio generation or Telegram upload failed")
        await status.edit_text(
            "Չհաջողվեց ստեղծել կամ ուղարկել աուդիոն։ Ստուգիր API բանալիները, "
            "Voice ID-ն, ստացողի բոտի Start-ը և ElevenLabs-ի քվոտան։"
        )


def validate_settings() -> Optional[str]:
    missing = []
    if not BOT_TOKEN:
        missing.append("TELEGRAM_BOT_TOKEN")
    if not ELEVENLABS_API_KEY:
        missing.append("ELEVENLABS_API_KEY")
    if not ELEVENLABS_VOICE_ID:
        missing.append("ELEVENLABS_VOICE_ID")
    if not ALLOWED_USER_IDS:
        missing.append("ALLOWED_TELEGRAM_USER_IDS (քո Telegram ID-ն)")
    if missing:
        return "Բացակայում են .env կարգավորումները՝ " + ", ".join(missing)
    return None


def main() -> None:
    error = validate_settings()
    if error:
        raise SystemExit(error + "\nՊատճենիր .env.example-ը որպես .env և լրացրու դաշտերը։")

    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("id", id_command))
    application.add_handler(CommandHandler("to", to_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_message))

    logger.info("Bot is running with polling")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
