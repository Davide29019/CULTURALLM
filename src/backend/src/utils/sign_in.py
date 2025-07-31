import base64
import hmac
import hashlib
import aiomysql

from utils.query_execute import execute_select
from utils.various_tools import get_specific_from_something


async def get_pass_and_salt(connection: aiomysql.Connection, user: str) -> dict[str,str]:
    """Metodo per ottenere password e salt della mail per il login"""

    pass_salt_query = "select password, salt from user where email=%s or username=%s"
    try:
        result:list[tuple[str]] = await execute_select(connection, pass_salt_query, (user, user,))
    except aiomysql.Error as e:
        print("Errore nella Login select")
        return {}
    if len(result) == 0:
        return {}
    pass_salt: dict[str,str] = {"password" : result[0][0], "salt" : result[0][1]}
    return pass_salt


def check_password(password: str, try_password:str, salt: str) -> bool:
    """"Metodo che controlla che la password inserita sia corretta"""

    password = base64.b64decode(password)   
    salt = base64.b64decode(salt)
    try_pass = hashlib.pbkdf2_hmac('sha256', try_password.encode(), salt, 100_000)
    return hmac.compare_digest(password, try_pass)



