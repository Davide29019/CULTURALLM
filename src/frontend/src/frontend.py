import hmac
import hashlib
import os
import time
from typing import Optional, Union
from fastapi.exceptions import RequestValidationError
from fastapi.staticfiles import StaticFiles
import httpx
from fastapi import Depends, FastAPI, File, HTTPException, Request, Form, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException
from urllib.parse import quote
from contextlib import asynccontextmanager

from utils.startup import check_backend


templates = Jinja2Templates(directory = "templates")


API_BASE_URL = "http://backend:8003"


active_users = {}   # Serve per gestire il numero di utenti online

token_map: dict[str, dict[str, str]] = {}   # Serve per gestire i passaggi di ID alle pagine html, con una mappatura di un hash che viene usato come chiave per l'id e un valore testuale (name, answer_text o question_text)



async def check_token_values(token: str):
    """Metodo per controllare che un token non sia stato modificato"""

    return token in token_map.keys()


async def genera_token(entity:str, id: str):
    """Genera un token per un id"""

    secret_key = os.environ["SECRET_KEY"]
    raw = f"{entity}:{id}"
    return hmac.new(secret_key.encode(), raw.encode(), hashlib.sha256).hexdigest()



async def session_timeout(timeout_seconds: int = 1800):
    """Funzione per gestire il timeout e la coda degli utenti attivi"""


    async def dependency(request: Request):
        
        session = request.session
        user_id = session.get("user_id")
        if not user_id:
            # Utente non loggato, salto controllo timeout
            return
        current_time = time.time()
        

        last_active = session.get("last_active")
        if last_active is not None:
            elapsed = current_time - last_active
            if elapsed > timeout_seconds:
                print("FERMO QUI!")
                raise HTTPException(status_code=401, detail="Sessione scaduta per inattività")

        session["last_active"] = current_time
        user_id = session.get("user_id")
        print(f"User_id {user_id} online")
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
                print(f"User_id {user_id} online")

    return dependency







@asynccontextmanager
async def lifespan(app: FastAPI):
    """Verifica che backend sia partito prima di startare il frontend"""

    if await check_backend(SECRET_KEY):
        print("Avvio del server frontend...")
    else:
        print("Impossibile avviare il frontend: il backend non è pronto.")

    yield

    






app = FastAPI(title = "Frontend-CulturaLLM", lifespan=lifespan)    
app.add_middleware(SessionMiddleware, secret_key=os.environ["SECRET_KEY"],  max_age=1800)  # Middleware per gestire le sessioni
app.mount("/images", StaticFiles(directory="/app/images"), name="images")   # Cartella con le immagini che serviranno per le pagine html

SECRET_KEY = os.environ["SECRET_KEY"]




@app.exception_handler(Exception)
async def internal_server_error_handler(request: Request, exc: Exception):
    """Gestisce tutte le eccezioni non previste con codice 500"""

    if isinstance(exc, HTTPException):
        if exc.headers and exc.headers.get("X-Custom-Error") == "UsernameTaken":
            # Qui fai qualcosa di specifico o lascia passare, evita 500
            # Ad esempio ritorna la risposta con quell'errore personalizzato
            return JSONResponse(
                status_code=exc.status_code,
                content={"detail": exc.detail},
                headers=exc.headers
            )

    # Puoi fare log dell'errore qui, ad esempio:
    print(f"Errore interno: {exc}")

    # Qui puoi personalizzare la risposta, ad esempio un redirect o una pagina di errore
    # Se vuoi fare redirect:
    origin = request.session.get("form_origin", "signin")
    return RedirectResponse(url=f"/{origin}", status_code=303)

@app.exception_handler(httpx.HTTPStatusError)
async def httpx_exception_handler(request: Request, exc: httpx.HTTPStatusError):
    # Loggalo se vuoi
    print(f"Errore HTTP da backend: {exc.response.status_code} - {exc.request.url}")
    request.session.clear()
    # Redirect a una pagina di errore o mostra un messaggio
    return RedirectResponse(url="/signin", status_code=303)



@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Gestisce la modifica inaspettata di valori dei form, riportando alla pagina da dove è arrivato l'errore"""


    # Recupera l'origine del form dalla sessione (o fallback)
    origin = request.session.get("form_origin")

    return RedirectResponse(url=f"/{origin}", status_code=303)


@app.exception_handler(StarletteHTTPException)
async def starlette_http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Gestisce errori su chiamate API sbagliate e riporta alla pagina di origine dell'errore"""

    if exc.status_code in (403, 404, 405):
        if "form_origin" not in request.session:
            origin = "signin"
        else:
            origin = request.session.get("form_origin", "signin")
        return RedirectResponse(url=f"/{origin}", status_code=303)
    return await http_exception_handler(request, exc)
    


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Per gestire le situazioni di timeout sessione"""

    if exc.headers and exc.headers.get("X-Custom-Error") == "UsernameTaken":
            # Qui fai qualcosa di specifico o lascia passare, evita 500
            # Ad esempio ritorna la risposta con quell'errore personalizzato
            return JSONResponse(
                status_code=exc.status_code,
                content={"detail": exc.detail},
                headers=exc.headers
            )


    # Se è 401 sessione scaduta, elimina cookie di sessione
    if exc.status_code == 401 and exc.detail == "Sessione scaduta per inattività":
        async with httpx.AsyncClient() as client:
            headers = {"x-api-key": SECRET_KEY, "user-id" : request.session["user_id"]}
            await client.post(f"{API_BASE_URL}/logout", headers = headers)

        request.session.clear()
        response = RedirectResponse(url="/signin", status_code=302)  # Redirect verso home
        response.delete_cookie(
            key="session",
            path="/",
            httponly=True,
            secure=False,
            samesite="lax"
        )
        return response
    # Altri errori
    if exc.status_code in (403, 404, 405):
        if "form_origin" not in request.session:
            origin = "signin"
        else:
            origin = request.session.get("form_origin", "signin")
        return RedirectResponse(url=f"/{origin}", status_code=303)





@app.get("/", response_class = HTMLResponse)
def index(request: Request):
    """Porta alla home dell'applicazione"""

    request.session["form_origin"] = "/"
    return templates.TemplateResponse("index.html", {"request" : request})



@app.get("/signin", response_class=HTMLResponse)
async def signin_page(request: Request):
    """API per il redirect alla pagina di signin"""

    request.session["form_origin"] = "signin"
    print("ORIGIN SETTATO")
    return templates.TemplateResponse("signin.html",{"request" : request})



@app.post("/signin")
async def signin(request: Request, user: str = Form(...), password: str = Form(...)):
    """API per la gestione del login lato frontend"""



    request.session["form_origin"] = "signin"

    


    async with httpx.AsyncClient(timeout = 180.0) as client:
        token_map.clear()
        login_json: dict[str, str] = {"user" : user, "password" : password}
        headers = {"x-api-key": SECRET_KEY}
        response = await client.post((f"{API_BASE_URL}/login"), json = login_json, headers = headers)
        response.raise_for_status()
        result = response.json()
        if result["status"]:
            request.session["user_id"]=int(result["warning"])
            request.session["last_active"] = time.time()
            active_users[request.session["user_id"]] = time.time()

            print(request.session["user_id"])
            
            return RedirectResponse(url="/home", status_code=303)
        else:
            return templates.TemplateResponse("signin.html", {"request" : request, "error": "username e/o password errati!", "user" : user})


@app.get("/signup", response_class=HTMLResponse)
async def signup_page(request: Request):
    """API per il redirect alla pagina di signup"""

    request.session["form_origin"] = "signup"
    return templates.TemplateResponse("signup.html",{"request" : request})


@app.post("/signup", response_class=HTMLResponse)
async def signup(request: Request, email: str = Form(...), username: str = Form(...), password = Form(...)):
    """API per la gestione della registrazione lato frontend"""


    async with httpx.AsyncClient(timeout = 30.0) as client:
        sign_up_json: dict[str, str] = {"email" : email, "username" : username, "password" : password}
        headers = {"x-api-key": SECRET_KEY}
        response = await client.post((f"{API_BASE_URL}/sign_up"), json = sign_up_json, headers = headers)
        response.raise_for_status()
        result = response.json()
        request.session["form_origin"] = "signup"
        if result["status"]:
            return templates.TemplateResponse("signup.html",{"request" : request, "message" : "Sign up successful, proceed to sign in."})
        else:
            return templates.TemplateResponse("signup.html", {"request": request, "message": result["warning"], "email": email, "username": username})

@app.post("/logout", response_class = RedirectResponse)
async def logout(request: Request):
    """API per il logout"""

    if "user_id" in request.session:
        del active_users[request.session["user_id"]]
        
        async with httpx.AsyncClient(timeout = 30.0) as client:
            headers = {"x-api-key": SECRET_KEY, "user-id": str(request.session["user_id"])}
            response = await client.post(f"{API_BASE_URL}/logout", headers = headers)
            response.raise_for_status()
            #GESTION ERRORE NELLA LOGOUT DEL BACKEND
        token_map.clear()
        request.session.clear()
    
    return RedirectResponse(url="/signin", status_code=303)

@app.get("/home", dependencies=[Depends(session_timeout)])
async def home_page(request: Request):
    """API per il redirect alla pagina home"""



    request.session["form_origin"] = "home"



    if "user_id" in request.session:
            async with httpx.AsyncClient(timeout = 180.0) as client:
                token_map.clear()

                headers = {"x-api-key": SECRET_KEY, "user-id": str(request.session["user_id"])}
                response = await client.get(f"{API_BASE_URL}/online_users", headers = headers)
                response.raise_for_status()
                result = response.json()
                request.session["online_users"] = result["number"]

                response = await client.get(f"{API_BASE_URL}/get_home_info", headers = headers)
                response.raise_for_status()
                result = response.json()
                res: dict ={}
                for key in result["trending_question"].keys():
                    question = result["trending_question"][key]
                    question_id_token = await genera_token("question", question["question_id"])
                    token_map[question_id_token] = {}
                    token_map[question_id_token]["id"] = question["question_id"]
                    token_map[question_id_token]["question_text"] = question["question_text"]
                    question["question_id"] = question_id_token
                for key in result["contributors"]:
                    contributor = result["contributors"][key]
                    contributor_id_token = await genera_token("contributor", contributor["user_id"])
                    token_map[contributor_id_token] = {}
                    token_map[contributor_id_token]["id"] = contributor["user_id"]
                    contributor["user_id"] = contributor_id_token

                print(token_map) 
                print(request.session["user_id"])
                request.session["last_active"] = time.time()
                active_users[request.session["user_id"]] = time.time()
                return templates.TemplateResponse(
                    "home.html",
                {
                    "request": request,
                    "contributors": result["contributors"],
                    "online_users": request.session["online_users"],
                    "user_data" : result["user_data"],
                    "weekly_question" : result["weekly_question"],
                    "trending_question" : result["trending_question"],
                    "week_themes" : result["week_themes"]
                })
            
    return RedirectResponse(url="/signin", status_code=303)


@app.get("/questions")
async def question_page(request: Request, question_id: str = None):
    """API per il redirect alla questions page"""

    
    if "user_id" not in request.session:
        return RedirectResponse(url="/signin", status_code=303)
    else:
        request.session["last_active"] = time.time()
        active_users[request.session["user_id"]] = time.time()
        if question_id is not None:
            if not await check_token_values(question_id):
                print("TOKEN SBAGLIATO")
                return RedirectResponse(url=f"/{request.session["form_origin"]}", status_code=303)
            question_id_obj = token_map[question_id]["id"]
        else:
            question_id_obj = None

        

        token_map.clear()
        request.session["last_visited"] = request.session.get("form_origin", "home")
        request.session["form_origin"] = "questions"
        async with httpx.AsyncClient(timeout = 60.0) as client:
            headers = {"x-api-key": SECRET_KEY, "user-id" : str(request.session["user_id"])} 
            response = await client.get(f"{API_BASE_URL}/get_question_page_info", headers = headers)
            response.raise_for_status()
            result = response.json()
            
            for key in result["questions"].keys():
                question = result["questions"][key]
                question_id_token = await genera_token("question", question["question_id"])
                token_map[question_id_token] = {}
                token_map[question_id_token]["id"] = question["question_id"]
                token_map[question_id_token]["question_text"] = question["question_text"]
                if question_id_obj is not None and question_id_obj == question["question_id"]:
                    question_id_obj = question_id_token
                    print("DOMANDA TROVATA")
                question["question_id"] = question_id_token
                for key in question["answers"]:
                    answer = question["answers"][key]
                    answer_id_token = await genera_token("answer", answer["answer_id"])
                    token_map[answer_id_token] = {}
                    token_map[answer_id_token]["id"] = answer["answer_id"]
                    token_map[answer_id_token]["answer_text"] = answer["answer_text"]
                    answer["answer_id"] = answer_id_token
                

            questions = result["questions"]

            headers = {"x-api-key": SECRET_KEY}
            response = await client.get(f"{API_BASE_URL}/create_question_info", headers = headers)
            response.raise_for_status()
            result = response.json()

            for key in result["llms"].keys():
                    llm = result["llms"][key]
                    llm_id_token = await genera_token("llm", llm["id"])
                    token_map[llm_id_token] = {}
                    token_map[llm_id_token]["id"] = llm["id"]
                    token_map[llm_id_token]["name"] = llm["name"]
                    llm["id"] = llm_id_token
            
            for key in result["themes"].keys():
                        theme = result["themes"][key]
                        theme_id_token = await genera_token("theme", theme["id"])
                        token_map[theme_id_token] = {}
                        token_map[theme_id_token]["id"] = theme["id"]
                        token_map[theme_id_token]["name"] = theme["name"]
                        theme["id"] = theme_id_token
            
            if question_id_obj is None:

                return templates.TemplateResponse(
                        "dashboard_question.html",    #nome pagine con lista domande
                    {
                        "request": request,
                        "questions" : questions,
                        "llms" : result["llms"],
                        "themes" : result["themes"]
                    })
            else:
                return templates.TemplateResponse(
                        "dashboard_question.html",    #nome pagine con lista domande
                    {
                        "request": request,
                        "questions" : questions,
                        "llms" : result["llms"],
                        "themes" : result["themes"],
                        "question_obj" : question_id_obj
                    })

        

@app.get("/post_question")
async def get_post_question_page(request: Request):
    """API per il redirect alla post question page"""

    
    if "user_id" not in request.session:
        return RedirectResponse(url="/signin", status_code=303)
    else:
        request.session["last_active"] = time.time()
        active_users[request.session["user_id"]] = time.time()
        token_map.clear()
        request.session["last_visited"] = request.session.get("form_origin", "home")
        request.session["form_origin"] = "post_question"
        async with httpx.AsyncClient(timeout = 30.0) as client:

            headers = {"x-api-key": SECRET_KEY}
            response = await client.get(f"{API_BASE_URL}/create_question_info", headers = headers)
            response.raise_for_status()
            result = response.json()
            for key in result["themes"].keys():
                    theme = result["themes"][key]
                    theme_id_token = await genera_token("theme", theme["id"])
                    token_map[theme_id_token] = {}
                    token_map[theme_id_token]["id"] = theme["id"]
                    token_map[theme_id_token]["name"] = theme["name"]
                    theme["id"] = theme_id_token

            for key in result["llms"].keys():
                    llm = result["llms"][key]
                    llm_id_token = await genera_token("llm", llm["id"])
                    token_map[llm_id_token] = {}
                    token_map[llm_id_token]["id"] = llm["id"]
                    token_map[llm_id_token]["name"] = llm["name"]
                    llm["id"] = llm_id_token

            return templates.TemplateResponse("post_question.html", {"request" : request, "themes" : result["themes"], "llms" : result["llms"]})


@app.post("/user_question")
async def user_question(request: Request, question_text: str = Form(...), theme: str = Form(...), llm: str = Form(...)):
    """API per l'inserimento di una question creata da un user"""


    if "user_id" not in request.session:
        return RedirectResponse(url="/signin", status_code=303)
    else:
        request.session["last_active"] = time.time()
        active_users[request.session["user_id"]] = time.time()
        async with httpx.AsyncClient(timeout = 660.0) as client:
            if not await check_token_values(theme) or not await check_token_values(llm):
                return RedirectResponse(url=f"/{request.session["form_origin"]}", status_code=303)

            
            question_json = {"question" : question_text, "theme" : int(token_map[theme]["id"]), "answering_llm" : token_map[llm]["name"], "llm" : ""}
            headers = {"x-api-key": SECRET_KEY, "user-id": str(request.session["user_id"])}
            response = await client.post(f"{API_BASE_URL}/question", json = question_json, headers = headers)
            response.raise_for_status()
            result = response.json()

            
            token_map.clear()
            return RedirectResponse(url="/questions", status_code=303)
        



@app.post("/llm_question")
async def llm_question(request: Request, llm_generate: str = Form(...), theme_generate: str = Form(...)):
    """API per l'inserimento di una question creata da un llm"""


    if "user_id" not in request.session:
        return RedirectResponse(url="/signin", status_code=303)
    else:
        request.session["last_active"] = time.time()
        active_users[request.session["user_id"]] = time.time()
        async with httpx.AsyncClient(timeout = 660.0) as client:
            if not await check_token_values(theme_generate) or not await check_token_values(llm_generate):
                return RedirectResponse(url=f"/{request.session["form_origin"]}", status_code=303)
            question_json = {"question" : "", "theme" : int(token_map[theme_generate]["id"]), "answering_llm" : token_map[llm_generate]["name"], "llm" : token_map[llm_generate]["name"]}
            headers = {"x-api-key": SECRET_KEY, "user-id": str(request.session["user_id"])}
            response = await client.post(f"{API_BASE_URL}/question", json = question_json, headers = headers)
            response.raise_for_status()
            result = response.json()

            
            token_map.clear()
            return RedirectResponse(url="/questions", status_code=303)







@app.post("/upvote")
async def upvote(request: Request, question_id: str = Form(...)):
    """API per impostare l'upvote dell'utente"""


    if "user_id" not in request.session:
        return RedirectResponse(url="/signin", status_code=303)
    else:
        request.session["last_active"] = time.time()
        active_users[request.session["user_id"]] = time.time()
        headers = {"x-api-key": SECRET_KEY, "user-id": str(request.session["user_id"])}
        if not await check_token_values(question_id):
            return RedirectResponse(url=f"/{request.session["form_origin"]}", status_code=303)
        async with httpx.AsyncClient(timeout = 60.0) as client:
            response = await client.post(f"{API_BASE_URL}/upvote", json = {"question_id" : int(token_map[question_id]["id"])}, headers = headers)
            response.raise_for_status()
            result = response.json()

            return RedirectResponse(url = "/questions", status_code = 303)

@app.post("/remove_upvote")
async def remove_upvote(request: Request, question_id: str = Form(...)):
    """API per rimuovere l'upvote dell'utente"""


    if "user_id" not in request.session:
        return RedirectResponse(url="/signin", status_code=303)
    else:
        request.session["last_active"] = time.time()
        active_users[request.session["user_id"]] = time.time()
        headers = {"x-api-key": SECRET_KEY, "user-id": str(request.session["user_id"])}
        if not await check_token_values(question_id):
            return RedirectResponse(url=f"/{request.session["form_origin"]}", status_code=303)
        async with httpx.AsyncClient(timeout = 60.0) as client:
            response = await client.post(f"{API_BASE_URL}/remove_upvote", json = {"question_id" : int(token_map[question_id]["id"])}, headers = headers)
            response.raise_for_status()
            result = response.json()

            return RedirectResponse(url = "/questions", status_code = 303)


@app.post("/downvote")
async def upvote(request: Request, question_id: str = Form(...)):
    """API per impostare il downvote dell'utente"""


    if "user_id" not in request.session:
        return RedirectResponse(url="/signin", status_code=303)
    else:
        request.session["last_active"] = time.time()
        active_users[request.session["user_id"]] = time.time()
        headers = {"x-api-key": SECRET_KEY, "user-id": str(request.session["user_id"])}
        if not await check_token_values(question_id):
            return RedirectResponse(url=f"/{request.session["form_origin"]}", status_code=303)
        async with httpx.AsyncClient(timeout = 60.0) as client:
            response = await client.post(f"{API_BASE_URL}/downvote", json = {"question_id" : int(token_map[question_id]["id"])}, headers = headers)
            response.raise_for_status()
            result = response.json()

            return RedirectResponse(url = "/questions", status_code = 303)

@app.post("/remove_downvote")
async def remove_downvote(request: Request, question_id: str = Form(...)):
    """API per rimuovere il downvote dell'utente"""


    if "user_id" not in request.session:
        return RedirectResponse(url="/signin", status_code=303)
    else:
        request.session["last_active"] = time.time()
        active_users[request.session["user_id"]] = time.time()
        headers = {"x-api-key": SECRET_KEY, "user-id": str(request.session["user_id"])}
        if not await check_token_values(question_id):
            return RedirectResponse(url=f"/{request.session["form_origin"]}", status_code=303)
        async with httpx.AsyncClient(timeout = 60.0) as client:
            response = await client.post(f"{API_BASE_URL}/remove_downvote", json = {"question_id" : int(token_map[question_id]["id"])}, headers = headers)
            response.raise_for_status()
            result = response.json()

            return RedirectResponse(url = "/questions", status_code = 303)
        

@app.post("/user_answer")
async def send_user_answer(request: Request, answer_text: str = Form(...), question_id: str = Form(...)):
    """API per l'invio della risposta dell'utente ad una domanda"""


    if "user_id" not in request.session:
        return RedirectResponse(url="/signin", status_code=303)
    else:
        request.session["last_active"] = time.time()
        active_users[request.session["user_id"]] = time.time()
        headers = {"x-api-key": SECRET_KEY, "user-id": str(request.session["user_id"])}
        if not await check_token_values(question_id):
            return RedirectResponse(url=f"/{request.session["form_origin"]}", status_code=303)
        async with httpx.AsyncClient(timeout = 60.0) as client:
            response = await client.post(f"{API_BASE_URL}/answer", json = {"question" : int(token_map[question_id]["id"]), "answer" : answer_text}, headers= headers)
            response.raise_for_status()
            return RedirectResponse(url = "/questions", status_code = 303)


@app.post("/llm_answer")
async def send_llm_answer(request: Request, llm: str = Form(...), question_id: str = Form(...)):
    """API per l'invio della risposta dell'utente ad una domanda"""


    if "user_id" not in request.session:
        return RedirectResponse(url="/signin", status_code=303)
    else:
        headers = {"x-api-key": SECRET_KEY, "user-id": str(request.session["user_id"])}
        request.session["last_active"] = time.time()
        active_users[request.session["user_id"]] = time.time()
        if not await check_token_values(question_id):
            print("TOKEN SBAGLIATO")
            return RedirectResponse(url=f"/{request.session["form_origin"]}", status_code=303)
        async with httpx.AsyncClient(timeout = 660.0) as client:
            response = await client.post(f"{API_BASE_URL}/answer", json = {"question" : int(token_map[question_id]["id"]), "answering_llm" : token_map[llm]["name"]}, headers= headers)
            response.raise_for_status()
            return RedirectResponse(url = "/questions", status_code = 303)


@app.post("/report")
async def report(request: Request, question_id: str = Form(...)):
    """API per l'inserimento del report da parte dell'utente"""
    

    if "user_id" not in request.session:
        return RedirectResponse(url="/signin", status_code=303)
    else:
        request.session["last_active"] = time.time()
        active_users[request.session["user_id"]] = time.time()
        headers = {"x-api-key": SECRET_KEY, "user-id": str(request.session["user_id"])}
        if not await check_token_values(question_id):
            print("TOKEN SBAGLIATO")
            return RedirectResponse(url=f"/{request.session["form_origin"]}", status_code=303)
        async with httpx.AsyncClient(timeout = 60.0) as client:
            response = await client.post(f"{API_BASE_URL}/report", json = {"question" : int(token_map[question_id]["id"])}, headers= headers)
            response.raise_for_status()
            return RedirectResponse(url = "/questions", status_code = 303)


@app.post("/remove_report")
async def send_report(request: Request, question_id: str = Form(...)):
    """API per la rimozione del report"""

    if "user_id" not in request.session:
        return RedirectResponse(url="/signin", status_code=303)
    else:
        request.session["last_active"] = time.time()
        active_users[request.session["user_id"]] = time.time()
        headers = {"x-api-key": SECRET_KEY, "user-id": str(request.session["user_id"])}
        if not await check_token_values(question_id):
            print("TOKEN SBAGLIATO")
            return RedirectResponse(url=f"/{request.session["form_origin"]}", status_code=303)
        async with httpx.AsyncClient(timeout = 60.0) as client:
            response = await client.post(f"{API_BASE_URL}/remove_report", json = {"question" : int(token_map[question_id]["id"])}, headers= headers)
            response.raise_for_status()
            return RedirectResponse(url = "/questions", status_code = 303)        


@app.post("/ranking")
async def send_ranking(request: Request, question_id: str = Form(...), ranking_1: str = Form(...), ranking_2: str = Form(...), ranking_3: str = Form(...), ranking_4: str = Form(...), ranking_5: str = Form(...) ):
    """API per inviare un ranking di una domanda"""


    if "user_id" not in request.session:
        return RedirectResponse(url="/signin", status_code=303)
    else:
        request.session["last_active"] = time.time()
        active_users[request.session["user_id"]] = time.time()
        headers = {"x-api-key": SECRET_KEY, "user-id": str(request.session["user_id"])}
        print(ranking_1, ranking_2, ranking_3, ranking_4, ranking_5, question_id)
        if not await check_token_values(question_id) or not await check_token_values(ranking_1) or not await check_token_values(ranking_2) or not await check_token_values(ranking_3) or not await check_token_values(ranking_4) or not await check_token_values(ranking_5):
            print("TOKEN SBAGLIATO")
            return RedirectResponse(url=f"/{request.session["form_origin"]}", status_code=303)
        async with httpx.AsyncClient(timeout = 60.0) as client:
            ranking_json = {"ranking" : {
                1 : int(token_map[ranking_1]["id"]),
                2 : int(token_map[ranking_2]["id"]),
                3 : int(token_map[ranking_3]["id"]),
                4 : int(token_map[ranking_4]["id"]),
                5 : int(token_map[ranking_5]["id"])
            },
            "question" : int(token_map[question_id]["id"])}
            response = await client.post(f"{API_BASE_URL}/validate", json= ranking_json, headers= headers)
            response.raise_for_status()
            result = response.json()
            return RedirectResponse(url = "/questions", status_code = 303)  
        

@app.get("/your_profile_page")
async def get_your_profile_page(request: Request):
    """API per redirecta alla pagina del profilo utente"""


    if "user_id" not in request.session:
        return RedirectResponse(url="/signin", status_code=303)
    else:
        request.session["last_active"] = time.time()
        active_users[request.session["user_id"]] = time.time()
        request.session["last_visited"] = request.session.get("form_origin", "home")
        request.session["form_origin"] = "your_profile_page"
        async with httpx.AsyncClient(timeout = 60.0) as client:
            headers = {"x-api-key": SECRET_KEY, "user-id": str(request.session["user_id"])}
            token_map.clear()
            response = await client.get(f"{API_BASE_URL}/get_profile_info", headers= headers)
            response.raise_for_status()
            result = response.json()
            #print(result)
            for key in result["user_question"].keys():
                question = result["user_question"][key]
                question_id_token = await genera_token("question", question["question_id"])
                token_map[question_id_token] = {}
                token_map[question_id_token]["id"] = question["question_id"]
                token_map[question_id_token]["question_text"] = question["question_text"]
                question["question_id"] = question_id_token
            
            for key in result["user_answer"].keys():
                answer = result["user_answer"][key]
                question_id_token = await genera_token("question", answer["question_id"])
                token_map[question_id_token] = {}
                token_map[question_id_token]["id"] = answer["question_id"]
                token_map[question_id_token]["question_text"] = answer["question_text"]
                answer["question_id"] = question_id_token

            for key in result["user_avatars"].keys():
                avatar = result["user_avatars"][key]
                avatar_id_token = await genera_token("question", avatar["id"])
                token_map[avatar_id_token] = {}
                token_map[avatar_id_token]["id"] = avatar["id"]
                token_map[avatar_id_token]["path"] = avatar["path"]
                avatar["id"] = avatar_id_token

            for key in result["user_avatars"].keys():
                avatar = result["user_avatars"][key]
                avatar_id_token = await genera_token("question", avatar["id"])
                token_map[avatar_id_token] = {}
                token_map[avatar_id_token]["id"] = avatar["id"]
                token_map[avatar_id_token]["path"] = avatar["path"]
                avatar["id"] = avatar_id_token


            for key in result["user_titles"].keys():
                title = result["user_titles"][key]
                title_id_token = await genera_token("question", title["id"])
                token_map[title_id_token] = {}
                token_map[title_id_token]["id"] = title["id"]
                token_map[title_id_token]["name"] = title["name"]
                title["id"] = title_id_token



            return templates.TemplateResponse("my_profile.html", {"request" : request, "user_data" : result['user_data'], "user_question" : result["user_question"], "user_answer" : result["user_answer"], "last_activities" : result["user_activities"], "user_avatars" : result["user_avatars"], "user_titles": result["user_titles"]})


@app.post("/visit_profile")
async def visit_profile_page(request: Request, user_id: str = Form(...)):
    """API per redirecta alla pagina del profilo utente"""


    if "user_id" not in request.session:
        return RedirectResponse(url="/signin", status_code=303)
    else:
        print(token_map, user_id)
        if not await check_token_values(user_id):
            print("TOKEN SBAGLIATO")
            return RedirectResponse(url=f"/{request.session["form_origin"]}", status_code=303)

        request.session["last_active"] = time.time()
        active_users[request.session["user_id"]] = time.time()
        async with httpx.AsyncClient(timeout = 60.0) as client:
            headers = {"x-api-key": SECRET_KEY, "user-id": str(request.session["user_id"])}
            
            response = await client.get(f"{API_BASE_URL}/get_profile_info", params={"user_id": int(token_map[user_id]["id"])}, headers= headers)
            response.raise_for_status()
            result = response.json()

            user_id_token = user_id

            token_map.clear()



            for key in result["user_question"].keys():
                question = result["user_question"][key]
                question_id_token = await genera_token("question", question["question_id"])
                token_map[question_id_token] = {}
                token_map[question_id_token]["id"] = question["question_id"]
                token_map[question_id_token]["question_text"] = question["question_text"]
                question["question_id"] = question_id_token
            
            for key in result["user_answer"].keys():
                answer = result["user_answer"][key]
                question_id_token = await genera_token("question", answer["question_id"])
                token_map[question_id_token] = {}
                token_map[question_id_token]["id"] = answer["question_id"]
                token_map[question_id_token]["question_text"] = answer["question_text"]
                answer["question_id"] = question_id_token

            token_map[user_id_token] = {}
            token_map[user_id_token]["id"] = result["user_data"]["user_id"]
            result["user_data"]["user_id"] = user_id_token

            return templates.TemplateResponse("profile.html", {"request" : request, "user_data" : result['user_data'], "user_question" : result["user_question"], "user_answer" : result["user_answer"], "last_activities" : result["user_activities"]})





@app.get("/missions")
async def mission_page(request: Request):
    """API per il redirect alla mission page"""

    if "user_id" not in request.session:
        return RedirectResponse(url="/signin", status_code=303)
    else:
        request.session["last_active"] = time.time()
        active_users[request.session["user_id"]] = time.time()
        async with httpx.AsyncClient(timeout = 60.0) as client:
            token_map.clear()
            headers = {"x-api-key": SECRET_KEY, "user-id": str(request.session["user_id"])}
            response = await client.get(f"{API_BASE_URL}/get_user_missions", headers = headers)
            response.raise_for_status()
            result = response.json()
            request.session["last_visited"] = request.session.get("form_origin", "home")
            request.session["form_origin"] = "missions"

            return templates.TemplateResponse("missions.html", {"request" : request, "missions" : result["user_mission"], "stats" : result["user_stats"]})


@app.post("/edit_profile")
async def edit_profile(request: Request, first_name: str = Form(...), last_name: str = Form(...), username: str = Form(...), bio: Optional[str] = Form(""), location: Optional[str] = Form(""), website: Optional[str] = Form(""), birthdate: Optional[str] = Form(""), selected_avatar_id: Optional[str] = Form(""), profile_title: Optional[str] = Form(""), profile_picture: Optional[UploadFile] = File(None), reset_profile_picture: Optional[str] = Form(None)):
    """API per inviare i dati di edit profile al backend"""


    if "user_id" not in request.session:
        return RedirectResponse(url="/signin", status_code=303)
    else:
        if not await check_token_values(selected_avatar_id) and not await check_token_values(profile_title):
            print("TOKEN SBAGLIATO")
            return RedirectResponse(url=f"/{request.session["form_origin"]}", status_code=303)
        request.session["last_active"] = time.time()
        active_users[request.session["user_id"]] = time.time()
        image_url = ""
        if reset_profile_picture == "1":
            print("→ Reimpostare immagine di default")
            default_image = 1
        elif profile_picture:
            print("→ Ricevuta nuova immagine:", profile_picture.filename)
            contents = await profile_picture.read()
            default_image = 0
            save_path = os.path.join("/app/images/uploads", profile_picture.filename)
            
            with open(save_path, "wb") as f:
                f.write(contents)
            
            image_url = f"/images/uploads/{profile_picture.filename}"
            
        else:
            default_image = 0
            print("→ Nessuna modifica all'immagine")

        if birthdate != "":
            birthdate_struct = time.strptime(birthdate, "%Y-%m-%d")
            birthdate = time.strftime("%d %B %Y", birthdate_struct).lower()

        if selected_avatar_id:
            selected_avatar_id = (token_map[selected_avatar_id]["id"])
        else:
            selected_avatar_id = ""

        # 1. Invia i dati testuali a un API esterna
        profile_data = {
            "name": first_name,
            "surname": last_name,
            "username": username,
            "bio": bio,
            "location": location,
            "website": website,
            "birthday": birthdate,
            "reset_profile_picture" : str(default_image),
            "new_image_url" : image_url, 
            "new_avatar" : selected_avatar_id,
            "new_title" : token_map[profile_title]["id"]
        }

        async with httpx.AsyncClient(timeout = 60.0) as client:
            headers = {"x-api-key": SECRET_KEY, "user-id": str(request.session["user_id"])}
            resp_data = await client.post(f"{API_BASE_URL}/edit_profile", json=profile_data, headers= headers)
            resp_data.raise_for_status()
            result = resp_data.json()
            print(result)
            if result["status"] == False and result["warning"] == "Username already in use!":
                print("STAMPO ERRORE")
                raise HTTPException(status_code=400, detail="Username already in use!", headers={"X-Custom-Error": "UsernameTaken"}) #ritorna alla pagina di modifica profilo? in qualche modo 
            
            

    return 

@app.get("/setting_page")
async def get_setting_page(request: Request):
    """API per il redirect alla pagina di settings"""


    if "user_id" not in request.session:
        return RedirectResponse(url="/signin", status_code=303)
    else:
        request.session["last_active"] = time.time()
        active_users[request.session["user_id"]] = time.time()

        request.session["last_visited"] = request.session.get("form_origin", "home")
        request.session["form_origin"] = "setting_page"
        headers = {"x-api-key": SECRET_KEY, "user-id": str(request.session["user_id"])}
        async with httpx.AsyncClient(timeout = 60.0) as client:
            response = await client.get(f"{API_BASE_URL}/get_setting_info", headers= headers)
            response.raise_for_status()
            result = response.json()

        if result['email_notification'] == '0':
            result["email_notification"] = 'false'
        else:
            result["email_notification"] = 'true'

        return templates.TemplateResponse("settings.html", {"request" : request, "setting_info" : result})
    

@app.post("/change_email_notifications")
async def change_email_notification(request: Request):
    """API per cambiare la scelta di notifiche su mail"""


    if "user_id" not in request.session:
        return RedirectResponse(url="/signin", status_code=303)
    else:
        request.session["last_active"] = time.time()
        active_users[request.session["user_id"]] = time.time()

        headers = {"x-api-key": SECRET_KEY, "user-id": str(request.session["user_id"])}
        async with httpx.AsyncClient(timeout = 60.0) as client:
            response = await client.post(f"{API_BASE_URL}/change_email_notifications", headers= headers)
            response.raise_for_status()
            result = response.json()
        if result["status"] == True:
            return JSONResponse(status_code = 200, content = result["warning"])
        else:
            return JSONResponse(status_code = 400, content = result["warning"])
        



@app.post("/change_password")
async def change_password(request: Request, current_password: str = Form(...), new_password: str = Form(...), confirm_password: str = Form(...)):
    """API per il cambio password"""


    if "user_id" not in request.session:
        return RedirectResponse(url="/signin", status_code=303)
    else:

        request.session["last_active"] = time.time()
        active_users[request.session["user_id"]] = time.time()

        if new_password != confirm_password:
            return JSONResponse(status_code=400, content={"error": "Le password non coincidono"})
        
        change_password_json = {"current_password" : current_password, "new_password" : new_password}
        async with httpx.AsyncClient(timeout = 60.0) as client:
            headers = {"x-api-key": SECRET_KEY, "user-id": str(request.session["user_id"])}
            response = await client.post(f"{API_BASE_URL}/change_password", json = change_password_json, headers = headers)
            response.raise_for_status()
            result = response.json()
            if result["status"] == True:
                return JSONResponse(status_code = 200, content = result["warning"])
            else:
                return JSONResponse(status_code = 400, content = result["warning"])

@app.post("/change_phone")
async def change_phone(request: Request, phone_number: str = Form(...)):
    """API per il cambio numero di telefono"""


    if "user_id" not in request.session:
        return RedirectResponse(url="/signin", status_code=303)
    else:

        request.session["last_active"] = time.time()
        active_users[request.session["user_id"]] = time.time()
        phone_json = {"phone_number" : phone_number}
        async with httpx.AsyncClient(timeout = 60.0) as client:
            headers = {"x-api-key": SECRET_KEY, "user-id": str(request.session["user_id"])}
            response = await client.post(f"{API_BASE_URL}/change_phone", json = phone_json, headers = headers)
            response.raise_for_status()
            result = response.json()
            if result["status"] == True:
                return JSONResponse(status_code = 200, content = result["warning"])
            else:
                return JSONResponse(status_code = 400, content = result["warning"])



@app.post("/delete_account")
async def delete_account(request: Request):
    """API per l'eliminazione dell'account dal db"""


    if "user_id" not in request.session:
        return RedirectResponse(url="/signin", status_code=303)
    else:
        async with httpx.AsyncClient(timeout = 60.0) as client:
            headers = {"x-api-key": SECRET_KEY, "user-id": str(request.session["user_id"])}
            response = await client.post(f"{API_BASE_URL}/delete_user", headers = headers)
            response.raise_for_status()
            result = response.json()

        del active_users[request.session["user_id"]]
        request.session.clear()
        return RedirectResponse(url="/", status_code=303)       




@app.get("/last_visited")
async def get_last_visited(request: Request):
    """API per il back page"""


    if "user_id" not in request.session:
        return RedirectResponse(url="/signin", status_code=303)
    else:
        request.session["last_active"] = time.time()
        active_users[request.session["user_id"]] = time.time()
        last_visited = request.session.get("last_visited", "home")
        return RedirectResponse(url=f"/{last_visited}", status_code=303)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8001)
