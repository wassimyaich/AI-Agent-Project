# ==============================================================================
# IMPORTS ET DÉFINITION DE L'ÉTAT (AgentState)
# ==============================================================================
import os
import time
from typing import TypedDict
from docx import Document
from langgraph.graph import END, StateGraph
from pypdf import PdfReader
import requests

# Constantes pour éviter les duplications et sécuriser le code
FILE_NOT_FOUND_MSG = "Fichier introuvable."
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "localhost")
OLLAMA_SCHEME = os.getenv("OLLAMA_SCHEME", "http")
OLLAMA_URL = f"{OLLAMA_SCHEME}://{OLLAMA_HOST}:11434/api/generate"

# Variable globale pour la mémoire longue
historique = ""


class AgentState(TypedDict):
    """Structure de l'état utilisé par les nœuds du graph."""

    question: str
    reponse: str
    type_question: str


# ==============================================================================
# Outils API OLLAMA
# ==============================================================================
def llm_local(prompt: str) -> str:
    """Envoie un prompt au modèle local via Ollama et renvoie sa réponse."""
    data = {"model": "gemma", "prompt": prompt, "stream": False}
    try:
        response = requests.post(OLLAMA_URL, json=data, timeout=30)
        response.raise_for_status()
        return response.json().get("response", "")
    except requests.RequestException as err:
        print(f"[LOG ERROR] Échec de la connexion à Ollama: {err}")
        return "Erreur lors de la communication avec le modèle AI."


# ==============================================================================
# FONCTIONS DE LECTURE DE FICHIERS (PDF, DOCX, TXT)
# ==============================================================================
def pdf_reader(chemin_fichier: str) -> str:
    """Extrait le texte d'un PDF avec gestion explicite des exceptions."""
    try:
        lecteur = PdfReader(chemin_fichier)
        contenu = ""
        for page in lecteur.pages:
            contenu += page.extract_text() or ""
        return contenu
    except (FileNotFoundError, Exception) as err:
        print(f"[LOG ERROR] Erreur lecture PDF ({chemin_fichier}): {err}")
        return FILE_NOT_FOUND_MSG


def docx_reader(chemin_fichier: str) -> str:
    """Extrait le texte d'un DOCX avec gestion explicite des exceptions."""
    try:
        doc = Document(chemin_fichier)
        contenu = ""
        for paragraphe in doc.paragraphs:
            contenu += paragraphe.text + "\n"
        return contenu
    except (FileNotFoundError, Exception) as err:
        print(f"[LOG ERROR] Erreur lecture DOCX ({chemin_fichier}): {err}")
        return FILE_NOT_FOUND_MSG


def txt_reader(chemin_fichier: str) -> str:
    """Lit un fichier TXT avec gestion explicite des exceptions."""
    try:
        with open(chemin_fichier, "r", encoding="utf-8") as fichier:
            return fichier.read()
    except (FileNotFoundError, Exception) as err:
        print(f"[LOG ERROR] Erreur lecture TXT ({chemin_fichier}): {err}")
        return FILE_NOT_FOUND_MSG


# ==============================================================================
# NŒUD D'ANALYSE ET NŒUD DE RÉPONSE GÉNÉRIQUE
# ==============================================================================
def analyse_node(state: AgentState) -> AgentState:
    """Affiche un log indiquant qu'une question a été reçue."""
    question = state["question"]
    print("[LOG] Question reçue:", question)
    return state


def documentation_node(state: AgentState) -> AgentState:
    """Interroge le LLM en utilisant l'historique et la question."""
    question = state["question"]
    prompt = f"Historique:\n{historique}\n\nQuestion:\n{question}\n\nRéponse:\n"
    state["reponse"] = llm_local(prompt)
    return state


# ==============================================================================
# NŒUDS DE TRAITEMENT SPÉCIFIQUES
# ==============================================================================
def calculatrice_node(state: AgentState) -> AgentState:
    """Traite les demandes de calcul en évaluant l'expression mathématique."""
    question = state["question"]
    try:
        expression = "".join(c for c in question if c in "0123456789+-*/.()")
        resultat = eval(expression)  # pylint: disable=eval-used
        state["reponse"] = str(resultat)
    except Exception as err:
        print(f"[LOG ERROR] Calcul impossible: {err}")
        state["reponse"] = "Calcul impossible"
    return state


def greeting_node(state: AgentState) -> AgentState:
    """Traite les salutations."""
    state["reponse"] = "Bonjour ! Comment puis-je vous aider ?"
    return state


def txt_reader_node(state: AgentState) -> AgentState:
    """Lit rh.txt, injecte l'historique + contexte et interroge Ollama."""
    contenu = txt_reader("documents/rh.txt")
    question = state["question"]
    prompt = f"Historique:\n{historique}\n\nContexte:\n{contenu}\n\nQuestion:\n{question}\n\nRéponse:\n"
    state["reponse"] = llm_local(prompt)
    return state


def pdf_reader_node(state: AgentState) -> AgentState:
    """Lit formation.pdf, injecte l'historique + contexte et interroge Ollama."""
    contenu = pdf_reader("documents/formation.pdf")
    question = state["question"]
    prompt = f"Historique:\n{historique}\n\nContexte:\n{contenu}\n\nQuestion:\n{question}\n\nRéponse:\n"
    state["reponse"] = llm_local(prompt)
    return state


def docx_reader_node(state: AgentState) -> AgentState:
    """Lit procedure.docx, injecte l'historique + contexte et interroge Ollama."""
    contenu = docx_reader("documents/procedure.docx")
    question = state["question"]
    prompt = f"Historique:\n{historique}\n\nContexte:\n{contenu}\n\nQuestion:\n{question}\n\nRéponse:\n"
    state["reponse"] = llm_local(prompt)
    return state


# ==============================================================================
# DÉCISION ET ROUTAGE
# ==============================================================================
def decision_node(state: AgentState) -> AgentState:
    """Détermine le type de question et ajoute un log pour tracer la décision."""
    question = state["question"].lower()

    if "bonjour" in question or "salut" in question:
        state["type_question"] = "salutation"
    elif any(op in question for op in ["+", "-", "*", "/"]):
        state["type_question"] = "calcul"
    elif ".pdf" in question or "formation" in question:
        state["type_question"] = "pdf"
    elif ".docx" in question or "procedure" in question:
        state["type_question"] = "docx"
    elif ".txt" in question or "rh" in question or "lis" in question:
        state["type_question"] = "txt"
    else:
        state["type_question"] = "documentation"

    print("[LOG] Outil sélectionné:", state["type_question"])
    return state


def route_question(state: AgentState) -> str:
    """Fonction de routage retournant le type de question défini dans l'état."""
    return state["type_question"]


# ==============================================================================
# CONSTRUCTION ET CONFIGURATION DU GRAPH (LangGraph)
# ==============================================================================
workflow = StateGraph(AgentState)

workflow.add_node("analyse", analyse_node)
workflow.add_node("salutation", greeting_node)
workflow.add_node("decision", decision_node)
workflow.add_node("calculatrice", calculatrice_node)
workflow.add_node("documentation", documentation_node)

workflow.add_node("txt_reader", txt_reader_node)
workflow.add_node("pdf_reader", pdf_reader_node)
workflow.add_node("docx_reader", docx_reader_node)

workflow.set_entry_point("analyse")
workflow.add_edge("analyse", "decision")

workflow.add_conditional_edges(
    "decision",
    route_question,
    {
        "salutation": "salutation",
        "calcul": "calculatrice",
        "pdf": "pdf_reader",
        "docx": "docx_reader",
        "txt": "txt_reader",
        "documentation": "documentation",
    },
)

workflow.add_edge("documentation", END)
workflow.add_edge("calculatrice", END)
workflow.add_edge("salutation", END)
workflow.add_edge("txt_reader", END)
workflow.add_edge("pdf_reader", END)
workflow.add_edge("docx_reader", END)

agent = workflow.compile()


# ==============================================================================
# EXECUTION ET TESTS
# ==============================================================================
if __name__ == "__main__":
    memoire = []
    questions = [
        "",
        "Quels sont les congés ?",
        "Lis formation.pdf",
        "50+20",
        "Lis procedure.docx",
    ]

    for q in questions:
        if not q:
            print("Veuillez saisir une question.")
            print("-------------")
            continue

        historique = "\n".join(memoire)

        debut = time.time()
        resultat = agent.invoke({"question": q})
        fin = time.time()

        rep = resultat["reponse"]

        memoire.append(f"Utilisateur: {q}")
        memoire.append(f"Assistant: {rep}")

        print("Réponse :", rep)
        print("[LOG] Réponse générée")
        print("Temps :", fin - debut, "secondes")
        print("-------------")
