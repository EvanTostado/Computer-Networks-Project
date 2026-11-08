import rsa
import os
import hmac
import bcrypt
from dotenv import load_dotenv #this is where the hashed password with the username is stored 

load_dotenv() #loads variables from .env

EXPECTED_USERNAME = os.getenv("AUTH_USERNAME") #well essentially have one account
EXPECTED_HASH = os.getenv("AUTH_PASSWORD_HASH", "").encode()

#this side will set up the public and private key
publicKey, privateKey = rsa.newkeys(2048) 

#this will have the decryption #decleration ensures no typing errors
def decryptPassword(encryptedPassword: bytes) -> str:
    return rsa.decrypt(encryptedPassword, privateKey).decode()

def requestPublicKey():
    return publicKey

#this checks the username and password against whats stored
def authenticate(username: str, password: str) -> bool:
    #compares constant time to prevent timing attacks
    user_matches = hmac.compare_digest(username, EXPECTED_USERNAME)

    #verify password is correct
    password_matches = bcrypt.checkpw(password.encode(), EXPECTED_HASH)

    return user_matches and password_matches

