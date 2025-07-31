from typing import Union
import aiomysql


# Variabile parametri serve per garantire sicurezza da SQL Injection


async def execute_select(connection: aiomysql.Connection, query: str, parametri: tuple[Union[str,int], ...] = ()) -> list[tuple[str]]:
    """Esegue la query di tipo select sulla connessione e restituisce il risultato."""


    try:
        async with connection.cursor() as cursor:
            await cursor.execute(query, parametri)
            results = await cursor.fetchall()
            return results
    except aiomysql.Error as e:
        print(f"Errore durante l'esecuzione della query SELECT: {e}")
        raise e
        


async def execute_modify(connection: aiomysql.Connection, query: str, parametri: tuple[Union[str,int], ...] = ()) -> None:
    """Esegue la query di tipo insert, delete o update sulla connessione."""

    try:
        async with connection.cursor() as cursor:
            await cursor.execute(query, parametri)
            await connection.commit()
    except aiomysql.Error as e:
        await connection.rollback()
        print(f"Errore durante l'inserimento: {e}")
        raise e

