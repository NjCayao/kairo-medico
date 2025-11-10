"""
Consultar uso y créditos REALES de OpenAI
"""

import requests
from datetime import datetime, timedelta
from typing import Dict, Optional

class OpenAIUsageChecker:
    """Consultar uso real de API OpenAI"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.openai.com/v1"
    
    def obtener_uso_actual(self, dias: int = 30) -> Optional[Dict]:
        """
        Obtener uso de los últimos N días
        
        Returns:
            {
                'total_usage': 15.50,  # Dólares gastados
                'daily_costs': [...],   # Desglose por día
                'token_usage': {...}    # Tokens por modelo
            }
        """
        try:
            # Fechas
            end_date = datetime.now()
            start_date = end_date - timedelta(days=dias)
            
            # Endpoint de uso
            url = f"{self.base_url}/usage"
            
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            params = {
                'start_date': start_date.strftime('%Y-%m-%d'),
                'end_date': end_date.strftime('%Y-%m-%d')
            }
            
            response = requests.get(url, headers=headers, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                return self._procesar_uso(data)
            else:
                print(f"❌ Error consultando uso: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Error: {e}")
            return None
    
    def obtener_credito_restante(self) -> Optional[Dict]:
        """
        Obtener crédito disponible (si tienes créditos prepagados)
        
        Nota: OpenAI deprecó este endpoint. Ahora usa billing directo.
        Debes revisar en: https://platform.openai.com/account/billing/overview
        """
        try:
            url = f"{self.base_url}/dashboard/billing/credit_grants"
            
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                total_granted = data.get('total_granted', 0)
                total_used = data.get('total_used', 0)
                total_available = data.get('total_available', 0)
                
                return {
                    'credito_inicial': total_granted,
                    'credito_usado': total_used,
                    'credito_disponible': total_available,
                    'porcentaje_usado': (total_used / total_granted * 100) if total_granted > 0 else 0
                }
            else:
                # Endpoint deprecado - usar dashboard web
                return {
                    'mensaje': 'Endpoint deprecado. Consulta en: https://platform.openai.com/account/billing',
                    'requiere_dashboard': True
                }
                
        except Exception as e:
            print(f"❌ Error consultando crédito: {e}")
            return None
    
    def _procesar_uso(self, data: Dict) -> Dict:
        """Procesar datos de uso de OpenAI"""
        
        daily_costs = data.get('daily_costs', [])
        
        total_usage = sum(day.get('cost', 0) for day in daily_costs)
        
        # Agrupar por modelo
        token_usage = {}
        for day in daily_costs:
            for line_item in day.get('line_items', []):
                model = line_item.get('name', 'unknown')
                cost = line_item.get('cost', 0)
                
                if model not in token_usage:
                    token_usage[model] = 0
                token_usage[model] += cost
        
        return {
            'total_usage': total_usage,
            'daily_costs': daily_costs,
            'token_usage': token_usage,
            'periodo': f"{len(daily_costs)} días"
        }
    
    def calcular_costo_consulta(self, tokens_input: int, tokens_output: int, modelo: str = 'gpt-4o-mini') -> float:
        """
        Calcular costo exacto de una consulta
        
        Precios actualizados (Nov 2024):
        - GPT-4o Mini: $0.150 / 1M input, $0.600 / 1M output
        - GPT-4o: $2.50 / 1M input, $10.00 / 1M output
        - GPT-4 Turbo: $10.00 / 1M input, $30.00 / 1M output
        - GPT-4: $30.00 / 1M input, $60.00 / 1M output
        """
        
        precios = {
            'gpt-4o-mini': {
                'input': 0.150 / 1_000_000,
                'output': 0.600 / 1_000_000
            },
            'gpt-4o': {
                'input': 2.50 / 1_000_000,
                'output': 10.00 / 1_000_000
            },
            'gpt-4-turbo': {
                'input': 10.00 / 1_000_000,
                'output': 30.00 / 1_000_000
            },
            'gpt-4': {
                'input': 30.00 / 1_000_000,
                'output': 60.00 / 1_000_000
            },
            'gpt-3.5-turbo': {
                'input': 0.50 / 1_000_000,
                'output': 1.50 / 1_000_000
            }
        }
        
        if modelo not in precios:
            modelo = 'gpt-4o-mini'  # Default
        
        costo_input = tokens_input * precios[modelo]['input']
        costo_output = tokens_output * precios[modelo]['output']
        
        return costo_input + costo_output


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PRUEBAS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

if __name__ == "__main__":
    import sys
    import os
    
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    sys.path.insert(0, BASE_DIR)
    
    from backend.core.ia_config_manager import IAConfigManager
    
    print("="*70)
    print("🔍 CONSULTAR USO REAL DE OPENAI")
    print("="*70)
    
    # Cargar API key desde BD
    config_manager = IAConfigManager()
    
    if not config_manager.tiene_api_key():
        print("❌ No hay API key configurada")
        exit(1)
    
    config = config_manager.obtener_config()
    api_key = config['api_key']
    
    checker = OpenAIUsageChecker(api_key)
    
    # 1. Uso de últimos 30 días
    print("\n📊 USO DE ÚLTIMOS 30 DÍAS:")
    uso = checker.obtener_uso_actual(dias=30)
    
    if uso:
        print(f"   Total gastado: ${uso['total_usage']:.4f} USD")
        print(f"   Equivalente: S/. {uso['total_usage'] * 3.8:.2f} PEN")
        print(f"\n   Desglose por modelo:")
        for modelo, costo in uso['token_usage'].items():
            print(f"   • {modelo}: ${costo:.4f}")
    
    # 2. Crédito disponible
    print("\n💰 CRÉDITO DISPONIBLE:")
    credito = checker.obtener_credito_restante()
    
    if credito:
        if credito.get('requiere_dashboard'):
            print("   ⚠️ Debes consultar en el dashboard web:")
            print("   https://platform.openai.com/account/billing/overview")
        else:
            print(f"   Inicial: ${credito['credito_inicial']:.2f}")
            print(f"   Usado: ${credito['credito_usado']:.2f}")
            print(f"   Disponible: ${credito['credito_disponible']:.2f}")
            print(f"   Porcentaje usado: {credito['porcentaje_usado']:.1f}%")
    
    # 3. Ejemplo de cálculo de costo
    print("\n🧮 EJEMPLO DE COSTOS:")
    print("   Consulta típica (500 tokens input, 200 output):")
    
    for modelo in ['gpt-4o-mini', 'gpt-4o', 'gpt-4']:
        costo = checker.calcular_costo_consulta(500, 200, modelo)
        print(f"   • {modelo}: ${costo:.6f} (S/. {costo * 3.8:.4f})")
    
    print("\n" + "="*70)