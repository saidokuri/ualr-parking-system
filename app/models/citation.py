from app import mongo
from werkzeug.security import generate_password_hash, check_password_hash

class Citation:
    collection = mongo.db.citations


    @classmethod
    def insert_many(cls, data):
        return cls.collection.insert_many(data)
    

    @classmethod
    def get_all_filtered(cls, query, skip=0, limit=10):
        return cls.collection.find(query).skip(skip).limit(limit)
    

    @classmethod
    def count(cls, query):
        return cls.collection.count_documents(query)
    

    @classmethod
    def insert_one(cls, data):
        return cls.collection.insert_one(data)
    

    @classmethod
    def get_all(cls):
        return cls.collection.find()
    

    @classmethod
    def aggregate(cls, pipeline):
        return cls.collection.aggregate(pipeline)


    @classmethod
    def find(cls, query):
        return cls.collection.find(query)

    @classmethod
    def find_one(cls, query):
        return cls.collection.find_one(query)

    @classmethod
    def insert_many(cls, documents):
        return cls.collection.insert_many(documents)

    @classmethod
    def update_one(cls, query, update):
        return cls.collection.update_one(query, update)

    @classmethod
    def delete_one(cls, query):
        return cls.collection.delete_one(query)
