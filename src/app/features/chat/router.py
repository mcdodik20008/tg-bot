from aiogram import Router, F
from aiogram.types import Message
from ...services.local_llm import generate_reply

router = Router(name="feature.chat")


# Ловим все текстовые сообщения, которые не команды
@router.message(F.text & ~F.text.startswith("/"))
async def llm_chat(message: Message):
    user_text = message.text.strip()
    await message.chat.do("typing")
    reply = await generate_reply(
        user_text,
        system="Ты - вайбовый собеседователь. Шутишь так, что пятки сверкают. Отвечай кратко и на русском языке."
    )
    if len(reply) > 4000:
        reply = reply[:3990] + "…"
    await message.answer(reply)
