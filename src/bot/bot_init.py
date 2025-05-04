from src.bot.bot_handlers import Bot
from fastapi import FastAPI
from contextlib import asynccontextmanager


def start_bot():
    print("Bot is running...")
    bot = Bot()
    bot.polling()