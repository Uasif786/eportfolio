
from pymongo import MongoClient
from bson.objectid import ObjectId

class AnimalShelter(object):
    

    def __init__(self):
       # Connect to local MongoDB instance
        try:
            self.client = MongoClient(
            'mongodb://localhost:27017/',
            serverSelectionTimeoutMS=3000,
            socketTimeoutMS=30000,
            connectTimeoutMS=30000
            )
            self.client.server_info()  # Test connection
            self.database = self.client['AAC']
            self.collection = self.database['animals']
        except Exception as e:
            raise ConnectionError(f"MongoDB connection failed: {str(e)}")

    def create(self, data): # TODO: add schema validation to make interactive
        if data is not None and isinstance(data, dict):
            self.collection.insert_one(data)
            return True
        else:
            raise Exception("Nothing to save, because data parameter is empty or not a dictionary.")

    def read(self, query):
        if query is not None:
            return list(self.collection.find(query))
        else:
            return []
            
     # UPDATE
    def update(self, query, new_values):
        if query is not None and new_values is not None:
            result = self.collection.update_many(query, {'$set': new_values})
            return result.modified_count
        else:
            raise Exception("Missing query or new_values parameters.")

    # DELETE
    def delete(self, query):
        if query is not None:
            result = self.collection.delete_many(query)
            return result.deleted_count
        else:
            raise Exception("Missing query parameter.")

