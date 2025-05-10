import telebot
from telebot.types import Message, BotCommand
import os
from dotenv import load_dotenv
from src.parser.zelart_parser import PrestaShopScraper
from src.database.mongodb import Database
from apscheduler.schedulers.background import BackgroundScheduler

class ExceptionHandler(telebot.ExceptionHandler):
    def handle(self, exception):
        print("Exception occured: ", exception)

class Bot(telebot.TeleBot):
    def __init__(self):
        load_dotenv()
        BOT_TOKEN = os.getenv("BOT_TOKEN")
        super().__init__(BOT_TOKEN)

        self.db = Database()
        self.chat_id_for_reminder = os.getenv("REMINDER_CHAT_ID")

        self.scheduler = BackgroundScheduler()
        self.scheduler.add_job(self.send_daily_reminder, 'cron', hour=19, minute=0)
        self.scheduler.start()

        self.setup_command_menu()
        self.setup_command_handlers()

    def setup_command_menu(self):
        commands = [
            BotCommand(command="start", description="Начать работу"),
            BotCommand(command="parse", description="Запустить парсер"),
            BotCommand(command="help", description="Помощь"),
        ]
        self.set_my_commands(commands)

    def setup_command_handlers(self):
        @self.message_handler(commands=['start'])
        def send_welcome(message: Message):
            # self.chat_id_for_reminder = message.chat.id
            # self.send_daily_reminder()
            self.send_message(message.from_user.id, "Welcome! How can I assist you today?")

        @self.message_handler(commands=['parse'])
        def send_welcome(message: Message):
            self.send_message(message.from_user.id, "What would you like to parse? (input a link)")
            self.register_next_step_handler(message, self.process_parse_link)

        @self.message_handler(commands=['help'])
        def send_help(message: Message):
            self.send_message(message.from_user.id, "Here are the commands you can use:\n/start - Start the bot\n/parse - Parse a link\n/help - Get help")

    def process_parse_link(self, message: Message):
        link = message.text
        parser = PrestaShopScraper()
        product = parser.scrape_product(link)

        self.db.insert_product(product)

        self.send_message(
            message.from_user.id,
            f"""Parsing the link: {link}
Title: {product["title"]}
Price: {product["priceCur"]}
Price with discount: {product["priceWithDiscount"]}
Wholesale price: {product["priceBigOpt"]}
Wholesale quantity: {product["bigOptQuantity"]}
Recommended retail price: {product["priceSrp"]}
In stock?: {product["isHidden"]}
URL: {product["url"]}
"""
        )

    def send_daily_reminder(self):
        if self.chat_id_for_reminder:
            try:
                products = self.db.find_every_product()  
                parser = PrestaShopScraper()
                for product_database in products:
                    link = product_database["url"]
                    product_parser = parser.scrape_product(link)
                    for i in product_parser:
                        if product_parser[i] != product_database[i]:
                        # if True:
                            print(f"product {i} has changed")
                            self.send_message(self.chat_id_for_reminder, f"{product_parser["title"]} {i} has changed.\nOld {i}: {product_database[i]}\nNew {i}: {product_parser[i]}")
                            print("1")
                            self.db.update("url", link, i, product_parser[i])
                            print("2")
                        else:
                            print(f"product {i} has not changed")

            except Exception as e:
                print("Exception1:", e)
        else:
            print("No chat id found for reminder")