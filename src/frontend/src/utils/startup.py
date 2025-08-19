import httpx
import asyncio


async def check_backend(SECRET_KEY) -> bool:
    """ Aspetta di ricevere la risposta del backend prima di avviarsi."""


    backend_url = "http://backend:8003/health"  
    async with httpx.AsyncClient(timeout = 30.0) as client:

        for attempt in range(30):
            try:
                headers = {"x-api-key": SECRET_KEY}
                response: httpx.Response = await client.get(backend_url, headers = headers)
                if response.status_code == 200:
                    print("Backend è pronto!")
                    return True
            except httpx.RequestError as e:
                print(f"Errore nella connessione al backend: {e}")
            
            await asyncio.sleep(2)
        
        print("Il backend non è ancora pronto dopo 30 tentativi.")
        return False

