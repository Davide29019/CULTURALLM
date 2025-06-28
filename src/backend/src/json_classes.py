from pydantic import BaseModel



class QuestionInput(BaseModel):
    
    question : str


    theme: list[str]

    """Username dell'utente che ha creato la domanda"""
    username: str

    """Booleano che ci dice se la domanda la ha generata la LLM"""
    llm: bool


    """modello che deve rispondere alla domanda"""
    answering_llm: str


class AnswerInput(BaseModel):

    answer: str

class ValidateInput(BaseModel):
    
    """Dizionario con chiave la posizione e come valore l'id della risposta"""
    ranking: dict[int, int]

class LoginInput(BaseModel):

    email: str
    password: str

class SignUpInput(BaseModel):

    username: str
    email: str
    password:str


class BooleanResponse(BaseModel):

    status: bool

    """stringa per riportare i casi di username già in uso o cose del genere"""
    warning: str


class CreateQuestionResponse(BaseModel):
    answer: str

    question: str