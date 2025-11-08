"""
Intent Detector - Detector de Intenciones
Identifica qué quiere el usuario de forma inteligente
"""

import re
from typing import Dict, List, Tuple, Optional
from unidecode import unidecode

class IntentDetector:
    """
    Detector de intenciones del usuario
    Combina: Reglas + Palabras clave + Contexto
    """
    
    def __init__(self):
        """Inicializar detector"""
        
        # Patrones de intenciones
        self.patrones = {
            # Saludos
            'saludo': [
                'hola', 'buenos dias', 'buenas tardes', 'buenas noches',
                'hey', 'que tal', 'saludos', 'alo', 'buenas'
            ],
            
            # Despedida
            'despedida': [
                'adios', 'chao', 'hasta luego', 'nos vemos', 'bye',
                'gracias', 'muchas gracias', 'eso es todo', 'ya me voy'
            ],
            
            # Preguntas sobre Kairos
            'quien_eres': [
                'quien eres', 'que eres', 'como te llamas', 'tu nombre',
                'eres kairos', 'presentate', 'quien es kairos'
            ],
            
            # Preguntas sobre el creador
            'quien_te_creo': [
                'quien te creo', 'quien te hizo', 'tu creador', 'quien te programo',
                'quien te desarrollo', 'quien esta detras', 'quien te invento'
            ],
            
            # Capacidades
            'que_puedes_hacer': [
                'que puedes hacer', 'en que ayudas', 'para que sirves',
                'como funcionas', 'que haces', 'ayudas con', 'me ayudas'
            ],
            
            # Síntomas / Consulta médica
            'sintoma': [
                'me duele', 'tengo dolor', 'me siento', 'siento',
                'tengo', 'padezco', 'sufro', 'me molesta',
                'dolor de', 'problemas de', 'malestar'
            ],
            
            # Estados/condiciones
            'estado_salud': [
                'cansado', 'cansancio', 'fatiga', 'agotado', 'debil',
                'estres', 'ansiedad', 'nervioso', 'deprimido', 'triste',
                'insomnio', 'no duermo', 'mal', 'enfermo', 'jodido'
            ],
            
            # Preguntas sobre productos
            'producto': [
                'moringa', 'ganoderma', 'reishi', 'aceite',
                'que productos', 'que vendes', 'que tienes'
            ],
            
            # Preguntas sobre precios
            'precio': [
                'cuanto cuesta', 'cuanto vale', 'precio', 'costo',
                'cuanto sale', 'que precio', 'cuanto es'
            ],
            
            # Modo de uso
            'modo_uso': [
                'como lo tomo', 'como se toma', 'como se usa',
                'modo de uso', 'instrucciones', 'como lo uso',
                'cuantas capsulas', 'dosis'
            ],
            
            # Confirmación
            'confirmacion': [
                'si', 'ok', 'esta bien', 'correcto', 'exacto',
                'claro', 'vale', 'entiendo', 'de acuerdo', 'ajá'
            ],
            
            # Negación
            'negacion': [
                'no', 'nope', 'para nada', 'negativo', 'no quiero',
                'no gracias', 'tampoco', 'de ninguna manera'
            ]
        }
        
        # Palabras que indican síntomas específicos
        self.sintomas_especificos = {
            'dolor_cabeza': ['cabeza', 'cefalea', 'migraña', 'migrana'],
            'dolor_estomago': ['estomago', 'barriga', 'vientre', 'panza'],
            'gastritis': ['gastritis', 'acidez', 'reflujo'],
            'cansancio': ['cansado', 'cansancio', 'fatiga', 'agotado', 'sin energia'],
            'estres': ['estres', 'estresado', 'tension', 'presion'],
            'ansiedad': ['ansiedad', 'ansioso', 'nervioso', 'nervios'],
            'insomnio': ['insomnio', 'no duermo', 'no puedo dormir', 'mal sueno'],
            'depresion': ['depresion', 'deprimido', 'triste', 'tristeza'],
            'gripe': ['gripe', 'resfriado', 'resfrio', 'catarro'],
            'tos': ['tos', 'toser'],
            'fiebre': ['fiebre', 'calentura', 'temperatura'],
        }
        
        print("🎯 Intent Detector inicializado")
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # DETECCIÓN PRINCIPAL
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    def detectar(self, mensaje: str, contexto: Dict = None) -> Dict:
        """
        Detectar intención del mensaje
        
        Args:
            mensaje: Texto del usuario
            contexto: Contexto de la conversación
            
        Returns:
            Dict con intención, confianza, entidades extraídas
        """
        
        # Normalizar mensaje
        mensaje_norm = self._normalizar(mensaje)
        
        # Detectar intención primaria
        intencion_primaria = self._detectar_intencion_primaria(mensaje_norm)
        
        # Detectar síntomas específicos
        sintomas = self._detectar_sintomas(mensaje_norm)
        
        # Extraer entidades
        entidades = self._extraer_entidades(mensaje_norm)
        
        # Calcular confianza
        confianza = self._calcular_confianza(
            mensaje_norm, 
            intencion_primaria, 
            sintomas
        )
        
        resultado = {
            'intencion': intencion_primaria,
            'confianza': confianza,
            'sintomas': sintomas,
            'entidades': entidades,
            'es_consulta_medica': intencion_primaria in ['sintoma', 'estado_salud'] or len(sintomas) > 0,
            'es_conversacional': intencion_primaria in ['saludo', 'despedida', 'quien_eres', 'quien_te_creo', 'que_puedes_hacer'],
            'es_transaccional': intencion_primaria in ['producto', 'precio', 'modo_uso']
        }
        
        print(f"   🎯 Detectado: {intencion_primaria} (conf: {confianza:.0%})")
        if sintomas:
            print(f"   💊 Síntomas: {', '.join(sintomas)}")
        
        return resultado
    
    def _detectar_intencion_primaria(self, mensaje: str) -> str:
        """Detectar la intención principal"""
        
        # Verificar cada patrón
        for intencion, palabras_clave in self.patrones.items():
            for palabra in palabras_clave:
                if palabra in mensaje:
                    return intencion
        
        # Si menciona síntomas específicos
        if self._tiene_sintoma(mensaje):
            return 'sintoma'
        
        # Default
        return 'desconocida'
    
    def _detectar_sintomas(self, mensaje: str) -> List[str]:
        """Detectar síntomas específicos mencionados"""
        
        sintomas_encontrados = []
        
        for sintoma, palabras in self.sintomas_especificos.items():
            for palabra in palabras:
                if palabra in mensaje:
                    if sintoma not in sintomas_encontrados:
                        sintomas_encontrados.append(sintoma)
                    break
        
        return sintomas_encontrados
    
    def _tiene_sintoma(self, mensaje: str) -> bool:
        """Verificar si el mensaje menciona algún síntoma"""
        
        # Patrones de síntomas
        patrones_sintoma = [
            'me duele', 'me siento', 'tengo', 'siento',
            'dolor', 'molestia', 'malestar', 'problema'
        ]
        
        return any(patron in mensaje for patron in patrones_sintoma)
    
    def _extraer_entidades(self, mensaje: str) -> Dict:
        """Extraer entidades específicas del mensaje"""
        
        entidades = {}
        
        # Duración
        duracion = self._extraer_duracion(mensaje)
        if duracion:
            entidades['duracion'] = duracion
        
        # Intensidad (números del 1-10)
        intensidad = self._extraer_intensidad(mensaje)
        if intensidad:
            entidades['intensidad'] = intensidad
        
        # Frecuencia
        frecuencia = self._extraer_frecuencia(mensaje)
        if frecuencia:
            entidades['frecuencia'] = frecuencia
        
        # Momento del día
        momento = self._extraer_momento_dia(mensaje)
        if momento:
            entidades['momento_dia'] = momento
        
        return entidades
    
    def _extraer_duracion(self, mensaje: str) -> Optional[str]:
        """Extraer duración mencionada"""
        
        # Patrones: "3 días", "una semana", "hace 2 meses"
        patrones = [
            (r'(\d+)\s*dia', 'días'),
            (r'(\d+)\s*semana', 'semanas'),
            (r'(\d+)\s*mes', 'meses'),
            (r'(\d+)\s*ano', 'años'),
            (r'un\s*dia', '1 día'),
            (r'una\s*semana', '1 semana'),
            (r'un\s*mes', '1 mes'),
            (r'un\s*ano', '1 año'),
        ]
        
        for patron, unidad in patrones:
            match = re.search(patron, mensaje)
            if match:
                if match.groups():
                    return f"{match.group(1)} {unidad}"
                else:
                    return unidad
        
        return None
    
    def _extraer_intensidad(self, mensaje: str) -> Optional[int]:
        """Extraer nivel de intensidad (1-10)"""
        
        # Buscar números del 1 al 10
        numeros = re.findall(r'\b([1-9]|10)\b', mensaje)
        
        if numeros:
            return int(numeros[0])
        
        return None
    
    def _extraer_frecuencia(self, mensaje: str) -> Optional[str]:
        """Extraer frecuencia mencionada"""
        
        # Patrones: "2 veces a la semana", "todos los días"
        if 'todos los dias' in mensaje or 'todo el dia' in mensaje:
            return 'diario'
        
        if 'veces' in mensaje or 'vez' in mensaje:
            match = re.search(r'(\d+)\s*ve[cz]', mensaje)
            if match:
                return f"{match.group(1)} veces"
        
        return None
    
    def _extraer_momento_dia(self, mensaje: str) -> Optional[str]:
        """Extraer momento del día mencionado"""
        
        momentos = {
            'mañana': ['manana', 'matutino', 'madrugada', 'despertar'],
            'tarde': ['tarde', 'mediodia'],
            'noche': ['noche', 'nocturno', 'antes de dormir'],
            'todo_el_dia': ['todo el dia', 'siempre', 'constantemente']
        }
        
        for momento, palabras in momentos.items():
            if any(palabra in mensaje for palabra in palabras):
                return momento
        
        return None
    
    def _calcular_confianza(self, mensaje: str, intencion: str, 
                           sintomas: List[str]) -> float:
        """Calcular nivel de confianza de la detección"""
        
        confianza = 0.5  # Base
        
        # Aumentar si hay coincidencias claras
        if intencion != 'desconocida':
            confianza += 0.3
        
        # Aumentar si detectó síntomas
        if sintomas:
            confianza += 0.2
        
        # Limitar entre 0 y 1
        return min(1.0, confianza)
    
    def _normalizar(self, mensaje: str) -> str:
        """Normalizar mensaje para análisis"""
        
        # Minúsculas
        msg = mensaje.lower().strip()
        
        # Quitar acentos
        msg = unidecode(msg)
        
        # Correcciones ortográficas comunes
        correcciones = {
            'cabesa': 'cabeza',
            'estomago': 'estomago',
            'cansao': 'cansado',
            'jodido': 'muy mal',
            'fregado': 'muy mal',
            'pa': 'para',
            'q': 'que',
            'xq': 'porque',
            'k': 'que',
            've[cz]': 'vez'
        }
        
        for error, correcto in correcciones.items():
            msg = msg.replace(error, correcto)
        
        return msg
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # MÉTODOS DE UTILIDAD
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    def es_pregunta(self, mensaje: str) -> bool:
        """Verificar si el mensaje es una pregunta"""
        
        palabras_pregunta = [
            'que', 'como', 'cuando', 'donde', 'quien', 'cual',
            'por que', 'cuanto', 'puedes', 'tienes'
        ]
        
        mensaje_norm = self._normalizar(mensaje)
        
        return (mensaje.endswith('?') or 
                any(palabra in mensaje_norm for palabra in palabras_pregunta))
    
    def obtener_tipo_respuesta_sugerida(self, resultado: Dict) -> str:
        """Sugerir qué tipo de respuesta dar"""
        
        if resultado['es_conversacional']:
            return 'usar_reglas'  # Respuesta rápida con reglas
        
        elif resultado['es_consulta_medica']:
            if resultado['confianza'] > 0.7:
                return 'usar_contexto'  # Seguir flujo médico
            else:
                return 'usar_gpt'  # Consultar GPT para clarificar
        
        elif resultado['es_transaccional']:
            return 'usar_base_datos'  # Buscar en catálogo
        
        else:
            return 'usar_gpt'  # No se entiende, GPT ayuda


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TESTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

if __name__ == "__main__":
    print("="*70)
    print("🧪 TEST INTENT DETECTOR")
    print("="*70)
    
    detector = IntentDetector()
    
    mensajes_test = [
        "hola",
        "quien eres?",
        "quien te creo?",
        "me duele la cabeza hace 3 días",
        "tengo mucho estres",
        "cuanto cuesta la moringa?",
        "como se toma?",
        "todos los dias me siento cansado",
        "2 veces a la semana",
        "un 10"
    ]
    
    print("\n📝 DETECTANDO INTENCIONES:\n")
    
    for mensaje in mensajes_test:
        print(f"Mensaje: '{mensaje}'")
        resultado = detector.detectar(mensaje)
        print(f"  → Intención: {resultado['intencion']}")
        print(f"  → Confianza: {resultado['confianza']:.0%}")
        if resultado['sintomas']:
            print(f"  → Síntomas: {', '.join(resultado['sintomas'])}")
        if resultado['entidades']:
            print(f"  → Entidades: {resultado['entidades']}")
        print(f"  → Tipo sugerido: {detector.obtener_tipo_respuesta_sugerida(resultado)}")
        print()
    
    print("="*70)