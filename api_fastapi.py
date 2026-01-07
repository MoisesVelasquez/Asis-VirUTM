import os
import time
from typing import List
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_groq import ChatGroq
from fastapi import FastAPI
from fastapi.responses import FileResponse # Añade esta línea
from fastapi.staticfiles import StaticFiles
import os

# 1. CONFIGURACIÓN DE IA (GROQ - ONLINE)
# 1. CONFIGURACIÓN DE IA (GROQ - ONLINE)
load_dotenv()
api_key_final = os.getenv("GROQ_API_KEY")

# OPTIMIZACIÓN 1: Temperatura ajustada
llm = ChatGroq(
    api_key=api_key_final, 
    model="llama-3.3-70b-versatile",
    temperature=0.3,
    max_tokens=250
)
# En api_fastapi.py
persist_directory = "chroma_db" 
# ... código para cargar el vectorstore desde esa carpeta
# 2. CONFIGURACIÓN DE BASE DE DATOS (CHROMA)
embeddings_model = HuggingFaceEmbeddings(
    model_name="all-MiniLM-L6-v2",
    model_kwargs={'device': 'cpu'}
)

vector_db = Chroma(
    persist_directory="./chroma_db", 
    embedding_function=embeddings_model,
    collection_name="asistente_educativo_utem"
)

# --- Configuración de FastAPI ---
app = FastAPI(
    title="Asistente Educativo UTM API v3.1",
    description="IA Online con RAG Optimizado",
    version="3.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    user_query: str

# OPTIMIZACIÓN 2: PROMPT TEMPLATE BALANCEADO
TEMPLATE = """Eres un asistente académico de la UTM. Tu trabajo es responder basándote en el CONTEXTO del Syllabus.

INSTRUCCIONES:
1. Responde en máximo 2-3 oraciones cortas y directas
2. Si encuentras la información exacta en el contexto, respóndela directamente
3. Si la información está implícita o parcial en el contexto, sintetízala de forma razonable
4. SOLO di "Esa información no está en el Syllabus disponible" si el contexto no tiene NADA relacionado con la pregunta
5. Si hay nombres de unidades, temas o números en el contexto, menciónelos
6. Corrige mentalmente errores ortográficos del usuario (ej: "ceditos" = "créditos")

CONTEXTO DEL SYLLABUS:
{context}

PREGUNTA DEL ESTUDIANTE:
{question}

RESPUESTA (concisa y basada en el contexto):"""

# OPTIMIZACIÓN 3: FUNCIONES DE BÚSQUEDA MEJORADAS

def buscar_contexto_semantico(query: str, k: int = 6):
    """
    Búsqueda semántica optimizada con más documentos.
    K=6 mejora cobertura sin saturar el contexto.
    """
    docs = vector_db.similarity_search(query, k=k)
    
    # Filtra documentos duplicados
    contextos_unicos = []
    contenidos_vistos = set()
    
    for doc in docs:
        contenido = doc.page_content.strip()
        # Evita duplicados exactos
        if contenido not in contenidos_vistos:
            página = doc.metadata.get('page', '?')
            contextos_unicos.append(f"[Pág. {página}]: {contenido}")
            contenidos_vistos.add(contenido)
    
    return "\n\n".join(contextos_unicos)

def buscar_contexto_con_score(query: str, k: int = 6, score_threshold: float = 0.3):
    """
    ALTERNATIVA: Búsqueda con umbral de similitud.
    Usa esto si quieres filtrar resultados poco relevantes.
    """
    docs_with_scores = vector_db.similarity_search_with_score(query, k=k)
    
    contextos_relevantes = []
    for doc, score in docs_with_scores:
        # Score más bajo = más similar (distancia coseno)
        if score <= score_threshold:
            página = doc.metadata.get('page', '?')
            contextos_relevantes.append(f"[Pág. {página}]: {doc.page_content}")
    
    return "\n\n".join(contextos_relevantes) if contextos_relevantes else "No se encontró información relevante."

def limpiar_respuesta(respuesta: str) -> str:
    """Elimina espacios innecesarios y saltos de línea excesivos"""
    return ' '.join(respuesta.split()).strip()

# --- ENDPOINTS ---

@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    try:
        query = request.user_query
        if not query or query.strip() == "":
            raise HTTPException(status_code=400, detail="La pregunta está vacía")

        start_time = time.time()

        # OPCIÓN 1: Búsqueda semántica estándar (recomendada)
        contexto = buscar_contexto_semantico(query, k=6)
        
        # OPCIÓN 2: Búsqueda con score (descomenta si quieres probar)
        # contexto = buscar_contexto_con_score(query, k=6, score_threshold=0.4)
        
        # Construir el Prompt
        prompt_completo = TEMPLATE.format(context=contexto, question=query)
        
        # Invocar a Groq con el contexto optimizado
        respuesta_raw = llm.invoke(prompt_completo)
        respuesta_final = limpiar_respuesta(respuesta_raw.content)
        
        total_time = time.time() - start_time
        
        return {
            "response": respuesta_final,
            "query": query,
            "docs_found": len(contexto.split("[Pág.")),
            "model": "llama-3.3-70b-online",
            "total_time": f"{total_time:.2f}s"
        }
    
    except Exception as e:
        print(f"❌ Error en el servidor: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {
        "status": "online",
        "ia_provider": "GroqCloud",
        "database": "ChromaDB - RAG Optimizado v3.1",
        "optimizations": [
            "max_tokens=200",
            "k=6 documentos",
            "Deduplicación de contexto",
            "Prompt anti-alucinación"
        ]
    }

@app.post("/debug")
async def debug_search(request: ChatRequest):
    """
    Endpoint para debuggear: muestra el contexto recuperado sin invocar la IA.
    Útil para verificar qué está encontrando ChromaDB.
    """
    try:
        query = request.user_query
        contexto = buscar_contexto_semantico(query, k=6)
        docs_with_scores = vector_db.similarity_search_with_score(query, k=6)
        
        return {
            "query": query,
            "contexto_encontrado": contexto,
            "scores": [{"page": doc.metadata.get('page'), "score": score} 
                      for doc, score in docs_with_scores]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
    
    @app.get("/")
async def read_index():
    # Esto busca el archivo index.html en la carpeta principal
    return FileResponse('index.html')