import bcrypt
pw = "SenhaForte123"
print(bcrypt.hashpw(pw.encode(), bcrypt.gensalt()).decode())
