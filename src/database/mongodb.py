import pymongo
import os
from dotenv import load_dotenv, dotenv_values

class Database():
    def __init__(self):
        load_dotenv()
        config = dotenv_values(".env")
        self.client = pymongo.MongoClient(config["MONGODB"])
        self.db = self.client["zelart-parser"]
        self.products_collection = self.db["products"]
        self.users_collection = self.db["users"]


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
        
    def find_every_product(self):
        try:
            products = self.products_collection.find()
            # print("Products found in the database")
            # for product in products:
            #     print(product)
            return products
        except Exception as e:
            print(f"An error occurred: {e}")
            return None

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

    def delete(self):
        pass