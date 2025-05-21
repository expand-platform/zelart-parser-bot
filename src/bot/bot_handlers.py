import telebot
from telebot.types import Message, BotCommand
import os
from src.parser.zelart_parser import PrestaShopScraper
from src.database.mongodb import Database
from apscheduler.schedulers.background import BackgroundScheduler
from dataclasses import dataclass
from src.bot.exception_handler import ExceptionHandler
from src.bot.helpers import Helpers
from src.bot.bot_messages import messages
from src.bot.constant_variables import constant_variables


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


class Bot:
    def __init__(self):
        BOT_TOKEN = os.environ["BOT_TOKEN"]
        self.bot = telebot.TeleBot(BOT_TOKEN, exception_handler=ExceptionHandler())

        self.helpers = Helpers(self.bot)

        self.db = Database()
        hours, minutes = self.db.get_parse_time()

        self.scheduler = BackgroundScheduler()
        self.helpers.schedule_parse_time(self.scheduler, hours, minutes) 
        # self.scheduler.remove_all_jobs()
        # self.scheduler.add_job(self.helpers.update_products_daily, 'cron', hour=14, minute=19)
        

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
        self.bot.set_my_commands(commands)


    def setup_command_handlers(self):
        @self.bot.message_handler(commands=[bot_commands.start])
        def send_welcome(message: Message):
            user = {
                "chat_id": message.from_user.id,
                "username": message.from_user.username,
            }
            self.db.insert_user(user)

            self.helpers.update_products_daily()
            self.bot.send_message(message.from_user.id, messages["start"].format(constant_variables["ZELART_WEBSITE"]))
            self.helpers.get_info(message)

        def add_product_command_chain():
            """ adds product to DB """
            # ? /add

            @self.bot.message_handler(commands=[bot_commands.add_product]) 
            def add_product(message: Message):
                """ first step of adding product """
                self.bot.send_message(message.from_user.id, messages["add_product_first_step"].format(constant_variables["ZELART_WEBSITE"]))
                self.bot.register_next_step_handler(message, process_parse_link)

            def process_parse_link(message: Message):
                """ second step of adding product """
                try:
                    link = message.text
                    parser = PrestaShopScraper()
                    product = parser.scrape_product(link)

                    self.db.insert_product(product)

                    if product["isHidden"] == True:
                        stock = "Немає в наявності"
                    elif product["isHidden"] == False:
                        stock = "Є в наявності"

                    discount_string = ""
                    if product["priceCur"] != product["priceWithDiscount"]:
                        discount_string = messages["optional_discount_string"].format(product["priceWithDiscount"])
                    
                    opt_string = ""
                    if product["priceBigOpt"] != 0:
                        opt_string = messages["optional_big_opt_string"].format(product["priceBigOpt"], product["bigOptQuantity"])

                    self.bot.send_message(message.from_user.id, messages["add_product_second_step"].format(link, product["title"], product["priceCur"], discount_string, opt_string, product["priceSrp"], stock))

                except:
                    self.bot.send_message(message.from_user.id, messages["add_product_second_step_fail"])
        add_product_command_chain()

        def set_time_command_chain():
            """ sets time for checking products """
            #? /time
            
            @self.bot.message_handler(commands=[bot_commands.set_time])
            def set_time(message: Message):
                """ first step of setting time """
                parse_time = self.helpers.get_parse_time()
                
                self.bot.send_message(message.from_user.id, messages["set_time_first_step"].format(parse_time))
                self.bot.register_next_step_handler(message, set_time_second_step)

            def set_time_second_step(message: Message) -> None:
                """ sets check time from given message """
                time: str = message.text
                hour, minutes = self.helpers.convert_time(time)
                #? print("🐍 hour / minutes: ",hour, minutes)
                self.helpers.save_time([hour, minutes])

                if hour is None or minutes is None:
                    self.bot.send_message(message.chat.id, messages["set_time_second_step_fail"])
                else: 
                    self.helpers.schedule_parse_time(self.scheduler, hour, minutes)
                    minutes = self.helpers.format_minutes(minutes)

                    self.bot.send_message(message.chat.id, messages["set_time_second_step_success"].format(hour, minutes))
        set_time_command_chain()
        
        def remove_product_command_chain():
            """ removes product from DB """
            #? /remove

            @self.bot.message_handler(commands=[bot_commands.remove_product])
            def remove_product(message: Message):
                """ first step of removing product """
                self.bot.send_message(message.from_user.id, messages["remove_product_first_step"])
                self.bot.register_next_step_handler(message, remove_product_second_step)

            def remove_product_second_step(message: Message):
                """ second step of removing product """
                link = message.text
                parser = PrestaShopScraper()
                product = parser.scrape_product(link)
                #? print("🐍 product: ",product)

                if product:
                    product_id = product["id"]
                    self.db.remove_product(product_id)
                    self.bot.send_message(message.chat.id, messages["remove_product_second_step_success"].format(product_id))

                else:
                    print(f"Can't get product info by this link: {link}")
                    self.bot.send_message(message.chat.id, messages["remove_product_second_step_fail"])
        remove_product_command_chain()
        
        #? /info
        @self.bot.message_handler(commands=[bot_commands.info])
        def get_info(message: Message):
            self.bot.send_message(message.from_user.id, messages["info"])
            self.helpers.get_info(message)
        
        #? /help
        @self.bot.message_handler(commands=[bot_commands.help])
        def get_help(message: Message):
            self.bot.send_message(message.from_user.id, messages["help"])