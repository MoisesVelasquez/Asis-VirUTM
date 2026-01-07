# Usar una imagen de Python
FROM python:3.9

# Crear un directorio de trabajo
WORKDIR /code

# Copiar los requerimientos e instalarlos
COPY ./requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

# Copiar todo el contenido del proyecto
COPY . .

# Comando para iniciar la API (sustituye el uvicorn que hacias manual)
CMD ["uvicorn", "api_fastapi:app", "--host", "0.0.0.0", "--port", "7860"]