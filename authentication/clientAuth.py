import rsa

#this side will encrypt the password with the public key it recieves from the server
def encryptPassword(password: str, publicKey) -> bytes:
    return rsa.encrypt(password.encode(), publicKey)
