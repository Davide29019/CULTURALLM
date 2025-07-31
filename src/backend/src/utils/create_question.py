import httpx
import aiomysql


from typing import Any, Union

from utils.query_execute import execute_modify, execute_select


async def request_to_ollama(client: httpx.AsyncClient, content: str, llm: str) -> str:
    """Metodo per mandare request ad ollama"""

    ollama_request: dict[str,Any] = {                                       # PER OLLAMA
                "model" : llm,
                "messages": [{ "role": "user", "content": content }],
                "stream": False
            }
    response = await client.post("http://ollama:11434/api/chat", json=ollama_request)
    response.raise_for_status()
    result = response.json()
    return result["message"]["content"]


async def insert_theme(connection: aiomysql.Connection, theme: int, question_id: int) -> None:
    """Metodo per inserire i temi delle domande nel db"""
    
    question_theme_query = "insert into question_theme (question_id, theme_id) values (%s, %s)"
    await execute_modify(connection, question_theme_query, (question_id, theme,))
                    

async def insert_question(connection: aiomysql.Connection, values_text: str, values: tuple[Union[str, int]]) -> int:
    """Metodo per inserire la question e ritornare l'id della question appena inserita"""
   
   
    question_query = "insert into question (" + values_text + ") values (%s, %s)"
       
    try:
        async with connection.cursor() as cursor:
            await cursor.execute(question_query, values)
            await connection.commit()
            question_id = cursor.lastrowid
            print(question_id)
            return question_id
    except aiomysql.Error as e:
        print(f"Errore durante l'esecuzione della query inser_question: {e}")
        raise e
        

async def insert_tags(client: httpx.Client ,connection: aiomysql.Connection, question: str, question_id: int) -> None:
    """Metodo che calcola i tags di una domanda e li inserisce nel db"""

    orange_json = {"question" : question}
    #COMMENTA QUESTE 3 RIGHE SOTTO
    response = await client.post("http://nlp_server:8069/orange", json = orange_json)
    response.raise_for_status()
    result = response.json()

    tags = result["tags"]
    tags_query = "update question set question_tags = %s where question_id = %s"
    #COMMENTA QUI SOPRA E INSERISCI:
    #tags_query = "update question set question_tags = '['prova','prova2','prova3']' where question_id = %s"

    await execute_modify(connection, tags_query, (tags, question_id))


async def check_week_theme(connection: aiomysql.Connection, theme_id: int) -> int:
    """Metodo per controllare se il tema è della settimana"""

    theme_query = f"select of_the_week from theme where theme_id = {theme_id}"
    result = await execute_select(connection, theme_query)
    return result[0][0]