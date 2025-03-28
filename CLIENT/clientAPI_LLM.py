import requests
import urllib.parse

# Get the list of all usable models
def get_list_model(addr):
    response = requests.get(addr + "/llm/")
    if response.status_code == 200:
        data = response.json()
        models = data.get('models', [])
        return models
    else:
        return {"error": "Erreur de connexion à l'API"}

# Query a model based on a prompt
def query(addr, model, prompt):
    """Envoie une requête pour obtenir une réponse du modèle."""
    data = {
        "model_name": model,
        "prompt": prompt
    }
    return requests.post(addr + "/llm/", json=data).json()

# Query a model based on a prompt and find info based on indexed documents
def query_index(addr, model, prompt):
    """Envoie une requête pour obtenir une réponse du modèle basé sur un index."""
    data = {
        "model_name": model,
        "prompt": prompt
    }
    return requests.post(addr + "/llm/indexed/", json=data).json()

# Refresh the index for query_index, delete the index if there is no uploaded files
def refresh_index(addr):
    """Actualise l'index."""
    return requests.get(addr + "/llm/indexed/refresh").json()

# Get the name of all files uploaded
def get_indexed_pdf(addr):
    """Retourne les fichiers PDF indexés."""
    return requests.get(addr + "/upload/").json()

# Upload a file from a path
def upload_pdf(addr, file_path):
    """Envoie un fichier PDF pour téléchargement."""
    with open(file_path, 'rb') as file:
        files = {'file': (file_path.split('/')[-1], file)}
        return requests.post(addr + "/upload/", files=files).json()

# Delete a file from his name
def delete_pdf(addr, name):
    """Supprime un fichier PDF sur le serveur."""
    return requests.delete(addr + f"/upload/indexed_documents/{urllib.parse.quote(name)}").json()