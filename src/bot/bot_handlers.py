import telebot
from telebot.types import Message, BotCommand
import os
from dotenv import load_dotenv, dotenv_values
from src.parser.zelart_parser import PrestaShopScraper
from src.database.mongodb import Database
from apscheduler.schedulers.background import BackgroundScheduler

class ExceptionHandler(telebot.ExceptionHandler):
    def handle(self, exception):
        print("Exception occured: ", exception)

class Bot(telebot.TeleBot):
    def __init__(self):
        # load_dotenv()
        # config = dotenv_values(".env")
    
        # BOT_TOKEN = config["BOT_TOKEN"]
        BOT_TOKEN = os.environ["BOT_TOKEN"]
        super().__init__(BOT_TOKEN)

        self.db = Database()
        # self.chat_id_for_reminder = os.getenv("REMINDER_CHAT_ID")

        self.scheduler = BackgroundScheduler()
        self.scheduler.add_job(self.send_daily_reminder, 'cron', hour=19, minute=0)
        self.scheduler.start()

        self.setup_command_menu()
        self.setup_command_handlers()

    def setup_command_menu(self):
        commands = [
            BotCommand(command="start", description="Почати роботу"),
            BotCommand(command="parse", description="Запустити парсинг"),
            BotCommand(command="help", description="Допомога"),
        ]
        self.set_my_commands(commands)

    def setup_command_handlers(self):
        @self.message_handler(commands=['start'])
        def send_welcome(message: Message):
            user = {
                "chat_id": message.from_user.id,
                "username": message.from_user.username,
            }
            self.db.insert_user(user)

            # self.send_daily_reminder()
            self.send_message(message.from_user.id, "Привіт! Я бот для парсингу zelart.com.ua")

        @self.message_handler(commands=['parse'])
        def send_welcome(message: Message):
            self.send_message(message.from_user.id, "Введіть посилання на товар, який потрібно парсити")
            self.register_next_step_handler(message, self.process_parse_link)

        @self.message_handler(commands=['help'])
        def send_help(message: Message):
            self.send_message(message.from_user.id, "Усі команди бота:\n/start - Старт\n/parse - Парсинг посилання\n/help - Список команд")

    def process_parse_link(self, message: Message):
        link = message.text
        parser = PrestaShopScraper()
        product = parser.scrape_product(link)

        self.db.insert_product(product)

        if product["isHidden"] == True:
            stock = "Немає в наявності"
        elif product["isHidden"] == False:
            stock = "Є в наявності"


        if product["priceCur"] == product["priceWithDiscount"]:
           self.send_message(
            message.from_user.id,
            f"""Парсинг посилання: {link}

Назва: {product["title"]}
Ціна: {product["priceCur"]} грн
Ціна оптом: {product["priceBigOpt"]} грн
Цількість товарів для опту: {product["bigOptQuantity"]} шт
Рекомендована роздрібна ціна: {product["priceSrp"]} грн
Наявність?: {stock}
"""
            )
        elif product["priceCur"] != product["priceWithDiscount"]:
            self.send_message(
            message.from_user.id,
            f"""Парсинг посилання: {link}

Назва: {product["title"]}
Ціна: {product["priceCur"]} грн
Ціна зі знижкою: {product["priceWithDiscount"]} грн
Ціна оптом: {product["priceBigOpt"]} грн
Цількість товарів для опту: {product["bigOptQuantity"]} шт
Рекомендована роздрібна ціна: {product["priceSrp"]} грн
Наявність?: {stock}
"""
            )

    def send_daily_reminder(self):
        users = self.db.find_every_user()
        for user in users:
            self.chat_id_for_reminder = user["chat_id"]
            if self.chat_id_for_reminder:
                try:
                    products = self.db.find_every_product()  
                    parser = PrestaShopScraper()
                    for product_database in products:
                        link = product_database["url"]
                        product_parser = parser.scrape_product(link)
                        reply_string = f"Характеристики товару {product_parser['title']} змінились:\n\n"
                        product_change_status = False
                        for i in product_parser:
                            if product_parser[i] != product_database[i]:
                                product_change_status = True
                        
                                print(f"product {i} has changed")

                                if i == "priceCur":
                                    key = "Ціна"
                                    key_value_database = f"{product_database[i]} грн"
                                    key_value_parser = f"{product_parser[i]} грн"
                                elif i == "priceWithDiscount":
                                    key = "Ціна зі знижкою"
                                    key_value_database = f"{product_database[i]} грн"
                                    key_value_parser = f"{product_parser[i]} грн"
                                elif i == "priceBigOpt":
                                    key = "Ціна оптом"
                                    key_value_database = f"{product_database[i]} грн"
                                    key_value_parser = f"{product_parser[i]} грн"
                                elif i == "bigOptQuantity":
                                    key = "Цількість товарів для опту"
                                    key_value_database = f"{product_database[i]} шт"
                                    key_value_parser = f"{product_parser[i]} шт"
                                elif i == "priceSrp":
                                    key = "Рекомендована роздрібна ціна"
                                    key_value_database = f"{product_database[i]} грн"
                                    key_value_parser = f"{product_parser[i]} грн"
                                elif i == "isHidden":
                                    key = "Наявність"
                                    key_value_parser = "Є в наявності" if product_parser[i] == False else "Немає в наявності"
                                    key_value_database = "Є в наявності" if product_database[i] == False else "Немає в наявності"

                                
                                # if i == "isHidden":
                                reply_string += f"{key} товару змінилась.\nРаніше: {key_value_database}\nЗараз: {key_value_parser}\n\n"
                                    # self.send_message(self.chat_id_for_reminder, f"{key} товару {product_parser['title']} змінилась.\n{key} раніше: {key_value_database}\n{key} зараз: {key_value_parser}")
                                # else:
                                    # reply_string += f"{key} товару змінилась.\nРаніше: {product_database[i]}\nЗараз: {product_parser[i]}\n\n"
                                    # self.send_message(self.chat_id_for_reminder, f"{key} товару {product_parser["title"]} змінилась.\n{key} раніше: {product_database[i]}\n{key} зараз: {product_parser[i]}")
                                self.db.update("url", link, i, product_parser[i])
                            else:
                                print(f"product {i} has not changed")
                        if product_change_status == True:
                            self.send_message(self.chat_id_for_reminder, reply_string)
                except Exception as e:
                    print("Exception1:", e)
            else:
                print("No chat id found for reminder")