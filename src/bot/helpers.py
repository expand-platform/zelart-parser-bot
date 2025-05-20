from src.database.mongodb import Database
from telebot.types import Message
from src.parser.zelart_parser import PrestaShopScraper
from src.bot.dataclass import FIELDS, FieldConfig


class Helpers:
    def __init__(self, bot):
        self.db = Database()
        self.bot = bot

    
    def update_products_daily(self):
        """ updates products in DB and sends message to users """
        products = self.db.get_products()  
        parser = PrestaShopScraper()
        parser.login()
        all_products_change_status = False
        for product_database in products:
            link = product_database["url"]
            product_parser = parser.parse_product(link)
            product_change_status = False
            reply_string = f"Характеристики товару {product_parser['title']} змінились:\n\n"
            for i in product_parser:
                if product_parser[i] != product_database[i]:
                    product_change_status = True
                    all_products_change_status = True

                    field = FIELDS.get(i)

                    if not field:
                        continue

                    key = field.display_name
                    key_value_database = field.format_func(product_database[i])
                    key_value_parser = field.format_func(product_parser[i])

                    if field.unit and i != "isHidden":
                        key_value_database += f" {field.unit}"
                        key_value_parser += f" {field.unit}"


                    reply_string += f"{key} товару змінилась.\nРаніше: {key_value_database}\nЗараз: {key_value_parser}\n\n"
                    self.db.update("url", link, i, product_parser[i])

            if product_change_status == False:
                print(f"product {i} has not changed")
            if product_change_status == True:
                print(f"product {i} has changed")
                users = self.db.find_every_user()
                for user in users:
                    self.chat_id_for_reminder = user["chat_id"]
                    try:
                        self.bot.send_message(self.chat_id_for_reminder, reply_string)
                    except Exception as e:
                        print(f"Error sending message to user {self.chat_id_for_reminder}: {e}")
        if all_products_change_status == False:
            try:
                users = self.db.find_every_user()
                for user in users:
                    self.bot.send_message(user["chat_id"], 'Характеристики товарів не змінились.')
            except Exception as e:
                print(f"Error sending message to user: {e}")

        
    

    def schedule_parse_time(self, scheduler, hour: int = 19, minutes: int = 0) -> None:
        scheduler.remove_all_jobs()
        scheduler.add_job(self.update_products_daily, 'cron', hour=hour, minute=minutes)
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
    

    def get_info(self, message: Message):
        products_count = self.db.get_products_count()
        parse_time = self.get_parse_time()
        
        info_message = f"1. Зараз я слiдкую за {products_count} товарами 🔍\n2. Я надсилаю тобi апдейти у {parse_time} ⌚"

        self.bot.send_message(message.chat.id, info_message)
