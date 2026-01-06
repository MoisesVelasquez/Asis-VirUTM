# INGESTA OPTIMIZADA - Versión Mejorada (Opcional, no necesaria con pre-carga en API)
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
import os
import time
import shutil

# --- Configuración Optimizada ---
RUTA_DOCUMENTO = "Syllabus.pdf" 
NOMBRE_COLECCION = "asistente_educativo_utem" 
PERSIST_DIRECTORY = "./chroma_db"

if not os.path.exists(RUTA_DOCUMENTO):
    print(f"❌ ERROR: No se encontró '{RUTA_DOCUMENTO}'")
    print("Colócalo en la misma carpeta que este script.")
    exit()

print("=" * 70)
print("🚀 INGESTA OPTIMIZADA DE DATOS")
print("=" * 70)
inicio_total = time.time()

# 1. Carga de Documentos
print("\n[1/4] 📄 Cargando PDF...")
inicio = time.time()
try:
    loader = PyPDFLoader(RUTA_DOCUMENTO)
    documentos = loader.load()
    tiempo = time.time() - inicio
    print(f"   ✅ {len(documentos)} páginas cargadas en {tiempo:.2f}s")
except Exception as e:
    print(f"   ❌ Error: {e}")
    exit()

# 2. Fragmentación OPTIMIZADA
print("\n[2/4] ✂️  Fragmentando texto...")
inicio = time.time()

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=800,
    chunk_overlap=150,
    separators=["\n\n", "\n", ". ", " ", ""],
    length_function=len,
)

fragmentos = text_splitter.split_documents(documentos)
tiempo = time.time() - inicio

print(f"   ✅ {len(fragmentos)} fragmentos creados en {tiempo:.2f}s")
print(f"   📊 Tamaño promedio: {sum(len(f.page_content) for f in fragmentos) // len(fragmentos)} caracteres")

# 3. Embeddings Optimizados
print("\n[3/4] 🧠 Inicializando modelo de embeddings...")
inicio = time.time()

embeddings_model = HuggingFaceEmbeddings(
    model_name="all-MiniLM-L6-v2",
    model_kwargs={'device': 'cpu'},
    encode_kwargs={'normalize_embeddings': True, 'batch_size': 64}
)

tiempo = time.time() - inicio
print(f"   ✅ Modelo cargado en {tiempo:.2f}s")

# 4. Almacenamiento en ChromaDB OPTIMIZADO
print("\n[4/4] 💾 Creando base de datos vectorial...")
inicio = time.time()

if os.path.exists(PERSIST_DIRECTORY):
    shutil.rmtree(PERSIST_DIRECTORY)
    print(f"   🗑️  Base de datos anterior eliminada")

vector_store = Chroma.from_documents(
    documents=fragmentos, 
    embedding=embeddings_model, 
    collection_name=NOMBRE_COLECCION,
    persist_directory=PERSIST_DIRECTORY,
    collection_metadata={"hnsw:space": "cosine", "hnsw:construction_ef": 100, "hnsw:M": 16}
)

tiempo = time.time() - inicio
tiempo_total = time.time() - inicio_total

print(f"   ✅ Base de datos creada en {time.time() - inicio:.2f}s")

cantidad = vector_store._collection.count()
print(f"\n{'=' * 70}")
print(f"✅ INGESTA COMPLETADA EXITOSAMENTE")
print(f"{'=' * 70}")
print(f"⏱️  Tiempo total: {tiempo_total:.2f} segundos")
print(f"📊 Fragmentos almacenados: {cantidad}")
print(f"💾 Ubicación: {PERSIST_DIRECTORY}/")
print(f"🎯 Colección: {NOMBRE_COLECCION}")
print(f"\n🚀 Siguiente paso: uvicorn api_fastapi:app --reload (opcional, pre-carga en API)")
print(f"{'=' * 70}")