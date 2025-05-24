from src.database.mongodb import Database
from telebot import TeleBot
from telebot.types import Message
from src.parser.zelart_parser import PrestaShopScraper
from src.bot.dataclass import FIELDS, FieldConfig
from src.bot.bot_messages import messages
from apscheduler.schedulers.background import BackgroundScheduler
from os import environ

class Helpers:
    def __init__(self, bot: TeleBot):
        self.db = Database()
        self.bot = bot
        self.ENVIRONMENT: str = environ["ENVIRONMENT"]

    # ! разбить стену кода на функции
    def update_products_daily(self):
        """ updates products in DB and sends message to users """
        users = self.db.find_every_user()
        
        #! убрать костыль с юзерами
        for user in users:
            try:
                self.bot.send_message(user["chat_id"], messages["scheduler_start_parsing"])
            except Exception as e:
                print(f"Error sending message to user {user['chat_id']}: {e}")
        
        products = self.db.get_products()  
        parser = PrestaShopScraper()
        parser.login()

        all_products_change_status = False
        
        for product_from_database in products:
            link = product_from_database["url"]
            product_from_parser = parser.parse_product(link)
            product_change_status = False
            reply_string = messages["scheduler_parse_string_start"].format(product_from_parser["title"], link)
            
            for product_key in product_from_parser:
                if product_key == "priceCur" or product_key == "priceWithDiscount" or product_key == "priceSrp" or product_key == "isHidden":
                    if product_from_parser[product_key] != product_from_database[product_key]:
                        print("change happened")
                        product_change_status = True
                        all_products_change_status = True

                        field = FIELDS.get(product_key)

                        if not field:
                            continue

                        key = field.display_name
                        key_value_database = field.format_func(product_from_database[product_key])
                        key_value_parser = field.format_func(product_from_parser[product_key])

                        if field.unit and product_key != "isHidden":
                            key_value_database += f" {field.unit}"
                            key_value_parser += f" {field.unit}"


                        reply_string += messages["scheduler_parse_string_add"].format(key, key_value_database, key_value_parser)
                        self.db.update("url", link, product_key, product_from_parser[product_key])

            if product_change_status == False:
                print(f"➖ product has not changed")
            
            elif product_change_status == True:
                print(f"➕ product has changed")
                users = self.db.find_every_user()
                
                #! для этого можно и функцию написать, часто используется                
                for user in users:
                    self.chat_id_for_reminder = user["chat_id"]
                    try:
                        self.bot.send_message(self.chat_id_for_reminder, reply_string)
                    except Exception as e:
                        print(f"Error sending message to user {self.chat_id_for_reminder}: {e}")
        
        #! Временное решение, надо будет сделать контроль рассылки
        users = self.db.find_every_user()
        for user in users:
            try:
                if all_products_change_status == False:
                    self.bot.send_message(user["chat_id"], messages["scheduler_parse_string_no_changes"])
                else:
                    self.bot.send_message(user["chat_id"], messages["parse_final"])
            except Exception as e:
                print(f"Error sending message to user {user["chat_id"]}: {e}")


        
    def schedule_parse_time(self, scheduler: BackgroundScheduler, hour: int = 19, minute: int = 0) -> None:
        scheduler.remove_all_jobs()

        #? on server we substract 3 hours
        if self.ENVIRONMENT == "PRODUCTION":
            if hour >= 3:
                hour -= 3
            else:
                #? We can't make hours negative, so we transform it like these:
                #? -1 = 23
                #? -2 = 22
                #? -3 = 21
                hour = 24 + (hour - 3)
            scheduler.add_job(self.update_products_daily, 'cron', hour=hour, minute=minute) 

        elif self.ENVIRONMENT == "DEVELOPMENT":
            scheduler.add_job(self.update_products_daily, 'cron', hour=hour, minute=minute) 
        
        #? print(self.scheduler.get_jobs())
        print(f"🟢 Products check will be started at {hour}:{minute}")


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
    

    def get_info(self, message: Message):
        products_count = self.db.get_products_count()
        parse_time = self.get_parse_time()
        
        info_message = messages["info_string"].format(products_count, parse_time)

        self.bot.send_message(message.chat.id, info_message)
