# test_advanced.py - Pruebas avanzadas para la tesis
import asyncio
import aiohttp
import time
import csv
from datetime import datetime

API_URL = "http://127.0.0.1:8000/chat"

# RF2: Precisión de Respuestas
preguntas_precision = [
    ("¿Cuántos créditos tiene la asignatura?", "3"),
    ("¿Quién es la docente?", "Lucia"),
    ("¿Cuántas unidades tiene el curso?", "3"),
    ("¿Qué nivel es la asignatura?", "noveno"),
    ("¿Cuál es el código de la asignatura?", "ISI17"),
]

# RNF2: Latencia (objetivo: < 3 segundos)
preguntas_latencia = [
    "¿Cuál es el objetivo de la asignatura?",
    "¿Cómo se evalúa la asignatura?",
    "¿Qué bibliografía se utiliza?",
    "¿Cuáles son las unidades del curso?",
    "¿Qué es la toma de decisiones según el syllabus?",
    "¿Qué estrategias de SI se mencionan?",
    "¿Cómo se gestiona la adquisición de SI?",
]

async def medir_precision():
    """Mide la precisión de las respuestas (RF2)"""
    resultados = []
    print("\n" + "="*80)
    print("PRUEBA RF2: PRECISIÓN DE RESPUESTAS")
    print("="*80)
    
    async with aiohttp.ClientSession() as session:
        for i, (pregunta, respuesta_esperada) in enumerate(preguntas_precision, 1):
            print(f"\n[{i}/{len(preguntas_precision)}] Pregunta: {pregunta}")
            
            payload = {"user_query": pregunta}
            start = time.time()
            
            try:
                async with session.post(API_URL, json=payload) as resp:
                    data = await resp.json()
                    latency = time.time() - start
                    
                    # Verificar si la respuesta contiene la palabra clave esperada
                    respuesta = data['response'].lower()
                    correcto = respuesta_esperada.lower() in respuesta
                    
                    resultados.append({
                        'pregunta': pregunta,
                        'esperado': respuesta_esperada,
                        'obtenido': data['response'][:150],  # Primeros 150 caracteres
                        'correcto': correcto,
                        'latencia': f"{latency:.2f}s",
                        'cached': data.get('cached', False)
                    })
                    
                    print(f"   ✓ Respuesta: {data['response'][:100]}...")
                    print(f"   {'✅ CORRECTO' if correcto else '❌ INCORRECTO'} | Tiempo: {latency:.2f}s")
                    
            except Exception as e:
                print(f"   ❌ ERROR: {e}")
                resultados.append({
                    'pregunta': pregunta,
                    'esperado': respuesta_esperada,
                    'obtenido': f"ERROR: {e}",
                    'correcto': False,
                    'latencia': "N/A",
                    'cached': False
                })
    
    return resultados

async def medir_latencia():
    """Mide la latencia de respuesta (RNF2)"""
    tiempos = []
    print("\n" + "="*80)
    print("PRUEBA RNF2: LATENCIA DE RESPUESTA (Objetivo: < 3 segundos)")
    print("="*80)
    
    async with aiohttp.ClientSession() as session:
        for i, pregunta in enumerate(preguntas_latencia, 1):
            print(f"\n[{i}/{len(preguntas_latencia)}] {pregunta}")
            
            payload = {"user_query": pregunta}
            start = time.time()
            
            try:
                async with session.post(API_URL, json=payload) as resp:
                    data = await resp.json()
                    latency = time.time() - start
                    cumple = latency <= 3.0
                    
                    tiempos.append({
                        'pregunta': pregunta,
                        'latencia': latency,
                        'cumple_3s': cumple,
                        'cached': data.get('cached', False)
                    })
                    
                    emoji = "✅" if cumple else "⚠️"
                    cache_emoji = "⚡" if data.get('cached') else "🔄"
                    print(f"   {emoji} Tiempo: {latency:.2f}s {cache_emoji}")
                    
            except Exception as e:
                print(f"   ❌ ERROR: {e}")
                tiempos.append({
                    'pregunta': pregunta,
                    'latencia': 999,
                    'cumple_3s': False,
                    'cached': False
                })
    
    return tiempos

async def main():
    print("\n" + "="*80)
    print("🎓 PRUEBAS DE CALIDAD DEL SISTEMA - ASISTENTE EDUCATIVO UTM")
    print("="*80)
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"API URL: {API_URL}")
    
    # Verificar conexión
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("http://127.0.0.1:8000/health") as resp:
                if resp.status == 200:
                    print("✅ API conectada y saludable")
                else:
                    print("⚠️ API respondió pero con estado no saludable")
    except:
        print("❌ ERROR: No se puede conectar a la API. Asegúrate de que esté corriendo.")
        print("   Ejecuta: uvicorn api_fastapi:app --reload")
        return
    
    # Ejecutar pruebas
    print("\n⏳ Iniciando pruebas...")
    
    # RF2: Precisión
    precision = await medir_precision()
    
    # RNF2: Latencia
    latencia = await medir_latencia()
    
    # Resultados Finales
    print("\n" + "="*80)
    print("📊 RESULTADOS FINALES")
    print("="*80)
    
    # Precisión
    correctas = sum(1 for r in precision if r['correcto'])
    total_precision = len(precision)
    porcentaje_precision = (correctas / total_precision * 100) if total_precision > 0 else 0
    
    print(f"\n1️⃣ PRECISIÓN (RF2):")
    print(f"   Respuestas correctas: {correctas}/{total_precision}")
    print(f"   Porcentaje: {porcentaje_precision:.1f}%")
    print(f"   {'✅ APROBADO' if porcentaje_precision >= 80 else '❌ REPROBADO'} (Umbral: 80%)")
    
    # Latencia
    promedio = sum(t['latencia'] for t in latencia if t['latencia'] < 999) / len([t for t in latencia if t['latencia'] < 999])
    cumple = sum(1 for t in latencia if t['cumple_3s'])
    total_latencia = len(latencia)
    porcentaje_latencia = (cumple / total_latencia * 100) if total_latencia > 0 else 0
    
    print(f"\n2️⃣ LATENCIA (RNF2):")
    print(f"   Latencia promedio: {promedio:.2f}s")
    print(f"   Respuestas < 3s: {cumple}/{total_latencia}")
    print(f"   Porcentaje: {porcentaje_latencia:.1f}%")
    print(f"   {'✅ APROBADO' if porcentaje_latencia >= 90 else '❌ REPROBADO'} (Umbral: 90%)")
    
    # Guardar en CSV
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f'resultados_pruebas_{timestamp}.csv'
    
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        
        # Encabezados
        writer.writerow(['=== RESULTADOS DE PRUEBAS - ASISTENTE EDUCATIVO UTM ==='])
        writer.writerow([f'Fecha: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'])
        writer.writerow([])
        
        # Precisión
        writer.writerow(['PRUEBA RF2: PRECISIÓN'])
        writer.writerow(['Pregunta', 'Esperado', 'Obtenido', 'Correcto', 'Latencia', 'Cached'])
        for r in precision:
            writer.writerow([
                r['pregunta'], 
                r['esperado'], 
                r['obtenido'], 
                'SÍ' if r['correcto'] else 'NO',
                r['latencia'],
                'SÍ' if r['cached'] else 'NO'
            ])
        writer.writerow([])
        writer.writerow(['RESUMEN RF2'])
        writer.writerow(['Correctas', correctas])
        writer.writerow(['Total', total_precision])
        writer.writerow(['Porcentaje', f'{porcentaje_precision:.1f}%'])
        writer.writerow([])
        
        # Latencia
        writer.writerow(['PRUEBA RNF2: LATENCIA'])
        writer.writerow(['Pregunta', 'Latencia (s)', 'Cumple <3s', 'Cached'])
        for t in latencia:
            writer.writerow([
                t['pregunta'],
                f"{t['latencia']:.2f}",
                'SÍ' if t['cumple_3s'] else 'NO',
                'SÍ' if t['cached'] else 'NO'
            ])
        writer.writerow([])
        writer.writerow(['RESUMEN RNF2'])
        writer.writerow(['Latencia promedio', f'{promedio:.2f}s'])
        writer.writerow(['Respuestas < 3s', cumple])
        writer.writerow(['Total', total_latencia])
        writer.writerow(['Porcentaje', f'{porcentaje_latencia:.1f}%'])
    
    print(f"\n💾 Resultados guardados en: {filename}")
    print("="*80)
    print("✅ PRUEBAS COMPLETADAS")
    print("="*80)

if __name__ == "__main__":
    asyncio.run(main())