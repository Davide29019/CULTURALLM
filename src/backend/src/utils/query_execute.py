from typing import Union
import mariadb


# Variabile parametri serve per garantire sicurezza da SQL Injection


def execute_select(connection: mariadb.Connection, query: str, parametri: tuple[Union[str,int], ...] = ()) -> list[tuple[str]]:
    """Esegue la query di tipo select sulla connessione e restituisce il risultato."""


    try:
        cursor: mariadb.Cursor = connection.cursor()
        cursor.execute(query, parametri)
        results: list[tuple[str]] = cursor.fetchall()
        cursor.close()
        return results
    except mariadb.Error as e:
        print(f"Errore durante l'esecuzione della query SELECT: {e}")
        raise e 
        


def execute_modify(connection: mariadb.Connection, query: str, parametri: tuple[Union[str,int], ...] = ()) -> None:
    """Esegue la query di tipo insert, delete o update sulla connessione."""


    try:
        cursor: mariadb.Cursor = connection.cursor()
        cursor.execute(query, parametri)
        connection.commit()  
        cursor.close() 
    except mariadb.Error as e:
        connection.rollback()  # annulla tutte le operazioni non confermate
        print(f"Errore durante l'inserimento: {e}")
        raise e

