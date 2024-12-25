from app import mongo
from werkzeug.security import generate_password_hash, check_password_hash

class Payment:
    collection = mongo.db.payments



    @classmethod
    def insert_one(cls, payment):
        cls.collection.insert_one(payment)


    @classmethod
    def get_all(cls):
        return cls.collection.find()


    @classmethod
    def find(cls, query):
        return cls.collection.find(query)

    @classmethod
    def findBySupervisorId(cls, supervisor_id):
        return cls.collection.find({"owner_id": supervisor_id})


    @classmethod
    def aggregate(cls, pipeline):
        return cls.collection.aggregate(pipeline)