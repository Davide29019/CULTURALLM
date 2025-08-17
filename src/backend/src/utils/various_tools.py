import aiomysql

from typing import Any

from utils.query_execute import execute_select, execute_modify


async def get_something(connection: aiomysql.Connection, item: str, column: str) -> list[tuple[str]]:
    query = f"select {column} from {item}"
    try:
        return await execute_select(connection, query)
    except aiomysql.Error as e:
        print("Errore nella get_questions", e)
        return []
    

async def get_something_ordered(connection: aiomysql.Connection, item: str, order_by: str) -> list[tuple[str]]:
    query = f"select * from {item} order by {order_by}"
    try:
        return await execute_select(connection, query)
    except aiomysql.Error as e:
        print("Errore nella get_questions", e)
        return []
    

async def get_specific_from_something(connection: aiomysql.Connection, item: str, column: str,condition: str, values: tuple[Any, ...] = ()) -> list[tuple[str]]:
    """Metodo per prendere specifiche colonne da una tabella su una condizione"""
    
    query = f"select {column} from {item} where {condition}"
    try:
        return await execute_select(connection, query, values)
    except aiomysql.Error as e:
        print("Errore nella get_questions", e)
        return []
    
