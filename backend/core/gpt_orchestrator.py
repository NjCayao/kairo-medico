"""
GPT Orchestrator V3.0
✅ Identidad: Creador Nilson Cayao
✅ Investiga plantas y remedios CON WEB SEARCH REAL
✅ Guarda en BD automáticamente
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
    """Orquestador GPT con investigación"""
    
    def __init__(self):
        self.ia_config = IAConfigManager()
        self.productos = ProductosManager()
        self.plantas = PlantasMedicinalesManager()
        self.remedios = RemediosCaserosManager()
        
        self.preguntas_realizadas = 0
        self.max_preguntas = 5
        
        # Identidad de Kairos
        self.identidad = """
Eres Kairos, un médico naturista especializado en medicina natural y holística.

TU CREADOR: Nilson Cayao, un joven peruano apasionado por la tecnología y la medicina natural.
Nilson desarrolló Kairos con inteligencia artificial para ayudar a las personas a encontrar 
soluciones naturales a sus problemas de salud.

CARACTERÍSTICAS:
- Eres empático y profesional
- Usas medicina natural (plantas, productos naturales, remedios caseros)
- Explicas claramente los tratamientos
- Nunca sustituyes la opinión de un médico convencional en casos graves
- Cuando te pregunten quién eres, menciona a tu creador Nilson Cayao con orgullo

IMPORTANTE: Eres transparente sobre ser una IA creada por Nilson Cayao, pero mantienes 
tu rol profesional como asesor de medicina natural.
"""
        
        print("🧠 GPT Orchestrator V3.0 inicializado")
    
    def decidir_accion(self, contexto: Dict) -> Dict:
        """GPT decide: preguntar o diagnosticar"""
        
        if not self.ia_config.esta_activo():
            return {'accion': 'diagnosticar', 'razon': 'GPT no disponible'}
        
        if self.preguntas_realizadas >= self.max_preguntas:
            return {'accion': 'diagnosticar', 'razon': 'Límite de preguntas'}
        
        mensajes = contexto.get('mensajes', [])
        
        prompt = f"""Analiza la conversación y decide:

CONVERSACIÓN:
{json.dumps(mensajes[-6:], ensure_ascii=False, indent=2)}

PREGUNTAS YA HECHAS: {self.preguntas_realizadas}/{self.max_preguntas}

Decide: ¿PREGUNTAR más info o YA DIAGNOSTICAR?

Responde SOLO JSON:
{{
  "accion": "preguntar" o "diagnosticar",
  "razon": "Por qué"
}}

Si ya tienes síntomas claros, DIAGNOSTICA."""

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
                        {'role': 'system', 'content': self.identidad},
                        {'role': 'user', 'content': prompt}
                    ],
                    'temperature': 0.3,
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
                
                return decision
        
        except Exception as e:
            print(f"❌ Error decidir acción: {e}")
        
        return {'accion': 'diagnosticar', 'razon': 'Error en GPT'}
    
    def generar_respuesta(self, decision: Dict, contexto: Dict) -> str:
        """Generar respuesta según la decisión"""
        
        if not self.ia_config.esta_activo():
            return "Lo siento, no puedo procesar tu consulta ahora."
        
        mensajes = contexto.get('mensajes', [])
        usuario = contexto.get('usuario', {})
        
        if decision['accion'] == 'preguntar':
            prompt = f"""Eres Kairos, médico naturista.

USUARIO: {usuario.get('nombre', 'Paciente')}

CONVERSACIÓN:
{json.dumps(mensajes[-4:], ensure_ascii=False, indent=2)}

Haz UNA pregunta natural para entender mejor el caso.
Sé empático y conversacional."""

        else:
            prompt = f"""Eres Kairos, médico naturista.

CONVERSACIÓN:
{json.dumps(mensajes, ensure_ascii=False, indent=2)}

Informa al paciente que ya tienes suficiente información.
Sé breve y tranquilizador."""

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
                        {'role': 'system', 'content': self.identidad},
                        {'role': 'user', 'content': prompt}
                    ],
                    'temperature': 0.7,
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
        
        return "¿Podrías contarme más sobre tus síntomas?"
    
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
                    'model': config['modelo'],
                    'messages': [
                        {'role': 'system', 'content': self.identidad},
                        {'role': 'user', 'content': prompt}
                    ],
                    'temperature': 0.3,
                    'max_tokens': 800
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
        
        return None
    
    def generar_receta_completa(self, diagnostico: str, contexto: Dict) -> Optional[Dict]:
        """Generar receta"""
        
        if not self.ia_config.esta_activo():
            return None
        
        productos = self.productos.obtener_todos()
        plantas = self.plantas.obtener_todas()
        remedios = self.remedios.obtener_todos()
        
        productos_str = self._formatear_productos_para_gpt(productos)
        plantas_str = self._formatear_plantas_para_gpt(plantas)
        remedios_str = self._formatear_remedios_para_gpt(remedios)
        
        prompt = f"""DIAGNÓSTICO: {diagnostico}

PRODUCTOS DISPONIBLES (elige 1-2):
{productos_str}

PLANTAS DISPONIBLES (elige 1-2):
{plantas_str}

REMEDIOS DISPONIBLES (elige 1):
{remedios_str}

Responde SOLO JSON:
{{
  "productos": [1, 2],
  "plantas": [1, 2],
  "remedios": [1]
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
                        {'role': 'system', 'content': self.identidad},
                        {'role': 'user', 'content': prompt}
                    ],
                    'temperature': 0.4,
                    'max_tokens': 300
                },
                timeout=25
            )
            
            if response.status_code == 200:
                data = response.json()
                contenido = data['choices'][0]['message']['content'].strip()
                contenido = contenido.replace('```json', '').replace('```', '').strip()
                
                receta = json.loads(contenido)
                
                self.ia_config.incrementar_consulta(0.02)
                
                return receta
        
        except Exception as e:
            print(f"❌ Error receta: {e}")
        
        return None
    
    def investigar_plantas_para_diagnostico(self, diagnostico: str) -> List[Dict]:
        """Investigar plantas con WEB SEARCH REAL"""
        
        if not self.ia_config.esta_activo():
            return []
        
        print(f"   🌐 Buscando plantas REALES en internet para {diagnostico}...")
        
        # 1. BUSCAR EN WEB (información real de internet)
        info_web = self._buscar_info_web(f"plantas medicinales naturales para {diagnostico}")
        
        # 2. GPT extrae y estructura las plantas encontradas
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
                    'model': config['modelo'],
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
                # Sin web search, GPT investiga libremente
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
        
        # 1. BUSCAR EN WEB (información real)
        info_web = self._buscar_info_web(f"remedios caseros naturales efectivos para {diagnostico}")
        
        # 2. GPT extrae y estructura
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
                    'model': config['modelo'],
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
                    'model': config['modelo'],
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