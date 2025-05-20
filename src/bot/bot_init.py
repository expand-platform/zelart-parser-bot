from src.bot.bot_handlers import Bot
from dotenv import load_dotenv
import os


def start_bot():
    print(f"✅ Bot launched!") 
    environment = os.environ["ENVIRONMENT"]
    if environment == "PRODUCTION":
        print("🌐  Bot is running in production mode")
        Bot().bot.infinity_polling()
    elif environment == "DEVELOPMENT":
        print("⚙️  Bot is running in development mode")
        Bot().bot.infinity_polling(restart_on_change=True)