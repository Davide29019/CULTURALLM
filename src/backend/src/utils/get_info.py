
import time
from typing import Optional, Union
import aiomysql
import asyncio

from utils.various_tools import get_specific_from_something
from utils.query_execute import execute_select



async def get_hours(date: str, my_time: Optional[int] = None) -> dict[str,Union[int, str]]:
    # Tempo attuale in secondi epoch

        today = time.time()

        # Converti la tua stringa in struct_time
        mydate_struct = time.strptime(date, "%Y-%m-%d %H:%M:%S")

        # Converti struct_time in epoch
        mydate_epoch = time.mktime(mydate_struct)
        
        if my_time is not None:
            mydate_epoch += my_time


        

        

        # Calcola la differenza
        diff = abs(today - mydate_epoch)

        # Converti in ore
        hours = int(diff // 3600)
        if(hours<=24):
            type = "hours"
        elif hours<=168:
            type = "days"
            hours = hours//24
        else:
            type = "weeks"
            hours = hours//168
        return {"tempo": hours, "tipo": type}


async def get_question_answers(connection: aiomysql.Connection, question_id: int) -> dict[int, dict[str, str]]:
    """Metodo per ritornare tutte le risposte ad una domanda"""


    answers = await get_specific_from_something(connection, "answer", "*", f"question_id = {question_id}")
    i = 1
    result = {}
    for answer in answers:
        result[i] = {}
        result[i]["answer_id"] = str(answer[0])
        result[i]["answer_text"] = answer[5]
        if answer[1] is not None:
            result[i]["creator_type"] = "llm"
            creator = await get_specific_from_something(connection, "llm", "name", f"llm_id = {answer[1]}")
            result[i]["creator"] = creator[0][0]
        elif answer[2] is not None:
            result[i]["creator_type"] = "user"
            creator = await get_specific_from_something(connection, "user", "username, current_avatar_id, current_title_id", f"user_id = {answer[2]}")
            result[i]["creator"] = creator[0][0]
        result[i]["points"] = str(answer[6])
        result[i]["answered_at"] = str(answer[4])
        i += 1
    return result            





async def get_avatar_and_title(connection: aiomysql.Connection, avatar_id: int, title_id: int) -> dict[str, str]:
    """Metodo per prendere avatar e titile di un utente"""

    avatar = await get_specific_from_something(connection, "avatar", "path", f"avatar_id={avatar_id}")
    avatar = avatar[0][0]
    user_title = await get_specific_from_something(connection, "title", "name", f"title_id={title_id}")
    user_title = user_title[0][0]
    return {"avatar" : avatar, "user_title" : user_title}


async def get_user_info(connection: aiomysql.Connection, user_id: int) -> dict[str, Union[Optional[str], dict[int, dict[str, str]]]]:
    """Metodo per prendere i dati utente"""

    user_info = await get_specific_from_something(connection, "user", "*", f"user_id = {user_id}")
    user_info = user_info[0]
    user_data = {}
    user_data["user_id"] = str(user_info[0])
    avatar_title = await get_avatar_and_title(connection, user_info[6], user_info[7])
    user_data["avatar"] = avatar_title["avatar"]
    user_data["title"] = avatar_title["user_title"]
    user_position_query = f"SELECT user_id, RANK() OVER (ORDER BY user_points DESC) AS posizione FROM user"
    user_position = await execute_select(connection, user_position_query)

    for user in user_position:
        if user[0] == user_id:
            position = user[1]
            break


    user_data["position"] = str(position)


    user_data["name"] = user_info[3]
    
    
    user_data["surname"] = user_info[4]

    user_data["bio"] = user_info[5]
    user_data["user_points"] = str(user_info[10])
    user_data["user_coins"] = str(user_info[12])
    user_data["username"] = user_info[1]
    user_data["location"] = user_info[16]
    user_data["birthday"] = user_info[15]
    user_data["website"] = user_info[17]
    user_data["created_at"] = str(user_info[13])
    date_str = str(user_info[13])
    # Prima converti la stringa in struct_time con strptime di time
    time_struct = time.strptime(date_str, "%Y-%m-%d %H:%M:%S")

    # Ora formatta con strftime
    formatted_date = time.strftime("%d %B %Y", time_struct)

    user_data["formatted_created_at"] = str(formatted_date)
    
    user_data["custom_image"] = str(user_info[11])

    question_number = f"select count(*) from question where created_by_user_id = {user_id}"
    question_number = await execute_select(connection, question_number)

    user_data["question_number"] = str(question_number[0][0])

    answer_number = f"select count(*) from answer where user_id = {user_id}"
    answer_number = await execute_select(connection, answer_number)

    user_data["answer_number"] = str(answer_number[0][0])

    ranking_number = f"select count(*) from user_ranked_question where user_id = {user_id}"
    ranking_number = await execute_select(connection, ranking_number)

    user_data["ranking_number"] = str(ranking_number[0][0])

    mission_number = f"select count(*) from mission_user where user_id = {user_id} and completed =1"
    mission_number = await execute_select(connection, mission_number)

    user_data["mission_number"] = str(mission_number[0][0])


    user_badges = f"select b.badge_id, b.title, b.description, b.tier, b.path from badge b join badge_user bu on b.badge_id = bu.badge_id where bu.user_id = {user_id}"
    user_badges = await execute_select(connection, user_badges)
    if len(user_badges) != 0:
        i = 0
        user_data["badges"] = {}
        for badge in user_badges:
            user_data["badges"][i] = {}
            user_data["badges"][i]["title"] = badge[1]
            user_data["badges"][i]["description"] = badge[2]
            user_data["badges"][i]["tier"] = badge[3]
            user_data["badges"][i]["path"] = badge[4]
            i += 1



    user_titles = f"select t.title_id, t.name from title t join title_user tu on t.title_id = tu.title_id where tu.user_id = {user_id}"
    user_titles = await execute_select(connection, user_titles)

    if len(user_badges) != 0:
        i = 0
        user_data["titles"] = {}
        for title in user_titles:
            user_data["titles"][i] = {}
            user_data["titles"][i]["name"] = title[1]
            i += 1



    return user_data


async def get_contributors(connection: aiomysql.Connection) -> dict[int,dict[str, str]]:
    """Metodo per creare il dizionario dei top 10 contributors"""

    top_contributors_query = "select username, user_points,current_avatar_id, current_title_id, user_id  from user order by user_points desc limit 10"
    result = await execute_select(connection, top_contributors_query)
    contributors: dict[int,dict[str, str]] ={}
    i = 1
    for contributor in result:
        contributors[i] = {}
        contributors[i]["username"] = contributor[0]
        contributors[i]["points"] = str(contributor[1])
        avatar_title = await get_avatar_and_title(connection, contributor[2], contributor[3])
        contributors[i]["avatar"] = avatar_title["avatar"]
        contributors[i]["user_title"] = avatar_title["user_title"]
        contributors[i]["user_id"] = str(contributor[4])
        i+=1
    return contributors


async def get_weekly_question(connection: aiomysql.Connection) -> int:
    """Metodo per contare le domande create questa settimana"""

    weekly_question_query = "SELECT COUNT(*) FROM question WHERE created_at >= NOW() - INTERVAL 7 DAY;"
    number_weekly_question = await execute_select(connection, weekly_question_query)
    return number_weekly_question[0][0]



async def get_last_user_activities(connection: aiomysql.Connection, user_id: int) -> dict[str, str | None]:
    """Metodo per trovare le ultime attività utente"""


    user_last = f"select question_text, created_at from question where created_by_user_id = {user_id} order by created_at desc limit 1"
    user_last = await execute_select(connection, user_last)
    result = {}
    if len(user_last) != 0:
        hours = await get_hours(str(user_last[0][1]))
        result["question_hours"] = str(hours["tempo"])
        result["question_hours_type"] = hours["tipo"]
        result["last_question"] = user_last[0][0]
    else:
        result["last_question"] = None
    user_last = f"select answer_text, answered_at from answer where user_id = {user_id} order by answered_at desc limit 1"
    user_last = await execute_select(connection, user_last)
    if len(user_last) != 0:
        hours = await get_hours(str(user_last[0][1]))
        result["answer_hours"] = str(hours["tempo"])
        result["answer_hours_type"] = hours["tipo"]
        result["last_answer"] = user_last[0][0]
    else:
        result["last_answer"] = None
    user_last = f"select description, completed_at from mission m join mission_user mu on m.mission_id = mu.mission_id where mu.user_id = {user_id} and completed = 1 order by completed_at desc limit 1"
    user_last = await execute_select(connection, user_last)
    if len(user_last) != 0:
        hours = await get_hours(str(user_last[0][1]))
        result["mission_hours"] = str(hours["tempo"])
        result["mission_hours_type"] = hours["tipo"]
        result["last_mission"] = user_last[0][0]
    else:
        result["last_mission"] = None
    return result


async def get_last_user_questions(connection: aiomysql.Connection, user_id: int) -> dict[int, dict[str, str]]:
    """Metodo per trovare le ultime domande poste da un utente con il numero di risposte ricevute"""
  
  
    user_question_query = f"select question_id, question_text, rankings_times, status, created_at, upvotes, question_tags, downvotes from question where created_by_user_id = {user_id} limit 10"
    user_question = await execute_select(connection, user_question_query)
    i = 0
    result = {}
    for question in user_question:
        number_answer_query = f"select count(*) from answer where user_id ={user_id} and question_id = {question[0]}"
        number_answer = await execute_select(connection, number_answer_query)
        number_answer = number_answer[0][0]
        result[i] = {}
        result[i]["question_id"] = str(question[0])
        result[i]["question_text"] = question[1]
        result[i]["ranking_times"] = str(question[2])
        result[i]["status"] = question[3]
        result[i]["created_at"] = str(question[4])
        hours = await get_hours(str(question[4]))
        result[i]["hours"] = str(hours["tempo"])
        result[i]["hours_type"] = hours["tipo"]

        result[i]["answer_number"] = str(number_answer)
        result[i]["upvotes"] = str(question[5])
        result[i]["downvotes"] = str(question[7])
        result[i]["question_tags"] = question[6]
        i +=1
    return result 

async def get_last_user_answer(connection: aiomysql.Connection, user_id: int) -> dict[str, dict[str, str]]:
    """Metodo per trovare le ultime risposte fornite dall'utente e le rispettive domande"""
   
   
    user_answer_query= f"select answer_text, question_id, answer_id, answered_at from answer where user_id = {user_id} "
    user_answer = await execute_select(connection, user_answer_query)
    result = {}
    i = 0
    for answer in user_answer:
        question_answer_query = f"select question_id, question_text from question where question_id ={int(answer[1])}"
        question_text = await execute_select(connection, question_answer_query)
        result[i] = {}
        result[i]["question_text"] = question_text[0][1]
        result[i]["question_id"] = str(question_text[0][0])
        result[i]["answered_at"] = str(answer[3])

        hours = await get_hours(str(answer[3]))
        result[i]["hours"] = str(hours["tempo"])
        result[i]["hours_type"] = hours["tipo"]

        result[i]["answer_id"] = str(answer[2])
        result[i]["answer_text"] = str(answer[0])
        i += 1
    return result

async def get_ranking(connection: aiomysql.Connection, question_id: int) -> dict[int, dict[str, str]]:
    """Metodo per calcolare il ranking di una domanda"""
   
   
    ranking_query = f"select answer_text, points, user_id, llm_id from answer where question_id = {question_id} order by points desc limit 5"
    ranking = await execute_select(connection, ranking_query)
    result: dict[int, dict[str, str]]= {}
    i = 1
    
    for answer in ranking:
        result[i] = {}
        result[i]["answer_text"] = answer[0]
        result[i]["points"] = str(answer[1])
        if answer[3] is not None:
            llm = await get_specific_from_something(connection, "llm", "name", f"llm_id ={answer[3]}")
            result[i]["creator"] = llm[0][0]
        elif answer[2] is not None:
            user = await get_specific_from_something(connection, "user", "username", f"user_id = {answer[2]}")
            result[i]["creator"] = user[0][0]
        i += 1
    return result



async def get_questions(connection: aiomysql.Connection, user_id: int) -> dict[int, dict[str, Union[str, dict[int, dict[str, str]], list[str]]]]:
    """Metodo per ritornare le informazioni di tutte le domande non chiuse"""
    
    
    question_query = "select * from question"
    questions = await execute_select(connection, question_query)
    i = 0
    result: dict[int, dict[str, str]] = {}
    for question in questions:
        themes_query = f"select name from theme t, question_theme qt where t.theme_id = qt.theme_id and qt.question_id = {question[0]}"
        theme = await execute_select(connection, themes_query)
        if len(theme) == 0 or len(theme[0]) == 0:
            continue

        result[i] = {}
        
        result[i]["question_id"] = str(question[0])

        tags = question[1]

        tags = tags.split("[")[1].split("]")[0]
        print(tags)
        tags = tags.replace("'", "")
        tags = tags.replace(" ", "")
        tags = tags.split(",")
        print(tags)
        
        for j in range(0,3):
            tag = tags.pop(0)
            tag = tag.capitalize()
            tags.append(tag)
        
        result[i]["question_tags"] = tags
        result[i]["question_text"] = question[2]



        result[i]["status"] = question[9]

        #aggiungere lista rispose se status è ranking o close

        if question[9] == 'ranking':
            result[i]["ranking_times"] = str(question[6])
            check_ranking = f"select count(*) from user_ranked_question where user_id = {int(user_id)} and question_id = {int(question[0])}"
            check = await execute_select(connection, check_ranking)
            result[i]["ranked"] = str(check[0][0])

        elif question[9] == 'close':
            result[i]["ranking_times"] = str(question[6])
            result[i]["ranking"] = await get_ranking(connection, question[0])
        result[i]["created_at"] = str(question[5])

        hours = await get_hours(str(question[5]))

        result[i]["hours"] = str(hours["tempo"])
        result[i]["hours_type"] = hours["tipo"]
        

        result[i]["theme"] = theme[0][0]

        if question[4] is not None:
            result[i]["creator_type"] = "llm"
            creator = await get_specific_from_something(connection, "llm", "name", f"llm_id = {question[4]}")
            result[i]["creator"] = creator[0][0]
        elif question[3] is not None:
            result[i]["creator_type"] = "user"
            creator = await get_specific_from_something(connection, "user", "username, current_avatar_id, current_title_id", f"user_id = {question[3]}")
            print(creator)
            avatar = await get_avatar_and_title(connection, creator[0][1], creator[0][2])
            result[i]["user_avatar"] = avatar["avatar"]
            result[i]["creator"] = creator[0][0]
        user_upvote_query = f"select count(*) from user_question_upvote where question_id = {int(question[0])} and user_id = {user_id}"
        user_upvote = await execute_select(connection, user_upvote_query)
        result[i]["user_upvote"] = str(user_upvote[0][0])
        user_downvote_query = f"select count(*) from user_question_downvote where question_id = {int(question[0])} and user_id = {user_id}"
        user_downvote = await execute_select(connection, user_downvote_query)
        result[i]["user_downvote"] = str(user_downvote[0][0])
        
        result[i]["upvotes"] = str(question[8])
        result[i]["downvotes"] = str(question[10])

        
        number_answer_query = f"select count(*) from answer where question_id = {question[0]}"
        number_answer = await execute_select(connection, number_answer_query)
        result[i]["number_answer"] = str(number_answer[0][0])


        get_report = f"select count(*) from report where user_id = {user_id} and question_id = {question[0]}"
        report = await execute_select(connection, get_report)

        result[i]["report"] = str(report[0][0])

        result[i]["answers"] = await get_question_answers(connection, question[0])

        user_answered = f"select count(*) from answer where question_id = {question[0]} and user_id = {user_id}"
        user_answered = await execute_select(connection,user_answered)
        result[i]["answered"] = str(user_answered[0][0])
        



        

        #aggiungere lista rispose se status è ranking o close

        i += 1
    return result


async def get_trending_questions(connection: aiomysql.Connection) -> dict[int, dict[str, Union[str, list[str]]]]:
    """Metodo per ritornare le trending questions"""
    
    
    question_query = question_query = "select question_id, question_text, upvotes, question_tags, (select count(*) from answer where answer.question_id = question.question_id) as answers from question where created_at >= NOW() - INTERVAL 7 DAY order by upvotes desc, answers desc  limit 5;"
    questions = await execute_select(connection, question_query)
    i = 1
    result: dict[int, dict[str, str]] = {}
    for question in questions:
        themes_query = f"select name from theme t, question_theme qt where t.theme_id = qt.theme_id and qt.question_id = {question[0]}"
        theme = await execute_select(connection, themes_query)
        if len(theme) == 0 or len(theme[0]) == 0:
            continue

        result[i] = {}
        #number_answer = await get_specific_from_something(connection, "answer", "count(*)", f"question_id = {question[0]}")
        result[i]["question_id"] = str(question[0])
        result[i]["question_text"] = question[1]
        result[i]["votes"] = str(question[2])
        result[i]["number_answer"] = str(question[4])
        result[i]["question_tags"] = question[3]


        result[i]["theme"] = theme[0][0]
        i += 1
    return result



async def get_missions(connection: aiomysql.Connection, user_id: int) -> dict[int, dict[str, str]]:
    """Metodo per calcolare le missioni di un utente"""


    mission_query = f"select type, kind, theme, description, reward_coins, reward_points, value, progress, completed, expired, started_at, reward_badge from mission m, mission_user mu where m.mission_id = mu.mission_id and mu.user_id = {user_id} order by expired ASC, completed ASC,  progress desc, value ASC, reward_points DESC, reward_coins DESC"
    missions = await execute_select(connection, mission_query)
    result: dict[int, dict[str, str]] = {}
    i = 0
    for mission in missions:
        result[i] = {}
        result[i]["type"] = mission[0]
        result[i]["kind"] = mission[1]
        result[i]["theme"] = str(mission[2])
        result[i]["description"] = mission[3]
        result[i]["reward_coins"] = str(mission[4])
        result[i]["reward_points"] = str(mission[5])
        result[i]["value"] = str(mission[6])
        result[i]["progress"] = str(mission[7])
        result[i]["completed"] = str(mission[8])

        if mission[0] == "daily":
            time_diff = 24*60*60
        else:
            time_diff = 7 * 24 * 60 * 60

        hours = await get_hours(str(mission[10]), time_diff)

        result[i]["hours"] = str(hours["tempo"])
        result[i]["hours_type"] = hours["tipo"]
        if mission[11] is not None:
            badge = await get_specific_from_something(connection, "badge", "title", f"badge_id = {mission[11]}")
            result[i]["badge_name"] = badge[0][0]
        
        i += 1
    return result



async def get_user_stats(connection: aiomysql.Connection, user_id: int) -> dict[str, str]:
    """Metodo per ritornare valori statistici sull'utente"""

    result = {}
    completed = await get_specific_from_something(connection, "mission_user", "count(*)", f"user_id = {user_id} and completed = 1")
    result["completed"] = str(completed[0][0])
    active = await get_specific_from_something(connection, "mission_user", "count(*)", f"user_id = {user_id} and completed = 0 and expired = 0")
    result["active"] = str(active[0][0])

    badges = f"select count(*) from mission_user mu, mission m where m.mission_id = mu.mission_id and user_id ={user_id} and reward_badge is not null and completed = 1"
    badges = await execute_select(connection, badges)
    result["badges"] = str(badges[0][0])

    mission_points_earned = f"select IFNULL(SUM(reward_points), 0) from mission m, mission_user mu where m.mission_id =mu.mission_id and user_id = {user_id} and completed = 1"
    points = await execute_select(connection, mission_points_earned)
    result["points"] = str(points[0][0])
    return result


async def get_week_themes(connection: aiomysql.Connection) -> dict[int, dict[str, str]]:
    """Metodo per calcolare i temi della settimana"""


    theme_query = "select * from theme where of_the_week = 1"
    themes = await execute_select(connection, theme_query)

    result = {}
    i = 0
    for theme in themes:
        result[i] = {}
        result[i]["name"] = theme[1]
        result[i]["text"] = theme[3]
        result[i]["subtext"] = theme[4]

        number_question = f"select count(*) from question_theme where theme_id = {theme[0]}"
        number_question = await execute_select(connection, number_question)
        result[i]["questions"] = str(number_question[0][0])


        i += 1
    return result


async def get_avatars(connection: aiomysql.Connection, user_id: int) -> dict[int, dict[str, str]]:
    """Metodo per calcolare gli avatar posseduti da un utente"""


    avatar_query = f"select a.avatar_id, a.path from avatar a join avatar_user au on a.avatar_id = au.avatar_id where au.user_id = {user_id} and is_avatar = 1"
    avatars = await execute_select(connection, avatar_query)
    result = {}
    i = 0
    for avatar in avatars:
        result[i] = {}
        result[i]["id"] = str(avatar[0])
        result[i]["path"] = avatar[1]

        i += 1
    return result

async def get_titles(connection: aiomysql.Connection, user_id: int) -> dict[int, dict[str, str]]:
    """Metodo per calcolare gli avatar posseduti da un utente"""


    avatar_query = f"select a.title_id, a.name from title a join title_user au on a.title_id = au.title_id where au.user_id = {user_id}"
    avatars = await execute_select(connection, avatar_query)
    result = {}
    i = 0
    for avatar in avatars:
        result[i] = {}
        result[i]["id"] = str(avatar[0])
        result[i]["name"] = avatar[1]

        i += 1
    return result

