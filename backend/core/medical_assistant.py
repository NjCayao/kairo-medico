"""
Medical Assistant - Doctor de Cabecera COMPLETO
Versión CORREGIDA con nombre real del usuario
Creado por Nilson Cayao
"""

import sys
import os
from typing import Dict, List, Tuple, Optional
from datetime import datetime
import json
import requests

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BASE_DIR)
sys.path.insert(0, os.path.join(BASE_DIR, 'backend'))

from backend.core.classifier import IntentClassifier
from backend.database.productos_manager import ProductosManager
from backend.core.ia_config_manager import IAConfigManager

class MedicalAssistant:
    """
    Doctor de Cabecera Virtual - Kairos
    
    Características:
    - Usa el nombre REAL del paciente
    - Conversación natural y empática
    - No repite saludos ni presentaciones
    - Actúa como doctor de confianza
    - Hace pocas preguntas pero relevantes
    - Creado por Nilson Cayao
    """
    
    def __init__(self, modo_preguntas: str = 'dinamico'):
        """Inicializar asistente médico"""
        
        # Componentes
        self.classifier = IntentClassifier()
        self.productos = ProductosManager()
        self.ia_config = IAConfigManager()
        
        # Modo de preguntas
        self.modo_preguntas = modo_preguntas
        
        # INFORMACIÓN DEL USUARIO
        self.usuario_nombre = None
        self.usuario_primer_nombre = None
        self.usuario_dni = None
        
        # CONTROL DE CONVERSACIÓN
        self.ya_saludo = False
        self.ya_se_presento = False
        self.interacciones_totales = 0
        
        # Estado de la conversación
        self.contexto = {
            'sintoma_principal': None,
            'sintomas_adicionales': [],
            'ubicacion_dolor': None,
            'duracion': None,
            'intensidad': None,
            'momento_dia': None,
            'factores_mejoran': [],
            'factores_empeoran': [],
            'medicamentos_actuales': [],
            'alergias': [],
            'preguntas_realizadas': [],
            'respuestas_usuario': [],
            'informacion_clave': {}
        }
        
        # Contador
        self.preguntas_realizadas = 0
        self.max_preguntas = 6  # Menos preguntas, más análisis
        
        # Estado
        self.consulta_iniciada = False
        self.diagnostico_completo = False
        
        print("🤖 Kairos - Doctor de Cabecera Virtual")
        print(f"   Creado por: Nilson Cayao")
        print(f"   Modo: {modo_preguntas.upper()}")
        
        if modo_preguntas == 'dinamico' and self.ia_config.esta_activo():
            print(f"   IA: ✅ Activa")
        else:
            if modo_preguntas == 'dinamico':
                print(f"   IA: ⚠️ No disponible, modo estático")
                self.modo_preguntas = 'estatico'
    
    def procesar_mensaje(self, mensaje: str, usuario_info: Dict = None) -> Dict:
        """
        Procesar mensaje del usuario
        
        Args:
            mensaje: Mensaje del usuario
            usuario_info: {'nombre': 'Juan Pérez', 'dni': '12345678', 'edad': 30}
        
        Returns:
            Dict con respuesta y metadata
        """
        
        # GUARDAR INFO DEL USUARIO (solo primera vez)
        if usuario_info and not self.usuario_nombre:
            self.usuario_nombre = usuario_info.get('nombre', '')
            self.usuario_dni = usuario_info.get('dni', '')
            
            # Extraer primer nombre
            if self.usuario_nombre:
                self.usuario_primer_nombre = self.usuario_nombre.split()[0]
            
            print(f"👤 Paciente: {self.usuario_nombre} (DNI: {self.usuario_dni})")
        
        self.interacciones_totales += 1
        
        # Clasificar intención
        intencion, confianza, _ = self.classifier.predecir(mensaje)
        
        print(f"💭 Mensaje {self.interacciones_totales}: {intencion} ({confianza:.0%})")
        
        # Guardar en contexto
        self.contexto['preguntas_realizadas'].append(mensaje)
        
        # Generar respuesta según intención
        if intencion == 'saludo':
            respuesta = self._respuesta_saludo()
            tipo = 'saludo'
            
        elif intencion == 'consulta_medica':
            respuesta = self._respuesta_consulta_medica(mensaje)
            tipo = 'consulta'
            
        elif intencion == 'pregunta_producto':
            respuesta = self._respuesta_pregunta_producto(mensaje)
            tipo = 'info_producto'
            
        elif intencion == 'pregunta_uso':
            respuesta = self._respuesta_pregunta_uso(mensaje)
            tipo = 'info_uso'
            
        elif intencion == 'pregunta_precio':
            respuesta = self._respuesta_pregunta_precio(mensaje)
            tipo = 'info_precio'
            
        elif intencion == 'despedida':
            respuesta = self._respuesta_despedida()
            tipo = 'despedida'
            
        else:
            respuesta = self._respuesta_desconocida(mensaje)
            tipo = 'desconocida'
        
        return {
            'respuesta': respuesta,
            'intencion': intencion,
            'confianza': confianza,
            'tipo_respuesta': tipo,
            'contexto': self.contexto.copy(),
            'diagnostico_listo': self.diagnostico_completo
        }
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # RESPUESTAS
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    def _respuesta_saludo(self) -> str:
        """Respuesta a saludos"""
        
        if not self.ya_saludo:
            # Primera vez
            self.ya_saludo = True
            
            if self.usuario_primer_nombre:
                return f"¡Hola {self.usuario_primer_nombre}! 👋 Soy Kairos, tu médico de cabecera virtual en el que puedes confiar. ¿Qué molestia te trae hoy?"
            else:
                return "¡Hola! 👋 Soy Kairos, tu médico de cabecera virtual. ¿En qué puedo ayudarte?"
        else:
            # Ya saludó antes
            if self.usuario_primer_nombre:
                return f"Hola de nuevo {self.usuario_primer_nombre} 😊. ¿En qué más te ayudo?"
            else:
                return "Hola otra vez. ¿Qué más necesitas?"
    
    def _respuesta_consulta_medica(self, mensaje: str) -> str:
        """Respuesta a consulta médica - COMO DOCTOR REAL"""
        
        sintoma = self._extraer_sintoma(mensaje)
        
        if not self.consulta_iniciada:
            # PRIMERA VEZ - Iniciar consulta
            self.consulta_iniciada = True
            self.contexto['sintoma_principal'] = sintoma
            
            # Respuesta empática + primera pregunta
            if self.usuario_primer_nombre:
                empatia = f"Entiendo {self.usuario_primer_nombre}, {sintoma}."
            else:
                empatia = f"Entiendo, {sintoma}."
            
            primera_pregunta = self._siguiente_pregunta_diagnostico()
            
            return f"{empatia} {primera_pregunta}"
        
        else:
            # YA EN CONSULTA - Guardar respuesta y continuar
            self.contexto['respuestas_usuario'].append(mensaje)
            self.preguntas_realizadas += 1
            
            # Extraer información
            self._extraer_informacion_clave(mensaje)
            
            # ¿Ya suficiente info?
            if self.preguntas_realizadas >= self.max_preguntas or self._tiene_info_suficiente():
                self.diagnostico_completo = True
                
                if self.usuario_primer_nombre:
                    return f"Perfecto {self.usuario_primer_nombre}, ya tengo toda la información necesaria. Déjame analizar tu caso... 🔍"
                else:
                    return "Perfecto, ya tengo toda la información. Analizando tu caso... 🔍"
            
            # Siguiente pregunta
            return self._siguiente_pregunta_diagnostico()
    
    def _respuesta_pregunta_producto(self, mensaje: str) -> str:
        """Respuesta sobre productos"""
        
        mensaje_lower = mensaje.lower()
        
        if 'moringa' in mensaje_lower:
            producto = self.productos.obtener_por_id(1)
            if producto:
                return f"""🌿 **Moringa**

**Para qué sirve:**
{producto.get('para_que_sirve', 'Balance hormonal, energía, antiinflamatorio')}

**Precio:** S/. {producto.get('precio', 35):.2f}

¿Quieres saber el modo de uso{', ' + self.usuario_primer_nombre if self.usuario_primer_nombre else ''}?"""
        
        elif 'ganoderma' in mensaje_lower:
            producto = self.productos.obtener_por_id(2)
            if producto:
                return f"""🍄 **Ganoderma (Reishi)**

**Para qué sirve:**
{producto.get('para_que_sirve', 'Reduce estrés, mejora sueño, fortalece defensas')}

**Precio:** S/. {producto.get('precio', 40):.2f}

¿Necesitas más información?"""
        
        return "Tenemos **Moringa** y **Ganoderma**. ¿Sobre cuál quieres saber?"
    
    def _respuesta_pregunta_uso(self, mensaje: str) -> str:
        """Respuesta sobre modo de uso"""
        
        return f"""Para darte el modo de uso exacto{', ' + self.usuario_primer_nombre if self.usuario_primer_nombre else ''}, necesito saber:

1. ¿Qué producto? (Moringa o Ganoderma)
2. ¿Para qué molestia?

Así te doy instrucciones precisas."""
    
    def _respuesta_pregunta_precio(self, mensaje: str) -> str:
        """Respuesta sobre precios"""
        
        productos = self.productos.obtener_todos()
        
        respuesta = "💰 **Precios:**\n\n"
        for p in productos:
            respuesta += f"• {p['nombre']}: S/. {p['precio']:.2f}\n"
        
        respuesta += f"\n¿Te gustaría que diagnostique tu caso{', ' + self.usuario_primer_nombre if self.usuario_primer_nombre else ''}?"
        
        return respuesta
    
    def _respuesta_despedida(self) -> str:
        """Respuesta a despedida"""
        
        if self.usuario_primer_nombre:
            return f"¡Cuídate mucho {self.usuario_primer_nombre}! Si necesitas algo más, aquí estoy. ¡Que te mejores! 💚"
        else:
            return "¡Cuídate! Si necesitas algo más, aquí estoy. ¡Que te mejores! 💚"
    
    def _respuesta_desconocida(self, mensaje: str) -> str:
        """Respuesta cuando no entiende"""
        
        # Si está en consulta, asumir que es respuesta a pregunta
        if self.consulta_iniciada:
            return self._respuesta_consulta_medica(mensaje)
        
        return f"""No entendí bien{', ' + self.usuario_primer_nombre if self.usuario_primer_nombre else ''}. 🤔

Puedo ayudarte con:
• 🏥 Consultas médicas
• 💊 Información de productos
• 💰 Precios

¿Qué necesitas?"""
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # GENERACIÓN DE PREGUNTAS
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    def _siguiente_pregunta_diagnostico(self) -> str:
        """Generar siguiente pregunta"""
        
        if self.modo_preguntas == 'dinamico' and self.ia_config.esta_activo():
            return self._generar_pregunta_con_gpt()
        else:
            return self._generar_pregunta_estatica()
    
    def _generar_pregunta_con_gpt(self) -> str:
        """Generar pregunta con GPT"""
        
        sintoma = self.contexto['sintoma_principal']
        respuestas = "\n".join([f"- {r}" for r in self.contexto['respuestas_usuario']])
        
        info_capturada = []
        if self.contexto.get('ubicacion_dolor'):
            info_capturada.append(f"Ubicación: {self.contexto['ubicacion_dolor']}")
        if self.contexto.get('duracion'):
            info_capturada.append(f"Duración: {self.contexto['duracion']}")
        if self.contexto.get('intensidad'):
            info_capturada.append(f"Intensidad: {self.contexto['intensidad']}/10")
        
        info_str = "\n".join(info_capturada) if info_capturada else "Ninguna"
        
        prompt = f"""Eres Kairos, médico de cabecera cálido.

PACIENTE: {self.usuario_nombre or 'Paciente'}
SÍNTOMA: {sintoma}

RESPUESTAS PREVIAS:
{respuestas or 'Ninguna'}

INFO CAPTURADA:
{info_str}

GENERA UNA PREGUNTA:
- Corta (máximo 12 palabras)
- Empática y natural
- Que ayude al diagnóstico
- NO repitas info ya capturada
- Usa el nombre del paciente si lo tienes

SOLO LA PREGUNTA:"""
        
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
                        {'role': 'system', 'content': 'Eres médico empático.'},
                        {'role': 'user', 'content': prompt}
                    ],
                    'temperature': 0.7,
                    'max_tokens': 40
                },
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                pregunta = data['choices'][0]['message']['content'].strip()
                pregunta = pregunta.replace('"', '').replace("'", '')
                
                self.ia_config.incrementar_consulta(0.001)
                
                return pregunta
            else:
                return self._generar_pregunta_estatica()
                
        except Exception as e:
            print(f"   ⚠️ GPT error: {e}")
            return self._generar_pregunta_estatica()
    
    def _generar_pregunta_estatica(self) -> str:
        """Preguntas predefinidas (fallback)"""
        
        n = len(self.contexto['respuestas_usuario'])
        nombre = self.usuario_primer_nombre
        
        if n == 0:
            return f"¿Dónde exactamente{', ' + nombre if nombre else ''}?"
        elif n == 1:
            return f"¿Desde hace cuánto tiempo{', ' + nombre if nombre else ''}?"
        elif n == 2:
            return "Del 1 al 10, ¿qué tan fuerte es?"
        elif n == 3:
            return "¿En qué momento del día es peor?"
        elif n == 4:
            return "¿Algo hace que mejore?"
        else:
            return "¿Algo hace que empeore?"
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # ANÁLISIS
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    def _extraer_informacion_clave(self, respuesta: str):
        """Extraer información de la respuesta"""
        
        respuesta_lower = respuesta.lower()
        
        # Ubicación
        ubicaciones = ['cabeza', 'frente', 'sienes', 'nuca', 'estomago', 'barriga',
                      'pecho', 'espalda', 'piernas', 'brazos', 'cuello', 'muslo',
                      'pantorrilla', 'pie', 'mano']
        for ub in ubicaciones:
            if ub in respuesta_lower:
                self.contexto['ubicacion_dolor'] = ub
                break
        
        # Duración
        if 'dia' in respuesta_lower or 'dias' in respuesta_lower:
            self.contexto['duracion'] = 'días'
        elif 'semana' in respuesta_lower or 'semanas' in respuesta_lower:
            self.contexto['duracion'] = 'semanas'
        elif 'mes' in respuesta_lower or 'meses' in respuesta_lower:
            self.contexto['duracion'] = 'meses'
        
        # Intensidad
        import re
        numeros = re.findall(r'\b([0-9]|10)\b', respuesta)
        if numeros:
            self.contexto['intensidad'] = int(numeros[0])
        
        # Momento
        if 'manana' in respuesta_lower or 'matutino' in respuesta_lower:
            self.contexto['momento_dia'] = 'mañana'
        elif 'tarde' in respuesta_lower:
            self.contexto['momento_dia'] = 'tarde'
        elif 'noche' in respuesta_lower:
            self.contexto['momento_dia'] = 'noche'
        
        # Factores
        if 'descanso' in respuesta_lower or 'dormir' in respuesta_lower:
            if 'descanso' not in self.contexto['factores_mejoran']:
                self.contexto['factores_mejoran'].append('descanso')
        
        if 'estres' in respuesta_lower or 'trabajo' in respuesta_lower:
            if 'estrés' not in self.contexto['factores_empeoran']:
                self.contexto['factores_empeoran'].append('estrés')
    
    def _extraer_sintoma(self, mensaje: str) -> str:
        """Extraer síntoma del mensaje"""
        
        mensaje_lower = mensaje.lower()
        
        sintomas = {
            'cabeza': 'dolor de cabeza',
            'cefalea': 'dolor de cabeza',
            'migrana': 'migraña',
            'estomago': 'dolor de estómago',
            'barriga': 'dolor de estómago',
            'gastritis': 'gastritis',
            'cansancio': 'fatiga crónica',
            'cansado': 'fatiga crónica',
            'fatiga': 'fatiga crónica',
            'estres': 'estrés',
            'ansiedad': 'ansiedad',
            'insomnio': 'insomnio',
            'muscular': 'dolor muscular',
            'musculo': 'dolor muscular',
            'pierna': 'dolor en pierna',
            'golpe': 'contusión por golpe'
        }
        
        for palabra, sintoma in sintomas.items():
            if palabra in mensaje_lower:
                return sintoma
        
        return mensaje.strip()
    
    def _tiene_info_suficiente(self) -> bool:
        """Verificar si ya hay suficiente info"""
        
        tiene_sintoma = self.contexto['sintoma_principal'] is not None
        tiene_respuestas = len(self.contexto['respuestas_usuario']) >= 4
        
        info_clave = sum([
            self.contexto.get('ubicacion_dolor') is not None,
            self.contexto.get('duracion') is not None,
            self.contexto.get('intensidad') is not None,
        ])
        
        return tiene_sintoma and tiene_respuestas and info_clave >= 2
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # UTILIDADES
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    def obtener_resumen_consulta(self) -> Dict:
        """Resumen de consulta"""
        return {
            'sintoma_principal': self.contexto['sintoma_principal'],
            'respuestas': self.contexto['respuestas_usuario'],
            'usuario': self.usuario_nombre,
            'dni': self.usuario_dni,
            'total_interacciones': self.interacciones_totales,
            'diagnostico_completo': self.diagnostico_completo
        }
    
    def reiniciar_conversacion(self):
        """Reiniciar para nuevo paciente"""
        
        self.usuario_nombre = None
        self.usuario_primer_nombre = None
        self.usuario_dni = None
        self.ya_saludo = False
        self.ya_se_presento = False
        self.interacciones_totales = 0
        
        self.contexto = {
            'sintoma_principal': None,
            'sintomas_adicionales': [],
            'ubicacion_dolor': None,
            'duracion': None,
            'intensidad': None,
            'momento_dia': None,
            'factores_mejoran': [],
            'factores_empeoran': [],
            'medicamentos_actuales': [],
            'alergias': [],
            'preguntas_realizadas': [],
            'respuestas_usuario': [],
            'informacion_clave': {}
        }
        
        self.preguntas_realizadas = 0
        self.consulta_iniciada = False
        self.diagnostico_completo = False


if __name__ == "__main__":
    print("="*70)
    print("🧪 TEST MEDICAL ASSISTANT CORREGIDO")
    print("="*70)
    
    asistente = MedicalAssistant(modo_preguntas='estatico')
    
    # Simular conversación con nombre real
    usuario = {
        'nombre': 'Jhonny Cayao',
        'dni': '47458840',
        'edad': 28
    }
    
    mensajes = [
        "hola",
        "tengo dolores musculares",
        "en el muslo",
        "como una semana",
        "un 7",
        "al caminar"
    ]
    
    print(f"\n👤 Paciente: {usuario['nombre']} (DNI: {usuario['dni']})\n")
    
    for msg in mensajes:
        print(f"👤 Usuario: {msg}")
        resultado = asistente.procesar_mensaje(msg, usuario)
        print(f"🤖 Kairos: {resultado['respuesta']}\n")
        
        if resultado['diagnostico_listo']:
            print("✅ Listo para diagnóstico\n")
            break
    
    print("="*70)