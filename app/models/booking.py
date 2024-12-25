from app import mongo
from werkzeug.security import generate_password_hash, check_password_hash

class Booking:
    collection = mongo.db.bookings

    @classmethod
    def create(cls, data):
        return cls.collection.insert_one(data)
    

    @classmethod
    def get_all(cls):
        return cls.collection.find()
    
    @classmethod
    def findAll(cls):
        return cls.collection.find()

    @classmethod
    def findAllActive(cls):
        return cls.collection.find({"status": "active"})

    @classmethod
    def insert_one(cls, data):
        return cls.collection.insert_one(data)
    
    @classmethod
    def find_one(cls, query):
        return cls.collection.find_one(query)
    

    @classmethod
    def update_one(cls, query, data):
        return cls.collection.update_one(query, data)
    
    @classmethod
    def find(cls, query):
        return cls.collection.find(query)

    
    @classmethod
    def count_documents(cls, query):
        return cls.collection.count_documents(query)

    

    @classmethod
    def delete_one(cls, query):
        return cls.collection.delete_one(query)
    
    @classmethod
    def delete_one(cls, query):
        return cls.collection.delete_one(query)
    
    @classmethod
    def find_one_and_delete(cls, query):
        return cls.collection.find_one_and_delete(query)
    

    @classmethod
    def update_one(cls, query, data):
        return cls.collection.update_one(query, data)