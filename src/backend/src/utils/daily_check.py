
import time
import aiomysql
from utils.query_execute import execute_modify, execute_select
from utils.game_operation import update_points


async def chiudi_domande_scadute(connection: aiomysql.Connection):
    """Metodo per cambiare stato delle domande"""


    print("chiudi_domande_scadute")
    today = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
    print(today)
    ranking_question_query = "update question set status='ranking' where status='open' and TIMESTAMPDIFF(SECOND, created_at, %s) >= 7 * 24 * 60 * 60 and (select count(*) from answer a where a.question_id = question.question_id) > ((select 5 + count(*)/2 from user));" 
    await execute_modify(connection, ranking_question_query, (today, ))
    closing_question_query = "update question set status='close' where status='ranking' and TIMESTAMPDIFF(SECOND, created_at, %s) >= 14 * 24 * 60 * 60 and rankings_times > ((select count(*)/2 from user))"
    await execute_modify(connection, closing_question_query, (today, ))


    question_points_query = "select question_id,created_by_user_id, created_by_llm_id from question where status = 'close' and points_assigned = 0"
    questions = await execute_select(connection, question_points_query)
    for question in questions:
        answer_query = f"select llm_id, user_id, points from answer where question_id = {question[0]}"
        answers = await execute_select(connection, answer_query)
        for answer in answers:
            if answer[0] is not None:
                await update_points(connection, "llm", answer[2], answer[0])
                print(f"ASSEGNATI {answer[2]} PUNTI A LLM {answer[0]}")
            elif answer[1] is not None:
                await update_points(connection, "user", answer[2], answer[1])
                print(f"ASSEGNATI {answer[2]} PUNTI A {answer[1]}")
        points_assigned = f"update question set points_assigned = 1 where question_id = {question[0]}"
        await execute_modify(connection, points_assigned)

        
        number_answer_query = f"select count(*) from answer where question_id = {question[0]}"
        number_answer = await execute_select(connection, number_answer_query)

        if question[1] is not None:
            await update_points(connection, "user", int(number_answer[0][0])*10) #BISOGNA SCEGLIERE IL MODIFICATORE
        elif question[2] is not None:
            await update_points(connection,"llm", int(number_answer[0][0])*10)


        #AGGIUNGERE QUERY CHE CONTROLLA DOMANDE MOLTO VECCHIE E SETTA FLAG PER RENDERLE PIù ALTE IN PRIORITà


async def chiudi_missioni_scadute(connection: aiomysql.Connection):
    """Metodo per controllare le missioni scadute"""
    

    print("chiudi_missioni_scadute")
    today = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
    expired_mission_query = "select m.mission_id, m.type, mu.user_id from mission m, mission_user mu where m.mission_id = mu.mission_id and expired = 0 and (type = 'daily' or type = 'weekly')"
    expired_mission = await execute_select(connection, expired_mission_query)
    for mission in expired_mission:
        if mission[1] == "daily":
            time_diff = 24*60*60
        else:
            time_diff = 7 * 24 * 60 * 60
        update_mission_query = f"update mission_user set expired=1 where mission_id = {mission[0]} and user_id = {mission[2]} and TIMESTAMPDIFF(SECOND, started_at, '{today}')>={time_diff}"
        await execute_modify(connection, update_mission_query)
    to_reset_missions = "select mission_id, user_id from mission_user where expired=1 and completed = 0"
    missions = await execute_select(connection, to_reset_missions)
    for mission in missions:
        started = time.strftime('%Y-%m-%d %H:%M:%S')
        update_query = "update mission_user set expired = 0, started_at = %s where mission_id = %s and user_id = %s"
        await execute_modify(connection, update_query, (started, mission[0],mission[1],))
