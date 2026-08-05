# ==============================================================================
# IMPORTS ET DÉFINITION DE L'ÉTAT (AgentState)
# ==============================================================================
import ast
import operator
import os
import time
from typing import TypedDict
from docx import Document
from langgraph.graph import END, StateGraph
from pypdf import PdfReader
import requests

# Chemins absolus basés sur l'emplacement du fichier Agent.py
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOCS_DIR = os.path.join(BASE_DIR, "documents")

FILE_NOT_FOUND_MSG = "Fichier introuvable."
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "localhost")
OLLAMA_SCHEME = os.getenv("OLLAMA_SCHEME", "http")
OLLAMA_URL = f"{OLLAMA_SCHEME}://{OLLAMA_HOST}:11434/api/generate"

OPERATEURS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.USub: operator.neg,
}

historique = ""


class AgentState(TypedDict):
    """Structure de l'état utilisé par les nœuds du graph."""

    question: str
    reponse: str
    type_question: str


# ==============================================================================
# Outils API OLLAMA & CALCUL SÉCURISÉ
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


def safe_eval(node):
    """Évalue récursivement les opérations mathématiques basiques de façon sécurisée."""
    if isinstance(node, ast.Expression):
        return safe_eval(node.body)
    elif isinstance(node, ast.Constant):
        return node.value
    elif isinstance(node, ast.BinOp):
        left = safe_eval(node.left)
        right = safe_eval(node.right)
        return OPERATEURS[type(node.op)](left, right)
    elif isinstance(node, ast.UnaryOp):
        operand = safe_eval(node.operand)
        return OPERATEURS[type(node.op)](operand)
    else:
        raise ValueError("Expression non autorisée")


# ==============================================================================
# FONCTIONS DE LECTURE DE FICHIERS (PDF, DOCX, TXT)
# ==============================================================================
def pdf_reader(nom_fichier: str) -> str:
    """Extrait le texte d'un PDF à partir du dossier documents."""
    chemin = os.path.join(DOCS_DIR, nom_fichier)
    try:
        lecteur = PdfReader(chemin)
        contenu = "".join([page.extract_text() or "" for page in lecteur.pages]).strip()
        print(
            f"[LOG FILE] PDF '{nom_fichier}' lu avec succès ({len(contenu)} caractères)."
        )
        return contenu if contenu else FILE_NOT_FOUND_MSG
    except Exception as err:
        print(f"[LOG ERROR] Impossible de lire le PDF ({chemin}): {err}")
        return FILE_NOT_FOUND_MSG


def docx_reader(nom_fichier: str) -> str:
    """Extrait le texte d'un DOCX à partir du dossier documents."""
    chemin = os.path.join(DOCS_DIR, nom_fichier)
    try:
        doc = Document(chemin)
        contenu = "\n".join([p.text for p in doc.paragraphs if p.text.strip()]).strip()
        print(
            f"[LOG FILE] DOCX '{nom_fichier}' lu avec succès ({len(contenu)} caractères)."
        )
        return contenu if contenu else FILE_NOT_FOUND_MSG
    except Exception as err:
        print(f"[LOG ERROR] Impossible de lire le DOCX ({chemin}): {err}")
        return FILE_NOT_FOUND_MSG


def txt_reader(nom_fichier: str) -> str:
    """Lit un fichier TXT à partir du dossier documents."""
    chemin = os.path.join(DOCS_DIR, nom_fichier)
    try:
        with open(chemin, "r", encoding="utf-8") as fichier:
            contenu = fichier.read().strip()
            print(
                f"[LOG FILE] TXT '{nom_fichier}' lu avec succès ({len(contenu)} caractères)."
            )
            return contenu if contenu else FILE_NOT_FOUND_MSG
    except Exception as err:
        print(f"[LOG ERROR] Impossible de lire le TXT ({chemin}): {err}")
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
    """Traite les demandes de calcul via l'analyseur AST sécurisé."""
    question = state["question"]
    try:
        expression = "".join(c for c in question if c in "0123456789+-*/.()")
        tree = ast.parse(expression, mode="eval")
        resultat = safe_eval(tree)
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
    """Lit rh.txt (ou reglement.txt), injecte le contenu et interroge Ollama."""
    nom = (
        "reglement.txt"
        if os.path.exists(os.path.join(DOCS_DIR, "reglement.txt"))
        else "rh.txt"
    )
    contenu = txt_reader(nom)
    if contenu == FILE_NOT_FOUND_MSG:
        state["reponse"] = (
            f"Erreur : Le fichier TXT ({nom}) est introuvable dans {DOCS_DIR}."
        )
        return state
    question = state["question"]
    prompt = f"Réponds précisément à la question en utilisant le document suivant.\n\nDocument:\n{contenu}\n\nQuestion:\n{question}\n\nRéponse:"
    state["reponse"] = llm_local(prompt)
    return state


def pdf_reader_node(state: AgentState) -> AgentState:
    """Lit formation.pdf, injecte le contenu et interroge Ollama."""
    contenu = pdf_reader("formation.pdf")
    if contenu == FILE_NOT_FOUND_MSG:
        state["reponse"] = (
            f"Erreur : Le fichier formation.pdf est introuvable ou vide dans {DOCS_DIR}."
        )
        return state
    question = state["question"]
    prompt = f"Réponds précisément à la question en utilisant le document suivant.\n\nDocument:\n{contenu}\n\nQuestion:\n{question}\n\nRéponse:"
    state["reponse"] = llm_local(prompt)
    return state


def docx_reader_node(state: AgentState) -> AgentState:
    """Lit procedure.docx, injecte le contenu et interroge Ollama."""
    contenu = docx_reader("procedure.docx")
    if contenu == FILE_NOT_FOUND_MSG:
        state["reponse"] = (
            f"Erreur : Le fichier procedure.docx est introuvable ou vide dans {DOCS_DIR}."
        )
        return state
    question = state["question"]
    prompt = f"Réponds précisément à la question en utilisant le document suivant.\n\nDocument:\n{contenu}\n\nQuestion:\n{question}\n\nRéponse:"
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
    elif (
        ".txt" in question
        or "rh" in question
        or "reglement" in question
        or "lis" in question
    ):
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
