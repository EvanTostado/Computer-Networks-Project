import bcrypt

#test stuff
password = "this_is_a_test".encode()
hashed = bcrypt.hashpw(password, bcrypt.gensalt())
print(hashed.decode())  # Copy this output to your .env
