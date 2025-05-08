import pymongo

class Database():
    def __init__(self):
        self.client = pymongo.MongoClient("mongodb+srv://Kavun_:Dinamit2@zelart-parser.uqwx1o2.mongodb.net/")
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
        

    def find(self):
        pass

    def update(self):
        pass

    def delete(self):
        pass