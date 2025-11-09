"""
Motor de Diagnóstico de Kairos - VERSIÓN 2.0  
Sistema integrado: Productos + Plantas + Remedios
100% desde BD - GPT como maestro
"""

import sys
import os
from typing import Dict, List, Optional
import json
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BASE_DIR)

from backend.database.database_manager import DatabaseManager
from backend.database.productos_manager import ProductosManager
from backend.database.plantas_medicinales_manager import PlantasMedicinalesManager
from backend.database.remedios_caseros_manager import RemediosCaserosManager

class DiagnosticoEngine:
    """Motor de diagnóstico integrado completo"""
    
    def __init__(self):
        self.db = DatabaseManager()
        self.productos = ProductosManager()
        self.plantas = PlantasMedicinalesManager()
        self.remedios = RemediosCaserosManager()
        
        print("🧠 Motor de Diagnóstico V2.0 inicializado")
    
    def generar_receta_completa(self, diagnostico_gpt: Dict, usuario_id: int = None) -> Dict:
        """
        Generar receta completa desde diagnóstico GPT
        
        Args:
            diagnostico_gpt: Resultado de GPT con IDs de productos/plantas/remedios
            usuario_id: ID del usuario
            
        Returns:
            Dict con receta completa formateada
        """
        print(f"\n{'='*70}")
        print("📋 GENERANDO RECETA COMPLETA")
        print(f"{'='*70}\n")
        
        # PASO 1: Obtener productos por ID
        productos_receta = []
        for prod_id in diagnostico_gpt.get('productos_ids', []):
            producto = self._obtener_producto_por_id(prod_id)
            if producto:
                productos_receta.append(producto)
                self._incrementar_recomendacion_producto(prod_id)
                print(f"   ✅ Producto: {producto['nombre']}")
        
        # PASO 2: Obtener plantas por ID
        plantas_receta = []
        for planta_id in diagnostico_gpt.get('plantas_ids', []):
            planta = self.plantas.obtener_por_id(planta_id)
            if planta:
                plantas_receta.append(planta)
                self.plantas.incrementar_uso(planta_id)
                print(f"   ✅ Planta: {planta['nombre_comun']}")
        
        # PASO 3: Obtener remedios por ID
        remedios_receta = []
        for remedio_id in diagnostico_gpt.get('remedios_ids', []):
            remedio = self.remedios.obtener_por_id(remedio_id)
            if remedio:
                remedios_receta.append(remedio)
                self.remedios.incrementar_uso(remedio_id)
                print(f"   ✅ Remedio: {remedio['nombre']}")
        
        # PASO 4: Verificar combinaciones
        print("\n   🔍 Verificando combinaciones...")
        combinaciones = self._verificar_combinaciones_seguras(
            productos_receta,
            plantas_receta,
            remedios_receta
        )
        
        # PASO 5: Obtener info usuario
        usuario = self._obtener_info_usuario(usuario_id)
        
        # PASO 6: Construir receta
        receta = {
            'fecha': datetime.now().strftime('%d/%m/%Y %H:%M'),
            'paciente': usuario['nombre'] if usuario else 'Paciente',
            'dni': usuario['dni'] if usuario else '',
            'diagnostico': diagnostico_gpt['condicion'],
            'confianza': diagnostico_gpt['confianza'],
            'causas': diagnostico_gpt.get('causas', []),
            'productos': productos_receta,
            'plantas': plantas_receta,
            'remedios': remedios_receta,
            'combinaciones': combinaciones,
            'total': sum(float(p.get('precio', 0)) for p in productos_receta),
            'alimentos_aumentar': diagnostico_gpt.get('alimentos_aumentar', []),
            'alimentos_evitar': diagnostico_gpt.get('alimentos_evitar', []),
            'habitos': diagnostico_gpt.get('habitos', []),
            'advertencias': diagnostico_gpt.get('advertencias', []),
            'origen': diagnostico_gpt.get('origen', 'gpt')
        }
        
        # PASO 7: Formatear para ticket
        receta['texto_ticket'] = self._formatear_ticket(receta)
        
        print(f"\n{'='*70}")
        print("✅ RECETA COMPLETA GENERADA")
        print(f"{'='*70}\n")
        
        return receta
    
    def _obtener_producto_por_id(self, prod_id: int) -> Optional[Dict]:
        """Obtener producto directamente de BD por ID"""
        query = "SELECT * FROM productos_naturales WHERE id = %s AND activo = TRUE"
        resultado = self.db.ejecutar_query(query, (prod_id,))
        
        if resultado:
            return resultado[0]
        return None
    
    def _incrementar_recomendacion_producto(self, prod_id: int):
        """Incrementar contador de recomendaciones del producto"""
        query = """
        UPDATE productos_naturales 
        SET veces_recomendado = veces_recomendado + 1 
        WHERE id = %s
        """
        self.db.ejecutar_comando(query, (prod_id,))
    
    def _verificar_combinaciones_seguras(self, productos: List[Dict],
                                        plantas: List[Dict],
                                        remedios: List[Dict]) -> List[Dict]:
        """Verificar si las combinaciones son seguras"""
        
        combinaciones_encontradas = []
        
        # Verificar productos + plantas
        for prod in productos:
            for planta in plantas:
                # Buscar en tabla combinaciones_recomendadas
                query = """
                SELECT * FROM combinaciones_recomendadas
                WHERE activo = 1
                  AND tipo_combinacion = 'producto_planta'
                  AND (
                      (item_1_tipo = 'producto' AND item_1_id = %s AND item_2_tipo = 'planta' AND item_2_id = %s)
                      OR
                      (item_1_tipo = 'planta' AND item_1_id = %s AND item_2_tipo = 'producto' AND item_2_id = %s)
                  )
                """
                
                resultado = self.db.ejecutar_query(query, (prod['id'], planta['id'], planta['id'], prod['id']))
                
                if resultado:
                    combi = resultado[0]
                    combinaciones_encontradas.append({
                        'item1': prod['nombre'],
                        'item2': planta['nombre_comun'],
                        'sinergia': combi['sinergia'],
                        'explicacion': combi['explicacion'],
                        'instrucciones': combi['instrucciones']
                    })
                    
                    print(f"      ✓ Combinación validada: {prod['nombre']} + {planta['nombre_comun']}")
        
        # Verificar plantas entre sí
        for i in range(len(plantas)):
            for j in range(i + 1, len(plantas)):
                query = """
                SELECT * FROM combinaciones_recomendadas
                WHERE activo = 1
                  AND tipo_combinacion = 'planta_planta'
                  AND (
                      (item_1_id = %s AND item_2_id = %s)
                      OR
                      (item_1_id = %s AND item_2_id = %s)
                  )
                """
                
                resultado = self.db.ejecutar_query(
                    query,
                    (plantas[i]['id'], plantas[j]['id'], plantas[j]['id'], plantas[i]['id'])
                )
                
                if resultado:
                    combi = resultado[0]
                    combinaciones_encontradas.append({
                        'item1': plantas[i]['nombre_comun'],
                        'item2': plantas[j]['nombre_comun'],
                        'sinergia': combi['sinergia'],
                        'explicacion': combi['explicacion'],
                        'instrucciones': combi['instrucciones']
                    })
        
        return combinaciones_encontradas
    
    def _obtener_info_usuario(self, usuario_id: int) -> Optional[Dict]:
        """Obtener info del usuario"""
        
        if not usuario_id:
            return None
        
        query = "SELECT * FROM usuarios WHERE id = %s"
        resultado = self.db.ejecutar_query(query, (usuario_id,))
        
        if resultado:
            return resultado[0]
        
        return None
    
    def _formatear_ticket(self, receta: Dict) -> str:
        """Formatear receta para ticket térmico 58mm (32 caracteres)"""
        
        L = 32
        SEP = "=" * L
        
        ticket = f"""
{SEP}
  KAIROS INTELIGENCIA ARTIFICIAL
  Diagnóstico y Receta Natural
{SEP}

{receta['fecha']}
{receta['paciente'][:L]}
DNI: {receta['dni']}

{SEP}
DIAGNOSTICO
{SEP}

{receta['diagnostico'][:L]}
Confianza: {receta['confianza']:.0%}
"""
        
        # PRODUCTOS
        if receta['productos']:
            ticket += f"\n{SEP}\nPRODUCTOS NATURALES\n{SEP}\n"
            for prod in receta['productos']:
                ticket += f"\n• {prod['nombre'][:L-2]}\n"
                ticket += f"  S/. {float(prod['precio']):.2f}\n"
                dosis = prod.get('dosis_recomendada', 'Ver etiqueta')
                if dosis:
                    ticket += f"  {str(dosis)[:L-2]}\n"
            
            ticket += f"\nTOTAL: S/. {receta['total']:.2f}\n"
        
        # PLANTAS
        if receta['plantas']:
            ticket += f"\n{SEP}\nPLANTAS MEDICINALES\n{SEP}\n"
            for planta in receta['plantas']:
                ticket += f"\n• {planta['nombre_comun'][:L-2]}\n"
                
                # Preparación
                formas = planta.get('formas_preparacion', [])
                if formas and len(formas) > 0:
                    forma = formas[0]
                    tipo = forma.get('tipo', 'Infusión').title()
                    ticket += f"  {tipo}\n"
                
                # Dosis
                dosis = planta.get('dosis_recomendada', '3 tazas al día')
                if dosis:
                    ticket += f"  {str(dosis)[:L-2]}\n"
        
        # REMEDIOS
        if receta['remedios']:
            ticket += f"\n{SEP}\nREMEDIOS CASEROS\n{SEP}\n"
            for remedio in receta['remedios']:
                ticket += f"\n• {remedio['nombre'][:L-2]}\n"
                
                # Ingredientes
                ing_texto = remedio.get('ingredientes_texto', '')
                if ing_texto:
                    ticket += f"  Ing: {str(ing_texto)[:L-7]}\n"
                
                # Frecuencia
                freq = remedio.get('frecuencia', '')
                if freq:
                    ticket += f"  {str(freq)[:L-2]}\n"
        
        # COMBINACIONES
        if receta['combinaciones']:
            ticket += f"\n{SEP}\nCOMO COMBINAR\n{SEP}\n"
            for combi in receta['combinaciones'][:2]:  # Max 2
                ticket += f"\n✓ {combi['item1'][:12]} +\n"
                ticket += f"  {combi['item2'][:12]}\n"
                ticket += f"  {str(combi['instrucciones'])[:L-2]}\n"
        
        # ALIMENTACIÓN
        if receta['alimentos_aumentar']:
            ticket += f"\n{SEP}\nALIMENTOS AUMENTAR\n{SEP}\n\n"
            for alim in receta['alimentos_aumentar'][:4]:
                ticket += f"• {str(alim)[:L-2]}\n"
        
        if receta['alimentos_evitar']:
            ticket += f"\n{SEP}\nALIMENTOS EVITAR\n{SEP}\n\n"
            for alim in receta['alimentos_evitar'][:4]:
                ticket += f"• {str(alim)[:L-2]}\n"
        
        # HÁBITOS
        if receta['habitos']:
            ticket += f"\n{SEP}\nHABITOS RECOMENDADOS\n{SEP}\n\n"
            for habito in receta['habitos'][:4]:
                ticket += f"{str(habito)[:L]}\n"
        
        # ADVERTENCIAS
        # if receta['advertencias']:
        #     ticket += f"\n{SEP}\nIMPORTANTE\n{SEP}\n\n"
        #     for adv in receta['advertencias'][:3]:
        #         # Dividir en líneas
        #         palabras = str(adv).split()
        #         linea = ""
        #         for palabra in palabras:
        #             if len(linea) + len(palabra) + 1 <= L:
        #                 linea += palabra + " "
        #             else:
        #                 ticket += linea.strip() + "\n"
        #                 linea = palabra + " "
        #         if linea:
        #             ticket += linea.strip() + "\n"
        #         ticket += "\n"
        
        ticket += f"{SEP}\n¡QUE TE MEJORES!\n{SEP}\n"
        
        return ticket