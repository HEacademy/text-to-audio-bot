import io
import logging
import os
from typing import Optional

import httpx
from dotenv import load_dotenv
from telegram import Update
from telegram.constants import ChatAction
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


async def send_text(update: Update, text: str) -> None:
    if update.effective_message:
        await update.effective_message.reply_text(text)


def user_is_allowed(update: Update) -> bool:
    user = update.effective_user
    return bool(user and str(user.id) in ALLOWED_USER_IDS)


async def id_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if user:
        await send_text(
            update,
            f"Քո Telegram ID-ն է՝ {user.id}\n"
            "Այդ թիվը գրիր .env ֆայլի ALLOWED_TELEGRAM_USER_IDS դաշտում, "
            "հետո վերագործարկիր բոտը։",
        )


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not user_is_allowed(update):
        await send_text(
            update,
            "Այս բոտից օգտվելու թույլտվություն չկա։ Ուղարկիր /id հրամանը "
            "և ավելացրու քո ID-ն .env ֆայլում։",
        )
        return

    await send_text(
        update,
        "Բարև։ Ուղարկիր տեքստ, և ես այն կվերածեմ հայերեն աուդիոյի։\n"
        "Լրացուցիչ հրամաններ՝ /help և /id։",
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await send_text(
        update,
        "Ուղարկիր սովորական տեքստային հաղորդագրություն՝ MP3 ձայն ստանալու համար։\n"
        f"Առավելագույն երկարությունը՝ {MAX_TEXT_LENGTH} նիշ։\n"
        "Այս բոտը աուդիո է ուղարկում Telegram-ով, հեռախոսազանգ չի կատարում։",
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
            logger.warning("ElevenLabs returned HTTP %s", response.status_code)
            raise RuntimeError("ElevenLabs request failed")
        return response.content


async def text_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.effective_message
    if not message or not message.text:
        return

    if not user_is_allowed(update):
        await send_text(
            update,
            "Դու դեռ թույլատրված չես։ Ուղարկիր /id հրամանը, հետո քո ID-ն ավելացրու .env ֆայլում։",
        )
        return

    text = message.text.strip()
    if not text:
        return
    if len(text) > MAX_TEXT_LENGTH:
        await send_text(
            update,
            f"Տեքստը շատ երկար է։ Ուղարկիր առավելագույնը {MAX_TEXT_LENGTH} նիշ։",
        )
        return

    await context.bot.send_chat_action(chat_id=message.chat_id, action=ChatAction.UPLOAD_AUDIO)
    status = await message.reply_text("Ստեղծում եմ աուդիոն…")

    try:
        audio_bytes = await create_audio(text)
        audio_file = io.BytesIO(audio_bytes)
        audio_file.name = "generated-speech.mp3"
        await context.bot.send_audio(
            chat_id=message.chat_id,
            audio=audio_file,
            filename="generated-speech.mp3",
            title="Generated speech",
            caption="Աուդիոն ստեղծվել է քո ուղարկած տեքստից։",
        )
        await status.delete()
    except httpx.TimeoutException:
        logger.exception("ElevenLabs request timed out")
        await status.edit_text("Ձայնի ստեղծումը երկար տևեց։ Փորձիր նորից՝ ավելի կարճ տեքստով։")
    except Exception:
        logger.exception("Audio generation or Telegram upload failed")
        await status.edit_text(
            "Չհաջողվեց ստեղծել կամ ուղարկել աուդիոն։ Ստուգիր API բանալիները, "
            "Voice ID-ն և ElevenLabs-ի մնացորդը։"
        )


def validate_settings() -> Optional[str]:
    missing = []
    if not BOT_TOKEN:
        missing.append("TELEGRAM_BOT_TOKEN")
    if not ELEVENLABS_API_KEY:
        missing.append("ELEVENLABS_API_KEY")
    if not ELEVENLABS_VOICE_ID:
        missing.append("ELEVENLABS_VOICE_ID")
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
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, text_message)
    )

    logger.info("Bot is running with polling")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
