import clientAuth
import serverAuth

#its assumed the client sent the username with the encrpted password
username = "test_user"
password = "this_is_a_test"


print("Password: ", password)

#this would need to request the server for the public key
publicKey = serverAuth.requestPublicKey()

#then on the client side you would encrypt the password with the public key
encrptedPassword = clientAuth.encryptPassword(password, publicKey)
print("Encrypted Password: ", encrptedPassword.hex()) #hex or else it would be a long

#then send the encrypted password to the server where it will decrypt the password
decryptedPassword = serverAuth.decryptPassword(encrptedPassword)
print("Decrypted Password: " + decryptedPassword)

#then the server checks the password and username with whats stored
if serverAuth.authenticate(username, decryptedPassword):
    print("success")
else:
    print("failure")
