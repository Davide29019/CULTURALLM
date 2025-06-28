
import mariadb
import requests

from typing import Any
from fastapi import FastAPI
from contextlib import asynccontextmanager

from json_classes import QuestionInput, AnswerInput, ValidateInput, LoginInput, SignUpInput, BooleanResponse, CreateQuestionResponse
from utils.query_execute import execute_select
from utils.query_execute import execute_modify
from utils.connection import Connection
from utils.sign_up import sign_up_op, check_sign_up
from utils.sign_in import check_password

async def lifespan(app: FastAPI):
    """All'avvio dell'applicazione inizializza la connessione con il db, e la chiude in chiusura dell'app"""
    
    Connection.start_connection()       # Inizializza la connessione
    global connection
    connection = Connection.get_connection()
    if connection is None:
        raise RuntimeError("Impossibile connettersi al database durante l'avvio")
    
    for i in range(0,50):
        try:
            response = requests.get("http://ollama:11434/api/tags")             # Funzione sincrona, se bisogna fare altre operazioni asincrone dopo bisogna cambiarla
            if response.status_code == 200:
                    print("Ollama è pronto")
                    break
        except requests.RequestException:
            pass
    yield  # Periodo in cui applicazione è attiva

    
    try:   # Chiusura della connessione
        connection.close()
    except Exception as e:
        print("Errore durante la chiusura della connessione:", e)




app = FastAPI(title = "CulturaLLM",lifespan=lifespan)

connection: mariadb.Connection = None




@app.post("/login")
def login(login_json: LoginInput) -> BooleanResponse:
    """API per il login"""
    
    username_query = "select password, salt from user where email=?"
    try:
        result:list[tuple[str]] = execute_select(connection, username_query, (login_json.email,))
    except mariadb.Error as e:
        print("Errore nella Login select")
    if len(result) == 0:
        return BooleanResponse(status=False, warning="")
    password = result[0][0]
    salt:str = result[0][1]
    return BooleanResponse(status = check_password(password, login_json.password, salt), warning = "")


@app.post("/sign_up")
def sign_up(sign_up_json: SignUpInput) -> BooleanResponse:
    """API per la registrazione"""
    if check_sign_up(sign_up_json.email, connection):      
        return BooleanResponse(status = False, warning = "email già in uso")
      
    if check_sign_up(sign_up_json.username, connection):      
        return BooleanResponse(status = False, warning = "username già in uso")

    return BooleanResponse(status = sign_up_op(sign_up_json.password, sign_up_json.username, sign_up_json.email, connection), warning = "")
    



@app.post("/question")
def question(question_json: QuestionInput) -> CreateQuestionResponse:
    question = question_json.question
    try:
        if question_json.llm == False:
            id_query = "select user_id from user where username=?"
            id = execute_select(connection, id_query, (question_json.username,))
            id = int(id[0][0]) 
            question_query = "insert into question(question_text, created_by_user_id) values (?, ?)"
        else:
            ollama_request: dict[str,Any] = {                                       # PER OLLAMA
            "model" : question_json.username,
            "messages": [{ "role": "user", "content": f"Genera una nuova domanda specificamente culturale sul tema:{question_json.theme} per la cultura italiana. Genera solamente la domanda senza altro testo inutile." }],
            "stream": False
        }
            response = requests.post("http://ollama:11434/api/chat", json=ollama_request)
            response.raise_for_status()
            result = response.json()
            question = result["message"]["content"]
            id_query = "select llm_id from llm where name=?"
            id = execute_select(connection, id_query, (question_json.username,))
            id = int(id[0][0]) 
            question_query = "insert into question(question_text, created_by_llm_id) values (?, ?)"
        execute_modify(connection, question_query, (question, id))  
        """
        DA FARE UN CICLO CHE AGGIUNGE PER OGNI TEMA

        question_id_query = "select question_id from question where question_text=?"
        question_id = execute_select(connection, question_id_query, (question,))
        question_id = question_id[0][0]
        theme_id_query = "select theme_id from theme where name=?"
        theme_id = execute_select(connection, theme_id_query, (question_json.theme,))
        theme_id = theme_id[0][0]
        question_theme_query = "insert into question_theme (question_id, theme_id) values (?, ?)"
        execute_modify(connection, question_theme_query, (question_id, theme_id,))
        """
    

        ollama_request: dict[str,Any] = {                                       # PER OLLAMA
                "model" : question_json.answering_llm,
                "messages": [{ "role": "user", "content": f"{question} Rispondi in maniera concisa e come farebbe un umano." }],
                "stream": False
            }
        response = requests.post("http://ollama:11434/api/chat", json=ollama_request)
        response.raise_for_status()
        result = response.json()
        llm_answer = result["message"]["content"]

        if question_json.llm == False:
            question_id_query = "select question_id from question where question_text=? and created_by_user_id=?"
            result = execute_select(connection, question_id_query, (question, id))
            question_id = result[0][0]
            answer_query = "insert into answer (user_id, answer_text, question_id) values (?,?,?)"
            execute_modify(connection, answer_query,(id, llm_answer, question_id))
        else:
            question_id_query = "select question_id from question where question_text=? and created_by_llm_id=?"
            result = execute_select(connection, question_id_query, (question, id))
            question_id = result[0][0]
            answer_query = "insert into answer (llm_id, answer_text, question_id) values (?,?,?)"
            execute_modify(connection, answer_query,(id, llm_answer, question_id))
        return CreateQuestionResponse(answer = llm_answer, question = question)
    except mariadb.Error as e:
        print("Errore mariadb in creazione question: ",e)
    except requests.RequestException as e:
        print("Errore nella API:", e)


@app.post("/answer")
def answer(answer_json: AnswerInput) -> str:
    return


@app.post("/validate")
def validate(ranking_json: ValidateInput) -> bool:
    return


@app.post("/get_something")
def get_something(item: str, order_by: str) -> list[tuple[str]]:
    query = f"select * from {item}"
    try:
        return execute_select(connection, query)
    except mariadb.Error as e:
        print("Errore nella get_questions", e)
        raise e


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)

