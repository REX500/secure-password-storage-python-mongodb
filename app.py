# idea for this project:
# use case: person wants to save his username and a password in a database
# he enters his username and password in the terminal
# username gets saved as plaintext while password gets hashed using salt for
# extra randomness

# mongo connectors
import pymongo
from pymongo import MongoClient
# hashing lib for hashing passwords
import hashlib
# bcrypt
import bcrypt
# symetric encryption for saving notes
import nacl, nacl.secret, nacl.utils
from nacl.public import PrivateKey, SealedBox
from binascii import hexlify

# database vars
client = MongoClient('mongodb://localhost:27017/')
db = None
users = None
notes = None

# hashing
salt = bcrypt.gensalt(rounds = 12)

# user logged in
loggedIn = False

# symetric encryption
box = None
userKey = None # this will be assigned after the user logs in

def initDatabase():
    # using global vars
    global db
    global users
    global notes
    # Get the database and users collection
    db = client.crypto_db
    users = db.users
    notes = db.notes
    if db:
        print('Connection do db success...')
        return True
    # print(users)


# insert smth in the database
# json object has to have 2 fields - username and password
def insertUser(user):
    global salt
    global users
    global box
    # hashing a password just using bcrypt
    hashed = bcrypt.hashpw(user['password'].encode('utf-8'), salt)

    # saving hashed password back into user object
    user['password'] = hashed

    # generate a random 32 byte key
    userSecretKey = nacl.utils.random(nacl.secret.SecretBox.KEY_SIZE)

    user['key'] = userSecretKey
    users.insert_one(user)

# adds a note to database
def addNote(noteJson):
    global notes
    global box
    text = noteJson['note']
    key = noteJson['key']

    # store key in the safe
    box = nacl.secret.SecretBox(key)
    # generate nonce for extra randomness
    nonce = nacl.utils.random(nacl.secret.SecretBox.NONCE_SIZE)
    # finally encrypt the message
    encrypted = box.encrypt(text, nonce)


    if notes.insert_one({'note': encrypted}):
        return True
    else:
        return False
    # print(text)
    # print(encrypted)
    #
    # decrypted = box.decrypt(encrypted)
    # print(decrypted)



# login user
def login(userToLogin):
    global users
    global salt
    global userKey
    # finding object with the same username
    user = users.find_one({'username': userToLogin['username']})
    # if user exists
    if user:
        if bcrypt.hashpw(userToLogin['password'].encode('utf-8'), user['password']) == user['password']:
            userKey = user['key']
            return True
        else:
            # print('no match')
            return False
    else:
        print('User cannot be found')


# setting up db connection
initDatabase()

while True:
    print('Choose 1 for creating a user')
    print('Choose 2 for logging in')

    choice = input('press a number...')
    if choice == '1':
        print('You chose 1')
    else:
        print('You chose 2')
# getting user input
# add a new user to db
username = input('Enter username: ')
password = input('Enter password: ')

userJson = {
    'username': username,
    'password': password,
    'key': None
}

# adding user to db
# insertUser(userJson)

# tryig to authenticate the user
if login(userJson):
    loggedIn = True
    print('You are logged in')

if loggedIn:
    # add a note
    note = input('Add a note: ').encode('utf-8')
    noteJson = {
        'note': note,
        'key': userKey
    }
    if addNote(noteJson):
        print('Note added!')
    else:
        print('Note not added')

# userKdf = {
#     'username': 'superSecure',
#     'password': 'lenovochairWood40Candle'
# }
# key = bcrypt.kdf(
#     password = userKdf['password'].encode('utf-8'),
#     salt = salt,
#     desired_key_bytes = 32,
#     rounds = 100
# )
# to read the data from db
# fromDb = users.find() # returns a iterable cursor
# fromDB2 = users.list() # returns all from memory as a dict - what ever that means
# res = users.insert_one(user)
