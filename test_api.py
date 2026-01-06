import asyncio
import aiohttp

# URL de tu API
API_URL = "http://127.0.0.1:8000/chat"

# Lista de preguntas de prueba
preguntas = [
    "¿Cuál es el objetivo de la asignatura ISI17?",
    "¿Cuántos créditos tiene la asignatura?",
    "¿Quién es la docente que imparte la asignatura?",
    "¿Cuáles son las unidades de la asignatura?",
    "¿Qué bibliografía se utiliza?",
    "¿Cómo se evalúa la asignatura?",
]

async def hacer_pregunta(session, pregunta):
    """Envía una pregunta al asistente y muestra la respuesta"""
    try:
        payload = {"user_query": pregunta}
        async with session.post(API_URL, json=payload) as response:
            if response.status == 200:
                data = await response.json()
                return data['response']
            else:
                return f"Error {response.status}: {await response.text()}"
    
    except Exception as e:
        return f"Error de conexión: {e}"

async def main():
    async with aiohttp.ClientSession() as session:
        tasks = [hacer_pregunta(session, p) for p in preguntas]
        responses = await asyncio.gather(*tasks)
        for i, (p, r) in enumerate(zip(preguntas, responses), 1):
            print(f"\n{'─' * 80}")
            print(f"PREGUNTA {i}: {p}")
            print(f"{'─' * 80}")
            print(f"\nRESPUESTA:\n{r}")
            print()

if __name__ == "__main__":
    print("=" * 80)
    print("PRUEBA DEL ASISTENTE EDUCATIVO UTM")
    print("=" * 80)
    asyncio.run(main())
    print("=" * 80)
    print("PRUEBA COMPLETADA")
    print("=" * 80)