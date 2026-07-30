from fastapi import FastAPI
from Agent import agent
from pydantic import BaseModel

app = FastAPI()


@app.get("/")
def accueil():
    return {"message": "Bienvenue dans l'Agent IA"}


@app.get("/bonjour")
def bonjour():
    return {"message": "Bonjour"}


@app.get("/status")
def status():
    return {"status": "OK"}


@app.get("/info")
def info():
    return {"application": "Agent IA", "version": "1.0"}


@app.get("/utilisateur/{nom}")
def utilisateur(nom):
    return {"message": f"Bonjour {nom}"}


class QuestionRequest(BaseModel):
    question: str


# Déclarer la route /question
# @app.post(
#     "/question"
# )  # d'envoyer des données ( GET/POST et non simplement de consulter.
# def poser_question(request: QuestionRequest):
#     #  pass
#     resultat = agent.invoke({"question": request.question})
#     return resultat


@app.get("/status")
def status():
    return {"etat": "OK"}


@app.post("/question")
def poser_question(request: QuestionRequest):
    try:
        resultat = agent.invoke({"question": request.question})
        return {"reponse": resultat["reponse"]}
    except Exception as e:
        return {"erreur": str(e)}
