"""
Gestor de Base de Datos SQLite - MODO OFFLINE ROBUSTO
Sincronización bidireccional con MySQL
"""

import sqlite3
import json
import os
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BASE_DIR)

from backend.database.database_manager import DatabaseManager

class SQLiteManager:
    """
    Gestor completo de SQLite para modo offline
    
    Funcionalidades:
    - Base de datos local completa
    - Sincronización bidireccional con MySQL
    - Caché de conocimientos de GPT
    - Backup automático de consultas
    - Resolución de conflictos
    """
    
    def __init__(self, db_path: str = None):
        """
        Inicializar gestor SQLite
        
        Args:
            db_path: Ruta a la base de datos SQLite
        """
        if db_path:
            self.db_path = db_path
        else:
            # Ruta por defecto
            data_dir = os.path.join(BASE_DIR, 'backend', 'data')
            os.makedirs(data_dir, exist_ok=True)
            self.db_path = os.path.join(data_dir, 'kairos_offline.db')
        
        self.mysql_manager = None  # Para sincronización
        
        # Crear base de datos y tablas
        self._crear_tablas()
        
        print(f"✅ SQLite Manager inicializado")
        print(f"   Base de datos: {self.db_path}")
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # CONEXIÓN Y ESTRUCTURA
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    def conectar(self) -> sqlite3.Connection:
        """
        Crear conexión a SQLite
        
        Returns:
            Connection: Conexión a SQLite
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Para acceder por nombre de columna
        return conn
    
    def _crear_tablas(self):
        """Crear todas las tablas necesarias"""
        
        conn = self.conectar()
        cursor = conn.cursor()
        
        # Tabla: usuarios
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            dni TEXT UNIQUE NOT NULL,
            edad INTEGER,
            genero TEXT,
            celular TEXT,
            email TEXT,
            origen TEXT DEFAULT 'feria',
            evento_origen TEXT,
            fecha_registro TEXT DEFAULT CURRENT_TIMESTAMP,
            ultimo_contacto TEXT,
            total_consultas INTEGER DEFAULT 0,
            sincronizado INTEGER DEFAULT 0,
            mysql_id INTEGER
        )
        """)
        
        # Tabla: sesiones_autonomas
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS sesiones_autonomas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sesion_id TEXT UNIQUE NOT NULL,
            usuario_id INTEGER,
            evento TEXT,
            ubicacion TEXT,
            dispositivo TEXT,
            estado TEXT,
            nombre_capturado TEXT,
            dni_capturado TEXT,
            edad_capturada INTEGER,
            mensajes_json TEXT,
            contexto_json TEXT,
            diagnostico_final TEXT,
            productos_recomendados TEXT,
            receta_generada TEXT,
            ticket_impreso INTEGER DEFAULT 0,
            fecha_inicio TEXT DEFAULT CURRENT_TIMESTAMP,
            fecha_fin TEXT,
            duracion_segundos INTEGER,
            sincronizado INTEGER DEFAULT 0,
            mysql_id INTEGER
        )
        """)
        
        # Tabla: consultas_medicas
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS consultas_medicas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER,
            sesion_id TEXT,
            sintoma_principal TEXT NOT NULL,
            sintomas_adicionales TEXT,
            diagnostico_kairos TEXT,
            confianza_diagnostico REAL,
            causas_probables TEXT,
            productos_recomendados_json TEXT,
            receta_completa TEXT,
            remedios_caseros TEXT,
            consejos_dieta TEXT,
            consejos_habitos TEXT,
            mensajes_conversacion TEXT,
            fecha_consulta TEXT DEFAULT CURRENT_TIMESTAMP,
            duracion_minutos INTEGER,
            canal TEXT DEFAULT 'feria',
            modo_operacion TEXT DEFAULT 'feria',
            estado TEXT DEFAULT 'completada',
            sincronizado INTEGER DEFAULT 0,
            mysql_id INTEGER
        )
        """)
        
        # Tabla: conocimientos_completos (caché)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS conocimientos_completos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            condicion TEXT NOT NULL,
            sintomas_keywords TEXT,
            causas_json TEXT,
            tratamiento_json TEXT,
            alimentos_aumentar_json TEXT,
            alimentos_evitar_json TEXT,
            habitos_json TEXT,
            advertencias_json TEXT,
            cuando_ver_medico TEXT,
            productos_recomendados_json TEXT,
            origen TEXT DEFAULT 'gpt',
            confianza REAL,
            fecha_aprendido TEXT DEFAULT CURRENT_TIMESTAMP,
            veces_usado INTEGER DEFAULT 0,
            sincronizado INTEGER DEFAULT 0
        )
        """)
        
        # Tabla: conversaciones
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS conversaciones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER,
            sesion_id TEXT,
            mensaje_usuario TEXT NOT NULL,
            intencion_detectada TEXT,
            confianza_intencion REAL,
            respuesta_kairos TEXT NOT NULL,
            fecha TEXT DEFAULT CURRENT_TIMESTAMP,
            canal TEXT DEFAULT 'feria',
            sincronizado INTEGER DEFAULT 0
        )
        """)
        
        # Tabla: productos_naturales (caché)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS productos_naturales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            categoria TEXT,
            codigo_producto TEXT,
            descripcion_corta TEXT,
            presentacion TEXT,
            para_que_sirve TEXT,
            beneficios TEXT,
            dosis TEXT,
            precio REAL,
            activo INTEGER DEFAULT 1,
            sintomas_que_trata TEXT,
            fecha_cache TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # Tabla: log_sincronizacion
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS log_sincronizacion (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tipo TEXT NOT NULL,
            direccion TEXT NOT NULL,
            registros_procesados INTEGER,
            registros_exitosos INTEGER,
            registros_fallidos INTEGER,
            errores_json TEXT,
            fecha_sincronizacion TEXT DEFAULT CURRENT_TIMESTAMP,
            duracion_segundos REAL
        )
        """)
        
        conn.commit()
        conn.close()
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # OPERACIONES BÁSICAS - USUARIOS
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    def buscar_usuario_offline(self, dni: str) -> Optional[Dict]:
        """
        Buscar usuario por DNI en SQLite
        
        Args:
            dni: DNI del usuario
            
        Returns:
            Dict con datos del usuario o None
        """
        conn = self.conectar()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM usuarios WHERE dni = ?", (dni,))
        resultado = cursor.fetchone()
        
        conn.close()
        
        if resultado:
            return dict(resultado)
        return None
    
    def crear_usuario_offline(self, nombre: str, dni: str, edad: int = None) -> int:
        """
        Crear usuario en SQLite
        
        Args:
            nombre: Nombre completo
            dni: DNI
            edad: Edad opcional
            
        Returns:
            int: ID del usuario creado
        """
        conn = self.conectar()
        cursor = conn.cursor()
        
        cursor.execute("""
        INSERT INTO usuarios (nombre, dni, edad, origen, fecha_registro)
        VALUES (?, ?, ?, 'feria', datetime('now'))
        """, (nombre, dni, edad))
        
        usuario_id = cursor.lastrowid
        
        conn.commit()
        conn.close()
        
        print(f"✅ Usuario offline creado: {nombre} (ID: {usuario_id})")
        
        return usuario_id
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # OPERACIONES BÁSICAS - SESIONES
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    def guardar_sesion_offline(self, sesion_id: str, evento: str, ubicacion: str) -> bool:
        """
        Guardar sesión en SQLite
        
        Args:
            sesion_id: ID único de sesión
            evento: Nombre del evento
            ubicacion: Ubicación física
            
        Returns:
            bool: True si guardó correctamente
        """
        conn = self.conectar()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
            INSERT INTO sesiones_autonomas (sesion_id, evento, ubicacion, estado)
            VALUES (?, ?, ?, 'iniciando')
            """, (sesion_id, evento, ubicacion))
            
            conn.commit()
            return True
            
        except Exception as e:
            print(f"❌ Error guardando sesión offline: {e}")
            return False
            
        finally:
            conn.close()
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # OPERACIONES BÁSICAS - CONSULTAS
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    def guardar_consulta_offline(self, datos: Dict) -> int:
        """
        Guardar consulta médica en SQLite
        
        Args:
            datos: Diccionario con datos de la consulta
            
        Returns:
            int: ID de la consulta creada
        """
        conn = self.conectar()
        cursor = conn.cursor()
        
        cursor.execute("""
        INSERT INTO consultas_medicas (
            usuario_id, sesion_id, sintoma_principal, diagnostico_kairos,
            confianza_diagnostico, causas_probables, productos_recomendados_json,
            receta_completa, mensajes_conversacion, fecha_consulta,
            duracion_minutos, canal, modo_operacion
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), ?, ?, ?)
        """, (
            datos['usuario_id'],
            datos['sesion_id'],
            datos['sintoma_principal'],
            datos['diagnostico'],
            datos.get('confianza', 0.85),
            datos.get('causas', ''),
            json.dumps(datos['productos'], ensure_ascii=False),
            datos['receta_completa'],
            json.dumps(datos.get('conversacion', []), ensure_ascii=False),
            datos.get('duracion_minutos', 0),
            datos.get('canal', 'feria'),
            datos.get('modo', 'feria')
        ))
        
        consulta_id = cursor.lastrowid
        
        conn.commit()
        conn.close()
        
        print(f"✅ Consulta offline guardada (ID: {consulta_id})")
        
        return consulta_id
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # CACHÉ DE CONOCIMIENTOS
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    def buscar_conocimiento_cache(self, sintoma: str) -> Optional[Dict]:
        """
        Buscar conocimiento en caché local
        
        Args:
            sintoma: Síntoma a buscar
            
        Returns:
            Dict con conocimiento o None
        """
        conn = self.conectar()
        cursor = conn.cursor()
        
        # Buscar en condición o síntomas
        cursor.execute("""
        SELECT * FROM conocimientos_completos
        WHERE LOWER(condicion) LIKE ? OR LOWER(sintomas_keywords) LIKE ?
        ORDER BY veces_usado DESC
        LIMIT 1
        """, (f"%{sintoma.lower()}%", f"%{sintoma.lower()}%"))
        
        resultado = cursor.fetchone()
        
        if resultado:
            # Incrementar uso
            cursor.execute(
                "UPDATE conocimientos_completos SET veces_usado = veces_usado + 1 WHERE id = ?",
                (resultado['id'],)
            )
            conn.commit()
        
        conn.close()
        
        if resultado:
            return dict(resultado)
        return None
    
    def guardar_conocimiento_cache(self, conocimiento: Dict) -> bool:
        """
        Guardar conocimiento de GPT en caché
        
        Args:
            conocimiento: Dict con conocimiento completo
            
        Returns:
            bool: True si guardó correctamente
        """
        conn = self.conectar()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
            INSERT INTO conocimientos_completos (
                condicion, sintomas_keywords, causas_json, tratamiento_json,
                alimentos_aumentar_json, alimentos_evitar_json, habitos_json,
                advertencias_json, cuando_ver_medico, productos_recomendados_json,
                origen, confianza
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                conocimiento['condicion'],
                conocimiento.get('sintomas', ''),
                json.dumps(conocimiento.get('causas', []), ensure_ascii=False),
                json.dumps(conocimiento.get('tratamiento', []), ensure_ascii=False),
                json.dumps(conocimiento.get('alimentos_aumentar', []), ensure_ascii=False),
                json.dumps(conocimiento.get('alimentos_evitar', []), ensure_ascii=False),
                json.dumps(conocimiento.get('habitos', []), ensure_ascii=False),
                json.dumps(conocimiento.get('advertencias', []), ensure_ascii=False),
                conocimiento.get('cuando_ver_medico', ''),
                json.dumps(conocimiento.get('productos', []), ensure_ascii=False),
                'gpt',
                conocimiento.get('confianza', 0.85)
            ))
            
            conn.commit()
            print(f"✅ Conocimiento guardado en caché: {conocimiento['condicion']}")
            return True
            
        except Exception as e:
            print(f"❌ Error guardando conocimiento: {e}")
            return False
            
        finally:
            conn.close()
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # SINCRONIZACIÓN CON MYSQL
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    def sincronizar_desde_mysql(self, forzar: bool = False) -> Dict:
        """
        Sincronizar datos DESDE MySQL HACIA SQLite
        Copia productos, conocimientos, configuraciones
        
        Args:
            forzar: Si debe re-sincronizar todo
            
        Returns:
            Dict con resultado de sincronización
        """
        print(f"\n{'='*70}")
        print("📥 SINCRONIZANDO DESDE MYSQL → SQLITE")
        print(f"{'='*70}\n")
        
        inicio = datetime.now()
        
        try:
            # Conectar a MySQL
            mysql = DatabaseManager()
            
            resultado = {
                'productos': self._sincronizar_productos_desde_mysql(mysql),
                'conocimientos': self._sincronizar_conocimientos_desde_mysql(mysql),
                'errores': []
            }
            
            mysql.desconectar()
            
            # Log de sincronización
            duracion = (datetime.now() - inicio).total_seconds()
            self._registrar_log_sync('completa', 'mysql_to_sqlite', resultado, duracion)
            
            print(f"\n{'='*70}")
            print("✅ SINCRONIZACIÓN COMPLETADA")
            print(f"{'='*70}")
            print(f"   Productos: {resultado['productos']} registros")
            print(f"   Conocimientos: {resultado['conocimientos']} registros")
            print(f"   Duración: {duracion:.1f}s")
            print(f"{'='*70}\n")
            
            return resultado
            
        except Exception as e:
            print(f"❌ Error en sincronización: {e}")
            return {'error': str(e)}
    
    def _sincronizar_productos_desde_mysql(self, mysql: DatabaseManager) -> int:
        """Sincronizar productos desde MySQL"""
        
        print("📦 Sincronizando productos...")
        
        # Obtener productos de MySQL
        productos = mysql.ejecutar_query("""
        SELECT * FROM productos_naturales WHERE activo = TRUE
        """)
        
        if not productos:
            print("   ⚠️ No hay productos en MySQL")
            return 0
        
        conn = self.conectar()
        cursor = conn.cursor()
        
        # Limpiar tabla local
        cursor.execute("DELETE FROM productos_naturales")
        
        sincronizados = 0
        
        # Insertar productos
        for p in productos:
            try:
                # Convertir Decimal a float para precio
                precio = float(p['precio']) if p.get('precio') is not None else 0.0
                
                cursor.execute("""
                INSERT INTO productos_naturales (
                    id, nombre, categoria, codigo_producto, descripcion_corta,
                    presentacion, para_que_sirve, beneficios, dosis, precio,
                    activo, sintomas_que_trata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    int(p['id']),
                    str(p['nombre']),
                    str(p['categoria']) if p.get('categoria') else None,
                    str(p['codigo_producto']) if p.get('codigo_producto') else None,
                    str(p['descripcion_corta']) if p.get('descripcion_corta') else None,
                    str(p['presentacion']) if p.get('presentacion') else None,
                    str(p['para_que_sirve']) if p.get('para_que_sirve') else None,
                    str(p['beneficios_principales']) if p.get('beneficios_principales') else None,
                    str(p['dosis_recomendada']) if p.get('dosis_recomendada') else None,
                    precio,  # Ya convertido a float
                    1,
                    str(p['sintomas_que_trata']) if p.get('sintomas_que_trata') else None
                ))
                
                sincronizados += 1
                
            except Exception as e:
                print(f"   ⚠️ Error en producto '{p.get('nombre', 'desconocido')}': {e}")
                import traceback
                traceback.print_exc()
                continue
        
        conn.commit()
        conn.close()
        
        print(f"   ✅ {sincronizados} productos sincronizados")
        
        return sincronizados
    
    def _sincronizar_conocimientos_desde_mysql(self, mysql: DatabaseManager) -> int:
        """Sincronizar conocimientos desde MySQL"""
        
        print("🧠 Sincronizando conocimientos...")
        
        # Obtener conocimientos más usados
        conocimientos = mysql.ejecutar_query("""
        SELECT * FROM conocimientos_completos
        ORDER BY veces_usado DESC
        LIMIT 100
        """)
        
        if not conocimientos:
            print("   ⚠️ No hay conocimientos en MySQL")
            return 0
        
        conn = self.conectar()
        cursor = conn.cursor()
        
        # Limpiar tabla local
        cursor.execute("DELETE FROM conocimientos_completos")
        
        # Insertar conocimientos
        for c in conocimientos:
            cursor.execute("""
            INSERT INTO conocimientos_completos (
                condicion, sintomas_keywords, causas_json, tratamiento_json,
                alimentos_aumentar_json, alimentos_evitar_json, habitos_json,
                advertencias_json, cuando_ver_medico, productos_recomendados_json,
                origen, confianza, veces_usado
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                c['condicion'], c['sintomas_keywords'], c['causas_json'],
                c['tratamiento_json'], c['alimentos_aumentar_json'],
                c['alimentos_evitar_json'], c['habitos_json'],
                c['advertencias_json'], c['cuando_ver_medico'],
                c['productos_recomendados_json'], c['origen'],
                c['confianza'], c['veces_usado']
            ))
        
        conn.commit()
        conn.close()
        
        print(f"   ✅ {len(conocimientos)} conocimientos sincronizados")
        
        return len(conocimientos)
    
    def sincronizar_hacia_mysql(self) -> Dict:
        """
        Sincronizar datos DESDE SQLite HACIA MySQL
        Sube consultas, usuarios, sesiones pendientes
        
        Returns:
            Dict con resultado de sincronización
        """
        print(f"\n{'='*70}")
        print("📤 SINCRONIZANDO DESDE SQLITE → MYSQL")
        print(f"{'='*70}\n")
        
        inicio = datetime.now()
        
        try:
            mysql = DatabaseManager()
            
            resultado = {
                'usuarios': self._sincronizar_usuarios_hacia_mysql(mysql),
                'consultas': self._sincronizar_consultas_hacia_mysql(mysql),
                'sesiones': self._sincronizar_sesiones_hacia_mysql(mysql),
                'errores': []
            }
            
            mysql.desconectar()
            
            duracion = (datetime.now() - inicio).total_seconds()
            self._registrar_log_sync('pendientes', 'sqlite_to_mysql', resultado, duracion)
            
            print(f"\n{'='*70}")
            print("✅ SINCRONIZACIÓN COMPLETADA")
            print(f"{'='*70}")
            print(f"   Usuarios: {resultado['usuarios']} registros")
            print(f"   Consultas: {resultado['consultas']} registros")
            print(f"   Sesiones: {resultado['sesiones']} registros")
            print(f"   Duración: {duracion:.1f}s")
            print(f"{'='*70}\n")
            
            return resultado
            
        except Exception as e:
            print(f"❌ Error en sincronización: {e}")
            return {'error': str(e)}
    
    def _sincronizar_usuarios_hacia_mysql(self, mysql: DatabaseManager) -> int:
        """Sincronizar usuarios hacia MySQL"""
        
        print("👥 Sincronizando usuarios...")
        
        conn = self.conectar()
        cursor = conn.cursor()
        
        # Obtener usuarios no sincronizados
        cursor.execute("SELECT * FROM usuarios WHERE sincronizado = 0")
        usuarios = cursor.fetchall()
        
        if not usuarios:
            print("   ℹ️ No hay usuarios pendientes")
            conn.close()
            return 0
        
        sincronizados = 0
        
        for usuario in usuarios:
            # Verificar si ya existe en MySQL
            usuario_mysql = mysql.buscar_usuario_por_dni(usuario['dni'])
            
            if usuario_mysql:
                # Actualizar ID de MySQL
                cursor.execute(
                    "UPDATE usuarios SET sincronizado = 1, mysql_id = ? WHERE id = ?",
                    (usuario_mysql['id'], usuario['id'])
                )
            else:
                # Crear en MySQL
                mysql_id = mysql.crear_usuario(
                    usuario['nombre'],
                    usuario['dni'],
                    usuario['edad'],
                    usuario['origen'],
                    usuario['evento_origen']
                )
                
                # Actualizar SQLite
                cursor.execute(
                    "UPDATE usuarios SET sincronizado = 1, mysql_id = ? WHERE id = ?",
                    (mysql_id, usuario['id'])
                )
            
            sincronizados += 1
        
        conn.commit()
        conn.close()
        
        print(f"   ✅ {sincronizados} usuarios sincronizados")
        
        return sincronizados
    
    def _sincronizar_consultas_hacia_mysql(self, mysql: DatabaseManager) -> int:
        """Sincronizar consultas hacia MySQL"""
        
        print("🏥 Sincronizando consultas...")
        
        conn = self.conectar()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM consultas_medicas WHERE sincronizado = 0")
        consultas = cursor.fetchall()
        
        if not consultas:
            print("   ℹ️ No hay consultas pendientes")
            conn.close()
            return 0
        
        sincronizados = 0
        
        for consulta in consultas:
            datos = {
                'usuario_id': consulta['usuario_id'],
                'sesion_id': consulta['sesion_id'],
                'sintoma_principal': consulta['sintoma_principal'],
                'diagnostico': consulta['diagnostico_kairos'],
                'confianza': consulta['confianza_diagnostico'],
                'causas': consulta['causas_probables'] or '',
                'productos': json.loads(consulta['productos_recomendados_json'] or '[]'),
                'receta_completa': consulta['receta_completa'],
                'conversacion': json.loads(consulta['mensajes_conversacion'] or '[]'),
                'duracion_minutos': consulta['duracion_minutos'],
                'canal': consulta['canal'],
                'modo': consulta['modo_operacion']
            }
            
            mysql_id = mysql.guardar_consulta(datos)
            
            if mysql_id:
                cursor.execute(
                    "UPDATE consultas_medicas SET sincronizado = 1, mysql_id = ? WHERE id = ?",
                    (mysql_id, consulta['id'])
                )
                sincronizados += 1
        
        conn.commit()
        conn.close()
        
        print(f"   ✅ {sincronizados} consultas sincronizadas")
        
        return sincronizados
    
    def _sincronizar_sesiones_hacia_mysql(self, mysql: DatabaseManager) -> int:
        """Sincronizar sesiones hacia MySQL"""
        
        print("📋 Sincronizando sesiones...")
        
        conn = self.conectar()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM sesiones_autonomas WHERE sincronizado = 0")
        sesiones = cursor.fetchall()
        
        if not sesiones:
            print("   ℹ️ No hay sesiones pendientes")
            conn.close()
            return 0
        
        sincronizados = 0
        
        for sesion in sesiones:
            # Verificar si ya existe
            existe = mysql.ejecutar_query(
                "SELECT id FROM sesiones_autonomas WHERE sesion_id = ?",
                (sesion['sesion_id'],)
            )
            
            if not existe:
                # Crear en MySQL (simplificado - adaptar según necesidad)
                if mysql.crear_sesion(
                    sesion['sesion_id'],
                    sesion['evento'],
                    sesion['ubicacion'],
                    sesion['dispositivo']
                ):
                    cursor.execute(
                        "UPDATE sesiones_autonomas SET sincronizado = 1 WHERE id = ?",
                        (sesion['id'],)
                    )
                    sincronizados += 1
        
        conn.commit()
        conn.close()
        
        print(f"   ✅ {sincronizados} sesiones sincronizadas")
        
        return sincronizados
    
    def _registrar_log_sync(self, tipo: str, direccion: str, 
                           resultado: Dict, duracion: float):
        """Registrar log de sincronización"""
        
        conn = self.conectar()
        cursor = conn.cursor()
        
        total = sum(v for k, v in resultado.items() if isinstance(v, int))
        
        cursor.execute("""
        INSERT INTO log_sincronizacion (
            tipo, direccion, registros_procesados, registros_exitosos,
            registros_fallidos, errores_json, duracion_segundos
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            tipo, direccion, total, total,
            0, json.dumps(resultado.get('errores', [])),
            duracion
        ))
        
        conn.commit()
        conn.close()
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # UTILIDADES
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    def obtener_estadisticas(self) -> Dict:
        """Obtener estadísticas de la BD local"""
        
        conn = self.conectar()
        cursor = conn.cursor()
        
        stats = {}
        
        # Contar registros por tabla
        tablas = [
            'usuarios', 'sesiones_autonomas', 'consultas_medicas',
            'conocimientos_completos', 'conversaciones', 'productos_naturales'
        ]
        
        for tabla in tablas:
            cursor.execute(f"SELECT COUNT(*) as total FROM {tabla}")
            resultado = cursor.fetchone()
            stats[tabla] = resultado['total']
            
            # Contar pendientes de sincronizar
            if tabla in ['usuarios', 'sesiones_autonomas', 'consultas_medicas']:
                cursor.execute(f"SELECT COUNT(*) as pendientes FROM {tabla} WHERE sincronizado = 0")
                resultado = cursor.fetchone()
                stats[f"{tabla}_pendientes"] = resultado['pendientes']
        
        # Tamaño de BD
        import os
        if os.path.exists(self.db_path):
            stats['tamaño_mb'] = os.path.getsize(self.db_path) / (1024 * 1024)
        
        conn.close()
        
        return stats
    
    def limpiar_datos_antiguos(self, dias: int = 30) -> int:
        """
        Limpiar datos sincronizados antiguos
        
        Args:
            dias: Días de antigüedad
            
        Returns:
            int: Registros eliminados
        """
        conn = self.conectar()
        cursor = conn.cursor()
        
        fecha_limite = datetime.now().replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        fecha_limite = (fecha_limite - timedelta(days=dias)).strftime('%Y-%m-%d')
        
        # Eliminar consultas sincronizadas antiguas
        cursor.execute("""
        DELETE FROM consultas_medicas
        WHERE sincronizado = 1 AND fecha_consulta < ?
        """, (fecha_limite,))
        
        eliminados = cursor.rowcount
        
        conn.commit()
        conn.close()
        
        print(f"✅ {eliminados} registros antiguos eliminados")
        
        return eliminados


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PRUEBAS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

if __name__ == "__main__":
    print("\n" + "="*70)
    print(" "*20 + "🧪 TEST SQLITE MANAGER")
    print("="*70 + "\n")
    
    # Crear instancia
    sqlite = SQLiteManager()
    
    # Test 1: Crear usuario (o buscar si existe)
    print("TEST 1: Crear/Buscar usuario offline")
    
    # Primero buscar
    usuario = sqlite.buscar_usuario_offline("99999998")
    
    if usuario:
        print(f"   Usuario ya existe: {usuario['nombre']} (ID: {usuario['id']})")
        usuario_id = usuario['id']
    else:
        usuario_id = sqlite.crear_usuario_offline("Test Usuario", "99999998", 25)
        print(f"   Usuario creado: ID {usuario_id}")
    
    print()
    
    # Test 2: Buscar usuario
    print("TEST 2: Verificar búsqueda")
    usuario = sqlite.buscar_usuario_offline("99999998")
    if usuario:
        print(f"   ✅ Encontrado: {usuario['nombre']}\n")
    
    # Test 3: Sincronizar desde MySQL
    print("TEST 3: Sincronizar desde MySQL")
    try:
        resultado = sqlite.sincronizar_desde_mysql()
        print(f"   Productos: {resultado.get('productos', 0)}")
        print(f"   Conocimientos: {resultado.get('conocimientos', 0)}\n")
    except Exception as e:
        print(f"   ❌ Error: {e}\n")
    
    # Test 4: Verificar productos
    print("TEST 4: Verificar productos en SQLite")
    conn = sqlite.conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) as total FROM productos_naturales")
    resultado = cursor.fetchone()
    print(f"   Productos en SQLite: {resultado['total']}")
    
    if resultado['total'] > 0:
        cursor.execute("SELECT * FROM productos_naturales LIMIT 3")
        productos = cursor.fetchall()
        for p in productos:
            print(f"   • {p['nombre']} - S/. {p['precio']}")
    
    conn.close()
    print()
    
    # Test 5: Estadísticas
    print("TEST 5: Estadísticas generales")
    stats = sqlite.obtener_estadisticas()
    print(f"   Usuarios: {stats['usuarios']}")
    print(f"   Consultas: {stats['consultas_medicas']}")
    print(f"   Conocimientos: {stats['conocimientos_completos']}")
    print(f"   Productos: {stats['productos_naturales']}")
    print(f"   Tamaño BD: {stats.get('tamaño_mb', 0):.2f} MB")
    
    # Pendientes de sincronizar
    if stats.get('usuarios_pendientes', 0) > 0:
        print(f"\n   ⚠️ Pendientes de sincronizar:")
        print(f"      Usuarios: {stats.get('usuarios_pendientes', 0)}")
        print(f"      Consultas: {stats.get('consultas_medicas_pendientes', 0)}")
        print(f"      Sesiones: {stats.get('sesiones_autonomas_pendientes', 0)}")
    
    print("\n" + "="*70)
    print("✅ PRUEBAS COMPLETADAS")
    print("="*70 + "\n")