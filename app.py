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
from nacl.public import PrivateKey, SealedBox, PublicKey
from binascii import hexlify

# database vars
client = MongoClient('mongodb://localhost:27017/')
db = None
users = None
notes = None
secret_key = None

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
    global secret_key
    # Get the database and users collection
    db = client.crypto_db
    users = db.users
    notes = db.notes
    secret_key = db.secret_key
    if db:
        print('Connection do db success...')
        return True
    # print(users)


# insert smth in the database
# json object has to have 2 fields - username and password
def insertUser(user):
    global salt
    global users
    # global box
    global secret_key
    # hashing a password just using bcrypt
    hashed = bcrypt.hashpw(user['password'].encode('utf-8'), salt)

    # saving hashed password back into user object
    user['password'] = hashed

    # GENERATE PRIVATE KEY
    secretKey = PrivateKey.generate()

    # GENERATE PUBLIC KEY BASED ON THE PRIVATE KEY
    publicKey = secretKey.public_key

    # user['key'] = userSecretKey
    # save user
    isUserSaved = users.insert_one(user)
    if isUserSaved:
        # create key pair json in another table
        jsonToSave = {
            'username': user['username'],
            'secretKey': secretKey.encode(),
            'publicKey': publicKey.encode()
        }
        # insert into collection
        secret_key.insert_one(jsonToSave)

# adds a note to database
def addNote(noteJson):
    global notes
    # global box
    global userKey

    text = noteJson['note']
    username = noteJson['username']
    publicKey = userKey['publicKey']

    # create a box for encryption
    sealBox = SealedBox(publicKey)

    # encrypt the message
    encrypted = sealBox.encrypt(text)

    noteToInsert = {
        'username': username,
        'note': encrypted
    }

    if notes.insert_one(noteToInsert):
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
    global secret_key
    # finding object with the same username
    user = users.find_one({'username': userToLogin['username']})
    # if user exists
    if user:
        if bcrypt.hashpw(userToLogin['password'].encode('utf-8'), user['password']) == user['password']:
            # userKey = user['key']
            # print('This is the user key')
            # print(userKey)

            # find his keys
            keys = secret_key.find_one({'username': user['username']})
            if keys:
                # turning byte key values to proper types for SealedBox
                pubKey = PublicKey(keys['publicKey'])
                secKey = PrivateKey(keys['secretKey'])

                userKey = {
                    'publicKey': pubKey,
                    'secretKey': secKey
                }
                # print(type(pubKey))
                # print(type(secKey))
                return True
        else:
            # print('no match')
            return False
    else:
        print('User cannot be found')

# read notes
def readNotes(username):
    # key to decrypt the messages
    global userKey
    global notes

    # create a unseal box
    unsealBox = SealedBox(userKey['secretKey'])

    print(username)
    for note in notes.find({'username': username}):
        decryptedNote = unsealBox.decrypt(note['note'])

        print(decryptedNote)

# setting up db connection
initDatabase()

while True:
    print('Choose 1 for creating a user')
    print('Choose 2 for logging in')

    choice = input('press a number: ')
    # getting user input
    # add a new user to db
    username = input('Enter username: ')
    password = input('Enter password: ')

    userJson = {
    'username': username,
    'password': password,
    'key': None
    }
    if choice == '1':
        password2 = input('Repeat the password: ')
        if password2 == userJson['password']:
            # create user
            insertUser(userJson)
        else:
            print('Passwords do not match, fuck off!')
    else:
        # login user
        if login(userJson):
            loggedIn = True
            print('You are logged in')
            # setting
            break



while True:
    print('Choose 1 for adding a new note')
    print('Choose 2 for reading your notes')
    print('Choose 3 for killing the program')

    choice = input('press a number: ')

    if loggedIn and choice == '1':
        # add a note
        note = input('Add a note: ').encode('utf-8')
        noteJson = {
            'note': note,
            'username': userJson['username']
        }
        if addNote(noteJson):
            print('Note added!')
        else:
            print('Note not added')
    if loggedIn and choice == '2':
        readNotes(userJson['username'])
    if loggedIn and choice == '3':
        break
