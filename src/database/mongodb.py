import pymongo
import os
from dotenv import load_dotenv

class Database():
    def __init__(self):
        load_dotenv()
        self.client = pymongo.MongoClient(os.getenv("MONGODB"))
        self.db = self.client["zelart-parser"]
        self.collection = self.db["products"]


    def insert_product(self, product):
        try:
            status = self.collection.find_one({"id": product["id"]})
            if status:
                print("Product already exists in the database")
                return
            else:
                self.collection.insert_one(product)
                print("Product inserted into database")
        except Exception as e:
            print(f"An error occurred: {e}")
        
    def find_every_product(self):
        try:
            products = self.collection.find()
            # print("Products found in the database")
            # for product in products:
            #     print(product)
            return products
        except Exception as e:
            print(f"An error occurred: {e}")
            return None

    def find(self, key, value):
        self.collection.find_one({key: value})
        

    def update(self, key, value, field_name, new_value):
        try:
            self.collection.update_one({key: value}, {"$set": {field_name: new_value}})
            print(f"Updated {field_name} to {new_value} for {key}: {value}")
        except Exception as e:
            print(f"An error occurred: {e}")

    def delete(self):
        pass