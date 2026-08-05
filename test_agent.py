import ast
from unittest.mock import patch
import pytest

from Agent import (
    safe_eval,
    decision_node,
    greeting_node,
    calculatrice_node,
    analyse_node,
    txt_reader_node,
    pdf_reader_node,
    docx_reader_node,
    documentation_node,
    AgentState,
    FILE_NOT_FOUND_MSG,
)


# ------------------------------------------------------------------------------
# TESTS MATÉMATIQUES & ÉVALUATION AST
# ------------------------------------------------------------------------------
def test_safe_eval_operations():
    assert safe_eval(ast.parse("50+20", mode="eval")) == 70
    assert safe_eval(ast.parse("100-30", mode="eval")) == 70
    assert safe_eval(ast.parse("10*5", mode="eval")) == 50
    assert safe_eval(ast.parse("20/4", mode="eval")) == 5.0
    assert safe_eval(ast.parse("-10", mode="eval")) == -10


def test_safe_eval_invalid():
    with pytest.raises(ValueError):
        safe_eval(ast.parse("import os", mode="exec"))


# ------------------------------------------------------------------------------
# TESTS DE ROUTAGE ET NŒUD DE DÉCISION
# ------------------------------------------------------------------------------
def test_decision_node():
    state_hello: AgentState = {
        "question": "Bonjour",
        "reponse": "",
        "type_question": "",
    }
    assert decision_node(state_hello)["type_question"] == "salutation"

    state_calc: AgentState = {"question": "50+20", "reponse": "", "type_question": ""}
    assert decision_node(state_calc)["type_question"] == "calcul"

    state_pdf: AgentState = {
        "question": "Lis formation.pdf",
        "reponse": "",
        "type_question": "",
    }
    assert decision_node(state_pdf)["type_question"] == "pdf"

    state_docx: AgentState = {
        "question": "Lis procedure.docx",
        "reponse": "",
        "type_question": "",
    }
    assert decision_node(state_docx)["type_question"] == "docx"

    state_txt: AgentState = {
        "question": "Lis rh.txt",
        "reponse": "",
        "type_question": "",
    }
    assert decision_node(state_txt)["type_question"] == "txt"

    state_doc: AgentState = {
        "question": "Quels sont les congés ?",
        "reponse": "",
        "type_question": "",
    }
    assert decision_node(state_doc)["type_question"] == "documentation"


# ------------------------------------------------------------------------------
# TESTS DES NŒUDS DE L'AGENT
# ------------------------------------------------------------------------------
def test_greeting_node():
    state: AgentState = {
        "question": "Bonjour",
        "reponse": "",
        "type_question": "salutation",
    }
    res = greeting_node(state)
    assert "Bonjour" in res["reponse"]


def test_analyse_node():
    state: AgentState = {"question": "Test", "reponse": "", "type_question": ""}
    res = analyse_node(state)
    assert res["question"] == "Test"


def test_calculatrice_node_success():
    state: AgentState = {"question": "50+20", "reponse": "", "type_question": "calcul"}
    res = calculatrice_node(state)
    assert res["reponse"] == "70"


def test_calculatrice_node_error():
    state: AgentState = {
        "question": "invalid",
        "reponse": "",
        "type_question": "calcul",
    }
    res = calculatrice_node(state)
    assert res["reponse"] == "Calcul impossible"


@patch("Agent.llm_local")
def test_documentation_node(mock_llm):
    mock_llm.return_value = "Les congés sont des jours de repos."
    state: AgentState = {
        "question": "Quels sont les congés ?",
        "reponse": "",
        "type_question": "documentation",
    }
    res = documentation_node(state)
    assert "congés" in res["reponse"]


# ------------------------------------------------------------------------------
# TESTS DES LECTEURS DE DOCUMENTS (MOCKÉS)
# ------------------------------------------------------------------------------
@patch("Agent.pdf_reader")
@patch("Agent.llm_local")
def test_pdf_reader_node_success(mock_llm, mock_reader):
    mock_reader.return_value = "Texte du PDF"
    mock_llm.return_value = "Résumé PDF"
    state: AgentState = {
        "question": "Lis formation.pdf",
        "reponse": "",
        "type_question": "pdf",
    }

    res = pdf_reader_node(state)
    assert res["reponse"] == "Résumé PDF"


@patch("Agent.pdf_reader")
def test_pdf_reader_node_not_found(mock_reader):
    mock_reader.return_value = FILE_NOT_FOUND_MSG
    state: AgentState = {
        "question": "Lis formation.pdf",
        "reponse": "",
        "type_question": "pdf",
    }

    res = pdf_reader_node(state)
    assert "introuvable" in res["reponse"] or "Erreur" in res["reponse"]


@patch("Agent.docx_reader")
@patch("Agent.llm_local")
def test_docx_reader_node_success(mock_llm, mock_reader):
    mock_reader.return_value = "Texte du DOCX"
    mock_llm.return_value = "Résumé DOCX"
    state: AgentState = {
        "question": "Lis procedure.docx",
        "reponse": "",
        "type_question": "docx",
    }

    res = docx_reader_node(state)
    assert res["reponse"] == "Résumé DOCX"


@patch("Agent.txt_reader")
@patch("Agent.llm_local")
def test_txt_reader_node_success(mock_llm, mock_reader):
    mock_reader.return_value = "Texte du TXT"
    mock_llm.return_value = "Résumé TXT"
    state: AgentState = {
        "question": "Lis rh.txt",
        "reponse": "",
        "type_question": "txt",
    }

    res = txt_reader_node(state)
    assert res["reponse"] == "Résumé TXT"
