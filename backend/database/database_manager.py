"""
Gestor de Base de Datos MySQL para Kairos
Creado desde cero - Versión 2.0
"""

import mysql.connector
from mysql.connector import Error
import json
from datetime import datetime
from typing import Optional, List, Dict, Any
import sys
import os

# Agregar path para imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from config.settings import Config

class DatabaseManager:
    """
    Gestor de conexión y operaciones con MySQL
    """
    
    def __init__(self):
        """Inicializar gestor de BD"""
        self.config = {
            'host': Config.DB_HOST,
            'user': Config.DB_USER,
            'password': Config.DB_PASSWORD,
            'database': Config.DB_NAME,
            'port': Config.DB_PORT
        }
        self.conexion = None
        self.conectar()
    
    def conectar(self) -> bool:
        """
        Establecer conexión con MySQL
        
        Returns:
            bool: True si conectó exitosamente
        """
        try:
            self.conexion = mysql.connector.connect(**self.config)
            
            if self.conexion.is_connected():
                print(f"✅ Conectado a {self.config['database']}")
                return True
            
        except Error as e:
            print(f"❌ Error al conectar: {e}")
            return False
    
    def desconectar(self):
        """Cerrar conexión"""
        if self.conexion and self.conexion.is_connected():
            self.conexion.close()
            print("🔌 Desconectado de MySQL")
    
    def ejecutar_query(self, query: str, parametros: tuple = None) -> Optional[List[Dict]]:
        """
        Ejecutar query SELECT
        
        Args:
            query: SQL query
            parametros: Tupla de parámetros
            
        Returns:
            Lista de diccionarios con resultados
        """
        try:
            cursor = self.conexion.cursor(dictionary=True)
            
            if parametros:
                cursor.execute(query, parametros)
            else:
                cursor.execute(query)
            
            resultados = cursor.fetchall()
            cursor.close()
            
            return resultados
            
        except Error as e:
            print(f"❌ Error en query: {e}")
            return None
    
    def ejecutar_comando(self, query: str, parametros: tuple = None) -> bool:
        """
        Ejecutar comando INSERT/UPDATE/DELETE
        
        Args:
            query: SQL comando
            parametros: Tupla de parámetros
            
        Returns:
            bool: True si ejecutó correctamente
        """
        try:
            cursor = self.conexion.cursor()
            
            if parametros:
                cursor.execute(query, parametros)
            else:
                cursor.execute(query)
            
            self.conexion.commit()
            cursor.close()
            
            return True
            
        except Error as e:
            print(f"❌ Error en comando: {e}")
            self.conexion.rollback()
            return False
    
    def obtener_ultimo_id(self) -> int:
        """
        Obtener último ID insertado
        
        Returns:
            int: ID del último registro
        """
        cursor = self.conexion.cursor()
        cursor.execute("SELECT LAST_INSERT_ID() as id")
        resultado = cursor.fetchone()
        cursor.close()
        return resultado[0] if resultado else 0
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # FUNCIONES ESPECÍFICAS - USUARIOS
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    def buscar_usuario_por_dni(self, dni: str) -> Optional[Dict]:
        """
        Buscar usuario por DNI
        
        Args:
            dni: DNI del usuario (8 dígitos)
            
        Returns:
            Dict con datos del usuario o None
        """
        query = "SELECT * FROM usuarios WHERE dni = %s LIMIT 1"
        resultados = self.ejecutar_query(query, (dni,))
        
        return resultados[0] if resultados else None
    
    def crear_usuario(self, nombre: str, dni: str, edad: int = None,
                     origen: str = 'feria', evento: str = None) -> int:
        """
        Crear nuevo usuario
        
        Args:
            nombre: Nombre completo
            dni: DNI 8 dígitos
            edad: Edad opcional
            origen: feria, web, consultorio
            evento: Nombre del evento
            
        Returns:
            int: ID del usuario creado
        """
        query = """
        INSERT INTO usuarios (nombre, dni, edad, origen, evento_origen, fecha_registro)
        VALUES (%s, %s, %s, %s, %s, NOW())
        """
        
        parametros = (nombre, dni, edad, origen, evento)
        
        if self.ejecutar_comando(query, parametros):
            usuario_id = self.obtener_ultimo_id()
            print(f"✅ Usuario creado: {nombre} (ID: {usuario_id})")
            return usuario_id
        
        return 0
    
    def actualizar_ultimo_contacto(self, usuario_id: int):
        """Actualizar fecha de último contacto"""
        query = "UPDATE usuarios SET ultimo_contacto = NOW() WHERE id = %s"
        self.ejecutar_comando(query, (usuario_id,))
    
    def incrementar_total_consultas(self, usuario_id: int):
        """Incrementar contador de consultas"""
        query = "UPDATE usuarios SET total_consultas = total_consultas + 1 WHERE id = %s"
        self.ejecutar_comando(query, (usuario_id,))
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # FUNCIONES ESPECÍFICAS - SESIONES
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    def crear_sesion(self, sesion_id: str, evento: str, ubicacion: str,
                    dispositivo: str) -> bool:
        """
        Crear nueva sesión autónoma
        
        Args:
            sesion_id: ID único de sesión (FERIA-20251107-001)
            evento: Nombre del evento
            ubicacion: Ubicación física
            dispositivo: ID del dispositivo
            
        Returns:
            bool: True si creó correctamente
        """
        query = """
        INSERT INTO sesiones_autonomas 
        (sesion_id, evento, ubicacion, dispositivo, estado, fecha_inicio)
        VALUES (%s, %s, %s, %s, 'iniciando', NOW())
        """
        
        parametros = (sesion_id, evento, ubicacion, dispositivo)
        return self.ejecutar_comando(query, parametros)
    
    def actualizar_estado_sesion(self, sesion_id: str, estado: str):
        """
        Actualizar estado de sesión
        
        Estados: iniciando, capturando_datos, consultando, 
                generando_receta, imprimiendo, finalizada
        """
        query = "UPDATE sesiones_autonomas SET estado = %s WHERE sesion_id = %s"
        self.ejecutar_comando(query, (estado, sesion_id))
    
    def guardar_datos_capturados(self, sesion_id: str, nombre: str, 
                                 dni: str, edad: int = None, usuario_id: int = None):
        """Guardar datos capturados en sesión"""
        query = """
        UPDATE sesiones_autonomas 
        SET nombre_capturado = %s, dni_capturado = %s, 
            edad_capturada = %s, usuario_id = %s
        WHERE sesion_id = %s
        """
        
        parametros = (nombre, dni, edad, usuario_id, sesion_id)
        self.ejecutar_comando(query, parametros)
    
    def guardar_conversacion_sesion(self, sesion_id: str, mensajes: List[Dict], 
                                    contexto: Dict):
        """Guardar conversación completa en sesión"""
        mensajes_json = json.dumps(mensajes, ensure_ascii=False)
        contexto_json = json.dumps(contexto, ensure_ascii=False)
        
        query = """
        UPDATE sesiones_autonomas 
        SET mensajes_json = %s, contexto_json = %s
        WHERE sesion_id = %s
        """
        
        parametros = (mensajes_json, contexto_json, sesion_id)
        self.ejecutar_comando(query, parametros)
    
    def finalizar_sesion(self, sesion_id: str, diagnostico: str, 
                        productos: List[int], receta: str, 
                        consulta_id: int = None):
        """
        Finalizar sesión y guardar resultado
        
        Args:
            sesion_id: ID de sesión
            diagnostico: Diagnóstico final
            productos: Lista de IDs de productos
            receta: Receta completa generada
            consulta_id: ID de consulta asociada
        """
        productos_str = ','.join(map(str, productos))
        duracion = self._calcular_duracion_sesion(sesion_id)
        
        query = """
        UPDATE sesiones_autonomas 
        SET diagnostico_final = %s, productos_recomendados = %s,
            receta_generada = %s, consulta_id = %s,
            estado = 'finalizada', fecha_fin = NOW(),
            duracion_segundos = %s
        WHERE sesion_id = %s
        """
        
        parametros = (diagnostico, productos_str, receta, 
                     consulta_id, duracion, sesion_id)
        
        return self.ejecutar_comando(query, parametros)
    
    def _calcular_duracion_sesion(self, sesion_id: str) -> int:
        """Calcular duración de sesión en segundos"""
        query = """
        SELECT TIMESTAMPDIFF(SECOND, fecha_inicio, NOW()) as duracion
        FROM sesiones_autonomas WHERE sesion_id = %s
        """
        
        resultado = self.ejecutar_query(query, (sesion_id,))
        return resultado[0]['duracion'] if resultado else 0
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # FUNCIONES ESPECÍFICAS - CONSULTAS
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    def guardar_consulta(self, datos: Dict) -> int:
        """
        Guardar consulta médica completa
        
        Args:
            datos: Diccionario con todos los datos de la consulta
            
        Returns:
            int: ID de la consulta creada
        """
        query = """
        INSERT INTO consultas_medicas (
            usuario_id, sesion_id, sintoma_principal, sintomas_adicionales,
            diagnostico_kairos, confianza_diagnostico, causas_probables,
            productos_recomendados_json, receta_completa, remedios_caseros,
            consejos_dieta, consejos_habitos, mensajes_conversacion,
            fecha_consulta, duracion_minutos, canal, modo_operacion, estado
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 
            NOW(), %s, %s, %s, 'completada'
        )
        """
        
        parametros = (
            datos['usuario_id'],
            datos['sesion_id'],
            datos['sintoma_principal'],
            datos.get('sintomas_adicionales', ''),
            datos['diagnostico'],
            datos.get('confianza', 0.85),
            datos.get('causas', ''),
            json.dumps(datos['productos'], ensure_ascii=False),
            datos['receta_completa'],
            datos.get('remedios_caseros', ''),
            datos.get('consejos_dieta', ''),
            datos.get('consejos_habitos', ''),
            json.dumps(datos.get('conversacion', []), ensure_ascii=False),
            datos.get('duracion_minutos', 0),
            datos.get('canal', 'feria'),
            datos.get('modo', 'feria')
        )
        
        if self.ejecutar_comando(query, parametros):
            consulta_id = self.obtener_ultimo_id()
            print(f"✅ Consulta guardada (ID: {consulta_id})")
            return consulta_id
        
        return 0
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # FUNCIONES ESPECÍFICAS - IMPRESIONES
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    def registrar_impresion(self, sesion_id: str, consulta_id: int,
                           usuario_id: int, estado: str = 'exitosa',
                           impresora: str = None, error: str = None) -> bool:
        """
        Registrar intento de impresión
        
        Args:
            sesion_id: ID de sesión
            consulta_id: ID de consulta
            usuario_id: ID de usuario
            estado: exitosa, fallida, reintento
            impresora: Modelo de impresora
            error: Mensaje de error si falló
        """
        query = """
        INSERT INTO impresiones (
            sesion_id, consulta_id, usuario_id, tipo_impresion,
            estado, impresora_usada, error_mensaje, fecha_impresion
        ) VALUES (%s, %s, %s, 'ticket', %s, %s, %s, NOW())
        """
        
        parametros = (sesion_id, consulta_id, usuario_id, 
                     estado, impresora, error)
        
        return self.ejecutar_comando(query, parametros)
    
    def marcar_ticket_impreso(self, sesion_id: str):
        """Marcar sesión como ticket impreso"""
        query = "UPDATE sesiones_autonomas SET ticket_impreso = TRUE WHERE sesion_id = %s"
        self.ejecutar_comando(query, (sesion_id,))
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # FUNCIONES ESPECÍFICAS - CONVERSACIONES (ML)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    def guardar_mensaje(self, usuario_id: int, sesion_id: str,
                       mensaje: str, intencion: str, confianza: float,
                       respuesta: str):
        """
        Guardar mensaje individual para entrenar ML
        
        Args:
            usuario_id: ID del usuario
            sesion_id: ID de sesión
            mensaje: Mensaje del usuario
            intencion: Intención detectada
            confianza: Nivel de confianza
            respuesta: Respuesta de Kairos
        """
        query = """
        INSERT INTO conversaciones (
            usuario_id, sesion_id, mensaje_usuario, intencion_detectada,
            confianza_intencion, respuesta_kairos, fecha, canal
        ) VALUES (%s, %s, %s, %s, %s, %s, NOW(), 'feria')
        """
        
        parametros = (usuario_id, sesion_id, mensaje, 
                     intencion, confianza, respuesta)
        
        self.ejecutar_comando(query, parametros)
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # FUNCIONES ESPECÍFICAS - ESTADÍSTICAS
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    def obtener_estadisticas_hoy(self) -> Dict:
        """
        Obtener estadísticas del día actual
        
        Returns:
            Dict con estadísticas
        """
        stats = {}
        
        # Total consultas hoy
        query = """
        SELECT COUNT(*) as total 
        FROM sesiones_autonomas 
        WHERE DATE(fecha_inicio) = CURDATE()
        """
        resultado = self.ejecutar_query(query)
        stats['total_consultas'] = resultado[0]['total'] if resultado else 0
        
        # Duración promedio
        query = """
        SELECT AVG(duracion_segundos)/60 as promedio 
        FROM sesiones_autonomas 
        WHERE DATE(fecha_inicio) = CURDATE() AND duracion_segundos > 0
        """
        resultado = self.ejecutar_query(query)
        stats['duracion_promedio'] = round(resultado[0]['promedio'], 1) if resultado and resultado[0]['promedio'] else 0
        
        # Tickets impresos
        query = """
        SELECT COUNT(*) as total 
        FROM impresiones 
        WHERE DATE(fecha_impresion) = CURDATE() AND estado = 'exitosa'
        """
        resultado = self.ejecutar_query(query)
        stats['tickets_impresos'] = resultado[0]['total'] if resultado else 0
        
        return stats
    
    def obtener_configuracion(self, clave: str) -> Optional[str]:
        """
        Obtener valor de configuración
        
        Args:
            clave: Nombre de la configuración
            
        Returns:
            str: Valor de la configuración
        """
        query = "SELECT valor FROM configuracion_sistema WHERE clave = %s"
        resultado = self.ejecutar_query(query, (clave,))
        
        return resultado[0]['valor'] if resultado else None

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PRUEBAS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

if __name__ == "__main__":
    print("="*60)
    print("PROBANDO DATABASE MANAGER")
    print("="*60)
    
    # Crear instancia
    db = DatabaseManager()
    
    if db.conexion and db.conexion.is_connected():
        print("\n✅ Conexión exitosa\n")
        
        # Probar buscar usuario
        print("📝 Buscando usuario con DNI 12345678...")
        usuario = db.buscar_usuario_por_dni('12345678')
        if usuario:
            print(f"   ✅ Encontrado: {usuario['nombre']}")
        
        # Probar crear sesión
        print("\n📝 Creando sesión de prueba...")
        sesion_id = f"TEST-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        if db.crear_sesion(sesion_id, "Feria Test", "Stand Test", "PC-Test"):
            print(f"   ✅ Sesión creada: {sesion_id}")
        
        # Estadísticas
        print("\n📊 Estadísticas de hoy:")
        stats = db.obtener_estadisticas_hoy()
        for key, value in stats.items():
            print(f"   {key}: {value}")
        
        # Cerrar
        db.desconectar()
    
    else:
        print("\n❌ No se pudo conectar")
    
    print("\n" + "="*60)