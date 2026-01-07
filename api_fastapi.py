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
from fastapi.staticfiles import StaticFiles

# 1. CONFIGURACIÓN DE IA Y ENTORNO
load_dotenv()
api_key_final = os.getenv("GROQ_API_KEY")

# Inicialización del LLM (Groq)
llm = ChatGroq(
    api_key=api_key_final, 
    model="llama-3.3-70b-versatile",
    temperature=0.3,
    max_tokens=250
)

# 2. CONFIGURACIÓN DE BASE DE DATOS (CHROMA)
# Asegúrate de que la carpeta 'chroma_db' esté en la raíz de tu proyecto
embeddings_model = HuggingFaceEmbeddings(
    model_name="all-MiniLM-L6-v2",
    model_kwargs={'device': 'cpu'}
)

vector_db = Chroma(
    persist_directory="./chroma_db", 
    embedding_function=embeddings_model,
    collection_name="asistente_educativo_utem"
)

# 3. CONFIGURACIÓN DE FASTAPI
app = FastAPI(
    title="Asistente Educativo UTM API v3.1",
    description="IA Online con RAG Optimizado",
    version="3.1.0",
)

# Configuración de CORS necesaria para Hugging Face
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    user_query: str

# PROMPT TEMPLATE
TEMPLATE = """Eres un asistente académico de la UTM. Tu trabajo es responder basándote en el CONTEXTO del Syllabus.

INSTRUCCIONES:
1. Responde en máximo 2-3 oraciones cortas y directas.
2. Si encuentras la información exacta en el contexto, respóndela directamente.
3. Si la información está implícita o parcial, sintetízala razonablemente.
4. SOLO di "Esa información no está en el Syllabus disponible" si no hay relación alguna.
5. Menciona números de unidades o temas si aparecen.

CONTEXTO DEL SYLLABUS:
{context}

PREGUNTA DEL ESTUDIANTE:
{question}

RESPUESTA:"""

# FUNCIONES DE APOYO
def buscar_contexto_semantico(query: str, k: int = 6):
    docs = vector_db.similarity_search(query, k=k)
    contextos_unicos = []
    contenidos_vistos = set()
    
    for doc in docs:
        contenido = doc.page_content.strip()
        if contenido not in contenidos_vistos:
            página = doc.metadata.get('page', '?')
            contextos_unicos.append(f"[Pág. {página}]: {contenido}")
            contenidos_vistos.add(contenido)
    
    return "\n\n".join(contextos_unicos)

def limpiar_respuesta(respuesta: str) -> str:
    return ' '.join(respuesta.split()).strip()

# --- ENDPOINTS ---

# RUTA PRINCIPAL: Muestra tu interfaz HTML
@app.get("/")
async def read_index():
    return FileResponse('index.html')

# RUTA DE CHAT: Procesa las preguntas
@app.post("/preguntar") # Cambiado a /preguntar para coincidir con tu fetch
async def chat_endpoint(request: ChatRequest):
    try:
        query = request.user_query
        if not query or query.strip() == "":
            raise HTTPException(status_code=400, detail="La pregunta está vacía")

        start_time = time.time()
        contexto = buscar_contexto_semantico(query, k=6)
        
        prompt_completo = TEMPLATE.format(context=contexto, question=query)
        respuesta_raw = llm.invoke(prompt_completo)
        respuesta_final = limpiar_respuesta(respuesta_raw.content)
        
        total_time = time.time() - start_time
        
        return {
            "respuesta": respuesta_final, # Cambiado a 'respuesta' para tu JS
            "total_time": f"{total_time:.2f}s"
        }
    
    except Exception as e:
        print(f"❌ Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {"status": "online", "database": "ChromaDB conectado"}

if __name__ == "__main__":
    import uvicorn
    # Puerto 7860 para Hugging Face
    uvicorn.run(app, host="0.0.0.0", port=7860)