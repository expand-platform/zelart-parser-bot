import pymongo
import os
from dotenv import load_dotenv, dotenv_values
from pymongo.collection import Collection, ObjectId

from dataclasses import dataclass

@dataclass
class ConfigDocument:
    id: str = "_id"
    parse_time: str = "parse_time"

@dataclass
class ProductDocument:
    _id: str = "_id"
    id: str = "id"

config_document = ConfigDocument()
product_document = ProductDocument()


class Database():
    def __init__(self):
        self.client = pymongo.MongoClient(os.environ["MONGODB"])
        self.db = self.client["zelart-parser"]
        self.products_collection = self.db["products"]
        self.users_collection = self.db["users"]
        self.config_collection = self.db["config"]


    def insert_product(self, product):
        try:
            status = self.products_collection.find_one({"id": product["id"]})
            if status:
                print("Product already exists in the database")
                return
            else:
                self.products_collection.insert_one(product)
                print("Product inserted into database")
        except Exception as e:
            print(f"An error occurred: {e}")

        
    def get_products(self) -> list:
        try:
            products = self.products_collection.find({})
            return products
        except Exception as e:
            print(f"An error occurred: {e}")
            return None
        
    def get_products_count(self) -> list:
        return len(list(self.get_products()))


    def insert_user(self, user):
        try:
            status = self.users_collection.find_one({"chat_id": user["chat_id"]})
            if status:
                print("User already exists in the database")
                return
            else:
                self.users_collection.insert_one(user)
                print("User inserted into database")
        except Exception as e:
            print(f"An error occurred: {e}")

    def find_every_user(self):
        try:
            users = self.users_collection.find()
            # print("Users found in the database")
            # for user in users:
            #     print(user)
            return users
        except Exception as e:
            print(f"An error occurred: {e}")
            return None

    def find(self, key, value):
        self.products_collection.find_one({key: value})
        

    def update(self, key, value, field_name, new_value):
        try:
            self.products_collection.update_one({key: value}, {"$set": {field_name: new_value}})
            print(f"Updated {field_name} to {new_value} for {key}: {value}")
        except Exception as e:
            print(f"An error occurred: {e}")


    def update_config(self, key: str = "", new_value: str | int | bool = ""):
        document = self.config_collection.find_one({})
        print("🐍 document: ",document)

        if document:
            document_id = document[config_document.id]
        else:
            print(f"🔴 No config document found!")
        
        update_data = {'$set': {key: new_value}}
        result = self.config_collection.update_one({'_id': ObjectId(document_id)}, update_data)
        
        if result.modified_count > 0:
            print("🟢 Config updated!")

        elif result.matched_count > 0:
            print("🟡 Nothing new in config")
        
        else:
            print("🔴 Error: no such _id or document in config collection")


    def get_parse_time(self) -> list[int]:
        document = self.config_collection.find_one({})

        parse_time = [19, 0]

        if document is None:
            #? set default time
            document = {
                config_document.parse_time: parse_time
            }
            self.config_collection.insert_one(document)

        else:
            parse_time = document[config_document.parse_time]
            #? print("🐍 parse_time: ",parse_time)

            #? set default time
            for time in parse_time:
                if time is None:
                    parse_time = [19, 0]
            
        return parse_time
        

    def remove_product(self, id: int) -> None:
        document = self.products_collection.delete_one({product_document.id: id})

        if document:
            print(f"🟢 product {id} deleted from DB!")
        else:
            print(f"🟡 Product with {id} not found in DB!")
