import os
import hashlib
import base64
import mariadb

from utils.query_execute import execute_modify, execute_select


def hash_password(password) -> tuple[bytes, bytes]:
    """Funzione che effettua l'hashing della password, e la ritorna in un formato string-friendly"""


    salt: bytes = os.urandom(16)  # 16 byte di salt casuale
    hash_pw: bytes = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 100_000)
    hash_pw: bytes = base64.b64encode(hash_pw).decode('utf-8')
    salt: bytes = base64.b64encode(salt).decode('utf-8')
    return salt, hash_pw


def check_sign_up(username: str, connection: mariadb.Connection) -> bool:
    """Funzione che controlla che l'username non sia già presente"""


    query = "select count(*) from user where username=?"
    result: list[tuple[str]] = execute_select(connection, query, (username,))
    if result[0][0] == 0:
        return False
    return True


def sign_up_op(password: str, username: str, email:str, connection: mariadb.Connection) -> bool:
    """Funzione che effettua la registrazione, inserendo i dati nel db"""


    hashed = hash_password(password)
    password: bytes = hashed[1]
    salt: bytes = hashed[0]

    sign_up_query = "insert into user(username, email, password, salt) values (?, ?, ?, ?)"
    try:
        execute_modify(connection, sign_up_query, (username, email, password, salt,))
    except mariadb.Error as e:
        print("Errore nella Registrazione")
        return False
    return True