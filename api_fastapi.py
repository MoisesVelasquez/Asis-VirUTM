import os
import time
from typing import List
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_groq import ChatGroq
from fastapi.responses import FileResponse
import uvicorn

# 1. CARGA DE CONFIGURACIÓN
load_dotenv()
api_key_final = os.getenv("GROQ_API_KEY")
current_dir = os.path.dirname(os.path.realpath(__file__))

# 2. INICIALIZACIÓN DE MODELOS
# Groq Llama 3
llm = ChatGroq(
    api_key=api_key_final, 
    model="llama-3.3-70b-versatile",
    temperature=0.3,
    max_tokens=250
)

# Embeddings y Base de Datos (Chroma)
embeddings_model = HuggingFaceEmbeddings(
    model_name="all-MiniLM-L6-v2",
    model_kwargs={'device': 'cpu'}
)

vector_db = Chroma(
    persist_directory=os.path.join(current_dir, "chroma_db"), 
    embedding_function=embeddings_model,
    collection_name="asistente_educativo_utem"
)

# 3. CONFIGURACIÓN DE FASTAPI
app = FastAPI(title="Asistente Educativo UTM")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    user_query: str

# PROMPT PARA LA IA
TEMPLATE = """Eres un asistente académico de la UTM. Tu trabajo es responder basándote en el CONTEXTO del Syllabus.
INSTRUCCIONES:
1. Responde en máximo 2-3 oraciones cortas.
2. Si no sabes, di: "Esa información no está en el Syllabus disponible".
CONTEXTO: {context}
PREGUNTA: {question}
RESPUESTA:"""

# 4. FUNCIONES DE BÚSQUEDA
def buscar_contexto(query: str):
    docs = vector_db.similarity_search(query, k=5)
    return "\n\n".join([f"[Pág. {d.metadata.get('page', '?')}]: {d.page_content}" for d in docs])

# 5. ENDPOINTS (RUTAS)

# RUTA PARA MOSTRAR EL HTML (EL INDEX)
@app.get("/")
async def read_index():
    # Intento 1: Ruta absoluta
    path = os.path.join(current_dir, "index.html")
    if os.path.exists(path):
        return FileResponse(path)
    
    # Intento 2: Búsqueda en el directorio de trabajo actual
    path_alt = os.path.join(os.getcwd(), "index.html")
    if os.path.exists(path_alt):
        return FileResponse(path_alt)
        
    # Si falla, dinos qué archivos ve el servidor realmente
    files_in_dir = os.listdir(current_dir)
    return {
        "error": "No se encontró index.html",
        "ruta_buscada": path,
        "archivos_que_existen_en_raiz": files_in_dir
    }

# RUTA PARA PROCESAR PREGUNTAS
@app.post("/preguntar")
async def chat_endpoint(request: ChatRequest):
    try:
        query = request.user_query
        contexto = buscar_contexto(query)
        prompt = TEMPLATE.format(context=contexto, question=query)
        
        respuesta_raw = llm.invoke(prompt)
        
        return {
            "respuesta": respuesta_raw.content.strip(),
            "status": "success"
        }
    except Exception as e:
        return {"respuesta": f"Error en el servidor: {str(e)}", "status": "error"}

# 6. ARRANQUE
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=7860)