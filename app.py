# idea for this project:
# use case: person wants to save his username and a password in a database
# he enters his username and password in the terminal
# username gets saved as plaintext while password gets hashed using salt for
# extra randomness

import pymongo
from pymongo import MongoClient

client = MongoClient('mongodb://localhost:27017/')

# Get the database and users collection
db = client.crypto_db
users = db.users
print(users)

# insert smth in the database
user = {
    'username': 'username',
    'password': 'password'
}

res = users.insert_one(user)
print(res)
