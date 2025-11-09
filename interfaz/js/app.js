/**
 * ═══════════════════════════════════════════════════════════════
 * KAIROS - Aplicación Principal - CORREGIDO V2
 * ✅ Voz limpia (sin JSON/timestamps)
 * ✅ No cierra automáticamente
 * ✅ Permite chat post-diagnóstico
 * ═══════════════════════════════════════════════════════════════
 */

class KairosApp {
  constructor() {
    this.estado = "espera";
    this.datosUsuario = null;
    this.mensajes = [];
    this.diagnosticoActual = null;

    console.log("🚀 Kairos App inicializada");
    console.log("🔧 Debug mode:", KairosConfig.DEBUG);

    this.inicializar();
  }

  /**
   * Inicializar aplicación
   */
  async inicializar() {
    console.log("✨ Kairos Minimalista cargado");

    // Verificar conexión API
    const conectado = await api.healthCheck();
    if (!conectado) {
      this.mostrarError("No se pudo conectar con el servidor");
      return;
    }

    // Cargar estadísticas
    this.actualizarEstadisticas();

    // Auto-refresh estadísticas cada 30 seg
    setInterval(() => this.actualizarEstadisticas(), 30000);

    // Detectar inactividad
    this.resetearInactividad();
  }

  /**
   * Actualizar estadísticas
   */
  async actualizarEstadisticas() {
    try {
      const result = await api.obtenerEstadisticas();
      if (result.success) {
        document.getElementById("contador-hoy").textContent =
          result.estadisticas.total_consultas || 0;
      }
    } catch (error) {
      console.error("Error obteniendo estadísticas:", error);
    }
  }

  /**
   * Cambiar pantalla
   */
  cambiarPantalla(nombre) {
    // Ocultar todas
    document.querySelectorAll(".screen").forEach((s) => {
      s.classList.remove("active");
    });

    // Mostrar nueva
    const elemento = document.getElementById(`pantalla-${nombre}`);
    if (elemento) {
      elemento.classList.add("active");
      this.estado = nombre;
    }

    console.log(`📺 Pantalla: ${nombre}`);
  }

  /**
   * Iniciar consulta
   */
  async iniciarConsulta() {
    try {
      const result = await api.nuevaSesion();

      if (result.success) {
        console.log("✅ Sesión creada:", result.sesion_id);
        this.cambiarPantalla("datos");
      } else {
        this.mostrarError("No se pudo iniciar sesión");
      }
    } catch (error) {
      this.mostrarError("Error al iniciar sesión");
    }
  }

  /**
   * Capturar datos del paciente
   */
  async capturarDatos() {
    const nombre = document.getElementById("nombre").value.trim();
    const dni = document.getElementById("dni").value.trim();
    const edadInput = document.getElementById("edad").value;
    const edad = edadInput ? parseInt(edadInput) : null;

    // Validar
    const validacion = this.validarDatos(nombre, dni, edad);
    if (!validacion.valido) {
      this.mostrarValidacion(validacion.errores);
      return;
    }

    try {
      const result = await api.capturarDatos(nombre, dni, edad);

      if (result.success) {
        this.datosUsuario = {
          nombre: nombre,
          dni: dni,
          edad: edad,
          ...result.info,
        };

        // Actualizar UI
        document.getElementById("nombre-paciente").textContent = nombre;
        document.getElementById("dni-paciente").textContent = `DNI: ${dni}`;

        // Ir a chat
        this.cambiarPantalla("chat");

        // Mensaje inicial
        const primerNombre = nombre.split(" ")[0];
        const mensajeBienvenida = `Hola ${primerNombre}, ¿en qué puedo ayudarte hoy?`;

        this.agregarMensajeKairos(mensajeBienvenida);

        console.log("✅ Datos capturados:", this.datosUsuario);
      } else {
        this.mostrarValidacion([
          result.info?.errores?.[0] || "Error capturando datos",
        ]);
      }
    } catch (error) {
      console.error("Error:", error);
      this.mostrarValidacion(["Error de conexión con el servidor"]);
    }
  }

  /**
   * Validar datos
   */
  validarDatos(nombre, dni, edad) {
    const errores = [];

    if (!nombre || nombre.length < 6) {
      errores.push("Ingresa tu nombre completo (mínimo 6 caracteres)");
    }

    if (!/^\d{8}$/.test(dni)) {
      errores.push("El DNI debe tener exactamente 8 dígitos");
    }

    if (edad && (edad < 0 || edad > 120)) {
      errores.push("Edad inválida");
    }

    return {
      valido: errores.length === 0,
      errores,
    };
  }

  /**
   * Mostrar validación
   */
  mostrarValidacion(errores) {
    const div = document.getElementById("validacion");

    if (errores.length === 0) {
      div.innerHTML = "";
      div.className = "validation-message";
    } else {
      div.innerHTML = errores.map((e) => `• ${e}`).join("<br>");
      div.className = "validation-message error";
    }
  }

  /**
   * ⭐ CORREGIDO: Enviar mensaje con detección automática Y voz limpia
   */
  async enviarMensaje() {
    const input = document.getElementById("mensaje-input");
    const mensaje = input.value.trim();

    if (!mensaje) return;

    // Agregar mensaje del usuario
    this.agregarMensajeUsuario(mensaje);
    input.value = "";

    // Mostrar indicador "escribiendo"
    document.getElementById("escribiendo").style.display = "flex";

    try {
      const result = await api.enviarMensaje(mensaje);

      // Ocultar indicador
      document.getElementById("escribiendo").style.display = "none";

      if (result.success) {
        const res = result.resultado;

        // Agregar respuesta de Kairos
        this.agregarMensajeKairos(res.respuesta);

        // ⭐ LIMPIAR TEXTO PARA VOZ (sin JSON, timestamps)
        if (voz && voz.vozActiva) {
          let textoLimpio = res.respuesta;

          // Si es objeto con content
          if (typeof res.respuesta === "object" && res.respuesta.content) {
            textoLimpio = res.respuesta.content;
          }

          // Limpiar cualquier JSON residual
          textoLimpio = String(textoLimpio)
            .replace(/\{[^}]*"timestamp"[^}]*\}/gi, "") // Quitar objetos con timestamp
            .replace(/\{[^}]*"role"[^}]*\}/gi, "") // Quitar objetos con role
            .replace(/timestamp.*$/gim, "") // Quitar líneas con timestamp
            .replace(/\{[^}]*\}/g, "") // Quitar cualquier JSON
            .trim();

          if (textoLimpio) {
            voz.hablar(textoLimpio);
          }
        }

        // ⭐ Si ya hay diagnóstico, es chat post-diagnóstico
        if (this.diagnosticoActual && res.tipo === 'respuesta_duda') {
          console.log("💬 Chat post-diagnóstico activo");
          return; // Solo agregar mensaje y hablar, no hacer nada más
        }

        // ⭐ DETECCIÓN AUTOMÁTICA: Verificar si está listo para diagnosticar
        if (res.listo_diagnostico) {
          console.log("🎯 Diagnóstico listo - generando automáticamente...");

          // Esperar 1.5 segundos para que usuario vea mensaje
          await this.esperar(1500);

          // Generar diagnóstico automáticamente
          await this.generarDiagnosticoAutomatico();
        }
      }
    } catch (error) {
      document.getElementById("escribiendo").style.display = "none";
      this.mostrarError("Error enviando mensaje");
      console.error(error);
    }
  }

  /**
   * ⭐ CORREGIDO: Generar diagnóstico y MOSTRAR RECETA (no cerrar)
   */
  async generarDiagnosticoAutomatico() {
    console.log("🧠 Generando diagnóstico...");

    // Cambiar a pantalla "Generando"
    this.cambiarPantalla("generando");

    // Animar pasos
    setTimeout(() => {
      const paso = document.getElementById("paso-productos");
      if (paso) paso.classList.add("active");
    }, 1000);

    setTimeout(() => {
      const paso = document.getElementById("paso-receta");
      if (paso) paso.classList.add("active");
    }, 2000);

    try {
      // Llamar API para generar diagnóstico
      const result = await api.generarDiagnostico();

      if (result.success) {
        const diagnostico = result.diagnostico;

        console.log("✅ Diagnóstico recibido:", diagnostico.diagnostico);
        console.log("   Confianza:", diagnostico.confianza);
        console.log("   Productos:", diagnostico.productos?.length || 0);
        console.log("   Plantas:", diagnostico.plantas?.length || 0);
        console.log("   Remedios:", diagnostico.remedios?.length || 0);

        // Guardar globalmente
        this.diagnosticoActual = diagnostico;

        // Esperar animación
        await this.esperar(1500);

        // ⭐ MOSTRAR RECETA CON CHAT (NO CERRAR)
        await this.mostrarRecetaConChat();
      } else {
        throw new Error(result.error || "Error generando diagnóstico");
      }
    } catch (error) {
      console.error("❌ Error diagnóstico:", error);
      this.mostrarError("Error generando diagnóstico: " + error.message);
    }
  }

  /**
   * ⭐ NUEVO: Mostrar receta COMPLETA con todos los detalles
   */
  async mostrarRecetaConChat() {
    console.log("📋 Mostrando receta completa...");

    this.cambiarPantalla("chat");

    const diagnostico = this.diagnosticoActual;
    
    let mensajeReceta = `✅ DIAGNÓSTICO: ${diagnostico.diagnostico}\n`;
    mensajeReceta += `Confianza: ${Math.round(diagnostico.confianza * 100)}%\n\n`;
    
    if (diagnostico.causas && diagnostico.causas.length > 0) {
      mensajeReceta += "🔍 CAUSAS PROBABLES:\n";
      diagnostico.causas.forEach(causa => mensajeReceta += `• ${causa}\n`);
      mensajeReceta += "\n";
    }
    
    if (diagnostico.explicacion_causas) {
      mensajeReceta += `💡 POR QUÉ SURGE:\n${diagnostico.explicacion_causas}\n\n`;
    }
    
    if (diagnostico.productos && diagnostico.productos.length > 0) {
      mensajeReceta += "📦 PRODUCTOS NATURALES:\n";
      diagnostico.productos.forEach(p => {
        mensajeReceta += `• ${p.nombre} - S/.${p.precio}\n`;
        mensajeReceta += `  Dosis: ${p.dosis || 'Ver etiqueta'}\n`;
        mensajeReceta += `  Cuándo: ${p.cuando_tomar || 'Con alimentos'}\n`;
        mensajeReceta += `  Duración: ${p.duracion || '1 mes'}\n\n`;
      });
    }

    if (diagnostico.plantas && diagnostico.plantas.length > 0) {
      mensajeReceta += "🌿 PLANTAS MEDICINALES:\n";
      diagnostico.plantas.forEach(p => {
        mensajeReceta += `• ${p.nombre_comun}\n`;
        mensajeReceta += `  Forma: ${p.forma_uso || 'Infusión'}\n`;
        mensajeReceta += `  Dosis: ${p.dosis || '1-3 tazas'}\n\n`;
      });
    }

    if (diagnostico.remedios && diagnostico.remedios.length > 0) {
      mensajeReceta += "🍯 REMEDIOS CASEROS:\n";
      diagnostico.remedios.forEach(r => {
        mensajeReceta += `• ${r.nombre}\n`;
        if (r.ingredientes) mensajeReceta += `  Ingredientes: ${r.ingredientes}\n`;
        if (r.preparacion) mensajeReceta += `  Preparación: ${r.preparacion}\n`;
        if (r.como_usar) mensajeReceta += `  Uso: ${r.como_usar}\n`;
        mensajeReceta += "\n";
      });
    }
    
    if (diagnostico.consejos_dieta && diagnostico.consejos_dieta.length > 0) {
      mensajeReceta += "🥗 DIETA:\n";
      diagnostico.consejos_dieta.forEach(c => mensajeReceta += `• ${c}\n`);
      mensajeReceta += "\n";
    }
    
    if (diagnostico.consejos_habitos && diagnostico.consejos_habitos.length > 0) {
      mensajeReceta += "💪 HÁBITOS:\n";
      diagnostico.consejos_habitos.forEach(c => mensajeReceta += `• ${c}\n`);
      mensajeReceta += "\n";
    }
    
    if (diagnostico.tiempo_mejoria) {
      mensajeReceta += `⏱️ TIEMPO ESTIMADO:\n${diagnostico.tiempo_mejoria}\n\n`;
    }
    
    mensajeReceta += "💬 ¿Preguntas?";

    this.agregarMensajeKairos(mensajeReceta);

    if (voz && voz.vozActiva) {
      voz.hablar("Tu receta está lista. ¿Tienes alguna pregunta?");
    }

    const botonFinalizar = document.getElementById("boton-finalizar-container");
    if (botonFinalizar) botonFinalizar.style.display = "block";

    try {
      await api.imprimirReceta();
    } catch (error) {
      console.error("⚠️ Error:", error);
    }
  }

  /**
   * ⭐ NUEVO: Finalizar consulta (botón manual)
   */
  async finalizarConsulta() {
    console.log("👋 Finalizando consulta...");

    try {
      // Llamar API para finalizar
      const result = await api.finalizarSesion();

      if (result.success) {
        console.log("✅ Sesión finalizada");
        console.log("   Duración:", result.resumen?.duracion_minutos || 0, "min");
      }
    } catch (error) {
      console.error("❌ Error finalizando:", error);
    }

    // Ir a despedida
    this.mostrarDespedida();
  }

  /**
   * Agregar mensaje al chat
   */
  agregarMensajeUsuario(texto) {
    const container = document.getElementById("chat-mensajes");

    const div = document.createElement("div");
    div.className = "mensaje usuario";
    div.innerHTML = `<div class="mensaje-bubble">${this.escaparHTML(
      texto
    )}</div>`;

    container.appendChild(div);
    container.scrollTop = container.scrollHeight;
  }

  agregarMensajeKairos(texto) {
    const container = document.getElementById("chat-mensajes");

    const div = document.createElement("div");
    div.className = "mensaje kairos";
    div.innerHTML = `<div class="mensaje-bubble">${this.escaparHTML(
      texto
    )}</div>`;

    container.appendChild(div);
    container.scrollTop = container.scrollHeight;
  }

  /**
   * Escapar HTML para prevenir XSS
   */
  escaparHTML(texto) {
    const div = document.createElement("div");
    div.textContent = texto;
    return div.innerHTML;
  }

  /**
   * Animar barra de progreso
   */
  animarProgreso() {
    const barra = document.getElementById("print-progress");
    if (!barra) return;

    let progreso = 0;
    const intervalo = setInterval(() => {
      progreso += 5;
      barra.style.width = `${progreso}%`;

      if (progreso >= 100) {
        clearInterval(intervalo);
      }
    }, 150);
  }

  /**
   * Esperar (helper)
   */
  esperar(ms) {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }

  /**
   * Mostrar despedida
   */
  mostrarDespedida() {
    // Ir a despedida
    this.cambiarPantalla("despedida");

    // Nombre correcto del usuario
    if (this.datosUsuario && this.datosUsuario.nombre) {
      const primerNombre = this.datosUsuario.nombre.split(" ")[0];
      document.getElementById("nombre-despedida").textContent = primerNombre;
    } else {
      document.getElementById("nombre-despedida").textContent = "Paciente";
    }

    // Contador regresivo
    let segundos = 5;
    const contador = document.getElementById("contador");

    const intervalo = setInterval(() => {
      segundos--;
      if (contador) {
        contador.textContent = segundos;
      }

      if (segundos <= 0) {
        clearInterval(intervalo);
        this.resetear();
      }
    }, 1000);
  }

  /**
   * Resetear aplicación
   */
  resetear() {
    // Limpiar datos
    this.datosUsuario = null;
    this.mensajes = [];
    this.diagnosticoActual = null;

    // Limpiar formularios
    const inputs = ["nombre", "dni", "edad", "mensaje-input"];
    inputs.forEach((id) => {
      const el = document.getElementById(id);
      if (el) el.value = "";
    });

    // Limpiar chat
    const chatMensajes = document.getElementById("chat-mensajes");
    if (chatMensajes) {
      chatMensajes.innerHTML = "";
    }

    // Limpiar validación
    const validacion = document.getElementById("validacion");
    if (validacion) {
      validacion.innerHTML = "";
      validacion.className = "validation-message";
    }

    // Volver a inicio
    this.cambiarPantalla("espera");

    // Actualizar estadísticas
    this.actualizarEstadisticas();

    console.log("🔄 Sistema reseteado");
  }

  /**
   * Mostrar error
   */
  mostrarError(mensaje) {
    const errorElement = document.getElementById("mensaje-error");
    if (errorElement) {
      errorElement.textContent = mensaje;
    }
    this.cambiarPantalla("error");
  }

  /**
   * Resetear timer de inactividad
   */
  resetearInactividad() {
    let timeoutId;

    const reiniciarTimer = () => {
      clearTimeout(timeoutId);
      if (this.estado !== "espera") {
        timeoutId = setTimeout(() => {
          console.log("⏰ Tiempo de inactividad alcanzado");
          this.resetear();
        }, 300000); // 5 minutos
      }
    };

    // Detectar actividad
    ["mousedown", "keydown", "touchstart", "scroll"].forEach((event) => {
      document.addEventListener(event, reiniciarTimer);
    });

    reiniciarTimer();
  }
}

// ═══════════════════════════════════════════════════════════════
// FUNCIONES GLOBALES (llamadas desde HTML)
// ═══════════════════════════════════════════════════════════════

let app;

// Inicializar al cargar
window.addEventListener("DOMContentLoaded", () => {
  app = new KairosApp();
});

function iniciarConsulta() {
  if (app) app.iniciarConsulta();
}

function capturarDatos() {
  if (app) app.capturarDatos();
}

function enviarMensaje() {
  if (app) app.enviarMensaje();
}

function volverInicio() {
  if (app) app.resetear();
}

function confirmarTerminar() {
  if (confirm("¿Seguro que quieres terminar la consulta?")) {
    if (app) app.finalizarConsulta();
  }
}

// ⭐ NUEVO: Finalizar consulta manualmente
function finalizarConsulta() {
  if (app) app.finalizarConsulta();
}

// Voz
async function dictarNombre() {
  if (!voz) {
    console.error("Sistema de voz no disponible");
    return;
  }

  try {
    const texto = await voz.escuchar();
    const inputNombre = document.getElementById("nombre");
    if (inputNombre) {
      inputNombre.value = texto;
    }
  } catch (error) {
    console.error("Error dictado:", error);
  }
}

function toggleVoz() {
  if (voz) {
    const activa = voz.toggle();
    console.log(`🔊 Voz: ${activa ? "ON" : "OFF"}`);
  }
}

// Exportar para debugging
window.KairosApp = app;