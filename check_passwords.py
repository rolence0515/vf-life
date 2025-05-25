import hashlib

users = [
    {
        "email": "v29@gm.cjjh.tc.edu.tw",
        "password": "8b916383258b58c4266d645e3eb3a1f4f7a7f86e69abec27a3ccceee775b4ffb"
    },
    {
        "email": "jackylam45@gmail.com",
        "password": "dfeef530bc911649ad87e7a3a372a0ee8d6be5221469e57ae0c19a25959b77bb"
    },
    {
        "email": "a0980855967@yahoo.com.tw",
        "password": "c95cd1a5cf39b3831b89f24f517eb81f7d6a965fd149e65f92579064024c19c0"
    },
    {
        "email": "0980855967@yahoo.com.tw",
        "password": "c95cd1a5cf39b3831b89f24f517eb81f7d6a965fd149e65f92579064024c19c0"
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
