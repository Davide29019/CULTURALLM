import asyncio
from contextlib import asynccontextmanager
from typing import AsyncContextManager, AsyncGenerator
import aiomysql


class Connection:
    """Gestore asincrono della connessione al database MariaDB usando aiomysql."""

    pool: aiomysql.Pool = None

    @classmethod
    async def start_connection(cls) -> None:
        """Inizializza il pool di connessioni al database, aspettando che sia pronto."""

        for attempt in range(30):
            try:
                cls.pool = await aiomysql.create_pool(
                    host="mariadb-culturaLLM",
                    port=3306,
                    user="user",
                    password="pwd",
                    db="culturaLLM",
                    autocommit=True,
                    minsize=1,
                    maxsize=10,
                )
                print("Connessione asincrona al database stabilita!!")
                return
            except aiomysql.OperationalError as e:
                print(f"Tentativo {attempt+1}: DB non pronto, riprovo tra 2 secondi...")
                await asyncio.sleep(2)

        raise ConnectionError("Impossibile connettersi al db dopo 30 tentativi")

    @classmethod
    @asynccontextmanager
    async def get_connection(cls) -> AsyncGenerator[aiomysql.Connection, None]:
        if cls.pool is None:
            raise ConnectionError("Pool di connessioni non inizializzato")
        conn = await cls.pool.acquire()
        try:
            yield conn
        finally:
            cls.pool.release(conn)

    @classmethod
    async def close_connection(cls) -> None:
        """Chiude il pool di connessioni."""
        if cls.pool:
            cls.pool.close()
            await cls.pool.wait_closed()
            print("Pool di connessioni chiuso.")