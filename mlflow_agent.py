import mlflow
import time
from Agent import agent

mlflow.set_tracking_uri("sqlite:///mlflow.db")

# Nom de l'expérience dans l'UI MLflow
mlflow.set_experiment("Agent_Documentaire")


question = "Quels sont les congés ?"

debut = time.time()
resultat = agent.invoke({"question": question})
fin = time.time()

with mlflow.start_run():
    # Paramètres
    mlflow.log_param("modele", "phi3")
    mlflow.log_param("question", question)

    # Métriques
    mlflow.log_metric("temps_reponse", fin - debut)

    # Texte de réponse (Artifact/Text)
    reponse_texte = resultat.get("reponse", "")
    mlflow.log_text(reponse_texte, "reponse.txt")

    print(reponse_texte)
