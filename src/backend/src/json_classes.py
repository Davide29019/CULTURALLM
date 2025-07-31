from typing import Optional, Union
from fastapi import UploadFile
from pydantic import BaseModel



class QuestionInput(BaseModel):
    
    """Testo della domanda da creare"""
    question : str

    """Lista degli id dei temi scelti"""
    theme: int

    """Booleano che ci dice se la domanda la ha generata la LLM"""
    llm: str = ""


    """modello che deve rispondere alla domanda"""
    answering_llm: str


class AnswerInput(BaseModel):

    """ID Domanda riguardante la risposta"""
    question: int

    """Testo risposta alla domanda"""
    answer: str = ""


    """LLM che deve generare la risposta se presente"""
    answering_llm: str = ""



class ValidateInput(BaseModel):
    
    """Dizionario con chiave la posizione e come valore l'id della risposta"""
    ranking: dict[int, int]

    """ID Domanda di cui fare il ranking"""
    question: int



class LoginInput(BaseModel):

    """Username/Email dell'utente"""
    user: str

    """Password per il login"""
    password: str

class SignUpInput(BaseModel):

    """Username utente"""
    username: str

    """Email utente"""
    email: str
    
    """Password utente"""
    password:str


class ReportInput(BaseModel):
    
    
    """ID Domanda riguardante il report"""
    question: int

class BooleanResponse(BaseModel):

    """Status della risposta (TRUE se andato tutto bene)"""
    status: bool

    """stringa per riportare i casi di username già in uso o cose del genere"""
    warning: str = ""


class CreateQuestionResponse(BaseModel):
    
    """Risposta della LLM riguardo la question"""
    answer: str

    """Testo domanda appena creata"""
    question: str

class HomeInfoResponse(BaseModel):

    """Top 10 contributors tra gli user"""
    contributors: dict[int,dict[str, str]]

    """Dati utente di sessione"""
    user_data: dict[str, Union[Optional[str], dict[int, dict[str, str]]]]

    """Domande settimanali"""
    weekly_question: int 

    """Domande settimanali in trend"""
    trending_question: dict[int, dict[str, Union[str, list[str]]]]

    week_themes: dict[int, dict[str, str]]


class OnlineUserResponse(BaseModel):

    """Numero di utenti online"""
    number: int

class ProfileInfoResponse(BaseModel):

    """Dati utente di sessione"""
    user_data: dict[str, Union[Optional[str], dict[int, dict[str, str]]]]

    """Ultime domande poste dall'utente"""
    user_question: dict[int, dict[str, str]]

    """Ultime risposte inviate dall'utente"""
    user_answer: dict[int, dict[str, str]]

    user_activities: dict[str, str | None]

class QuestionPageResponse(BaseModel):

    """Domande e relativi dati"""
    questions: dict[int, dict[str, Union[str, dict[int, dict[str, str]], list[str]]]]


class AnswerResponse(BaseModel):

    """ID della risposta generata"""
    answer_id: int

    """Testo della risposta generata"""
    answer_text: str


class LlmResponse(BaseModel):

    """Nomi delle LLM presenti"""
    llms: dict[int, str]

class UserMissionResponse(BaseModel):


    """Missioni utente disponibili e complete"""
    user_mission: dict[int, dict[str, str]]

    user_stats: dict[str, str]


class ProfileUpdateInput(BaseModel):

    name: str

    surname: str

    username: str

    bio: str = ""

    location: str = ""

    website: str = ""

    birthday: str = ""

    reset_profile_picture: str

    new_image_url: str

    #new_avatar_id: int

    #new_title_id: int





class CreateQuestionPageResponse(BaseModel):

    themes: dict[int, dict[str, str]]

    llms: dict[int, dict[str, str]]


class VoteInput(BaseModel):

    question_id: int


class ChangePasswordInput(BaseModel):

    current_password: str

    new_password: str

class PhoneInput(BaseModel):

    phone_number: str