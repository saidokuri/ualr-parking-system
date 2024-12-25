from app import mongo
from werkzeug.security import generate_password_hash, check_password_hash
from bson import ObjectId


class Car:
    collection = mongo.db.cars

    @classmethod
    def save_car_details(cls, car_details):
        cls.collection.insert_one(car_details)


    @classmethod
    def get_all(cls):
        return cls.collection.find()


    @classmethod
    def find_by_user_id(cls, user_id):
        return cls.collection.find({"user_id": user_id})

    @classmethod
    def count_documents(cls, query):
        """Count the number of documents matching a query."""
        return cls.collection.count_documents(query)
    
    @classmethod
    def insert_one(cls, car_details):
        return cls.collection.insert_one(car_details)

    @classmethod
    def delete_car(cls, car_id):
        # Convert car_id to ObjectId and delete the car
        query = {"_id": ObjectId(car_id)}
        return cls.collection.delete_one(query)


    @classmethod
    def update_one(cls, query, update):
        query = {"_id": ObjectId(query["_id"])}
        return cls.collection.update_one(query, update)


        
    @classmethod
    def find(cls, query):
        return cls.collection.find(query)
    

    @classmethod
    def find_one(cls, query): 
        return cls.collection.find_one(query)