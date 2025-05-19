from src.bot.bot_handlers import Bot
from fastapi import FastAPI
from contextlib import asynccontextmanager


def start_bot():
    bot = Bot()
    #! нужно использовать infinity_polling!
    print(f"🟢 Bot launched!")
    bot.polling()