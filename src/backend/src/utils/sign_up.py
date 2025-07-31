import os
import hashlib
import base64
import aiomysql

from utils.query_execute import execute_modify, execute_select
from utils.various_tools import get_specific_from_something, get_something


def hash_password(password) -> tuple[bytes, bytes]:
    """Funzione che effettua l'hashing della password, e la ritorna in un formato string-friendly"""

    
    salt: bytes = os.urandom(16)  # 16 byte di salt casuale
    hash_pw: bytes = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 100_000)
    hash_pw: bytes = base64.b64encode(hash_pw).decode('utf-8')
    salt: bytes = base64.b64encode(salt).decode('utf-8')
    return salt, hash_pw


async def check_sign_up(username: str, connection: aiomysql.Connection) -> bool:
    """Funzione che controlla che l'username non sia già presente"""

    try:
        query = "select count(*) from user where username=%s"
        result: list[tuple[str]] = await execute_select(connection, query, (username,))
    except aiomysql.Error as e:
        print("Errore nel check_sign_up",e)
        return False
    if result[0][0] == 0:
        return False
    return True


async def sign_up_op(password: str, username: str, email:str, connection: aiomysql.Connection) -> bool:
    """Funzione che effettua la registrazione, inserendo i dati nel db"""


    hashed = hash_password(password)
    password: bytes = hashed[1]
    salt: bytes = hashed[0]

    sign_up_query = "insert into user(username, email, password, salt) values (%s, %s, %s, %s)"
    try:
        await execute_modify(connection, sign_up_query, (username, email, password, salt,))
    except aiomysql.Error as e:
        print("Errore nella Registrazione")
        return False
    return True

async def insert_missions(username: str, connection: aiomysql.Connection) -> None:
    """Funzione che assegna ad ogni utente le missioni"""

    user_id = await get_specific_from_something(connection, "user", "user_id", "username = %s" , (username, ))
    user_id = user_id[0][0]

    missions = await get_something(connection, "mission", "mission_id")
    for mission in missions:
        insert_mission_query = "insert into mission_user (user_id, mission_id) values (%s, %s)"
        await execute_modify(connection, insert_mission_query, (user_id, mission[0]))
    