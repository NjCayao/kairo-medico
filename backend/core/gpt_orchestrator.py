"""
GPT Orchestrator V4.1 - ANÁLISIS DE COMPOSICIÓN + CONFIGURACIÓN DINÁMICA
✅ Identidad: Creador Nilson Cayao
✅ Sin límites hardcodeados de preguntas
✅ Detecta mensajes repetidos y confusión
✅ Lee configuración desde panel admin (modelo, temperatura, etc.)
✅ Investiga plantas y remedios CON WEB SEARCH REAL
✅ Guarda en BD automáticamente
✅ Analiza composición de productos para recomendar el más efectivo
"""

import sys
import os
import json
import requests
from typing import Dict, List, Optional

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BASE_DIR)

from backend.core.ia_config_manager import IAConfigManager
from backend.database.productos_manager import ProductosManager
from backend.database.plantas_medicinales_manager import PlantasMedicinalesManager
from backend.database.remedios_caseros_manager import RemediosCaserosManager

# ⭐ Importar WebSearcher
try:
    from backend.core.web_searcher import obtener_buscador
    WEB_SEARCH_DISPONIBLE = True
except:
    WEB_SEARCH_DISPONIBLE = False
    print("⚠️ WebSearcher no disponible")

class GPTOrchestrator:
    """Orquestador GPT 100% conversacional como doctor real"""
    
    def __init__(self):
        self.ia_config = IAConfigManager()
        self.productos = ProductosManager()
        self.plantas = PlantasMedicinalesManager()
        self.remedios = RemediosCaserosManager()
        
        # ⭐ CAMBIO 1: Eliminar límite hardcodeado
        self.preguntas_realizadas = 0
        self.preguntas_sugeridas = 8  # Solo referencia, NO límite obligatorio
        
        # ⭐ CAMBIO 2: Identidad mejorada - Doctor de cabecera REAL
        self.identidad = """
Eres Kairos, un médico de cabecera especializado en medicina natural y holística.

TU CREADOR: Nilson Cayao, un joven peruano apasionado por la tecnología y la medicina natural.

CÓMO ACTÚAS COMO DOCTOR REAL:

1. ESCUCHA ACTIVAMENTE:
   - Reconoce lo que el paciente dice sin repetirlo obvio
   - Si menciona "insomnio" NO preguntes "¿qué te molesta?", di "¿desde cuándo?"
   
2. DETECTA SITUACIONES ESPECIALES:
   - Si el paciente repite lo mismo 2 veces → ACEPTA que no tiene más info y diagnostica
   - Si dice "solo eso" o "nada más" → NO insistas, tienes suficiente información
   - Paciente confundido/nervioso → "Tranquilo, con lo que me dijiste puedo ayudarte"
   
3. CONVERSACIÓN NATURAL:
   - Máximo 3-4 preguntas para casos simples (insomnio, dolor de cabeza)
   - NO seas insistente si el paciente ya respondió
   - Si el paciente dice "solo X" 2 veces → diagnostica
   
4. CUÁNDO DIAGNOSTICAR:
   - Casos SIMPLES (insomnio, dolor de cabeza, cansancio): 2-3 preguntas son suficientes
   - Casos COMPLEJOS (dolor fuerte, múltiples síntomas): 4-6 preguntas
   - Si el paciente se repite → ya tienes suficiente info
   
5. EMPATÍA REAL:
   - Si dice "me duele mucho" → "Entiendo que debe ser muy molesto"
   - Si se repite → "Perfecto, con eso puedo ayudarte. Déjame analizar..."
   - Usa el nombre del paciente naturalmente

IMPORTANTE: 
- Eres transparente sobre ser una IA creada por Nilson Cayao
- Mantienes tu rol profesional como médico naturista
- NUNCA repitas información que el paciente ya dio
- Si el paciente dice "solo eso" o "nada más" → DIAGNOSTICA
- No seas insistente si ya tienes: síntoma + duración aproximada
"""
        
        print("🧠 GPT Orchestrator V4.1 inicializado")
        
        # ⭐ Mostrar configuración actual
        if self.ia_config.esta_activo():
            config = self.ia_config.obtener_config()
            print(f"   📡 Modelo: {config.get('modelo', 'N/A')}")
            print(f"   🌡️ Temperatura: {config.get('temperatura', 'N/A')}")
            print(f"   📊 Max tokens: {config.get('max_tokens', 'N/A')}")
        else:
            print("   ⚠️ GPT desactivado en configuración")
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # ⭐ CAMBIO 3: DECISIÓN INTELIGENTE (sin límites hardcodeados)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    def decidir_accion(self, contexto: Dict) -> Dict:
        """GPT decide libremente: preguntar o diagnosticar"""
        
        if not self.ia_config.esta_activo():
            return {'accion': 'diagnosticar', 'razon': 'GPT no disponible'}
        
        mensajes = contexto.get('mensajes', [])
        
        # ⭐ DETECCIÓN INTELIGENTE: Mensajes repetidos
        mensaje_repetido = self._detectar_mensaje_repetido(mensajes)
        
        # ⭐ CAMBIO 4: Prompt sin mencionar límites
        prompt = f"""Analiza la conversación médica y decide la mejor acción.

CONVERSACIÓN COMPLETA:
{json.dumps(mensajes[-8:], ensure_ascii=False, indent=2)}

{'⚠️ ALERTA: El paciente repitió su último mensaje. Puede estar confundido o nervioso.' if mensaje_repetido else ''}

DECIDE:
- PREGUNTAR: Si necesitas más información para un diagnóstico responsable
- DIAGNOSTICAR: Si ya tienes suficiente información (síntoma + contexto básico)

CRITERIOS PARA DIAGNOSTICAR:
✅ Tienes: síntoma principal + duración aprox + intensidad + algo sobre qué lo mejora/empeora
✅ El paciente ya dio suficientes detalles
✅ Han conversado lo suficiente (no necesitas 20 preguntas, con 4-6 buenas preguntas basta)

NO DIAGNOSTIQUES SI:
❌ Solo sabes el síntoma sin contexto
❌ El paciente solo saludó o dijo algo confuso
❌ Falta información crítica (ejemplo: dice "me duele" pero no dónde ni desde cuándo)

Responde SOLO JSON:
{{
  "accion": "preguntar" o "diagnosticar",
  "razon": "Explicación breve de por qué"
}}

Si decides PREGUNTAR y detectaste mensaje repetido, el siguiente paso será responder con empatía.
Si decides DIAGNOSTICAR, el paciente ya dio suficiente información."""

        try:
            config = self.ia_config.obtener_config()
            
            response = requests.post(
                'https://api.openai.com/v1/chat/completions',
                headers={
                    'Authorization': f"Bearer {config['api_key']}",
                    'Content-Type': 'application/json'
                },
                json={
                    'model': config['modelo'],  # ⭐ Lee desde BD
                    'messages': [
                        {'role': 'system', 'content': self.identidad},
                        {'role': 'user', 'content': prompt}
                    ],
                    'temperature': float(config.get('temperatura', 0.3)),  # ⭐ Lee desde BD
                    'max_tokens': 150
                },
                timeout=20
            )
            
            if response.status_code == 200:
                data = response.json()
                contenido = data['choices'][0]['message']['content'].strip()
                contenido = contenido.replace('```json', '').replace('```', '').strip()
                
                decision = json.loads(contenido)
                
                if decision['accion'] == 'preguntar':
                    self.preguntas_realizadas += 1
                
                self.ia_config.incrementar_consulta(0.01)
                
                print(f"   🤔 Decisión: {decision['accion'].upper()}")
                print(f"   💭 Razón: {decision['razon']}")
                
                return decision
        
        except Exception as e:
            print(f"❌ Error decidir acción: {e}")
            import traceback
            traceback.print_exc()
        
        # Fallback inteligente
        if len(mensajes) >= 10:
            return {'accion': 'diagnosticar', 'razon': 'Conversación suficiente'}
        
        return {'accion': 'preguntar', 'razon': 'Error GPT, seguir preguntando'}
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # ⭐ CAMBIO 5: RESPUESTA CONVERSACIONAL NATURAL
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    def generar_respuesta(self, decision: Dict, contexto: Dict) -> str:
        """Generar respuesta natural como doctor de cabecera"""
        
        if not self.ia_config.esta_activo():
            return "Lo siento, no puedo procesar tu consulta ahora."
        
        mensajes = contexto.get('mensajes', [])
        usuario = contexto.get('usuario', {})
        
        # ⭐ DETECCIÓN: Mensaje repetido
        mensaje_repetido = self._detectar_mensaje_repetido(mensajes)
        
        if decision['accion'] == 'preguntar':
            # ⭐ CAMBIO 6: Prompt mejorado para preguntas naturales
            prompt = f"""Eres Kairos, médico de cabecera que conversa naturalmente.

PACIENTE: {usuario.get('nombre', 'Paciente')}

CONVERSACIÓN COMPLETA (últimos 8 mensajes):
{json.dumps(mensajes[-8:], ensure_ascii=False, indent=2)}

{'⚠️ SITUACIÓN: El paciente repitió su mensaje. Puede estar nervioso o confundido.' if mensaje_repetido else ''}

INSTRUCCIONES:

1. Si detectaste mensaje repetido:
   - Responde con EMPATÍA: "Ya te escuché. Tranquilo, cuéntame con confianza..."
   - NO repitas la misma pregunta
   - Reformula de forma más clara y amable

2. Si el paciente solo saludó sin mencionar síntomas:
   - Responde natural: "Hola [nombre], ¿qué te trae por aquí hoy?"
   - NO digas: "¿Podrías contarme más sobre tus síntomas?" (muy robótico)

3. Si el paciente ya mencionó un síntoma:
   - NO repitas el síntoma obvio
   - Pregunta lo que falta: duración, intensidad, momento del día, qué lo mejora/empeora
   - Ejemplo: Si dijo "gastritis", pregunta "¿Desde cuándo la tienes?" NO "cuéntame sobre tu gastritis"

4. Sé CONVERSACIONAL:
   - Máximo 2-3 líneas
   - Usa el nombre del paciente naturalmente
   - Haz UNA pregunta clara y específica
   - Si necesitas, da contexto primero: "Entiendo que es molesto. ¿Desde hace cuánto lo tienes?"

5. Reconoce lo que ya dijeron:
   - Si dijo "me duele la cabeza" NO preguntes "¿qué te duele?"
   - Pregunta lo siguiente lógico: "¿Desde hace cuánto?" o "¿Qué tan fuerte del 1 al 10?"

Responde de forma natural y empática. SOLO el texto que le dirías al paciente."""

        else:  # diagnosticar
            prompt = f"""Eres Kairos, médico de cabecera.

CONVERSACIÓN:
{json.dumps(mensajes, ensure_ascii=False, indent=2)}

Ya tienes suficiente información para diagnosticar.

Responde de forma natural:
- Agradece al paciente por la información
- Dile que ya puedes ayudarle
- Mantén 2-3 líneas máximo
- Usa su nombre si lo tienes

Ejemplo: "Perfecto [nombre], ya tengo toda la información necesaria. Déjame analizar tu caso..."

SOLO el texto natural, sin explicaciones extras."""

        try:
            config = self.ia_config.obtener_config()
            
            response = requests.post(
                'https://api.openai.com/v1/chat/completions',
                headers={
                    'Authorization': f"Bearer {config['api_key']}",
                    'Content-Type': 'application/json'
                },
                json={
                    'model': config['modelo'],  # ⭐ Lee desde BD
                    'messages': [
                        {'role': 'system', 'content': self.identidad},
                        {'role': 'user', 'content': prompt}
                    ],
                    'temperature': float(config.get('temperatura', 0.7)),  # ⭐ Lee desde BD
                    'max_tokens': 150
                },
                timeout=20
            )
            
            if response.status_code == 200:
                data = response.json()
                respuesta = data['choices'][0]['message']['content'].strip()
                
                self.ia_config.incrementar_consulta(0.01)
                
                return respuesta
        
        except Exception as e:
            print(f"❌ Error generar respuesta: {e}")
            import traceback
            traceback.print_exc()
        
        # Fallback empático
        if mensaje_repetido:
            return f"Tranquilo {usuario.get('nombre', '')}, cuéntame con confianza: ¿qué molestia tienes?"
        
        return "¿Podrías contarme más sobre lo que te molesta?"
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # ⭐ CAMBIO 7: DETECCIÓN DE MENSAJES REPETIDOS
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    def _detectar_mensaje_repetido(self, mensajes: List[Dict]) -> bool:
        """Detectar si el usuario repitió su último mensaje"""
        
        if len(mensajes) < 2:
            return False
        
        # Filtrar solo mensajes del usuario
        mensajes_usuario = [m for m in mensajes if m.get('role') == 'user']
        
        if len(mensajes_usuario) < 2:
            return False
        
        # Comparar últimos 2 mensajes del usuario
        ultimo = mensajes_usuario[-1].get('content', '').lower().strip()
        penultimo = mensajes_usuario[-2].get('content', '').lower().strip()
        
        # Considerar repetido si son muy similares
        if ultimo == penultimo:
            return True
        
        # También si uno contiene al otro (variaciones pequeñas)
        if len(ultimo) > 3 and len(penultimo) > 3:
            if ultimo in penultimo or penultimo in ultimo:
                return True
        
        return False
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # RESTO DE FUNCIONES (usando config desde BD)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    def generar_diagnostico_final(self, contexto: Dict) -> Optional[Dict]:
        """Generar diagnóstico CON CAUSAS"""
        
        if not self.ia_config.esta_activo():
            return None
        
        prompt = f"""Analiza los síntomas y genera un diagnóstico.

SÍNTOMAS:
{json.dumps(contexto, ensure_ascii=False, indent=2)}

Responde SOLO JSON:
{{
  "diagnostico": "Nombre de la condición",
  "confianza": 0.85,
  "causas": ["Causa 1", "Causa 2", "Causa 3"],
  "explicacion_causas": "Explicación clara",
  "consejos_dieta": ["Consejo 1", "Consejo 2"],
  "consejos_habitos": ["Hábito 1", "Hábito 2"],
  "advertencias": ["Si aplica"],
  "cuando_ver_medico": "Cuándo consultar"
}}"""

        try:
            config = self.ia_config.obtener_config()
            
            response = requests.post(
                'https://api.openai.com/v1/chat/completions',
                headers={
                    'Authorization': f"Bearer {config['api_key']}",
                    'Content-Type': 'application/json'
                },
                json={
                    'model': config['modelo'],  # ⭐ Lee desde BD
                    'messages': [
                        {'role': 'system', 'content': self.identidad},
                        {'role': 'user', 'content': prompt}
                    ],
                    'temperature': float(config.get('temperatura', 0.3)),  # ⭐ Lee desde BD
                    'max_tokens': int(config.get('max_tokens', 800))  # ⭐ Lee desde BD
                },
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                contenido = data['choices'][0]['message']['content'].strip()
                contenido = contenido.replace('```json', '').replace('```', '').strip()
                
                diagnostico = json.loads(contenido)
                
                self.ia_config.incrementar_consulta(0.03)
                
                return diagnostico
        
        except Exception as e:
            print(f"❌ Error diagnóstico: {e}")
            import traceback
            traceback.print_exc()
        
        return None
    
    def generar_receta_completa(self, diagnostico: str, contexto: Dict) -> Optional[Dict]:
        """Generar receta CON ANÁLISIS DE COMPOSICIÓN"""
        
        if not self.ia_config.esta_activo():
            return None
        
        productos = self.productos.obtener_todos()
        plantas = self.plantas.obtener_todas()
        remedios = self.remedios.obtener_todos()
        
        # ⭐ NUEVO: Formatear con composición
        productos_str = self._formatear_productos_con_composicion(productos)
        plantas_str = self._formatear_plantas_para_gpt(plantas)
        remedios_str = self._formatear_remedios_para_gpt(remedios)
        
        prompt = f"""Eres médico naturista experto. Analiza CIENTÍFICAMENTE qué producto es más efectivo.

DIAGNÓSTICO: {diagnostico}

PRODUCTOS DISPONIBLES (con composición):
{productos_str}

PLANTAS DISPONIBLES:
{plantas_str}

REMEDIOS CASEROS:
{remedios_str}

INSTRUCCIONES:
1. SIEMPRE recomienda AL MENOS 1 producto
2. Analiza la COMPOSICIÓN de cada producto
3. Elige el que tenga ingredientes activos MÁS efectivos para este caso
4. Explica POR QUÉ ese producto (basado en su composición)

CRITERIOS DE SELECCIÓN:
- Para INSOMNIO: busca triptófano, magnesio, valeriana, pasiflora
- Para ESTRÉS: busca ashwagandha, magnesio, vitamina B
- Para CANSANCIO: busca hierro, vitamina B12, ginseng, maca
- Para DOLOR: busca omega-3, cúrcuma, jengibre, MSM

REGLAS:
- Casos SIMPLES: 1 producto + 1-2 plantas + 1 remedio
- Casos COMPLEJOS: 1-2 productos + 1-2 plantas + 1 remedio
- PRIORIZA productos con ingredientes activos específicos para el caso
- Si ningún producto tiene ingredientes específicos, elige el más completo

Responde SOLO JSON:
{{
  "productos": [1],
  "plantas": [1, 2],
  "remedios": [1],
  "razon_producto": "Este producto contiene X que ayuda con Y porque Z"
}}"""

        try:
            config = self.ia_config.obtener_config()
            
            response = requests.post(
                'https://api.openai.com/v1/chat/completions',
                headers={
                    'Authorization': f"Bearer {config['api_key']}",
                    'Content-Type': 'application/json'
                },
                json={
                    'model': config['modelo'],
                    'messages': [
                        {'role': 'system', 'content': 'Eres médico que analiza composición química de productos naturales.'},
                        {'role': 'user', 'content': prompt}
                    ],
                    'temperature': 0.3,
                    'max_tokens': 400
                },
                timeout=25
            )
            
            if response.status_code == 200:
                data = response.json()
                contenido = data['choices'][0]['message']['content'].strip()
                contenido = contenido.replace('```json', '').replace('```', '').strip()
                
                receta = json.loads(contenido)
                
                self.ia_config.incrementar_consulta(0.02)
                
                # ⭐ Agregar explicación de por qué ese producto
                print(f"   ✅ Producto recomendado: {receta.get('razon_producto', 'N/A')}")
                
                return receta
        
        except Exception as e:
            print(f"❌ Error receta: {e}")
        
        return None
    
    def _formatear_productos_con_composicion(self, productos: List[Dict]) -> str:
        """Formatear productos CON análisis de composición"""
        lineas = []
        for p in productos[:10]:
            precio = float(p.get('precio', 0))
            
            lineas.append(f"ID {p['id']}: {p['nombre']} (S/.{precio:.0f})")
            lineas.append(f"   Para qué: {p.get('para_que_sirve', 'N/A')[:100]}")
            
            # ⭐ COMPOSICIÓN
            if p.get('composicion_activos'):
                lineas.append(f"   Composición: {p['composicion_activos'][:150]}")
            
            if p.get('mecanismo_accion'):
                lineas.append(f"   Cómo funciona: {p['mecanismo_accion'][:150]}")
            
            if p.get('efectividad_estimada'):
                efectividad_pct = float(p['efectividad_estimada']) * 100
                lineas.append(f"   Efectividad: {efectividad_pct:.0f}%")
            
            lineas.append("")
        
        return '\n'.join(lineas)
    
    def investigar_plantas_para_diagnostico(self, diagnostico: str) -> List[Dict]:
        """Investigar plantas con WEB SEARCH REAL"""
        
        if not self.ia_config.esta_activo():
            return []
        
        print(f"   🌐 Buscando plantas REALES en internet para {diagnostico}...")
        
        info_web = self._buscar_info_web(f"plantas medicinales naturales para {diagnostico}")
        
        prompt = f"""Analiza esta información REAL de internet sobre plantas para {diagnostico}:

INFORMACIÓN DE INTERNET:
{info_web}

Extrae 2 plantas medicinales REALES, VERIFICADAS y FÁCILES de conseguir.

Responde SOLO JSON:
[
  {{
    "nombre_comun": "Nombre común",
    "nombre_cientifico": "Nombre científico",
    "propiedades": "Propiedades principales",
    "dosis": "Dosis recomendada",
    "forma_uso": "Infusión/Decocción/Tópico",
    "preparacion": "Instrucciones simples",
    "cuando_tomar": "Mejor momento"
  }}
]

IMPORTANTE: Solo plantas mencionadas en la información proporcionada."""

        try:
            config = self.ia_config.obtener_config()
            
            response = requests.post(
                'https://api.openai.com/v1/chat/completions',
                headers={
                    'Authorization': f"Bearer {config['api_key']}",
                    'Content-Type': 'application/json'
                },
                json={
                    'model': config['modelo'],  # ⭐ Lee desde BD
                    'messages': [
                        {'role': 'system', 'content': self.identidad + '\n\nExtrae plantas REALES de información verificada.'},
                        {'role': 'user', 'content': prompt}
                    ],
                    'temperature': 0.3,
                    'max_tokens': 800
                },
                timeout=35
            )
            
            if response.status_code == 200:
                data = response.json()
                contenido = data['choices'][0]['message']['content'].strip()
                contenido = contenido.replace('```json', '').replace('```', '').strip()
                
                plantas = json.loads(contenido)
                
                self.ia_config.incrementar_consulta(0.03)
                
                print(f"   ✅ Encontré {len(plantas)} plantas verificadas")
                for p in plantas:
                    print(f"      • {p['nombre_comun']}")
                
                return plantas
        
        except Exception as e:
            print(f"❌ Error investigar plantas: {e}")
            import traceback
            traceback.print_exc()
        
        return []
    
    def _buscar_info_web(self, query: str) -> str:
        """Buscar información REAL en internet"""
        try:
            if WEB_SEARCH_DISPONIBLE:
                buscador = obtener_buscador()
                info = buscador.buscar(query, num_resultados=5)
                return info
            else:
                return f"""Investiga en tu conocimiento médico actualizado: {query}

Proporciona información verificada sobre plantas/remedios:
- Comunes y accesibles
- Con respaldo tradicional o científico
- Seguros para uso general"""
            
        except Exception as e:
            print(f"⚠️ Error web search: {e}")
            return "Investiga plantas/remedios verificados y comunes."
    
    def investigar_remedios_para_diagnostico(self, diagnostico: str) -> List[Dict]:
        """Investigar remedios con WEB SEARCH REAL"""
        
        if not self.ia_config.esta_activo():
            return []
        
        print(f"   🌐 Buscando remedios REALES en internet para {diagnostico}...")
        
        info_web = self._buscar_info_web(f"remedios caseros naturales efectivos para {diagnostico}")
        
        prompt = f"""Analiza esta información REAL sobre remedios para {diagnostico}:

INFORMACIÓN DE INTERNET:
{info_web}

Extrae 2 remedios caseros DIFERENTES (NO Aloe Vera).

Requisitos:
- Ingredientes comunes y accesibles
- Preparación simple
- Remedios PROBADOS
- Económicos

Responde SOLO JSON:
[
  {{
    "nombre": "Nombre descriptivo",
    "descripcion": "Descripción breve",
    "ingredientes": "Lista de ingredientes",
    "preparacion": "Pasos de preparación",
    "como_usar": "Cómo aplicar/tomar",
    "frecuencia": "Frecuencia de uso"
  }}
]

IMPORTANTE: Solo remedios mencionados en la información."""

        try:
            config = self.ia_config.obtener_config()
            
            response = requests.post(
                'https://api.openai.com/v1/chat/completions',
                headers={
                    'Authorization': f"Bearer {config['api_key']}",
                    'Content-Type': 'application/json'
                },
                json={
                    'model': config['modelo'],  # ⭐ Lee desde BD
                    'messages': [
                        {
                            'role': 'system', 
                            'content': self.identidad + '\n\nExtrae remedios REALES de información verificada. NO repitas remedios.'
                        },
                        {'role': 'user', 'content': prompt}
                    ],
                    'temperature': 0.4,
                    'max_tokens': 800
                },
                timeout=35
            )
            
            if response.status_code == 200:
                data = response.json()
                contenido = data['choices'][0]['message']['content'].strip()
                contenido = contenido.replace('```json', '').replace('```', '').strip()
                
                remedios = json.loads(contenido)
                
                self.ia_config.incrementar_consulta(0.03)
                
                print(f"   ✅ Encontré {len(remedios)} remedios verificados")
                for r in remedios:
                    print(f"      • {r['nombre']}")
                
                return remedios
        
        except Exception as e:
            print(f"❌ Error investigar remedios: {e}")
            import traceback
            traceback.print_exc()
        
        return []
    
    def responder_duda_tratamiento(self, contexto: Dict) -> str:
        """Responder dudas sobre el tratamiento"""
        
        if not self.ia_config.esta_activo():
            return "Lo siento, no puedo responder ahora."
        
        prompt = f"""El paciente tiene este tratamiento:

DIAGNÓSTICO: {contexto['diagnostico']}
PRODUCTOS: {', '.join(contexto['productos'])}
PLANTAS: {', '.join(contexto['plantas'])}

PREGUNTA DEL PACIENTE:
{contexto['pregunta']}

Responde clara, breve y práctica como Kairos.
Máximo 3-4 líneas."""

        try:
            config = self.ia_config.obtener_config()
            
            response = requests.post(
                'https://api.openai.com/v1/chat/completions',
                headers={
                    'Authorization': f"Bearer {config['api_key']}",
                    'Content-Type': 'application/json'
                },
                json={
                    'model': config['modelo'],  # ⭐ Lee desde BD
                    'messages': [
                        {'role': 'system', 'content': self.identidad},
                        {'role': 'user', 'content': prompt}
                    ],
                    'temperature': 0.5,
                    'max_tokens': 200
                },
                timeout=20
            )
            
            if response.status_code == 200:
                data = response.json()
                respuesta = data['choices'][0]['message']['content'].strip()
                
                self.ia_config.incrementar_consulta(0.01)
                
                return respuesta
        
        except Exception as e:
            print(f"❌ Error respondiendo duda: {e}")
        
        return "Lo siento, no pude procesar tu pregunta."
    
    def _formatear_productos_para_gpt(self, productos: List[Dict]) -> str:
        """Formatear productos para GPT"""
        lineas = []
        for p in productos[:10]:
            descripcion = p.get('para_que_sirve', '') or p.get('descripcion_corta', '')
            precio = float(p.get('precio', 0))
            lineas.append(f"ID {p['id']}: {p['nombre']} (S/.{precio:.0f}) - {descripcion[:100]}")
        return '\n'.join(lineas)
    
    def _formatear_plantas_para_gpt(self, plantas: List[Dict]) -> str:
        """Formatear plantas para GPT"""
        lineas = []
        for p in plantas[:15]:
            sirve = p.get('propiedades_curativas', '') or p.get('sintomas_que_trata', '')
            lineas.append(f"ID {p['id']}: {p['nombre_comun']} - {sirve[:80]}")
        return '\n'.join(lineas)
    
    def _formatear_remedios_para_gpt(self, remedios: List[Dict]) -> str:
        """Formatear remedios para GPT"""
        lineas = []
        for r in remedios[:10]:
            desc = r.get('descripcion', '')
            lineas.append(f"ID {r['id']}: {r['nombre']} - {desc[:80]}")
        return '\n'.join(lineas)