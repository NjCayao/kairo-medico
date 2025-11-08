"""
Context Manager - Gestor de Contexto Médico
Mantiene y gestiona toda la información del paciente durante la conversación
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
import json

class ContextManager:
    """
    Gestor de Contexto Médico
    
    Responsabilidades:
    - Almacenar información del paciente
    - Actualizar contexto con nueva información
    - Decidir si hay suficiente info para diagnóstico
    - Sugerir siguiente pregunta inteligente
    """
    
    def __init__(self):
        """Inicializar gestor de contexto"""
        
        # Contexto completo del paciente
        self.contexto = {
            # Información personal
            'paciente': {
                'nombre': None,
                'dni': None,
                'edad': None,
                'genero': None
            },
            
            # Información médica principal
            'medico': {
                'sintoma_principal': None,
                'sintomas_adicionales': [],
                'duracion': None,
                'frecuencia': None,
                'intensidad': None,
                'momento_dia': None,
                'ubicacion': None,
                'tipo_dolor': None  # punzante, sordo, pulsante, etc
            },
            
            # Factores contextuales
            'factores': {
                'mejoran': [],
                'empeoran': [],
                'desencadenantes': []
            },
            
            # Historial y tratamientos
            'historial': {
                'medicamentos_actuales': [],
                'alergias': [],
                'enfermedades_previas': [],
                'tratamientos_probados': []
            },
            
            # Estilo de vida
            'estilo_vida': {
                'alimentacion': None,
                'ejercicio': None,
                'sueno': None,
                'estres': None,
                'trabajo': None
            },
            
            # Contexto conversacional
            'conversacion': {
                'preguntas_hechas': [],
                'respuestas_usuario': [],
                'temas_discutidos': [],
                'informacion_confirmada': []
            }
        }
        
        # Estado de la consulta
        self.estado = {
            'fase': 'inicial',  # inicial, recopilando, analizando, finalizando
            'preguntas_realizadas': 0,
            'info_clave_capturada': 0,
            'listo_para_diagnostico': False,
            'nivel_completitud': 0.0
        }
        
        print("🧠 Context Manager inicializado")
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # ACTUALIZACIÓN DE CONTEXTO
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    def actualizar_paciente(self, nombre: str = None, dni: str = None, 
                           edad: int = None, genero: str = None):
        """Actualizar información del paciente"""
        
        if nombre:
            self.contexto['paciente']['nombre'] = nombre
        if dni:
            self.contexto['paciente']['dni'] = dni
        if edad:
            self.contexto['paciente']['edad'] = edad
        if genero:
            self.contexto['paciente']['genero'] = genero
    
    def agregar_sintoma_principal(self, sintoma: str):
        """Establecer síntoma principal"""
        
        if not self.contexto['medico']['sintoma_principal']:
            self.contexto['medico']['sintoma_principal'] = sintoma
            self.estado['fase'] = 'recopilando'
            self._incrementar_info_clave()
            print(f"   ✅ Síntoma principal: {sintoma}")
    
    def agregar_sintoma_adicional(self, sintoma: str):
        """Agregar síntoma secundario"""
        
        if sintoma not in self.contexto['medico']['sintomas_adicionales']:
            self.contexto['medico']['sintomas_adicionales'].append(sintoma)
            self._incrementar_info_clave()
    
    def actualizar_desde_entidades(self, entidades: Dict):
        """Actualizar contexto desde entidades extraídas"""
        
        cambios = []
        
        if 'duracion' in entidades and not self.contexto['medico']['duracion']:
            self.contexto['medico']['duracion'] = entidades['duracion']
            self._incrementar_info_clave()
            cambios.append(f"duración: {entidades['duracion']}")
        
        if 'intensidad' in entidades and not self.contexto['medico']['intensidad']:
            self.contexto['medico']['intensidad'] = entidades['intensidad']
            self._incrementar_info_clave()
            cambios.append(f"intensidad: {entidades['intensidad']}/10")
        
        if 'frecuencia' in entidades and not self.contexto['medico']['frecuencia']:
            self.contexto['medico']['frecuencia'] = entidades['frecuencia']
            self._incrementar_info_clave()
            cambios.append(f"frecuencia: {entidades['frecuencia']}")
        
        if 'momento_dia' in entidades and not self.contexto['medico']['momento_dia']:
            self.contexto['medico']['momento_dia'] = entidades['momento_dia']
            self._incrementar_info_clave()
            cambios.append(f"momento: {entidades['momento_dia']}")
        
        if cambios:
            print(f"   📝 Contexto actualizado: {', '.join(cambios)}")
    
    def agregar_pregunta_respuesta(self, pregunta: str, respuesta: str):
        """Registrar pregunta y respuesta"""
        
        self.contexto['conversacion']['preguntas_hechas'].append(pregunta)
        self.contexto['conversacion']['respuestas_usuario'].append(respuesta)
        self.estado['preguntas_realizadas'] += 1
    
    def agregar_factor_mejora(self, factor: str):
        """Agregar factor que mejora el síntoma"""
        
        if factor not in self.contexto['factores']['mejoran']:
            self.contexto['factores']['mejoran'].append(factor)
            self._incrementar_info_clave()
    
    def agregar_factor_empeora(self, factor: str):
        """Agregar factor que empeora el síntoma"""
        
        if factor not in self.contexto['factores']['empeoran']:
            self.contexto['factores']['empeoran'].append(factor)
            self._incrementar_info_clave()
    
    def _incrementar_info_clave(self):
        """Incrementar contador de información clave capturada"""
        
        self.estado['info_clave_capturada'] += 1
        self._calcular_completitud()
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # ANÁLISIS DEL CONTEXTO
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    def tiene_info_suficiente(self) -> bool:
        """
        Determinar si hay suficiente información para diagnóstico
        
        Criterios:
        - Síntoma principal identificado
        - Al menos 4 datos clave adicionales
        - O al menos 5 interacciones
        """
        
        tiene_sintoma = self.contexto['medico']['sintoma_principal'] is not None
        
        datos_clave = sum([
            self.contexto['medico']['duracion'] is not None,
            self.contexto['medico']['intensidad'] is not None,
            self.contexto['medico']['frecuencia'] is not None,
            self.contexto['medico']['momento_dia'] is not None,
            len(self.contexto['factores']['mejoran']) > 0,
            len(self.contexto['factores']['empeoran']) > 0,
            len(self.contexto['medico']['sintomas_adicionales']) > 0
        ])
        
        suficientes_interacciones = self.estado['preguntas_realizadas'] >= 5
        
        listo = tiene_sintoma and (datos_clave >= 4 or suficientes_interacciones)
        
        if listo and not self.estado['listo_para_diagnostico']:
            self.estado['listo_para_diagnostico'] = True
            self.estado['fase'] = 'analizando'
            print("   ✅ Información suficiente para diagnóstico")
        
        return listo
    
    def _calcular_completitud(self):
        """Calcular nivel de completitud del contexto (0-1)"""
        
        campos_importantes = [
            self.contexto['medico']['sintoma_principal'],
            self.contexto['medico']['duracion'],
            self.contexto['medico']['intensidad'],
            self.contexto['medico']['frecuencia'],
            self.contexto['medico']['momento_dia'],
            len(self.contexto['factores']['mejoran']) > 0,
            len(self.contexto['factores']['empeoran']) > 0
        ]
        
        campos_llenos = sum(1 for campo in campos_importantes if campo)
        total_campos = len(campos_importantes)
        
        self.estado['nivel_completitud'] = campos_llenos / total_campos
    
    def obtener_info_faltante(self) -> List[str]:
        """Obtener lista de información que falta por recopilar"""
        
        faltante = []
        
        if not self.contexto['medico']['sintoma_principal']:
            faltante.append('sintoma_principal')
        
        if not self.contexto['medico']['duracion']:
            faltante.append('duracion')
        
        if not self.contexto['medico']['intensidad']:
            faltante.append('intensidad')
        
        if not self.contexto['medico']['frecuencia']:
            faltante.append('frecuencia')
        
        if not self.contexto['medico']['momento_dia']:
            faltante.append('momento_dia')
        
        if not self.contexto['factores']['mejoran']:
            faltante.append('factores_mejoran')
        
        if not self.contexto['factores']['empeoran']:
            faltante.append('factores_empeoran')
        
        return faltante
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # SUGERENCIAS INTELIGENTES
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    def sugerir_siguiente_pregunta(self) -> Optional[str]:
        """
        Sugerir la siguiente pregunta más relevante
        Basado en lo que falta por recopilar
        """
        
        faltante = self.obtener_info_faltante()
        
        if not faltante:
            return None
        
        # Priorizar según importancia
        prioridad = [
            'sintoma_principal',
            'duracion',
            'intensidad',
            'frecuencia',
            'momento_dia',
            'factores_empeoran',
            'factores_mejoran'
        ]
        
        for campo in prioridad:
            if campo in faltante:
                return self._generar_pregunta_para_campo(campo)
        
        return None
    
    def _generar_pregunta_para_campo(self, campo: str) -> str:
        """Generar pregunta conversacional para un campo específico"""
        
        nombre = self.contexto['paciente']['nombre']
        primer_nombre = nombre.split()[0] if nombre else ''
        
        preguntas = {
            'sintoma_principal': f"Cuéntame{', ' + primer_nombre if primer_nombre else ''}, ¿qué molestia tienes?",
            
            'duracion': f"¿Desde hace cuánto tiempo{', ' + primer_nombre if primer_nombre else ''}?",
            
            'intensidad': f"Del 1 al 10, ¿qué tan fuerte es la molestia?",
            
            'frecuencia': f"¿Esto te pasa todos los días o solo a veces?",
            
            'momento_dia': f"¿En qué momento del día te molesta más?",
            
            'factores_mejoran': f"¿Hay algo que hagas que te ayude a sentirte mejor?",
            
            'factores_empeoran': f"¿Y algo que haga que empeore?"
        }
        
        return preguntas.get(campo, "¿Algo más que deba saber?")
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # GENERACIÓN DE RESUMEN
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    def obtener_resumen_clinico(self) -> str:
        """
        Generar resumen clínico del paciente
        Para enviar a GPT o guardar en BD
        """
        
        partes = []
        
        # Paciente
        nombre = self.contexto['paciente']['nombre']
        if nombre:
            partes.append(f"PACIENTE: {nombre}")
        
        # Síntoma principal
        sintoma = self.contexto['medico']['sintoma_principal']
        if sintoma:
            partes.append(f"\nSÍNTOMA PRINCIPAL: {sintoma}")
        
        # Duración
        duracion = self.contexto['medico']['duracion']
        if duracion:
            partes.append(f"Duración: {duracion}")
        
        # Intensidad
        intensidad = self.contexto['medico']['intensidad']
        if intensidad:
            partes.append(f"Intensidad: {intensidad}/10")
        
        # Frecuencia
        frecuencia = self.contexto['medico']['frecuencia']
        if frecuencia:
            partes.append(f"Frecuencia: {frecuencia}")
        
        # Momento del día
        momento = self.contexto['medico']['momento_dia']
        if momento:
            partes.append(f"Momento: {momento}")
        
        # Síntomas adicionales
        if self.contexto['medico']['sintomas_adicionales']:
            sintomas_add = ', '.join(self.contexto['medico']['sintomas_adicionales'])
            partes.append(f"Síntomas adicionales: {sintomas_add}")
        
        # Factores que mejoran
        if self.contexto['factores']['mejoran']:
            mejoran = ', '.join(self.contexto['factores']['mejoran'])
            partes.append(f"Mejora con: {mejoran}")
        
        # Factores que empeoran
        if self.contexto['factores']['empeoran']:
            empeoran = ', '.join(self.contexto['factores']['empeoran'])
            partes.append(f"Empeora con: {empeoran}")
        
        # Conversación
        if self.contexto['conversacion']['respuestas_usuario']:
            partes.append(f"\nRESPUESTAS DEL PACIENTE:")
            for i, respuesta in enumerate(self.contexto['conversacion']['respuestas_usuario'][-3:], 1):
                partes.append(f"  {i}. {respuesta}")
        
        return '\n'.join(partes)
    
    def obtener_contexto_completo(self) -> Dict:
        """Obtener contexto completo como diccionario"""
        
        return {
            'contexto': self.contexto,
            'estado': self.estado,
            'resumen_clinico': self.obtener_resumen_clinico(),
            'info_faltante': self.obtener_info_faltante(),
            'completitud': f"{self.estado['nivel_completitud']:.0%}"
        }
    
    def obtener_contexto_para_gpt(self) -> str:
        """
        Obtener contexto formateado para enviar a GPT
        """
        
        return f"""CONTEXTO DEL PACIENTE:

{self.obtener_resumen_clinico()}

NIVEL DE INFORMACIÓN: {self.estado['nivel_completitud']:.0%}
PREGUNTAS REALIZADAS: {self.estado['preguntas_realizadas']}
FASE: {self.estado['fase']}

INFO QUE AÚN FALTA: {', '.join(self.obtener_info_faltante()) if self.obtener_info_faltante() else 'Ninguna'}"""
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # REINICIO
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    def reiniciar(self):
        """Reiniciar contexto para nuevo paciente"""
        
        self.__init__()
        print("🔄 Contexto reiniciado")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TESTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

if __name__ == "__main__":
    print("="*70)
    print("🧪 TEST CONTEXT MANAGER")
    print("="*70)
    
    context = ContextManager()
    
    # Simular conversación
    print("\n📝 SIMULANDO CONVERSACIÓN:\n")
    
    context.actualizar_paciente(nombre="Juan Pérez", dni="12345678")
    print("1. Paciente registrado")
    
    context.agregar_sintoma_principal("dolor de cabeza")
    print("2. Síntoma principal agregado")
    
    context.actualizar_desde_entidades({
        'duracion': '3 días',
        'intensidad': 7
    })
    print("3. Entidades actualizadas")
    
    context.agregar_pregunta_respuesta(
        "¿En qué momento del día?",
        "Por la mañana"
    )
    print("4. P&R registrada")
    
    context.agregar_factor_empeora("estrés")
    print("5. Factor agregado")
    
    print(f"\n📊 ESTADO:")
    print(f"   Completitud: {context.estado['nivel_completitud']:.0%}")
    print(f"   Preguntas: {context.estado['preguntas_realizadas']}")
    print(f"   Info clave: {context.estado['info_clave_capturada']}")
    print(f"   Listo: {context.tiene_info_suficiente()}")
    
    print(f"\n📋 RESUMEN CLÍNICO:")
    print(context.obtener_resumen_clinico())
    
    print(f"\n❓ SIGUIENTE PREGUNTA SUGERIDA:")
    print(context.sugerir_siguiente_pregunta())
    
    print("\n" + "="*70)