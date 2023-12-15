import logging
import os
from aiogram import types
from aiogram.dispatcher import Dispatcher
from aiogram.types import ContentType
from aiogram import Bot, Dispatcher, executor, types

from prompts import *
from yandex_api import *


API_TOKEN = ""
token = ''
folderid = ''

yandex_api = YandexAPI(token, folderid)

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize bot and dispatcher
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)


language = 'ru'


@dp.message_handler(commands=['start', 'help', 'reset', 'language'])
async def send_welcome(message: types.Message):
    args = message.get_args()
    cmd = message.get_command()
    if cmd == '/reset':
        if args == 'default':
            user_messages[message.from_user.id] = [
                {"role": "system", "content": jail_break_prompt},
            ]
        elif args == 'alice':
            user_messages[message.from_user.id] = [
                {"role": "system", "content": alice_prompt},
            ]
        else:
            user_messages[message.from_user.id] = [
                {"role": "system", "content": args},
            ]
        await message.reply("reseted")

    elif cmd == '/language':
        global language
        language = args
        await message.reply("changed lang")
    else:
        await message.reply("Hi!")


user_messages = {}

i = 0


@dp.message_handler(content_types=[ContentType.VOICE])
async def handle_voice_message(message: types.Message):
    if message.from_user.id not in user_messages:
        user_messages[message.from_user.id] = [
            {"role": "system", "content": alice_prompt},
        ]

    file_id = message.voice.file_id
    voice_file = await bot.get_file(file_id)

    ogg_path = f"in_voice_{file_id}.ogg"
    await voice_file.download(ogg_path)

    with open(ogg_path, "rb") as audio_file:
        transcription = await yandex_api.transcribe(audio_file.read())
    transcription_en = await yandex_api.translate(transcription, 'en')
    user_messages[message.from_user.id].append(
        {"role": "user", "content": transcription_en})

    openai_ans = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=user_messages[message.from_user.id]
    )
    answer_text_en = openai_ans["choices"][0]["message"]["content"]
    loc = answer_text_en.find('Ω')
    answer_text_en = answer_text_en[loc+1:]

    if language == 'ru':
        answer_text_ru = await yandex_api.translate(answer_text_en, 'ru')
    else:
        answer_text_ru = answer_text_en

    user_messages[message.from_user.id].append(
        {"role": "assistant", "content": answer_text_en})

    voice = await yandex_api.synthesize(answer_text_ru)

    await message.answer_voice(voice)

    print(transcription, transcription_en, ":", answer_text_en, answer_text_ru)
    os.remove(ogg_path)


@dp.message_handler(content_types=[ContentType.TEXT])
async def echo(message: types.Message):
    if message.from_user.id not in user_messages:
        user_messages[message.from_user.id] = [
            {"role": "system", "content": jail_break_prompt},
        ]

    transcription = message.text
    transcription_en = await yandex_api.translate(transcription, 'en')
    user_messages[message.from_user.id].append(
        {"role": "user", "content": transcription_en})

    openai_ans = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=user_messages[message.from_user.id]
    )
    answer_text_en = openai_ans["choices"][0]["message"]["content"]
    loc = answer_text_en.find('Ω')
    answer_text_en = answer_text_en[loc+1:]

    if language == 'ru':
        answer_text_ru = await yandex_api.translate(answer_text_en, 'ru')
    else:
        answer_text_ru = answer_text_en
    user_messages[message.from_user.id].append(
        {"role": "assistant", "content": answer_text_en})

    await message.answer(answer_text_ru)

    print(transcription, transcription_en, ":", answer_text_en, answer_text_ru)


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
