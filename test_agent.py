import pytest
from Agent import calculatrice_node, greeting_node, decision_node


def test_greeting_node():
    state = {"question": "bonjour", "reponse": "", "type_question": ""}
    result = greeting_node(state)
    assert result["reponse"] == "Bonjour ! Comment puis-je vous aider ?"


def test_calculatrice_node():
    state = {"question": "50+20", "reponse": "", "type_question": ""}
    result = calculatrice_node(state)
    assert result["reponse"] == "70"


def test_decision_node():
    state = {"question": "salut", "reponse": "", "type_question": ""}
    result = decision_node(state)
    assert result["type_question"] == "salutation"
