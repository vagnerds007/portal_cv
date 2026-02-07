import bcrypt
pw = "aa"
print(bcrypt.hashpw(pw.encode(), bcrypt.gensalt()).decode())
