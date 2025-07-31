import time
import aiomysql
import httpx
from utils.query_execute import execute_modify, execute_select
from utils.create_question import request_to_ollama


async def insert_answer(connection: aiomysql.Connection, answer: str, question_id: int, llm: int = None, user: int = None) -> None:
    """Metodo per inserimento risposta in db"""
    
    if llm is None:
        answer_query = "insert into answer (user_id, answer_text, question_id) values (%s,%s,%s)"
        await execute_modify(connection, answer_query,(user, answer, question_id))
    else:
        answer_query = "insert into answer (llm_id, answer_text, question_id) values (%s,%s,%s)"
        await execute_modify(connection, answer_query,(llm, answer, question_id))


async def ask_llm_answer(question: str, client: httpx.Client, llm: str):
    """Metodo per chiedere e ritornare la risposta della llm ad una domanda"""
    content = f"{question} Rispondi in maniera concisa, corta e come farebbe un vero umano, evitando parole inutili, genera solo la risposta vera e propria."
    llm_answer = await request_to_ollama(client, content, llm)
    
    humanize_json = {"llm_response" : llm_answer, "level" : 4}

    #COMMENTA QUESTE 3 RIGHE SOTTO
    response = await client.post("http://nlp_server:8069/magenta", json = humanize_json)
    response.raise_for_status()
    result = response.json()
    print("RIPOSTA UMANIZZATA GENERATA")


    return result["humanized_response"]
    #COMMENTA QUESTA SOPRA E SOSTITUISCI CON:
    # return llm_answer



async def update_points(connection: aiomysql.Connection, item: str, points: int, id: int) -> bool:
    """Metodo per aggiornare i punti assegnati alle risposte o ad un utente"""

    if item == "user":
        query = f"update user set user_points = user_points+{points} where user_id = {id}"
    elif item == "answer":
        query = f"update answer set points = points+{points} where answer_id = {id}"
    else:
        query = f"update llm set llm_points = llm_points+{points} where llm_id = {id}"
    try:
        await execute_modify(connection, query)
    except aiomysql.Error as e:
        print("Errore nella update_points", e)
        return False
    return True



async def check_missions(connection: aiomysql.Connection, item: str, user_id: int, theme: int = None) -> None:
    """Metodo per controllare ed aggiornare le missioni, in base all'item (question o answer)"""



    mission_to_update_query = f"select m.mission_id from mission m, mission_user mu where m.mission_id = mu.mission_id and mu.user_id = {user_id} and mu.completed = 0 and m.kind = '{item}' and theme is null"
    mission_to_update_no_theme = await execute_select(connection, mission_to_update_query)

    mission_to_update_theme_query = f"select m.mission_id from mission m, mission_user mu where m.mission_id = mu.mission_id and mu.user_id = {user_id} and mu.completed = 0 and m.kind = '{item}' and m.mission_id in (select mission_id from mission where theme is not null) and theme = {theme}"
    mission_to_update_theme = await execute_select(connection, mission_to_update_theme_query)

    mission_to_update = mission_to_update_no_theme + mission_to_update_theme

    for mission in mission_to_update:
        mission_id = mission[0]
        update_mission_query = f"update mission_user set progress= progress+1 where mission_id ={mission_id} and user_id = {user_id}"
        await execute_modify(connection, update_mission_query)
        completed_missions_select_query = f"select m.mission_id from mission m, mission_user mu where m.mission_id = mu.mission_id and mu.user_id ={user_id} and m.value = mu.progress and mu.completed = 0"
        completed_mission = await execute_select(connection, completed_missions_select_query)
        for completed_mission_id in completed_mission:
            completed_at = time.strftime('%Y-%m-%d %H:%M:%S')
            update_completed_missions = f"update mission_user set completed = 1, completed_at = '{completed_at}' where mission_id = {completed_mission_id[0]} and user_id = {user_id}"
            await execute_modify(connection, update_completed_missions)
            completed_mission_prize_query = f"select reward_coins, reward_points, reward_badge, reward_title from mission where mission_id = {completed_mission_id[0]}"
            prize = await execute_select(connection, completed_mission_prize_query)
            points = prize[0][1]
            coins = prize[0][0]
            await check_missions(connection, "mission", user_id,theme)
            update_user_prize_query = f"update user set user_points = user_points+{points}, user_coins = user_coins+{coins} where user_id = {user_id}"
            await execute_modify(connection, update_user_prize_query)
            if prize[0][2] is not None:
                update_badge_query = f"insert into badge_user (badge_id, user_id) values ({prize[0][2]}, {user_id})"
                await execute_modify(connection, update_badge_query)
            if prize[0][3] is not None:
                update_title_query = f"insert into title_user (title_id, user_id) values ({prize[0][3]}, {user_id})"
                await execute_modify(connection, update_title_query)
                

    return

