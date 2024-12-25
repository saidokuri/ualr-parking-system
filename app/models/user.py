from app import mongo
from werkzeug.security import generate_password_hash, check_password_hash
from app.models.booking import Booking
from bson import ObjectId, errors

class User:
    collection = mongo.db.users

    @classmethod
    def create(cls, data):
        return cls.collection.insert_one(data)
    

    @classmethod
    def get_all_faculties_with_permits(cls):
        faculties = cls.collection.find({"role": "faculty"})
        faculties_with_permits = []
        
        for faculty in faculties:
            permits = list(Booking.find({"user_id": str(faculty["_id"])}))  # Convert cursor to list
            if permits:  # Check if there are any permits
                faculty["permits"] = permits  # Add permits to the faculty object
                faculties_with_permits.append(faculty)  # Append faculty to the result list

        return faculties_with_permits
    

    @classmethod
    def get_all_students_with_permits(cls):
        students = cls.collection.find({"role": "student"})
        students_with_permits = []
        
        for student in students:
            permits = list(Booking.find({"user_id": str(student["_id"])}))
            if permits:
                student["permits"] = permits
                students_with_permits.append(student)

        return students_with_permits
    
    @classmethod
    def get_all_faculties(cls):
        return cls.collection.find({"role": "faculty"})
    
    @classmethod
    def get_all_students(cls):
        return cls.collection.find({"role": "student"})
    
    @classmethod
    def get_all_police(cls):
        return cls.collection.find({"role": "police"})
    
    @classmethod
    def get_all_sodexo(cls):
        return cls.collection.find({"role": "sodexo"})
    
    @classmethod
    def get_all(cls):
        return cls.collection.find()

    @classmethod
    def get_by_email(cls, email):
        return cls.collection.find_one({"email": email})

    @classmethod
    def check_password(cls, user, password):
        return check_password_hash(user["password"], password)

    @classmethod
    def exists_by_email(cls, email):
        return cls.collection.find_one({"email": email}) is not None

    @classmethod
    def get_user_name_by_id(cls, user_id):
        try:
            user = cls.collection.find_one({"_id": ObjectId(user_id)}) 
            # print(f"Found user: {user}")
            return user['name'] if user else None
        except errors.PyMongoError as e:
            print(f"An error occurred while fetching user name: {e}")
            return None


    @classmethod
    def find_one(cls, query):
        return cls.collection.find_one(query)