# ==============================================================================
# IMPORTS ET DÉFINITION DE L'ÉTAT (AgentState)
# ==============================================================================
import time
from typing import TypedDict
from docx import Document
from langgraph.graph import END, StateGraph
from pypdf import PdfReader
import requests

# Variable globale pour la mémoire longue (Doc 4, Partie 1 & 2)
historique = ""


class AgentState(TypedDict):
    """Structure de l'état utilisé par les nœuds du graph."""

    question: str
    reponse: str
    type_question: str


# ==============================================================================
# Outils API OLLAMA (Doc 1 - Étape 13 / Doc 2 - Étape 16 / Doc 3 - Étape 33)
# ==============================================================================


def llm_local(prompt):
    """Envoie un prompt à Phi-3 (ou un autre modèle local) via Ollama et renvoie sa réponse."""
    url = "http://localhost:11434/api/generate"
    data = {"model": "phi3", "prompt": prompt, "stream": False}
    response = requests.post(url, json=data)
    return response.json()["response"]


# ==============================================================================
# FONCTIONS DE LECTURE DE FICHIERS (PDF, DOCX, TXT)
# ==============================================================================

# ------------------------------------------------------------------------------
# ANCIENNES VERSIONS (Jour 7) - COMMENTÉES
# ------------------------------------------------------------------------------
# def pdf_reader(chemin_fichier):
#     """Extrait le texte d'un fichier PDF page par page."""
#     lecteur = PdfReader(chemin_fichier)
#     contenu = ""
#     for page in lecteur.pages:
#         contenu += page.extract_text() or ""
#     return contenu

# def docx_reader(chemin_fichier):
#     """Extrait le texte d'un fichier DOCX paragraphe par paragraphe."""
#     doc = Document(chemin_fichier)
#     contenu = ""
#     for paragraphe in doc.paragraphs:
#         contenu += paragraphe.text + "\n"
#     return contenu

# def txt_reader(chemin_fichier):
#     """Lit le contenu complet d'un fichier texte (.txt)."""
#     with open(chemin_fichier, "r", encoding="utf-8") as fichier:
#         contenu = fichier.read()
#     return contenu


# ------------------------------------------------------------------------------
# NOUVELLES VERSIONS AVEC GESTION DES ERREURS (Doc 4 - Partie 3)
# ------------------------------------------------------------------------------
def pdf_reader(chemin_fichier):
    """Extrait le texte d'un PDF avec gestion des erreurs (fichier introuvable)."""
    try:
        lecteur = PdfReader(chemin_fichier)
        contenu = ""
        for page in lecteur.pages:
            contenu += page.extract_text() or ""
        return contenu
    except:
        return "Fichier introuvable."


def docx_reader(chemin_fichier):
    """Extrait le texte d'un DOCX avec gestion des erreurs (fichier introuvable)."""
    try:
        doc = Document(chemin_fichier)
        contenu = ""
        for paragraphe in doc.paragraphs:
            contenu += paragraphe.text + "\n"
        return contenu
    except:
        return "Fichier introuvable."


def txt_reader(chemin_fichier):
    """Lit un fichier TXT avec gestion des erreurs (fichier introuvable)."""
    try:
        with open(chemin_fichier, "r", encoding="utf-8") as fichier:
            return fichier.read()
    except:
        return "Fichier introuvable."


# ==============================================================================
# NŒUD D'ANALYSE ET NŒUD DE RÉPONSE GÉNÉRIQUE
# ==============================================================================

# ------------------------------------------------------------------------------
# ANCIENNE VERSION (Jour 6) - COMMENTÉE
# ------------------------------------------------------------------------------
# def analyse_node(state):
#     """Affiche le message d'analyse de la question."""
#     print("Analyse de la question...")
#     return state


# ------------------------------------------------------------------------------
# NOUVELLE VERSION AVEC LOG (Doc 4 - Étape 43)
# ------------------------------------------------------------------------------
def analyse_node(state):
    """Affiche un log indiquant qu'une question a été reçue."""
    question = state["question"]
    print("[LOG] Question reçue:", question)
    return state


# ------------------------------------------------------------------------------
# ANCIENNES VERSIONS DOCUMENTATION NODE - COMMENTÉES
# ------------------------------------------------------------------------------
# def reponse_node(state):
#     """Formate une réponse générique en répétant la question."""
#     question = state["question"]
#     state["reponse"] = f"Votre question est : {question}"
#     return state

# def documentation_node(state):
#     """Ancienne version statique (Jour 6)."""
#     state["reponse"] = "Réponse documentaire"
#     return state

# def documentation_node(state):
#     """Version interrogeant Phi-3 sans historique (Doc 2 - Étape 18)."""
#     question = state["question"]
#     prompt = f"Réponds à cette question :\n{question}"
#     reponse = llm_local(prompt)
#     state["reponse"] = reponse
#     return state


# ------------------------------------------------------------------------------
# NOUVELLE VERSION AVEC HISTORIQUE (Doc 4 - Étape 37)
# ------------------------------------------------------------------------------
def documentation_node(state):
    """Interroge le LLM en utilisant l'historique et la question."""
    question = state["question"]
    prompt = f"""Historique:
{historique}

Question:
{question}

Réponse:
"""
    reponse = llm_local(prompt)
    state["reponse"] = reponse
    return state


# ==============================================================================
# NŒUDS DE TRAITEMENT SPÉCIFIQUES (Calcul, Doc, Salutation, Lecteurs)
# ==============================================================================


def calculatrice_node(state):
    """Traite les demandes de calcul en évaluant l'expression mathématique."""
    question = state["question"]
    try:
        # Nettoyage pour ne garder que l'expression numérique
        expression = "".join(c for c in question if c in "0123456789+-*/.()")
        resultat = eval(expression)
        state["reponse"] = str(resultat)
    except Exception:
        state["reponse"] = "Calcul impossible"
    return state


def greeting_node(state):
    """Traite les salutations."""
    state["reponse"] = "Bonjour ! Comment puis-je vous aider ?"
    return state


# ------------------------------------------------------------------------------
# ANCIENNES VERSIONS DES LECTEURS EN tant QUE NŒUDS - COMMENTÉES
# ------------------------------------------------------------------------------
# def txt_reader_node(state):
#     """Ancienne version (Jour 7) - Renvoie le contenu brut."""
#     contenu = txt_reader("documents/rh.txt")
#     state["reponse"] = contenu
#     return state

# def pdf_reader_node(state):
#     """Ancienne version (Jour 7) - Renvoie le contenu brut."""
#     contenu = pdf_reader("documents/formation.pdf")
#     state["reponse"] = contenu
#     return state

# def docx_reader_node(state):
#     """Ancienne version (Jour 7) - Renvoie le contenu brut."""
#     contenu = docx_reader("documents/procedure.docx")
#     state["reponse"] = contenu
#     return state

# def txt_reader_node(state):
#     """Version Doc 2 - Sans Historique."""
#     contenu = txt_reader("documents/rh.txt")
#     question = state["question"]
#     prompt = f"Contexte:\n{contenu}\n\nQuestion:\n{question}\n\nRéponse:"
#     state["reponse"] = llm_local(prompt)
#     return state


# ------------------------------------------------------------------------------
# NOUVELLES VERSIONS AVEC HISTORIQUE ET CONTEXTE (Doc 4 - Étapes 38 et 39)
# ------------------------------------------------------------------------------
def txt_reader_node(state):
    """Lit rh.txt, injecte l'historique + contexte documentaire et interroge Phi-3."""
    contenu = txt_reader("documents/rh.txt")
    question = state["question"]
    prompt = f"""Historique:
{historique}

Contexte:
{contenu}

Question:
{question}

Réponse:
"""
    state["reponse"] = llm_local(prompt)
    return state


def pdf_reader_node(state):
    """Lit formation.pdf, injecte l'historique + contexte documentaire et interroge Phi-3."""
    contenu = pdf_reader("documents/formation.pdf")
    question = state["question"]
    prompt = f"""Historique:
{historique}

Contexte:
{contenu}

Question:
{question}

Réponse:
"""
    state["reponse"] = llm_local(prompt)
    return state


def docx_reader_node(state):
    """Lit procedure.docx, injecte l'historique + contexte documentaire et interroge Phi-3."""
    contenu = docx_reader("documents/procedure.docx")
    question = state["question"]
    prompt = f"""Historique:
{historique}

Contexte:
{contenu}

Question:
{question}

Réponse:
"""
    state["reponse"] = llm_local(prompt)
    return state


# ==============================================================================
# DÉCISION ET ROUTAGE
# ==============================================================================

# ------------------------------------------------------------------------------
# ANCIENNE VERSION DECISION_NODE - COMMENTÉE
# ------------------------------------------------------------------------------
# def decision_node(state):
#     """Détermine la catégorie de la question selon son contenu."""
#     question = state["question"].lower()
#
#     if "bonjour" in question or "salut" in question:
#         state["type_question"] = "salutation"
#     elif any(op in question for op in ["+", "-", "*", "/"]):
#         state["type_question"] = "calcul"
#     elif ".pdf" in question or "formation" in question:
#         state["type_question"] = "pdf"
#     elif ".docx" in question or "procedure" in question:
#         state["type_question"] = "docx"
#     elif ".txt" in question or "rh" in question or "lis" in question:
#         state["type_question"] = "txt"
#     else:
#         state["type_question"] = "documentation"
#
#     return state


# ------------------------------------------------------------------------------
# NOUVELLE VERSION DECISION_NODE AVEC LOG (Doc 4 - Étape 44)
# ------------------------------------------------------------------------------
def decision_node(state):
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


def route_question(state):
    """Fonction de routage retournant le type de question défini dans l'état."""
    return state["type_question"]


# ==============================================================================
# CONSTRUCTION ET CONFIGURATION DU GRAPH (LangGraph)
# ==============================================================================

workflow = StateGraph(AgentState)

# Ajout des nœuds au graph
workflow.add_node("analyse", analyse_node)
workflow.add_node("salutation", greeting_node)
workflow.add_node("decision", decision_node)
workflow.add_node("calculatrice", calculatrice_node)
workflow.add_node("documentation", documentation_node)

workflow.add_node("txt_reader", txt_reader_node)
workflow.add_node("pdf_reader", pdf_reader_node)
workflow.add_node("docx_reader", docx_reader_node)

# Configuration du point d'entrée et liaisons
workflow.set_entry_point("analyse")
workflow.add_edge("analyse", "decision")

# Routage conditionnel depuis la décision
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

# Arrivées à la fin du graph (END)
workflow.add_edge("documentation", END)
workflow.add_edge("calculatrice", END)
workflow.add_edge("salutation", END)
workflow.add_edge("txt_reader", END)
workflow.add_edge("pdf_reader", END)
workflow.add_edge("docx_reader", END)

# Compilation du workflow
agent = workflow.compile()


# ==============================================================================
# EXECUTION ET TESTS (Doc 4 - Partie 9 : Campagne de Tests Consolidée)
# ==============================================================================

if __name__ == "__main__":
    # Liste de questions de test incluant cas d'erreur / réels
    questions = [
        "",  # Test Cas 1: Question vide
        "Quels sont les congés ?",
        "Lis formation.pdf",
        "50+20",
        "Lis procedure.docx",
    ]

    memoire = []

    for question in questions:
        # Contrôle question vide (Doc 4 - Étape 40)
        if question == "":
            print("Veuillez saisir une question.")
            print("-------------")
            continue

        # Reconstruction dynamique de l'historique via variable globale (Doc 4 - Étape 36)
        historique = "\n".join(memoire)

        # Mesure du temps d'exécution (Doc 4 - Étape 47)
        debut = time.time()
        resultat = agent.invoke({"question": question})
        fin = time.time()

        reponse = resultat["reponse"]

        # Mise à jour de la mémoire longue (Doc 4 - Étape 35)
        memoire.append(f"Utilisateur: {question}")
        memoire.append(f"Assistant: {reponse}")

        print("Réponse :", reponse)
        print("[LOG] Réponse générée")
        print("Temps :", fin - debut, "secondes")
        print("-------------")
