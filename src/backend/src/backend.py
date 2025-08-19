
import asyncio
from typing import Optional
from fastapi import Body, Depends, FastAPI, File, HTTPException, Header, Query, Request, UploadFile
from fastapi.responses import JSONResponse
from starlette.middleware.sessions import SessionMiddleware
import time
import aiomysql
import requests
import httpx
import os

from contextlib import asynccontextmanager

from json_classes import QuestionInput, AnswerInput, ValidateInput, LoginInput, SignUpInput, BooleanResponse, CreateQuestionResponse, ReportInput, ProfileUpdateInput
from json_classes import LlmResponse, HomeInfoResponse, OnlineUserResponse, ProfileInfoResponse, QuestionPageResponse, UserMissionResponse
from json_classes import CreateQuestionPageResponse, VoteInput, ChangePasswordInput, PhoneInput
from utils.query_execute import execute_modify, execute_select
from utils.sign_up import sign_up_op, check_sign_up, insert_missions, insert_title
from utils.sign_in import check_password, get_pass_and_salt
from utils.startup import wait_for_ollama, close_connections, wait_for_nlp
from utils.various_tools import get_specific_from_something, get_something
from utils.create_question import insert_question, insert_theme, insert_tags, check_week_theme
from utils.session_handler import timeout
from utils.get_info import get_user_info, get_contributors, get_weekly_question, get_last_user_questions, get_last_user_answer, get_questions, get_trending_questions
from utils.get_info import get_missions, get_user_stats, get_last_user_activities, get_week_themes, get_avatars, get_titles
from utils.game_operation import insert_answer, ask_llm_answer, update_points, check_missions
from utils.connection import Connection
from utils.daily_check import chiudi_domande_scadute, chiudi_missioni_scadute
from utils.edit_profile import check_edit_profile, set_image, check_current_pass, edit_password




active_users = {}


async def verify_api_key( x_api_key: str = Header(...)):
    if x_api_key != os.environ["SECRET_KEY"]:
        raise HTTPException(status_code=403, detail="Invalid API Key")


async def set_user_id(request: Request, user_id: str = Header(...)):
    request.session["user_id"] = int(user_id)


async def session_timeout(timeout_seconds: int = 1800):
    """Funzione per gestire il timeout e la coda degli utenti attivi"""


    async def dependency(request: Request):
        
        session = request.session
        user_id = session.get("user_id")
        if not user_id:
            # Utente non loggato, salto controllo timeout
            return
        current_time = time.time()
        timeout(current_time, session.get("last_active"), timeout_seconds)
        session["last_active"] = current_time
        user_id = session.get("user_id")
        if user_id:
            active_users[user_id] = time.time()
            # Pulisce utenti inattivi (ultimi 30 min?)
            cutoff = time.time() - 1800
            to_remove = [uid for uid, ts in active_users.items() if ts < cutoff]
            for uid in to_remove:
                del active_users[uid]
            if user_id not in active_users:
                print(f"User {user_id} rimosso dalla sessione per inattività")
                raise HTTPException(status_code=401, detail="Sessione scaduta per inattività")
            else:

                async with Connection.get_connection() as connection:
                    update_last_login_query = "update user set last_login_at = %s where user_id = %s"
                    await execute_modify(connection, update_last_login_query, (time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())), request.session["user_id"],))
                    print(f"User_id {user_id} online")

    return dependency



async def periodic_task():
    while True:
        async with Connection.get_connection() as connection:

            print("periodic_task")
            await chiudi_domande_scadute(connection)
            await chiudi_missioni_scadute(connection)
            await asyncio.sleep(24 * 60 * 60)  # ogni 24 ore






@asynccontextmanager
async def lifespan(app: FastAPI):
    """All'avvio dell'applicazione inizializza la connessione con il db, e la chiude in chiusura dell'app"""

    await Connection.start_connection()



    await wait_for_ollama()

    await wait_for_nlp()

    periodic = asyncio.create_task(periodic_task())

    yield  # Periodo in cui applicazione è attiva

    periodic.cancel()


    await close_connections()
    



app = FastAPI(title = "Backend-CulturaLLM", lifespan=lifespan, dependencies=[Depends(verify_api_key)])
app.add_middleware(SessionMiddleware, secret_key=os.environ["SECRET_KEY"])


    
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:


    # Se è 401 sessione scaduta, elimina cookie di sessione, per gestire i periodi di inattività
    if exc.status_code == 401 and exc.detail == "Sessione scaduta per inattività":
        request.session.clear()
        response = JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})
        response.delete_cookie(
            key="session",
            path="/",
            httponly=True,
            secure=False,       # perché https_only=False
            samesite="lax"
        )
        return response
    # Altri errori
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})




@app.get("/health")
def health() -> dict[str, str]:
    """API per la sincronizzazione del frontend con il backend."""


    return {"status": "ok"}


@app.get("/online_users", dependencies=[Depends(set_user_id)])
async def online_users(request: Request) -> OnlineUserResponse:
    """API per il calcolo degli utenti online"""



    if request.session.get("user_id") not in active_users.keys():
        active_users[request.session.get("user_id")] = time.time()
    print(request.session["user_id"])
    print(active_users)
    return OnlineUserResponse(number = len(active_users))


@app.post("/logout", dependencies=[Depends(set_user_id)])
async def logout(request: Request) -> BooleanResponse:
    """API per il logout"""


    if "user_id" in request.session:
        del active_users[request.session["user_id"]]
    request.session.clear()
    print("LOGOUT")
    return BooleanResponse(status = True)


@app.post("/login")
async def login(login_json: LoginInput, request: Request) -> BooleanResponse:
    """API per il login"""


    async with Connection.get_connection() as connection:

        result = await get_pass_and_salt(connection, login_json.user)
        if len(result) == 0:
            return BooleanResponse(status=False)
        password = result["password"]
        salt:str = result["salt"]
        if check_password(password, login_json.password, salt):
            user_id = await get_specific_from_something(connection, "user", "user_id", f"email=%s or username=%s", (login_json.user, login_json.user,))
            user_id = user_id[0][0]
            request.session["user_id"] = int(user_id)
            request.session["last_active"] = time.time()
            active_users[user_id] = time.time()

            update_last_login_query = "update user set last_login_at = %s where user_id = %s"
            await execute_modify(connection, update_last_login_query, (time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())), request.session["user_id"],))



            print(request.session["user_id"])
            return BooleanResponse(status = True, warning=f"{user_id}")
        return BooleanResponse(status = False)


@app.post("/sign_up")
async def sign_up(sign_up_json: SignUpInput, request: Request) -> BooleanResponse:
    """API per la registrazione"""


    async with Connection.get_connection() as connection:

        if await check_sign_up(sign_up_json.email, connection):      
            return BooleanResponse(status = False, warning = "Email already in use!")
        
        if await check_sign_up(sign_up_json.username, connection):      
            return BooleanResponse(status = False, warning = "Username already in use!")
        
        status = await sign_up_op(sign_up_json.password, sign_up_json.username, sign_up_json.email, connection)

        await insert_missions(sign_up_json.username, connection)

        await insert_title(sign_up_json.username, connection)

        return BooleanResponse(status = status)
    



@app.post("/question", dependencies=[Depends(set_user_id)])
async def question(question_json: QuestionInput, request: Request) -> CreateQuestionResponse:
    """API per la creazione di una question"""


    async with Connection.get_connection() as connection:
        request.session["last_active"] = time.time()
        active_users[request.session["user_id"]] = time.time()
        question = question_json.question
        async with httpx.AsyncClient(timeout = 600.0) as client:
            try:
                if question_json.llm == "":
                    id = request.session.get("user_id")
                    print("ID:", id)
                    question_id = await insert_question(connection, "question_text, created_by_user_id", (question, id,))
                    print("domanda inserita!!!")
                    points = 10
                    if await check_week_theme(connection, question_json.theme):
                        points *= 2.5

                    await update_points(connection, "user", points, id)  #DECIDERE POI QUANTI PUNTI DARE PER LA CREAZIONE DI UNA DOMANDA
                    print("punti assegnati!!!")
                    await check_missions(connection, "question", request.session.get("user_id"), question_json.theme)
                    print("missioni aggiornate!!!")
                else:
                    
                    theme = await get_specific_from_something(connection, "theme", "name", f"theme_id = {question_json.theme}")
                    theme = theme[0][0]
                    yellow_json = {"argument" : theme}

                    response = await client.post("http://nlp_server:8069/yellow", json = yellow_json)
                    # PER TESTARE SENZA NLP EVITA RICHIESTE DI DOMANDA A LLM:
                    response.raise_for_status()
                    result = response.json()

                    print(result)   
                    id = await get_specific_from_something(connection, "llm", "llm_id", "name=%s", (question_json.llm,))
                    id = int(id[0][0]) 
                    question = result["question_generated"]
                    question_id = await insert_question(connection, "question_text, created_by_llm_id", (question, id,))

                    points = 10
                    if await check_week_theme(connection, question_json.theme):
                        points *= 2.5

                    await update_points(connection, "llm", points, id)


                    await check_missions(connection, "llm", request.session.get("user_id"), question_json.theme)

                print("DOMANDA INSERITA")
                await insert_tags(client, connection, question, question_id)
                # PER TESTARE SENZA NLP commenta quello dentro questa funzione sopra
                

                
                print("TAG INSERITI")
                await insert_theme(connection, question_json.theme, question_id)
                

                llm_answer = await ask_llm_answer(question, client, question_json.answering_llm)
                # PER TESTARE SENZA NLP commentra dentro questa funzione

                await insert_answer(connection, llm_answer, question_id, id, user = None)

                print("RISPOSTA GENERATA")
                return CreateQuestionResponse(answer = llm_answer, question = question)
            except aiomysql.Error as e:
                print("Errore mariadb in creazione question: ",e)
            except httpx.RequestError as e:
                print("Errore nella API:", e)


@app.post("/answer", dependencies=[Depends(set_user_id)])
async def answer(answer_json: AnswerInput, request: Request) -> BooleanResponse:
    """API per l'inserimento di una answer di una domanda"""


    request.session["last_active"] = time.time()
    active_users[request.session["user_id"]] = time.time()

    async with Connection.get_connection() as connection:
        user = None
        llm = None
        try:
            question_id = answer_json.question
            if answer_json.answering_llm == "":
                user = request.session.get("user_id")
                answer = answer_json.answer
                theme = await get_specific_from_something(connection, "question_theme", "theme_id" ,f"question_id = {question_id}")
                await check_missions(connection, "answer", request.session.get("user_id"), theme[0][0])
            else:
                async with httpx.AsyncClient(timeout = 660.0) as client:
                    question = await get_specific_from_something(connection, "question", "question_text", f"question_id = {question_id}")
                    answer = await ask_llm_answer(question, client, answer_json.answering_llm)
                id = await get_specific_from_something(connection, "llm", "llm_id", "name=%s", (answer_json.answering_llm,))
                if id == []:
                    return BooleanResponse(status = False)
                llm = id[0][0]

            await insert_answer(connection, answer, question_id, llm, user)
        except aiomysql.Error as e:
            print("Errore nella answer",e)
            return BooleanResponse(status = False)    
        return BooleanResponse(status = True)


@app.post("/validate", dependencies=[Depends(set_user_id)])
async def validate(ranking_json: ValidateInput, request: Request) -> BooleanResponse:
    """API per l'inserimento di una classifica delle risposte di una domanda"""


    request.session["last_active"] = time.time()
    active_users[request.session["user_id"]] = time.time()
    async with Connection.get_connection() as connection:

        user_id = request.session.get("user_id")

        try:
            question_id = ranking_json.question
            ranking: dict[int,int] = ranking_json.ranking

            check_ranking = f"select count(*) from user_ranked_question where user_id = {user_id} and question_id = {question_id}"
            check = await execute_select(connection, check_ranking)
            if(check[0][0] == 0):

                points = 250
                for position in ranking.keys():
                    answer = ranking[position]
                    await update_points(connection, "answer", points, answer)
                    print(f"AGGIUNTI {points} a Risposta {answer}")
                    points -= 50
                number_ranking_query = "update question set rankings_times = rankings_times+1 where question_id = %s"
                await execute_modify(connection, number_ranking_query, (question_id,))

                await update_points(connection, "user", 50, user_id)

                theme = await get_specific_from_something(connection, "question_theme", "theme_id", f"question_id = {question_id}")
                await check_missions(connection, "ranking", user_id, theme[0][0])

                insert_user_ranking = "insert into user_ranked_question(user_id, question_id) values (%s,%s)"
                await execute_modify(connection, insert_user_ranking, (user_id, question_id,))
            else:
                return BooleanResponse(status=False, warning="RANKING GIà EFFETTUATO DALL'UTENTE SU QUESTA DOMANDA")

        except aiomysql.Error as e:
            print("Errore nella validate", e)
            return BooleanResponse(status = False)
        return BooleanResponse(status = True)


@app.post("/report", dependencies=[Depends(set_user_id)])
async def report(report_json: ReportInput, request: Request) -> BooleanResponse:
    """API per l'inserimento di un report"""


    request.session["last_active"] = time.time()
    active_users[request.session["user_id"]] = time.time()
    async with Connection.get_connection() as connection:

        user_id = request.session.get("user_id")
        try:

            check_report = f"select count(*) from report where question_id = {report_json.question} and user_id = {user_id}"
            check = await execute_select(connection, check_report)
            if int(check[0][0]) == 0:
                #report_query = "insert into report (description, report_type_id, user_id, question_id) values (?,?,?,?)"
                report_query = "insert into report (user_id, question_id) values (%s,%s)"

                #await execute_modify(connection, report_query, (report_json.report, report_json.type, user_id, report_json.question,))
                await execute_modify(connection, report_query, (user_id, report_json.question,))
                return BooleanResponse(status = True)
            else:
                return BooleanResponse(status= False)
        except aiomysql.Error as e:
            print("Errore nella report", e)
            return BooleanResponse(status = False)
        
@app.post("/remove_report", dependencies=[Depends(set_user_id)])
async def report(report_json: ReportInput, request: Request) -> BooleanResponse:
    """API per la rimozione di un report"""


    request.session["last_active"] = time.time()
    async with Connection.get_connection() as connection:

        user_id = request.session.get("user_id")
        try:
            #report_query = "insert into report (description, report_type_id, user_id, question_id) values (?,?,?,?)"
            check_report = f"select count(*) from report where question_id = {report_json.question} and user_id = {user_id}"
            check = await execute_select(connection, check_report)
            if int(check[0][0]) == 1:

                report_query = "delete from report where user_id = %s and question_id = %s"

                #await execute_modify(connection, report_query, (report_json.report, report_json.type, user_id, report_json.question,))
                await execute_modify(connection, report_query, (user_id, report_json.question,))
                return BooleanResponse(status = True)
            else:
                return BooleanResponse(status = False)
        except aiomysql.Error as e:
            print("Errore nella report", e)
            return BooleanResponse(status = False)



@app.get("/get_home_info", dependencies=[Depends(set_user_id), Depends(session_timeout)])
async def get_home_info(request: Request) -> HomeInfoResponse:
    """API per ottenere le informazione della home dal db"""
    

    request.session["last_active"] = time.time()
    active_users[request.session["user_id"]] = time.time()
    async with Connection.get_connection() as connection:

        # Costruiamo il dizionario dei 10 migliori contributors
        contributors: dict[int,dict[str, str]] = await get_contributors(connection)

        # Costruiamo il dizionario dello user
        user_data = await get_user_info(connection, request.session["user_id"])

        # Calcoliamo le domande settimanali
        weekly_question = await get_weekly_question(connection)

        # Calcoliamo le trending questions
        trending_questions = await get_trending_questions(connection)

        # Calcoliamo i temi della settimana
        week_themes = await get_week_themes(connection)

        return HomeInfoResponse(contributors = contributors, user_data = user_data, weekly_question = weekly_question, trending_question = trending_questions, week_themes = week_themes)



@app.get("/get_profile_info", dependencies=[Depends(set_user_id)])
async def get_profile_info(request: Request, user_id: Optional[int] = Query(None)) -> ProfileInfoResponse:
    """API per ottenere le informazioni della pagina profilo"""


    request.session["last_active"] = time.time()
    active_users[request.session["user_id"]] = time.time()
    async with Connection.get_connection() as connection:
        if user_id:
            user_id = user_id
        else:
            user_id = request.session.get("user_id")
        user_data = await get_user_info(connection, user_id)
        user_question = await get_last_user_questions(connection, user_id)
        user_answer = await get_last_user_answer(connection, user_id)
        user_last = await get_last_user_activities(connection, user_id)
        user_avatars = await get_avatars(connection, user_id)
        user_titles = await get_titles(connection, user_id)

        print(user_data)

        return ProfileInfoResponse(user_data = user_data, user_question = user_question, user_answer = user_answer, user_activities = user_last, user_avatars = user_avatars, user_titles = user_titles)


@app.get("/get_question_page_info", dependencies=[Depends(set_user_id)])
async def get_question_page_info(request: Request) -> QuestionPageResponse:
    """API per ottenere le informazioni della pagina delle questions"""


    request.session["last_active"] = time.time()
    active_users[request.session["user_id"]] = time.time()
    async with Connection.get_connection() as connection:
        questions = await get_questions(connection, request.session["user_id"])
    return QuestionPageResponse(questions= questions)


@app.get("/get_llms")
async def get_llms(request: Request) -> LlmResponse:
    """API per ritornare i nomi di tutte le LLM presenti"""


    request.session["last_active"] = time.time()
    active_users[request.session["user_id"]] = time.time()
    async with Connection.get_connection() as connection:
        llms_query = "select llm_id, name, llm_points from llm"
        llms = await execute_select(connection, llms_query)
        result = {}
        for llm in llms:
            result[llm[0]] = llm[1]
        return LlmResponse(llms = result)
    
@app.get("/get_user_missions", dependencies=[Depends(set_user_id)])
async def get_user_missions(request: Request) -> UserMissionResponse:
    """API per ritornare tutte le missioni disponibili e completate da un utente"""


    request.session["last_active"] = time.time()
    active_users[request.session["user_id"]] = time.time()
    async with Connection.get_connection() as connection:
        result = await get_missions(connection, request.session["user_id"])

        stats = await get_user_stats(connection, request.session["user_id"])

        return UserMissionResponse(user_mission = result, user_stats = stats)


@app.post("/edit_profile", dependencies = [Depends(set_user_id)])
async def edit_profile(request: Request, profile_json: ProfileUpdateInput) -> BooleanResponse:
    """API per l'aggiormanento dei dati profilo"""


    print(profile_json)
    request.session["last_active"] = time.time()
    active_users[request.session["user_id"]] = time.time()
    async with Connection.get_connection() as connection:
        user_id = request.session.get("user_id")
        if await check_edit_profile(profile_json.username, user_id, connection):
            return BooleanResponse(status = False, warning = "Username already in use!")
        user_id = request.session.get("user_id")
        values_text  = "username = %s, name = %s, surname = %s, current_title_id = %s"
        values_tuple = (profile_json.username, profile_json.name, profile_json.surname, int(profile_json.new_title),)
        if profile_json.bio != "":
            values_text +=", bio = %s"
            values_tuple += (profile_json.bio,)
        if profile_json.location != "":
            values_text +=", location = %s"
            values_tuple += (profile_json.location,)
        if profile_json.birthday != "":
            values_text +=", birthday = %s"
            values_tuple += (profile_json.birthday,)
        if profile_json.website != "":
            values_text +=", website = %s"
            values_tuple += (profile_json.website,)
        if profile_json.reset_profile_picture == "1":
            values_text +=", current_avatar_id = %s"
            values_tuple += (1,)
        if profile_json.new_image_url != "":
            values_text +=", current_avatar_id = %s"
            if profile_json.new_image_url != f"/images/uploads/{profile_json.username}.jpg":        # Per evitare utente che modifica nome immagine che viene salvata
                values_tuple += (1,)
                
            else:
                id = await set_image(user_id, profile_json.new_image_url, connection)
                values_tuple += (id,)
        if profile_json.new_avatar != "":
            values_text +=", current_avatar_id = %s"
            values_tuple += (profile_json.new_avatar,)

        update_profile_query = f"update user set {values_text} where user_id = {user_id}"        

        await execute_modify(connection, update_profile_query, values_tuple)

        return BooleanResponse(status = True)
    


@app.post("/change_password", dependencies=[Depends(set_user_id)])
async def change_password(request: Request, change_password_json: ChangePasswordInput) -> BooleanResponse:
    """API per il cambio della password"""
        


    request.session["last_active"] = time.time()
    active_users[request.session["user_id"]] = time.time()
    async with Connection.get_connection() as connection:
        if await check_current_pass(connection, change_password_json.current_password, request.session["user_id"]) == False:
            return BooleanResponse(status = False, warning= "Password Sbagliata!!")
        await edit_password(connection, change_password_json.new_password, request.session["user_id"])
        return BooleanResponse(status = True, warning= "Password cambiata con successo!!")
    

@app.post("/change_phone", dependencies=[Depends(set_user_id)])
async def change_phone(request: Request, phone_json: PhoneInput) -> BooleanResponse:
    """API per l'aggiornamento del numero di telefono"""


    async with Connection.get_connection() as connection:
        update_phone = "update user set phone_number = %s where user_id = %s"
        await execute_modify(connection, update_phone, (phone_json.phone_number, request.session["user_id"],))
    return BooleanResponse(status = True)

@app.post("/change_email_notifications", dependencies=[Depends(set_user_id)])
async def change_email_notifications(request: Request) -> BooleanResponse:
    """API per il cambio della preferenza notifiche mail"""


    async with Connection.get_connection() as connection:
        update_email_notification = f"update user set email_notification = 1 - email_notification where user_id = {request.session["user_id"]}"
        await execute_modify(connection, update_email_notification)
    return BooleanResponse(status= True)

    

@app.get("/get_setting_info", dependencies=[Depends(set_user_id)])
async def get_setting_info(request: Request) -> dict[str, str | None]:
    """API per prendere le informazioni per la pagina settings"""

    info_query = f"select phone_number, email_notification from user where user_id = {request.session["user_id"]}"
    async with Connection.get_connection() as connection:
        info = await execute_select(connection, info_query)
    
    return {"phone_number" : info[0][0], "email_notification": str(info[0][1])}




@app.get("/create_question_info")
async def get_create_question_info(request: Request) -> CreateQuestionPageResponse:
    """API per ritornare le informazioni per la pagine di create question"""


    request.session["last_active"] = time.time()
    async with Connection.get_connection() as connection:  
        themes_db = await get_something(connection, "theme", "*")
        i = 0
        themes = {}
        for theme in themes_db:
            themes[i] = {}
            themes[i]["id"] = str(theme[0])
            themes[i]["name"] = theme[1]
            i += 1

        
        llms_db = await get_something(connection, "llm" , "llm_id, name")

        i = 0
        llms = {}
        for llm in llms_db:
            llms[i] = {}
            llms[i]["id"] = str(llm[0])
            llms[i]["name"] = llm[1]
            i += 1


        return CreateQuestionPageResponse(themes = themes, llms = llms)


@app.post("/upvote", dependencies=[Depends(set_user_id)])
async def upvote(request: Request, upvote_json: VoteInput) -> BooleanResponse:
    """API per fare l'upvote di una question da parte dell'utente"""
    
    
    request.session["last_active"] = time.time()
    async with Connection.get_connection() as connection:
        question_id = upvote_json.question_id
        print(question_id)
        user_id = request.session["user_id"]
        check_upvote_query = f"select count(*) from user_question_upvote where question_id = {question_id} and user_id = {user_id}"
        check = await execute_select(connection, check_upvote_query)
        if(int(check[0][0]) == 0):
            upvote_query = "insert into user_question_upvote(question_id, user_id) values (%s,%s)"
            await execute_modify(connection, upvote_query, (question_id, user_id,))
            update_upvote = f"update question set upvotes = upvotes + 1 where question_id = {question_id}"
            await execute_modify(connection, update_upvote)

            return BooleanResponse(status = True)
        else:
            return BooleanResponse(status = False)
        
@app.post("/downvote", dependencies=[Depends(set_user_id)])
async def downvote(request: Request, downvote_json: VoteInput) -> BooleanResponse:
    """API per fare il downvote di una question da parte dell'utente"""
    
    
    request.session["last_active"] = time.time()
    active_users[request.session["user_id"]] = time.time()
    async with Connection.get_connection() as connection:
        question_id = downvote_json.question_id
        user_id = request.session["user_id"]
        check_downvote_query = f"select count(*) from user_question_downvote where question_id = {question_id} and user_id = {user_id}"
        check = await execute_select(connection, check_downvote_query)
        if(int(check[0][0]) == 0):
            downvote_query = "insert into user_question_downvote(question_id, user_id) values (%s,%s)"
            await execute_modify(connection, downvote_query, (question_id, user_id,))
            update_downvote = f"update question set downvotes = downvotes + 1 where question_id = {question_id}"
            await execute_modify(connection, update_downvote)
            
            return BooleanResponse(status = True)
        else:
            return BooleanResponse(status = False)
        

@app.post("/remove_upvote", dependencies=[Depends(set_user_id)])
async def upvote(request: Request, upvote_json: VoteInput) -> BooleanResponse:
    """API per rimuovere l'upvote di una question da parte dell'utente"""
    
    
    request.session["last_active"] = time.time()
    active_users[request.session["user_id"]] = time.time()
    async with Connection.get_connection() as connection:
        question_id = upvote_json.question_id
        user_id = request.session["user_id"]
        check_upvote_query = f"select count(*) from user_question_upvote where question_id = {question_id} and user_id = {user_id}"
        check = await execute_select(connection, check_upvote_query)
        if(int(check[0][0]) == 1):
            upvote_query = "delete from user_question_upvote where question_id = %s and user_id = %s"
            await execute_modify(connection, upvote_query, (question_id, user_id,))
            update_upvote = f"update question set upvotes = upvotes - 1 where question_id = {question_id}"
            await execute_modify(connection, update_upvote)
            
            return BooleanResponse(status = True)
        else:
            return BooleanResponse(status = False)
        
@app.post("/remove_downvote", dependencies=[Depends(set_user_id)])
async def upvote(request: Request, upvote_json: VoteInput) -> BooleanResponse:
    """API per rimuovere il downvote di una question da parte dell'utente"""
    
    
    request.session["last_active"] = time.time()
    active_users[request.session["user_id"]] = time.time()
    async with Connection.get_connection() as connection:
        question_id = upvote_json.question_id
        user_id = request.session["user_id"]
        check_downvote_query = f"select count(*) from user_question_downvote where question_id = {question_id} and user_id = {user_id}"
        check = await execute_select(connection, check_downvote_query)
        if(int(check[0][0]) == 1):
            downvote_query = "delete from user_question_downvote where question_id = %s and user_id = %s"
            await execute_modify(connection, downvote_query, (question_id, user_id,))
            update_downvote = f"update question set downvotes = downvotes - 1 where question_id = {question_id}"
            await execute_modify(connection, update_downvote)
            
            return BooleanResponse(status = True)
        else:
            return BooleanResponse(status = False)
        

@app.post("/delete_user", dependencies=[Depends(set_user_id)])
async def delete_user(request: Request) -> BooleanResponse:
    """API per l'eliminazione di uno user dal db"""


    user_id = request.session["user_id"]
    async with Connection.get_connection() as connection:
        delete_query = f"delete from user where user_id = {user_id}"
        await execute_modify(connection, delete_query)
    request.session.clear()
    if user_id in active_users.keys():
        del active_users[user_id]
    return BooleanResponse(status= True)


    

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)

