import aiomysql

from utils.sign_up import check_sign_up
from utils.various_tools import get_specific_from_something
from utils.query_execute import execute_modify, execute_select
from utils.sign_in import get_pass_and_salt, check_password
from utils.sign_up import hash_password


async def check_edit_profile(username: str, user_id: int, connection: aiomysql.Connection) -> bool:
    """Metodo per controllare che lo username non sia già in uso"""

    check_user_username = await get_specific_from_something(connection, "user", "username", f"user_id = {user_id}")

    if username == check_user_username[0][0]:
        return False
    
    else:
        return await check_sign_up(username, connection)
    

async def set_image(user_id: int, path: str, connection: aiomysql.Connection) -> int:
    """Metodo per eliminare eventuali image già presenti per l'utente"""

    if path != "/images/assets/avatar/default-avatar-circle.jpg":
        username = await get_specific_from_something(connection, "user", "username", f"user_id = {user_id}")
        username = username[0][0]
        if path != f"/images/uploads/{username}.jpg":
            set_id = f"update user set current_avatar_id = 1 where user_id = {user_id}"
            await execute_modify(connection, set_id)
            old_image = f"delete from avatar where path ='/images/uploads/{username}.jpg'"
            await execute_modify(connection, old_image)
        
        query = f"select count(*) from avatar where path = '{path}'"
        check = await execute_select(connection, query)
        if check[0][0] == 0:
            new_image = f"insert into avatar(path) values ('{path}')"
            await execute_modify(connection, new_image)
        new_id = "select avatar_id from avatar where path =%s"
        new_id = await execute_select(connection, new_id, (path,))
        return new_id[0][0]
    return 1



async def check_current_pass(connection: aiomysql.Connection, current_password: str, user_id: int) -> bool:
    """Metodo per controllare se la password inserita dall'utente è corretta"""

    username = await get_specific_from_something(connection, "user", "username", f"user_id = {user_id}")

    result = await get_pass_and_salt(connection, username[0][0])
    password = result["password"]
    salt = result["salt"]
    return check_password(password, current_password, salt)



async def edit_password(connection: aiomysql.Connection, new_password: str, user_id: int) -> None:
    """Metodo per cambiare la password utente"""

    
    
    result = hash_password(new_password)

    update_password = "update user set password = %s, salt = %s where user_id = %s"
    await execute_modify(connection, update_password, (result[1], result[0], user_id))

