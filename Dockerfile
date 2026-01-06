# Usa una imagen de Python ligera
FROM python:3.10-slim

# Crea un directorio de trabajo
WORKDIR /app

# Copia los archivos de requerimientos e instala las librerías
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia todo el contenido de tu carpeta al contenedor
COPY . .

# Expone el puerto que usa Hugging Face Spaces (7860)
EXPOSE 7860

# Comando para ejecutar la API
# Usamos el puerto 7860 porque es el que Hugging Face requiere por defecto
CMD ["uvicorn", "api_fastapi:app", "--host", "0.0.0.0", "--port", "7860"]