"""
Motor de Diagnóstico de Kairos
GPT como maestro - Sin hardcoding
"""

import sys
import os
from typing import Dict, List, Optional
import json
import requests
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BASE_DIR)

from backend.database.database_manager import DatabaseManager
from backend.database.productos_manager import ProductosManager

class DiagnosticoEngine:
    """Motor de diagnóstico con GPT como maestro"""
    
    def __init__(self):
        self.db = DatabaseManager()
        self.productos = ProductosManager()
        self.config_ia = self._cargar_config_ia()
        
        print("🧠 Motor de Diagnóstico inicializado")
        if self.config_ia and self.config_ia.get('activo'):
            print(f"   ✅ IA: {self.config_ia['proveedor']}")
        else:
            print("   ⚠️ IA no configurada")
    
    def _cargar_config_ia(self) -> Optional[Dict]:
        """Cargar config IA desde BD"""
        try:
            query = "SELECT * FROM configuracion_ia WHERE activo = TRUE LIMIT 1"
            resultado = self.db.ejecutar_query(query)
            return resultado[0] if resultado else None
        except:
            return None
    
    def analizar_completo(self, contexto: Dict, sesion_id: str = None, 
                         usuario_id: int = None) -> Dict:
        """Análisis completo: Diagnóstico + Receta"""
        
        sintoma = contexto.get('sintoma_principal', '').lower()
        
        print(f"\n{'='*60}")
        print(f"🔍 ANALIZANDO: {sintoma}")
        print(f"{'='*60}")
        
        # PASO 1: Obtener diagnóstico (3 capas)
        diagnostico = self._obtener_diagnostico(sintoma, contexto, sesion_id, usuario_id)
        
        # PASO 2: Generar receta
        print("\n📋 Generando receta...")
        receta = self._generar_receta(diagnostico, contexto, usuario_id)
        
        resultado = {
            **diagnostico,
            'receta': receta,
            'timestamp': datetime.now().isoformat()
        }
        
        print(f"\n{'='*60}")
        print("✅ ANÁLISIS COMPLETO")
        print(f"{'='*60}\n")
        
        return resultado
    
    def _obtener_diagnostico(self, sintoma: str, contexto: Dict,
                            sesion_id: str = None, usuario_id: int = None) -> Dict:
        """Sistema 3 capas: Local → IA → Fallback"""
        
        # CAPA 1: Buscar en conocimiento aprendido
        print("\n📚 CAPA 1: Buscando conocimiento previo...")
        diag_local = self._buscar_conocimiento(sintoma)
        
        if diag_local:
            print("   ✅ Encontrado en conocimiento previo")
            return diag_local
        
        print("   ⚠️ No encontrado")
        
        # CAPA 2: Consultar GPT
        if self._puede_usar_ia():
            print("\n🤖 CAPA 2: Consultando GPT...")
            diag_ia = self._consultar_gpt(sintoma, contexto, sesion_id, usuario_id)
            
            if diag_ia:
                print("   ✅ Diagnóstico de GPT recibido")
                
                # Guardar TODO para próximas consultas
                if diag_ia.get('confianza', 0) >= 0.70:
                    self._guardar_conocimiento_completo(sintoma, diag_ia)
                
                return diag_ia
        
        # CAPA 3: Fallback
        print("\n⚠️ FALLBACK: Respuesta básica")
        return self._fallback(sintoma)
    
    def _buscar_conocimiento(self, sintoma: str) -> Optional[Dict]:
        """Buscar conocimiento completo aprendido de GPT"""
        
        query = """
        SELECT * FROM conocimientos_completos 
        WHERE LOWER(condicion) LIKE %s OR LOWER(sintomas_keywords) LIKE %s
        ORDER BY veces_usado DESC
        LIMIT 1
        """
        
        busqueda = f"%{sintoma}%"
        resultado = self.db.ejecutar_query(query, (busqueda, busqueda))
        
        if not resultado:
            return None
        
        c = resultado[0]
        
        # Incrementar uso
        self.db.ejecutar_comando(
            "UPDATE conocimientos_completos SET veces_usado = veces_usado + 1 WHERE id = %s",
            (c['id'],)
        )
        
        # Deserializar JSONs
        return {
            'condicion': c['condicion'],
            'confianza': float(c['confianza']),
            'causas': json.loads(c['causas_json']) if c['causas_json'] else [],
            'tratamiento': json.loads(c['tratamiento_json']) if c['tratamiento_json'] else [],
            'alimentos_aumentar': json.loads(c['alimentos_aumentar_json']) if c['alimentos_aumentar_json'] else [],
            'alimentos_evitar': json.loads(c['alimentos_evitar_json']) if c['alimentos_evitar_json'] else [],
            'habitos': json.loads(c['habitos_json']) if c['habitos_json'] else [],
            'advertencias': json.loads(c['advertencias_json']) if c['advertencias_json'] else [],
            'productos': self._buscar_productos(sintoma),
            'origen': c['origen']
        }
    
    def _puede_usar_ia(self) -> bool:
        """Verificar si puede usar IA"""
        if not self.config_ia or not self.config_ia.get('activo'):
            return False
        
        api_key = self.config_ia.get('api_key', '')
        if not api_key or api_key == 'TU_API_KEY_AQUI':
            return False
        
        if self.config_ia.get('consultas_realizadas_hoy', 0) >= self.config_ia.get('limite_diario_consultas', 100):
            return False
        
        return True
    
    def _consultar_gpt(self, sintoma: str, contexto: Dict, 
                      sesion_id: str = None, usuario_id: int = None) -> Optional[Dict]:
        """Consultar GPT-4"""
        
        respuestas = "\n".join([f"- {r}" for r in contexto.get('respuestas_usuario', [])])
        
        prompt = f"""Eres médico especialista en medicina natural.

PACIENTE:
Síntoma: {sintoma}
Contexto:
{respuestas}

PRODUCTOS DISPONIBLES:
- Moringa (antiinflamatorio, balance hormonal, energía)
- Ganoderma Reishi (estrés, inmunidad, sueño)
- Aceite Moringa (digestión, piel)

RESPONDE SOLO JSON (sin markdown):
{{
    "condicion": "nombre exacto",
    "confianza": 0.85,
    "causas": ["causa1", "causa2", "causa3"],
    "tratamiento": ["tratamiento1", "tratamiento2"],
    "alimentos_aumentar": ["alimento1", "alimento2"],
    "alimentos_evitar": ["alimento1", "alimento2"],
    "habitos": ["hábito1 con emoji", "hábito2"],
    "productos_naturales": ["moringa", "ganoderma"],
    "cuando_ver_medico": "descripción breve"
}}"""
        
        try:
            response = requests.post(
                'https://api.openai.com/v1/chat/completions',
                headers={
                    'Authorization': f"Bearer {self.config_ia['api_key']}",
                    'Content-Type': 'application/json'
                },
                json={
                    'model': self.config_ia.get('modelo_gpt', 'gpt-4'),
                    'messages': [
                        {'role': 'system', 'content': 'Médico natural. Solo JSON.'},
                        {'role': 'user', 'content': prompt}
                    ],
                    'temperature': float(self.config_ia.get('temperatura', 0.3)),
                    'max_tokens': self.config_ia.get('max_tokens', 1000)
                },
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                contenido = data['choices'][0]['message']['content'].strip()
                
                # Limpiar markdown
                contenido = contenido.replace('```json', '').replace('```', '').strip()
                
                diag = json.loads(contenido)
                
                # Mapear productos
                diag['productos'] = self._mapear_productos(diag.get('productos_naturales', []))
                
                # Generar advertencias
                diag['advertencias'] = self._generar_advertencias(diag)
                
                # Incrementar contador
                self.db.ejecutar_comando(
                    "UPDATE configuracion_ia SET consultas_realizadas_hoy = consultas_realizadas_hoy + 1"
                )
                
                diag['origen'] = 'gpt'
                return diag
            
            return None
            
        except Exception as e:
            print(f"   ❌ Error GPT: {e}")
            return None
    
    def _mapear_productos(self, productos_gpt: List[str]) -> List[Dict]:
        """Mapear productos GPT a catálogo"""
        productos = []
        
        for nombre in productos_gpt:
            nombre_l = nombre.lower()
            
            if 'moringa' in nombre_l and 'aceite' not in nombre_l:
                prod_id = 1
            elif 'ganoderma' in nombre_l or 'reishi' in nombre_l:
                prod_id = 2
            elif 'aceite' in nombre_l:
                prod_id = 3
            else:
                continue
            
            prod = self.productos.obtener_por_id(prod_id)
            if prod:
                productos.append({
                    'id': prod['id'],
                    'nombre': prod['nombre'],
                    'precio': prod['precio'],
                    'dosis': prod['dosis']
                })
        
        return productos
    
    def _generar_advertencias(self, diag: Dict) -> List[str]:
        """Generar advertencias según diagnóstico"""
        adv = []
        
        if diag.get('confianza', 0) < 0.7:
            adv.append("⚠️ Confianza baja - consultar médico")
        
        if diag.get('cuando_ver_medico'):
            adv.append(f"📌 {diag['cuando_ver_medico']}")
        
        adv.append("📌 Productos naturales complementarios")
        
        if diag.get('productos'):
            adv.append("📌 Seguir dosis recomendada")
        
        return adv
    
    def _guardar_conocimiento_completo(self, sintoma: str, diag: Dict):
        """Guardar TODO lo que GPT respondió"""
        
        tema = diag.get('condicion', sintoma)
        
        # Verificar si existe
        query = "SELECT id FROM conocimientos_completos WHERE LOWER(condicion) = LOWER(%s)"
        existe = self.db.ejecutar_query(query, (tema,))
        
        if existe:
            self.db.ejecutar_comando(
                "UPDATE conocimientos_completos SET veces_usado = veces_usado + 1 WHERE id = %s",
                (existe[0]['id'],)
            )
            print("   ✅ Conocimiento actualizado")
        else:
            query = """
            INSERT INTO conocimientos_completos (
                condicion, sintomas_keywords,
                causas_json, tratamiento_json,
                alimentos_aumentar_json, alimentos_evitar_json,
                habitos_json, advertencias_json, cuando_ver_medico,
                productos_recomendados_json, origen, confianza, veces_usado
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'gpt', %s, 1)
            """
            
            parametros = (
                tema,
                sintoma,
                json.dumps(diag.get('causas', []), ensure_ascii=False),
                json.dumps(diag.get('tratamiento', []), ensure_ascii=False),
                json.dumps(diag.get('alimentos_aumentar', []), ensure_ascii=False),
                json.dumps(diag.get('alimentos_evitar', []), ensure_ascii=False),
                json.dumps(diag.get('habitos', []), ensure_ascii=False),
                json.dumps(diag.get('advertencias', []), ensure_ascii=False),
                diag.get('cuando_ver_medico', ''),
                json.dumps(diag.get('productos', []), ensure_ascii=False),
                diag.get('confianza', 0.85)
            )
            
            self.db.ejecutar_comando(query, parametros)
            print("   💾 Conocimiento completo guardado")
    
    def _fallback(self, sintoma: str) -> Dict:
        """Respuesta básica cuando todo falla"""
        return {
            'condicion': f'Molestia: {sintoma}',
            'confianza': 0.5,
            'causas': ['Requiere evaluación'],
            'tratamiento': ['Consultar profesional'],
            'alimentos_aumentar': ['Frutas', 'Verduras', 'Agua'],
            'alimentos_evitar': ['Procesados', 'Azúcar'],
            'habitos': ['💤 Dormir 8h', '🏃 Ejercicio', '💧 Hidratación'],
            'advertencias': ['⚠️ Consultar médico profesional'],
            'productos': self._buscar_productos(sintoma),
            'origen': 'fallback'
        }
    
    def _buscar_productos(self, sintoma: str) -> List[Dict]:
        """Buscar productos por síntoma"""
        productos_encontrados = self.productos.buscar_por_sintoma(sintoma)
        
        return [{
            'id': p['id'],
            'nombre': p['nombre'],
            'precio': p['precio'],
            'dosis': p['dosis']
        } for p in productos_encontrados[:2]]
    
    def _generar_receta(self, diag: Dict, contexto: Dict, usuario_id: int = None) -> Dict:
        """Generar receta completa"""
        
        # Obtener usuario
        usuario = None
        if usuario_id:
            query = "SELECT * FROM usuarios WHERE id = %s"
            resultado = self.db.ejecutar_query(query, (usuario_id,))
            if resultado:
                usuario = resultado[0]
        
        # Info botica
        botica = self._info_botica()
        
        receta = {
            'fecha': datetime.now().strftime('%d/%m/%Y %H:%M'),
            'paciente': usuario['nombre'] if usuario else 'Paciente',
            'dni': usuario['dni'] if usuario else '',
            'diagnostico': diag['condicion'],
            'confianza': diag['confianza'],
            'causas': diag.get('causas', [])[:3],
            'tratamiento': diag.get('tratamiento', [])[:3],
            'productos': diag.get('productos', []),
            'total': sum(p['precio'] for p in diag.get('productos', [])),
            'alimentos_aumentar': diag.get('alimentos_aumentar', [])[:4],
            'alimentos_evitar': diag.get('alimentos_evitar', [])[:4],
            'habitos': diag.get('habitos', [])[:4],
            'advertencias': diag.get('advertencias', []),
            'botica': botica
        }
        
        receta['texto_ticket'] = self._formatear_ticket(receta)
        
        return receta
    
    def _info_botica(self) -> Dict:
        """Información botica"""
        info = {
            'nombre': 'Botica NaturaVida',
            'direccion': 'Jr. Los Remedios 123',
            'telefono': '(01) 234-5678',
            'whatsapp': '987654321'
        }
        
        try:
            query = "SELECT * FROM configuracion_sistema WHERE clave LIKE '%botica%'"
            resultado = self.db.ejecutar_query(query)
            if resultado:
                for c in resultado:
                    clave = c['clave'].replace('_botica', '').replace('botica_', '')
                    if clave in info:
                        info[clave] = c['valor']
        except:
            pass
        
        return info
    
    def _formatear_ticket(self, receta: Dict) -> str:
        """Formatear para ticket 58mm"""
        
        L = "=" * 32
        
        t = f"""
{L}
  KAIROS MEDICINA NATURAL
{L}

{receta['fecha']}
{receta['paciente'][:30]}
DNI: {receta['dni']}

{L}
DIAGNÓSTICO
{L}

{receta['diagnostico']}
Confianza: {receta['confianza']:.0%}

{L}
PRODUCTOS
{L}
"""
        
        for p in receta['productos']:
            t += f"\n• {p['nombre'][:28]}\n"
            t += f"  S/. {p['precio']:.2f}\n"
            t += f"  {p['dosis'][:30]}\n"
        
        if receta['productos']:
            t += f"\n{L}\nTOTAL: S/. {receta['total']:.2f}\n"
        
        t += f"\n{L}\nALIMENTACIÓN\n{L}\n\nAUMENTAR:\n"
        for a in receta['alimentos_aumentar'][:3]:
            t += f"• {a[:30]}\n"
        
        t += "\nEVITAR:\n"
        for a in receta['alimentos_evitar'][:3]:
            t += f"• {a[:30]}\n"
        
        t += f"\n{L}\nHÁBITOS\n{L}\n\n"
        for h in receta['habitos'][:4]:
            t += f"{h[:32]}\n"
        
        t += f"\n{L}\nIMPORTANTE\n{L}\n\n"
        for adv in receta['advertencias']:
            t += f"{adv[:32]}\n"
        
        t += f"\n{L}\nDÓNDE COMPRAR\n{L}\n\n"
        t += f"{receta['botica']['nombre'][:32]}\n"
        t += f"{receta['botica']['direccion'][:32]}\n"
        t += f"Tel: {receta['botica']['telefono']}\n"
        t += f"WhatsApp: {receta['botica']['whatsapp']}\n"
        
        t += f"\n{L}\n¡QUE TE MEJORES!\n{L}\n"
        
        return t

# TEST
if __name__ == "__main__":
    print("="*70)
    print("TEST MOTOR")
    print("="*70)
    
    motor = DiagnosticoEngine()
    
    contexto = {
        'sintoma_principal': 'dolor de cabeza',
        'respuestas_usuario': [
            'En la frente',
            'Una semana',
            '7 de 10',
            'Mañanas',
            'Mejora con descanso'
        ]
    }
    
    resultado = motor.analizar_completo(contexto, 'TEST-001', 1)
    
    print("\nDiagnóstico:", resultado['condicion'])
    print("Confianza:", resultado['confianza'])
    print("Origen:", resultado['origen'])
    print("\n📋 RECETA:")
    print(resultado['receta']['texto_ticket'])