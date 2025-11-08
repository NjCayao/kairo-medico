"""
Medical Assistant - Cerebro principal de Kairos MEJORADO
Preguntas dinámicas generadas por GPT + Conversación inteligente
"""

import sys
import os
from typing import Dict, List, Tuple, Optional
from datetime import datetime
import json
import requests

# Agregar paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BASE_DIR)
sys.path.insert(0, os.path.join(BASE_DIR, 'backend'))

from backend.core.classifier import IntentClassifier
from backend.database.productos_manager import ProductosManager
from backend.core.ia_config_manager import IAConfigManager

class MedicalAssistant:
    """
    Asistente médico virtual de Kairos - VERSIÓN MEJORADA
    
    Mejoras v2.0:
    - Preguntas dinámicas generadas por GPT
    - Adaptación inteligente según respuestas
    - Detección automática de información suficiente
    - Modo conversacional natural
    """
    
    def __init__(self, modo_preguntas: str = 'dinamico'):
        """
        Inicializar asistente médico
        
        Args:
            modo_preguntas: 'dinamico' (GPT) o 'estatico' (hardcoded)
        """
        
        # Componentes
        self.classifier = IntentClassifier()
        self.productos = ProductosManager()
        self.ia_config = IAConfigManager()
        
        # Modo de preguntas
        self.modo_preguntas = modo_preguntas
        
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
            'informacion_clave': {}  # Para tracking de datos importantes
        }
        
        # Contador de preguntas
        self.preguntas_realizadas = 0
        self.max_preguntas = 8
        
        # Estado
        self.consulta_iniciada = False
        self.diagnostico_completo = False
        
        print("🤖 Kairos Medical Assistant MEJORADO inicializado")
        print(f"   Modo preguntas: {modo_preguntas.upper()}")
        if modo_preguntas == 'dinamico':
            if self.ia_config.esta_activo():
                print(f"   ✅ GPT disponible para preguntas dinámicas")
            else:
                print(f"   ⚠️ GPT no disponible, usando modo estático")
                self.modo_preguntas = 'estatico'
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # PROCESAMIENTO DE MENSAJES
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    def procesar_mensaje(self, mensaje: str, usuario_info: Dict = None) -> Dict:
        """
        Procesar mensaje del usuario y generar respuesta
        
        Args:
            mensaje: Mensaje del usuario
            usuario_info: Información del usuario (opcional)
            
        Returns:
            Dict con respuesta y datos
        """
        
        # Clasificar intención
        intencion, confianza, probabilidades = self.classifier.predecir(mensaje)
        
        print(f"💭 Intención: {intencion} ({confianza:.0%})")
        
        # Guardar en contexto
        self.contexto['preguntas_realizadas'].append(mensaje)
        
        # Determinar tipo de respuesta según intención
        if intencion == 'saludo':
            respuesta = self._respuesta_saludo(usuario_info)
            tipo_respuesta = 'saludo'
            
        elif intencion == 'consulta_medica':
            respuesta = self._respuesta_consulta_medica(mensaje)
            tipo_respuesta = 'consulta'
            
        elif intencion == 'pregunta_producto':
            respuesta = self._respuesta_pregunta_producto(mensaje)
            tipo_respuesta = 'info_producto'
            
        elif intencion == 'pregunta_uso':
            respuesta = self._respuesta_pregunta_uso(mensaje)
            tipo_respuesta = 'info_uso'
            
        elif intencion == 'pregunta_precio':
            respuesta = self._respuesta_pregunta_precio(mensaje)
            tipo_respuesta = 'info_precio'
            
        elif intencion == 'despedida':
            respuesta = self._respuesta_despedida()
            tipo_respuesta = 'despedida'
            
        else:
            respuesta = self._respuesta_desconocida(mensaje)
            tipo_respuesta = 'desconocida'
        
        return {
            'respuesta': respuesta,
            'intencion': intencion,
            'confianza': confianza,
            'tipo_respuesta': tipo_respuesta,
            'contexto': self.contexto.copy(),
            'diagnostico_listo': self.diagnostico_completo
        }
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # RESPUESTAS POR TIPO
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    def _respuesta_saludo(self, usuario_info: Dict = None) -> str:
        """Respuesta a saludos"""
        
        nombre = usuario_info.get('nombre', '') if usuario_info else ''
        nombre_primero = nombre.split()[0] if nombre else ''
        
        if nombre_primero:
            return f"¡Hola {nombre_primero}! 👋 Soy Kairos, tu asistente de salud natural. ¿En qué puedo ayudarte hoy?"
        else:
            return "¡Hola! 👋 Soy Kairos, tu asistente de salud natural. ¿Qué molestia tienes?"
    
    def _respuesta_consulta_medica(self, mensaje: str) -> str:
        """Respuesta a consulta médica - MEJORADO"""
        
        # Extraer síntoma del mensaje
        sintoma = self._extraer_sintoma(mensaje)
        
        if not self.consulta_iniciada:
            # Primera vez que menciona síntoma
            self.consulta_iniciada = True
            self.contexto['sintoma_principal'] = sintoma
            
            # Hacer primera pregunta (dinámica o estática)
            return self._siguiente_pregunta_diagnostico()
            
        else:
            # Ya estamos en consulta, guardar respuesta
            self.contexto['respuestas_usuario'].append(mensaje)
            self.preguntas_realizadas += 1
            
            # Analizar respuesta para extraer información clave
            self._extraer_informacion_clave(mensaje)
            
            # Verificar si ya tenemos suficiente información
            if self.preguntas_realizadas >= self.max_preguntas or self._tiene_info_suficiente():
                self.diagnostico_completo = True
                return "Perfecto, ya tengo toda la información necesaria. Dame un momento para analizar tu caso... 🔍"
            else:
                # Continuar con preguntas
                return self._siguiente_pregunta_diagnostico()
    
    def _respuesta_pregunta_producto(self, mensaje: str) -> str:
        """Respuesta sobre productos"""
        
        mensaje_lower = mensaje.lower()
        
        if 'moringa' in mensaje_lower:
            producto = self.productos.obtener_por_id(1)
            if producto:
                return f"""🌿 **{producto['nombre']}**

**¿Qué es?**
{producto['descripcion_corta']}

**Para qué sirve:**
{producto['para_que_sirve']}

**Beneficios principales:**
{producto['beneficios']}

**Precio:** S/. {producto['precio']:.2f}

¿Tienes alguna otra pregunta sobre la moringa?"""
        
        elif 'ganoderma' in mensaje_lower or 'reishi' in mensaje_lower:
            producto = self.productos.obtener_por_id(2)
            if producto:
                return f"""🍄 **{producto['nombre']}**

**¿Qué es?**
{producto['descripcion_corta']}

**Para qué sirve:**
{producto['para_que_sirve']}

**Beneficios principales:**
{producto['beneficios']}

**Precio:** S/. {producto['precio']:.2f}

¿Tienes alguna otra pregunta sobre el ganoderma?"""
        
        # Respuesta genérica
        productos = self.productos.obtener_todos()
        lista = "\n".join([f"• {p['nombre']} - S/. {p['precio']:.2f}" for p in productos])
        
        return f"""💊 **Nuestros Productos Naturales:**

{lista}

¿Sobre cuál te gustaría saber más?"""
    
    def _respuesta_pregunta_uso(self, mensaje: str) -> str:
        """Respuesta sobre modo de uso"""
        
        return """📋 **Modo de Uso General:**

Para darte la información exacta de cómo tomar el producto, primero necesito saber:

1. ¿Qué producto específico te interesa? (Moringa, Ganoderma, Aceite)
2. ¿Para qué molestia lo necesitas?

Así puedo darte las instrucciones precisas y personalizadas. 😊"""
    
    def _respuesta_pregunta_precio(self, mensaje: str) -> str:
        """Respuesta sobre precios"""
        
        productos = self.productos.obtener_todos()
        
        respuesta = "💰 **Nuestros Precios:**\n\n"
        
        for producto in productos:
            respuesta += f"• {producto['nombre']}\n"
            respuesta += f"  **S/. {producto['precio']:.2f}**\n"
            respuesta += f"  ({producto['presentacion']})\n\n"
        
        respuesta += "\n📦 **Nota:** El precio incluye el tratamiento completo recomendado.\n"
        respuesta += "¿Te gustaría saber qué producto se ajusta mejor a tu caso?"
        
        return respuesta
    
    def _respuesta_despedida(self) -> str:
        """Respuesta a despedida"""
        
        return """¡De nada! 😊 Fue un gusto ayudarte.

Recuerda:
✅ Sigue las indicaciones de la receta
✅ Mantén hábitos saludables
✅ Si tienes dudas, vuelve cuando quieras

¡Que te mejores pronto! 💚

*Puedes encontrar los productos en nuestra botica.*"""
    
    def _respuesta_desconocida(self, mensaje: str) -> str:
        """Respuesta cuando no se entiende"""
        
        return """Disculpa, no entendí bien tu pregunta. 🤔

Puedo ayudarte con:
- 🏥 Consultas médicas sobre tus síntomas
- 💊 Información sobre productos naturales
- 💰 Precios de productos
- 📋 Cómo usar los productos

¿Sobre qué te gustaría que hablemos?"""
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # GENERACIÓN DE PREGUNTAS - MEJORADO
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    def _siguiente_pregunta_diagnostico(self) -> str:
        """
        Generar siguiente pregunta para diagnóstico
        MODO DINÁMICO: Usa GPT para generar pregunta inteligente
        MODO ESTÁTICO: Usa preguntas predefinidas
        """
        
        if self.modo_preguntas == 'dinamico' and self.ia_config.esta_activo():
            return self._generar_pregunta_con_gpt()
        else:
            return self._generar_pregunta_estatica()
    
    def _generar_pregunta_con_gpt(self) -> str:
        """
        Generar pregunta usando GPT basándose en el contexto actual
        """
        
        # Construir contexto para GPT
        sintoma = self.contexto['sintoma_principal']
        respuestas_previas = "\n".join([
            f"- {r}" for r in self.contexto['respuestas_usuario']
        ])
        
        preguntas_ya_hechas = len(self.contexto['respuestas_usuario'])
        preguntas_restantes = self.max_preguntas - preguntas_ya_hechas
        
        # Información ya capturada
        info_capturada = []
        if self.contexto.get('ubicacion_dolor'):
            info_capturada.append(f"Ubicación: {self.contexto['ubicacion_dolor']}")
        if self.contexto.get('duracion'):
            info_capturada.append(f"Duración: {self.contexto['duracion']}")
        if self.contexto.get('intensidad'):
            info_capturada.append(f"Intensidad: {self.contexto['intensidad']}")
        
        info_str = "\n".join(info_capturada) if info_capturada else "Ninguna aún"
        
        prompt = f"""Eres un asistente médico haciendo un diagnóstico.

SÍNTOMA PRINCIPAL: {sintoma}

RESPUESTAS PREVIAS DEL PACIENTE:
{respuestas_previas if respuestas_previas else "Ninguna aún"}

INFORMACIÓN YA CAPTURADA:
{info_str}

PREGUNTAS RESTANTES: {preguntas_restantes}

GENERA UNA PREGUNTA:
- Corta y directa (máximo 15 palabras)
- Que ayude al diagnóstico
- Que NO repita información ya obtenida
- Enfocada en: ubicación, duración, intensidad, factores que mejoran/empeoran, síntomas adicionales

Responde SOLO con la pregunta, sin explicaciones.
"""
        
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
                        {'role': 'system', 'content': 'Eres asistente médico conciso.'},
                        {'role': 'user', 'content': prompt}
                    ],
                    'temperature': 0.7,
                    'max_tokens': 50
                },
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                pregunta = data['choices'][0]['message']['content'].strip()
                
                # Limpiar pregunta
                pregunta = pregunta.replace('"', '').replace("'", '')
                
                print(f"   🤖 Pregunta GPT: {pregunta}")
                
                # Incrementar contador de IA
                self.ia_config.incrementar_consulta(0.001)  # Costo bajo por pregunta
                
                return pregunta
            else:
                print(f"   ⚠️ GPT falló, usando pregunta estática")
                return self._generar_pregunta_estatica()
                
        except Exception as e:
            print(f"   ⚠️ Error GPT: {e}, usando pregunta estática")
            return self._generar_pregunta_estatica()
    
    def _generar_pregunta_estatica(self) -> str:
        """
        Generar pregunta usando lógica predefinida (fallback)
        """
        
        preguntas_realizadas = len(self.contexto['respuestas_usuario'])
        
        # Preguntas clave en orden de prioridad
        if preguntas_realizadas == 0:
            return f"Entiendo que tienes {self.contexto['sintoma_principal']}. ¿Dónde exactamente sientes esta molestia?"
        
        elif preguntas_realizadas == 1 and not self.contexto.get('duracion'):
            return "¿Desde hace cuánto tiempo tienes este problema? (días, semanas, meses)"
        
        elif preguntas_realizadas == 2 and not self.contexto.get('intensidad'):
            return "En una escala del 1 al 10, ¿qué tan fuerte es la molestia? (1=leve, 10=insoportable)"
        
        elif preguntas_realizadas == 3 and not self.contexto.get('momento_dia'):
            return "¿En qué momento del día es peor? (mañana, tarde, noche, todo el día)"
        
        elif preguntas_realizadas == 4 and len(self.contexto['factores_mejoran']) == 0:
            return "¿Algo hace que mejore? (descanso, comida, medicamento)"
        
        elif preguntas_realizadas == 5 and len(self.contexto['factores_empeoran']) == 0:
            return "¿Algo hace que empeore? (estrés, ciertos alimentos, actividades)"
        
        elif preguntas_realizadas == 6:
            return "¿Tomas algún medicamento actualmente?"
        
        else:
            return "¿Tienes alguna alergia a alimentos o medicamentos?"
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # ANÁLISIS Y EXTRACCIÓN
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    def _extraer_informacion_clave(self, respuesta: str):
        """
        Extraer información clave de la respuesta del usuario
        Actualiza el contexto automáticamente
        """
        
        respuesta_lower = respuesta.lower()
        
        # Detectar ubicación de dolor
        ubicaciones = ['cabeza', 'frente', 'sienes', 'nuca', 'estómago', 'barriga', 
                      'pecho', 'espalda', 'piernas', 'brazos', 'cuello']
        for ub in ubicaciones:
            if ub in respuesta_lower:
                self.contexto['ubicacion_dolor'] = ub
                break
        
        # Detectar duración
        if 'día' in respuesta_lower or 'dias' in respuesta_lower:
            self.contexto['duracion'] = 'días'
        elif 'semana' in respuesta_lower or 'semanas' in respuesta_lower:
            self.contexto['duracion'] = 'semanas'
        elif 'mes' in respuesta_lower or 'meses' in respuesta_lower:
            self.contexto['duracion'] = 'meses'
        elif 'año' in respuesta_lower or 'años' in respuesta_lower:
            self.contexto['duracion'] = 'años'
        
        # Detectar intensidad (números)
        import re
        numeros = re.findall(r'\b([0-9]|10)\b', respuesta)
        if numeros:
            self.contexto['intensidad'] = int(numeros[0])
        
        # Detectar momento del día
        momentos = ['mañana', 'tarde', 'noche', 'madrugada']
        for momento in momentos:
            if momento in respuesta_lower:
                self.contexto['momento_dia'] = momento
                break
        
        # Detectar factores que mejoran
        if 'descanso' in respuesta_lower or 'dormir' in respuesta_lower:
            self.contexto['factores_mejoran'].append('descanso')
        if 'comida' in respuesta_lower or 'comer' in respuesta_lower:
            self.contexto['factores_mejoran'].append('alimentación')
        
        # Detectar factores que empeoran
        if 'estrés' in respuesta_lower or 'estres' in respuesta_lower:
            self.contexto['factores_empeoran'].append('estrés')
        if 'actividad' in respuesta_lower or 'ejercicio' in respuesta_lower:
            self.contexto['factores_empeoran'].append('actividad física')
    
    def _extraer_sintoma(self, mensaje: str) -> str:
        """
        Extraer síntoma principal del mensaje
        """
        mensaje_lower = mensaje.lower()
        
        # Diccionario de síntomas comunes
        sintomas_conocidos = {
            'cabeza': 'dolor de cabeza',
            'cefalea': 'dolor de cabeza',
            'migraña': 'migraña',
            'estómago': 'dolor de estómago',
            'barriga': 'dolor de estómago',
            'gastritis': 'gastritis',
            'cansancio': 'fatiga crónica',
            'fatiga': 'fatiga crónica',
            'agotado': 'fatiga crónica',
            'estrés': 'estrés',
            'ansiedad': 'ansiedad',
            'insomnio': 'insomnio',
            'dormir': 'problemas de sueño',
            'quiste': 'quistes ováricos',
            'menstruación': 'irregularidad menstrual',
            'regla': 'irregularidad menstrual'
        }
        
        # Buscar síntoma conocido
        for palabra_clave, sintoma in sintomas_conocidos.items():
            if palabra_clave in mensaje_lower:
                return sintoma
        
        # Si no encuentra, usar el mensaje completo
        return mensaje.strip()
    
    def _tiene_info_suficiente(self) -> bool:
        """
        Verificar si tenemos suficiente información para diagnóstico
        """
        # Criterios mínimos
        tiene_sintoma = self.contexto['sintoma_principal'] is not None
        tiene_respuestas = len(self.contexto['respuestas_usuario']) >= 5
        
        # Verificar información clave capturada
        info_clave = sum([
            self.contexto.get('ubicacion_dolor') is not None,
            self.contexto.get('duracion') is not None,
            self.contexto.get('intensidad') is not None,
            len(self.contexto.get('factores_mejoran', [])) > 0 or 
            len(self.contexto.get('factores_empeoran', [])) > 0
        ])
        
        # Necesitamos al menos el síntoma + 5 respuestas + 2 datos clave
        return tiene_sintoma and tiene_respuestas and info_clave >= 2
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # UTILIDADES
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    def obtener_resumen_consulta(self) -> Dict:
        """
        Obtener resumen de la consulta
        """
        return {
            'sintoma_principal': self.contexto['sintoma_principal'],
            'sintomas_adicionales': self.contexto['sintomas_adicionales'],
            'respuestas': self.contexto['respuestas_usuario'],
            'preguntas': self.contexto['preguntas_realizadas'],
            'total_interacciones': self.preguntas_realizadas,
            'diagnostico_completo': self.diagnostico_completo,
            'informacion_clave': self.contexto['informacion_clave'],
            'modo_preguntas': self.modo_preguntas
        }
    
    def reiniciar_conversacion(self):
        """Reiniciar para nueva consulta"""
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
        
        print("🔄 Conversación reiniciada")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PRUEBAS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

if __name__ == "__main__":
    print("="*70)
    print(" "*15 + "🧪 TEST MEDICAL ASSISTANT MEJORADO")
    print("="*70)
    print()
    
    # Crear asistente (modo dinámico si GPT está disponible)
    asistente = MedicalAssistant(modo_preguntas='dinamico')
    
    # Simular conversación
    mensajes_prueba = [
        "Hola",
        "Me duele mucho la cabeza",
        "En la frente y las sienes",
        "Como una semana",
        "Un 7 de 10",
        "Por las mañanas es peor",
        "Mejora cuando descanso",
        "Empeora con el estrés"
    ]
    
    usuario_info = {
        'nombre': 'María López',
        'edad': 32
    }
    
    print("👤 Usuario: María López\n")
    print("━"*70)
    print("CONVERSACIÓN SIMULADA")
    print("━"*70)
    print()
    
    for i, mensaje in enumerate(mensajes_prueba, 1):
        print(f"👤 Usuario: {mensaje}")
        
        resultado = asistente.procesar_mensaje(mensaje, usuario_info)
        
        print(f"🤖 Kairos: {resultado['respuesta']}\n")
        
        if resultado['diagnostico_listo']:
            print("✅ Diagnóstico listo para generar\n")
            break
    
    # Resumen
    print("━"*70)
    print("RESUMEN DE CONSULTA")
    print("━"*70)
    resumen = asistente.obtener_resumen_consulta()
    print(f"Síntoma principal: {resumen['sintoma_principal']}")
    print(f"Modo preguntas: {resumen['modo_preguntas']}")
    print(f"Total preguntas: {len(resumen['preguntas'])}")
    print(f"Total respuestas: {len(resumen['respuestas'])}")
    print(f"Diagnóstico completo: {resumen['diagnostico_completo']}")
    
    print("\n" + "="*70)