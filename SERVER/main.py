from fastapi import FastAPI, HTTPException, UploadFile, File
from pydantic import BaseModel
from llama_index.llms.ollama import Ollama
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, Settings, load_index_from_storage, StorageContext
from llama_index.core.embeddings import resolve_embed_model
import ollama
import shutil
import os



app = FastAPI()



###############################
# QUERY WITHOUT INDEXING PART #
###############################

# Modèle de données pour les requêtes
class QueryRequest(BaseModel):
    model_name: str
    prompt: str

# Route pour connaitre les modèles disponibles
@app.get("/llm/")
async def query_llm():
    try:
        return ollama.list()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Route pour les requetes avec prompt
# {
#     "model_name": "EXAMPLE",
#     "prompt": "This is an example prompt"
# }
@app.post("/llm/")
async def query_llm(request: QueryRequest):
    try:
        # Configuration du modèle
        Settings.llm = Ollama(model=request.model_name, request_timeout=120.0)

        response = Settings.llm.complete(request.prompt)
        return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



############################
# QUERY WITH INDEXING PART #
############################

# Change your directory path for the one you use
UPLOAD_DIR = 'SERVER/indexed_documents'
STORAGE_DIR = 'SERVER/storage'
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(STORAGE_DIR, exist_ok=True)


# upload un fichier
import logging
logging.basicConfig(level=logging.INFO)

@app.post("/upload/")
async def upload_pdf(file: UploadFile = File()):
    if not file:
        raise HTTPException(status_code=400, detail="Aucun fichier reçu")
    
    # Extraire le nom du fichier sans le chemin
    filename = os.path.basename(file.filename)
    logging.info(f"Fichier reçu : {filename}")
    
    file_path = os.path.join(UPLOAD_DIR, filename)
    logging.info(f"Chemin de destination : {file_path}")
    
    # Créer le dossier de destination s'il n'existe pas
    if not os.path.exists(UPLOAD_DIR):
        os.makedirs(UPLOAD_DIR)
    
    # Sauvegarder le fichier
    with open(file_path, "wb") as f:
        f.write(await file.read())
    
    return {"filename": filename, "message": "Fichier uploadé avec succès !"}

# supprime un fichier
@app.delete("/upload/indexed_documents/{filename}")
async def delete_pdf(filename: str):
    file_path = os.path.join(UPLOAD_DIR, filename)
    
    if os.path.exists(file_path):
        os.remove(file_path)
        return {"filename": filename, "message": "Fichier supprimé avec succès !"}
    else:
        raise HTTPException(status_code=404, detail="Fichier non trouvé.")
    
# connaitre les fichiers indexés
@app.get("/upload/")
async def list_pdf():
    if not os.path.exists(UPLOAD_DIR):
        raise HTTPException(status_code=404, detail="Répertoire d'upload introuvable")
    
    files = os.listdir(UPLOAD_DIR)
    return {"files": files if files else "Aucun fichier trouvé"}

# Route pour les requetes avec prompt et indexage de fichiers
# {
#     "model_name": "EXAMPLE",
#     "prompt": "This is an example prompt"
# }
@app.post("/llm/indexed/")
async def query_llm_indexed(request: QueryRequest):
    try:
        # Vérifier si l’index existe
        if not os.path.exists(STORAGE_DIR):
            raise HTTPException(status_code=400, detail="Aucun index trouvé. Actualisez l'index d'abord !")

        # Configurer le modèle LLM
        Settings.llm = Ollama(model=request.model_name, request_timeout=120.0)
        Settings.embed_model = resolve_embed_model("local:BAAI/bge-small-en-v1.5")

        # Charger l’index depuis le stockage
        storage_context = StorageContext.from_defaults(persist_dir=STORAGE_DIR)
        index = load_index_from_storage(storage_context)
        query_engine = index.as_query_engine(similarity_top_k=2)

        # Exécuter la requête
        context = query_engine.query(request.prompt)
        response = Settings.llm.complete(f"Réponds en te basant sur ce contexte : {context}")

        return {"response": response}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Route pour actualiser l'index
@app.get("/llm/indexed/refresh/")
async def refresh_index():
    try:
        if not os.listdir(UPLOAD_DIR):  # Si le répertoire est vide
            if os.path.exists(STORAGE_DIR):
                # Afficher les fichiers et répertoires avant de supprimer
                print(f"Contenu du répertoire de stockage : {os.listdir(STORAGE_DIR)}")
                shutil.rmtree(STORAGE_DIR)  # Supprimer le répertoire et tout son contenu

            return {"message": "Aucun fichier à indexer. Le répertoire de stockage a été supprimé."}

        Settings.embed_model = resolve_embed_model("local:BAAI/bge-small-en-v1.5")
        documents = SimpleDirectoryReader(UPLOAD_DIR, required_exts=[".pdf"]).load_data()
        index = VectorStoreIndex.from_documents(documents)
        # Sauvegarde de l'index dans le dossier de stockage
        index.storage_context.persist(persist_dir=STORAGE_DIR)

        return {"message": f"Index actualisé avec succès ! {len(documents)} documents indexés."}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


###############
# SERVER PART #
###############

# Launch the server
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)