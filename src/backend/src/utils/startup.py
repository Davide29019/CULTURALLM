import httpx
import asyncio

from utils.connection import Connection

async def wait_for_ollama() -> None:
    """Metodo che aspetta l'avvio di ollama allo startup"""

    async with httpx.AsyncClient() as client:
        for i in range(50):
            try:
                response = await client.get("http://ollama:11434/api/tags")
                if response.status_code == 200:
                    print("Ollama è pronto")
                    break
            except httpx.RequestError:
                pass
            await asyncio.sleep(2) 


async def wait_for_nlp() -> None:
    "Metodo che aspetta l'avvio del docker nlp"  
    async with httpx.AsyncClient() as client:
        for i in range(100):
            try:
                response = await client.get("http://nlp_server:8069/")
                if response.status_code == 200:
                    print("nlp_server è pronto")
                    break
            except httpx.RequestError:
                pass
            await asyncio.sleep(2) 


async def close_connections() -> None:
    """Metodo che chiude la connessione con il db alla chiusura dell'applicazione"""

    try:   # Chiusura della connessione
        await Connection.close_connection()
    except Exception as e:
        print("Errore durante la chiusura della connessione:", e)