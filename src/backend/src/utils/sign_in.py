import base64
import hmac
import hashlib

def check_password(password: str, try_password:str, salt: str) -> bool:
    password = base64.b64decode(password)   
    salt = base64.b64decode(salt)
    try_pass = hashlib.pbkdf2_hmac('sha256', try_password.encode(), salt, 100_000)
    return hmac.compare_digest(password, try_pass)