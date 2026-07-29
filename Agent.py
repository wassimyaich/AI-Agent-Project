# ==============================================================================
# IMPORTS ET DÉFINITION DE L'ÉTAT (AgentState)
# ==============================================================================
from typing import TypedDict
from pypdf import PdfReader
from docx import Document
from langgraph.graph import StateGraph, END


class AgentState(TypedDict):
    """Structure de l'état utilisé par les nœuds du graph."""
    question: str
    reponse: str
    type_question: str


# ==============================================================================
# FONCTIONS DE LECTURE DE FICHIERS (PDF, DOCX, TXT)
# ==============================================================================

def pdf_reader(chemin_fichier):
    """Extrait le texte d'un fichier PDF page par page."""
    lecteur = PdfReader(chemin_fichier)
    contenu = ""
    for page in lecteur.pages:
        contenu += page.extract_text() or ""
    return contenu


def docx_reader(chemin_fichier):
    """Extrait le texte d'un fichier DOCX paragraphe par paragraphe."""
    doc = Document(chemin_fichier)
    contenu = ""
    for paragraphe in doc.paragraphs:
        contenu += paragraphe.text + "\n"
    return contenu


def txt_reader(chemin_fichier):
    """Lit le contenu complet d'un fichier texte (.txt)."""
    with open(chemin_fichier, "r", encoding="utf-8") as fichier:
        contenu = fichier.read()
    return contenu


# ==============================================================================
# NŒUD D'ANALYSE ET NŒUD DE RÉPONSE GÉNÉRIQUE
# ==============================================================================

def analyse_node(state):
    """Affiche le message d'analyse de la question."""
    print("Analyse de la question...")
    return state


def reponse_node(state):
    """Formate une réponse générique en répétant la question."""
    question = state["question"]
    state["reponse"] = f"Votre question est : {question}"
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


def documentation_node(state):
    """Traite les demandes d'information sur la documentation."""
    state["reponse"] = "Réponse documentaire"
    return state


def greeting_node(state):
    """Traite les salutations."""
    state["reponse"] = "Bonjour ! Comment puis-je vous aider ?"
    return state


def txt_reader_node(state):
    """Nœud pour lire le fichier RH au format TXT."""
    contenu = txt_reader("documents/rh.txt")
    state["reponse"] = contenu
    return state


def pdf_reader_node(state):
    """Nœud pour lire le fichier de formation au format PDF."""
    contenu = pdf_reader("documents/formation.pdf")
    state["reponse"] = contenu
    return state


def docx_reader_node(state):
    """Nœud pour lire le fichier de procédure au format DOCX."""
    contenu = docx_reader("documents/procedure.docx")
    state["reponse"] = contenu
    return state


# ==============================================================================
# DÉCISION ET ROUTAGE
# ==============================================================================

def decision_node(state):
    """Détermine la catégorie de la question selon son contenu."""
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
workflow.add_node("reponse", reponse_node)
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
        "documentation": "documentation"
    }
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
# EXECUTION ET TESTS
# ==============================================================================

if __name__ == "__main__":
    # Test 1 : Fichier TXT via mot-clé "RH"
    res1 = agent.invoke({"question": "Lis le fichier RH ?"})
    print("Test TXT       :", res1["reponse"])

    # Test 2 : Calcul
    res2 = agent.invoke({"question": "50+25"})
    print("Test Calcul    :", res2["reponse"])  # Affiche '75'

    # Test 3 : PDF
    res3 = agent.invoke({"question": "Lis formation.pdf"})
    print("Test PDF       :", res3["reponse"])

    # Test 4 : DOCX
    res4 = agent.invoke({"question": "Lis procedure.docx"})
    print("Test DOCX      :", res4["reponse"])

    # Test 5 : Salutation
    res5 = agent.invoke({"question": "Bonjour"})
    print("Test Salutation:", res5["reponse"])