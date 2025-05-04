import telebot
from telebot.types import Message, BotCommand
import os
from dotenv import load_dotenv

class ExceptionHandler(telebot.ExceptionHandler):
    def handle(self, exception):
        print("Exception occured: ", exception)

class Bot(telebot.TeleBot):
    def __init__(self):
        load_dotenv()
        BOT_TOKEN = os.getenv("BOT_TOKEN")
        super().__init__(BOT_TOKEN)

        self.setup_command_menu()
        self.setup_handlers()

    def setup_command_menu(self):
        commands = [
            BotCommand(command="start", description="Начать работу"),
            BotCommand(command="parse", description="Запустить парсер"),
            BotCommand(command="help", description="Помощь"),
        ]
        self.set_my_commands(commands)

    def setup_handlers(self):
        @self.message_handler(commands=['start'])
        def send_welcome(message: Message):
            self.send_message(message.from_user.id, "Welcome! How can I assist you today?")

        @self.message_handler(commands=['parse'])
        def send_welcome(message: Message):
            self.send_message(message.from_user.id, "What would you like to parse?")
        
        @self.message_handler(commands=['help'])
        def send_help(message: Message):
            self.send_message(message.from_user.id, "Here are the commands you can use:\n/start - Start the bot\n/parse - Parse a link\n/Help - Get help")

