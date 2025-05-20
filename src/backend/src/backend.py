import mariadb
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel


app = FastAPI(title = "CulturaLLM")


class QuestionInput(BaseModel):
    question : str


class AnswerInput(BaseModel):
    answer: str

class ValidateInput(BaseModel):
    
    """Dizionario con chiave la posizione e come valore l'id della risposta"""
    ranking: dict[int,int]



@app.post("/question")
def question(question_json: QuestionInput) -> str:
    return 


@app.post("/answer")
def answer(answer_json: AnswerInput) -> str:
    return

@app.post("/validate")
def validate(ranking_json: ValidateInput) -> bool:
    return


