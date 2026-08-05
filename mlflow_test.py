import mlflow

mlflow.start_run()
mlflow.log_param("modele", "phi3")
mlflow.log_metric("temps_reponse", 1.5)
mlflow.end_run()
print("Expérience enregistrée")


modeles = {"phi3": 1.2, "mistral": 1.8, "gemma": 2.1}
for modele, temps in modeles.items():
    with mlflow.start_run():
        mlflow.log_param("modele", modele)
        mlflow.log_metric("temps_reponse", temps)
