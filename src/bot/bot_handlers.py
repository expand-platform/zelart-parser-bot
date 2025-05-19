import telebot
from telebot.types import Message, BotCommand
import os
from dotenv import load_dotenv, dotenv_values
from src.parser.zelart_parser import PrestaShopScraper
from src.database.mongodb import Database
from apscheduler.schedulers.background import BackgroundScheduler
from dataclasses import dataclass

#! Это лучше вынести отдельно в ExceptionsHandler.py
class ExceptionHandler(telebot.ExceptionHandler):
    def handle(self, exception):
        print("Exception occured: ", exception)

#! Константы тоже лучше хранить отдельно
ZELART_WEBSITE = "zelart.com.ua"

#? датаклассы - это имба
@dataclass
class BotCommands:
    start: str = "start"
    add_product: str = "add"
    remove_product: str = "remove"
    set_time: str = "time"
    info: str = "info"
    help: str = "help"

bot_commands = BotCommands()


class Bot(telebot.TeleBot):
    def __init__(self):
        BOT_TOKEN = os.environ["BOT_TOKEN"]
        super().__init__(BOT_TOKEN)

        self.db = Database()
        hours, minutes = self.db.get_parse_time()

        self.scheduler = BackgroundScheduler()
        self.schedule_parse_time(hours, minutes)

        self.setup_command_menu()
        self.setup_command_handlers()


    def setup_command_menu(self):
        commands = [
            BotCommand(command=bot_commands.add_product, description="Додати товар"),
            BotCommand(command=bot_commands.remove_product, description="Видалити товар"),
            BotCommand(command=bot_commands.info, description="Звiт"),
            BotCommand(command=bot_commands.set_time, description="Задати час парсингу"),
            BotCommand(command=bot_commands.help, description="Всi команди бота"),
        ]
        self.set_my_commands(commands)


    def setup_command_handlers(self):
        @self.message_handler(commands=[bot_commands.start])
        def send_welcome(message: Message):
            user = {
                "chat_id": message.from_user.id,
                "username": message.from_user.username,
            }
            self.db.insert_user(user)

            self.send_message(message.from_user.id, f"Привіт! Я бот для парсингу {ZELART_WEBSITE}")
            self.get_info(message)

        @self.message_handler(commands=[bot_commands.add_product])
        def send_welcome(message: Message):
            self.send_message(message.from_user.id, f"Введи посилання на товар iз сайту {ZELART_WEBSITE}")
            self.register_next_step_handler(message, self.process_parse_link)
        
        #? /time
        @self.message_handler(commands=[bot_commands.set_time])
        def set_time(message: Message):
            parse_time = self.get_parse_time()
            
            self.send_message(message.from_user.id, f"О котрiй менi краще перевiряти товари?\n\nЗараз це {parse_time}")
            self.register_next_step_handler(message, self.set_time)
       
        #? /remove
        @self.message_handler(commands=[bot_commands.remove_product])
        def remove_product(message: Message):
            self.send_message(message.from_user.id, f"🔗 Вiдправ посилання на продукт, який хочеш видалити")
            self.register_next_step_handler(message, self.remove_product)
        
        #? /info
        @self.message_handler(commands=[bot_commands.info])
        def remove_product(message: Message):
            self.send_message(message.from_user.id, f"👷‍♂️ Звiтую про роботу")
            self.get_info(message)
        
        #? /help
        @self.message_handler(commands=[bot_commands.help])
        def get_help(message: Message):
            self.send_message(message.from_user.id, f"⭐ Усі команди бота\n\n/{bot_commands.start} - Старт\n/{bot_commands.add_product} - Додати товар\n/{bot_commands.remove_product} - Видалити товар\n/{bot_commands.info} - Звiт про роботу\n/{bot_commands.set_time} - Задати час парсингу")



    def process_parse_link(self, message: Message):
        link = message.text
        parser = PrestaShopScraper()
        product = parser.scrape_product(link)

        self.db.insert_product(product)

        if product["isHidden"] == True:
            stock = "Немає в наявності"
        elif product["isHidden"] == False:
            stock = "Є в наявності"

        #! Дальше идёт тупо дублирование кода, его можно оптимизировать
        if product["priceCur"] == product["priceWithDiscount"]:
           self.send_message(
            message.from_user.id,
            f"""➕ Тепер я слiдкую за товаром:\n{link}

- Назва: {product["title"]}
- Ціна оптом: {product["priceCur"]} грн
- Цількість товарів для опту: {product["bigOptQuantity"]} шт
- Рекомендована роздрібна ціна: {product["priceSrp"]} грн
- Наявність: {stock}
"""
            )
        elif product["priceCur"] != product["priceWithDiscount"]:
            self.send_message(
            message.from_user.id,
            f"""➕ Тепер я слiдкую за товаром:\n{link}

- Назва: {product["title"]}
- Ціна оптом: {product["priceCur"]} грн
- Ціна зі знижкою: {product["priceWithDiscount"]} грн
- Цількість товарів для опту: {product["bigOptQuantity"]} шт
- Рекомендована роздрібна ціна: {product["priceSrp"]} грн
- Наявність: {stock}
"""
            )

    #! Здесь очень плохой код 🤖
    def update_products_daily(self):
        users = self.db.find_every_user()
        for user in users:
            self.chat_id_for_reminder = user["chat_id"]
            if self.chat_id_for_reminder:
                try:
                    #! Цикл в цикле - плохо
                    #! Если ты будешь доставать товары массивом из DB, 
                    #! то сможешь избавиться от одного цикла 
                    products = self.db.get_products()  
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

                                #! Советую создать объект через dataclass для того, чтобы была подсветка и подсказки, а не просто хардкодить ключи
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


    #! В идеале нужно сделать, чтобы time сохранялся ещё и в БД
    def set_time(self, message: Message) -> None:
        """ sets check time from given message """
        time: str = message.text
        hour, minutes = self.convert_time(time)
        #? print("🐍 hour / minutes: ",hour, minutes)
        self.save_time([hour, minutes])

        if hour is None or minutes is None:
            self.send_message(message.chat.id, f"Перевiр формат вводу. Повинно бути два числа з двукрапкою: 19:00, 20:00...\n\nЗапусти команду /{bot_commands.set_time} ще раз та введи час у потрiбному форматi")
        else: 
            self.schedule_parse_time(hour, minutes)
            minutes = self.format_minutes(minutes)

            self.send_message(message.chat.id, f"Добре, заводжу годинник на {hour}:{minutes}!\n\nЧекай апдейти по товарам ⭐")

    def schedule_parse_time(self, hour: int = 19, minutes: int = 0) -> None:
        self.scheduler.remove_all_jobs()
        self.scheduler.add_job(self.update_products_daily, 'cron', hour=hour, minute=minutes)
        #? print(self.scheduler.get_jobs())
        print(f"🟢 Products check will be started at {hour}:{minutes}")


    def save_time(self, time: list[int]):
        """ saves time to DB """
        self.db.update_config(key="parse_time", new_value=time)


    def format_minutes(self, minutes: int) -> str:
        """Formats minutes as a 2-digit string (e.g. 0 → '00', 5 → '05')"""
        return f"{minutes:02}"


    def convert_time(self, time: str = "") -> list[int] | list[None]:
        """ converts string into list of integers """
        if ":" in time:
            return list(map(int, time.split(":")))
        return [None, None] 

    
    def get_parse_time(self) -> str:
        hours, minutes = self.db.get_parse_time()
        minutes = self.format_minutes(minutes)
        return f"{hours}:{minutes}"
    

    def remove_product(self, message: Message):
        link = message.text
        parser = PrestaShopScraper()
        product = parser.scrape_product(link)
        #? print("🐍 product: ",product)

        if product:
            product_id = product["id"]
            self.db.remove_product(product_id)
            self.send_message(message.chat.id, f"Товар з id {product_id} бiльше не вiдслiдковується 👌")

        else:
            print(f"Can't get product info by this link: {link}")
            self.send_message(message.chat.id, f"Я не змiг дiстати iнфу по цьому товару, вибач 😭")

    def get_info(self, message: Message):
        products_count = self.db.get_products_count()
        parse_time = self.get_parse_time()
        
        info_message = f"1. Зараз я слiдкую за {products_count} товарами 🔍\n2. Я надсилаю тобi апдейти у {parse_time} ⌚"

        self.send_message(message.chat.id, info_message)
