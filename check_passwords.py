import hashlib

users = [
    {
        "email": "1131240758@qq.com",
        "password": "7984f8c230cdf43c405c68908b1eca5879f3b6dd7b78cbd642e275b448a98fc5"
    },
    {
        "email": "huachin6@gmail.com",
        "password": "3c1fe5dde30a83604c286be2ab6c6e0fe210b34b0381bee5d3fc1c718b8fac8a"
    },
    {
        "email": "582474972@qq.com",
        "password": "9a21c1892b5314f3b65c5f3f33ce58af5116ee1ed9be166494aed58d3d8666fa"
    }
]

def gen_default_pw(email):
    return hashlib.sha256(email.encode('utf-8')).hexdigest()[:6]

for user in users:
    email = user["email"]
    db_password = user["password"]
    default_pw = gen_default_pw(email)
    pw = hashlib.sha256(default_pw.encode()).hexdigest()
    match = pw == db_password
    print(f"email: {email}")
    print(f"  default_pw: {default_pw}")
    print(f"  pw:         {pw}")
    print(f"  db_password:{db_password}")
    print(f"  match:      {match}")
    print("-" * 40)
