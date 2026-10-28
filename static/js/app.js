/* ==========================================================================
   Certificado Unilasallista — app.js (Identidad Visual Corporativa 2026)
   - Paleta corporativa basada estrictamente en tonos azules y neutros pizarra.
   - Iconografía 100% vectorial SVG (estilo Heroicons / Lucide), sin emojis.
   - Configuración dinámica del correo remitente (Frontend <-> Backend API).
   - Alerta y advertencia de seguridad corporativa tras modificación del remitente.
   ========================================================================== */

'use strict';

/* ── CATÁLOGO DE ICONOS VECTORIALES SVG ──────────────────────────────────── */
const ICONS = {
  check: `<svg class="icon-svg icon-svg-inline" viewBox="0 0 24 24"><polyline points="20 6 9 17 4 12"/></svg>`,
  alert: `<svg class="icon-svg icon-svg-inline" viewBox="0 0 24 24"><path d="M12 9v4"/><path d="M12 17h.01"/><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/></svg>`,
  error: `<svg class="icon-svg icon-svg-inline" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>`,
  mail: `<svg class="icon-svg icon-svg-inline" viewBox="0 0 24 24"><rect width="20" height="16" x="2" y="4" rx="2"/><path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"/></svg>`,
  send: `<svg class="icon-svg icon-svg-inline" viewBox="0 0 24 24"><path d="m22 2-7 20-4-9-9-4Z"/><path d="M22 2 11 13"/></svg>`,
  download: `<svg class="icon-svg icon-svg-inline" viewBox="0 0 24 24"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" x2="12" y1="15" y2="3"/></svg>`,
  upload: `<svg class="icon-svg icon-svg-inline" viewBox="0 0 24 24"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" x2="12" y1="3" y2="15"/></svg>`,
  filePdf: `<svg class="icon-svg icon-svg-inline" viewBox="0 0 24 24"><path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z"/><polyline points="14 2 14 8 20 8"/></svg>`,
  filePptx: `<svg class="icon-svg icon-svg-inline" viewBox="0 0 24 24"><rect width="18" height="18" x="3" y="3" rx="2"/><path d="M8 8h5a2 2 0 0 1 2 2v0a2 2 0 0 1-2 2H8v6"/></svg>`,
  packageZip: `<svg class="icon-svg icon-svg-inline" viewBox="0 0 24 24"><path d="M21 8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16Z"/><polyline points="3.29 7 12 12 20.71 7"/><line x1="12" x2="12" y1="22" y2="12"/></svg>`,
  award: `<svg class="icon-svg icon-svg-inline" viewBox="0 0 24 24"><circle cx="12" cy="8" r="6"/><path d="M15.477 12.89 17 22l-5-3-5 3 1.523-9.11"/></svg>`,
  calendar: `<svg class="icon-svg icon-svg-inline" viewBox="0 0 24 24"><rect width="18" height="18" x="3" y="4" rx="2"/><line x1="16" x2="16" y1="2" y2="6"/><line x1="8" x2="8" y1="2" y2="6"/><line x1="3" x2="21" y1="10" y2="10"/></svg>`,
  building: `<svg class="icon-svg icon-svg-inline" viewBox="0 0 24 24"><rect width="16" height="20" x="4" y="2" rx="2"/><path d="M9 22v-4h6v4"/><line x1="8" y1="6" x2="8.01" y2="6"/><line x1="16" y1="6" x2="16.01" y2="6"/><line x1="8" y1="10" x2="8.01" y2="10"/><line x1="16" y1="10" x2="16.01" y2="10"/></svg>`,
  eye: `<svg class="icon-svg icon-svg-inline" viewBox="0 0 24 24"><path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7Z"/><circle cx="12" cy="12" r="3"/></svg>`,
  users: `<svg class="icon-svg icon-svg-inline" viewBox="0 0 24 24"><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>`,
  plus: `<svg class="icon-svg icon-svg-inline" viewBox="0 0 24 24"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>`,
  clock: `<svg class="icon-svg icon-svg-inline" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>`,
  zap: `<svg class="icon-svg icon-svg-inline" viewBox="0 0 24 24"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>`,
  shield: `<svg class="icon-svg icon-svg-inline" viewBox="0 0 24 24"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>`,
  settings: `<svg class="icon-svg icon-svg-inline" viewBox="0 0 24 24"><path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z"/><circle cx="12" cy="12" r="3"/></svg>`,
  refresh: `<svg class="icon-svg icon-svg-inline" viewBox="0 0 24 24"><path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"/><path d="M21 3v5h-5"/><path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"/><path d="M8 16H3v5"/></svg>`,
};

/* ── Estado Global ───────────────────────────────────────────────────────── */
const estado = { eventoActual: '', eventos: [], remitenteActual: '' };
let cacheHistorial = [];
let plantillasDisponibles = [];

/* ── Inicialización ──────────────────────────────────────────────────────── */
document.addEventListener('DOMContentLoaded', () => {
  consultarEstado();
  cargarConfiguracionCorreo();
  cargarListaPlantillas();
  cargarTrazabilidad();
  cargarHistorialCompleto();

  // Listeners de formularios
  document.getElementById('form-procesar')?.addEventListener('submit', procesarEvento);
  document.getElementById('btn-trazabilidad')?.addEventListener('click', cargarTrazabilidad);

  // Sincronización en tiempo real del evento con la previsualización del correo
  const inpEvento = document.getElementById('evento');
  if (inpEvento) {
    inpEvento.addEventListener('input', () => {
      const box = document.getElementById('caja-ajuste-correo');
      if (box && !box.classList.contains('oculto')) {
        const txt = document.getElementById('ajuste-evento-txt');
        if (txt) txt.textContent = inpEvento.value.trim() || '[Evento ingresado arriba]';
      }
    });
  }

  // Cerrar modal al presionar tecla ESC
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      const modal = document.getElementById('modal-config-correo');
      if (modal && !modal.classList.contains('oculto')) {
        cerrarModalConfigCorreo();
      }
    }
  });
});

/* ── Escape HTML seguro ──────────────────────────────────────────────────── */
function esc(t) {
  return String(t === null || t === undefined ? '' : t)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

/* ── Indicador de Pasos del Flujo ────────────────────────────────────────── */
function setPaso(n) {
  for (let i = 1; i <= 3; i++) {
    document.getElementById(`paso-${i}`)?.classList.toggle('activo', i === n);
  }
}

/* ── Estado del Sistema / SMTP ───────────────────────────────────────────── */
async function consultarEstado() {
  const el = document.getElementById('estado-sistema');
  try {
    const r = await fetch('/api/estado');
    const d = await r.json();
    const smtp = d.smtp || {};
    const sim = smtp.simulacion;
    const ok = smtp.configurado;
    const cls = ok ? 'ok' : 'alerta';
    const remitente = d.remitente_correo || smtp.from || '';
    estado.remitenteActual = remitente;

    let txt = ok
      ? `SMTP listo · ${smtp.host}:${smtp.puerto}`
      : sim
        ? 'Modo simulación activo'
        : 'SMTP sin configurar';

    el.innerHTML = `<span class="punto ${cls}"></span> ${txt}`;
  } catch {
    el.innerHTML = '<span class="punto alerta"></span> Servicio no disponible';
  }
}

/* ==========================================================================
   NUEVA FUNCIONALIDAD: CONFIGURACIÓN DINÁMICA DEL CORREO REMITENTE
   ========================================================================== */

/**
 * Consulta la configuración actual del correo remitente desde el backend
 */
async function cargarConfiguracionCorreo() {
  try {
    const r = await fetch('/api/configuracion-correo');
    const d = await r.json();
    if (d.ok) {
      estado.remitenteActual = d.smtp_from || '';
      const etiquetaActual = document.getElementById('cfg-remitente-actual');
      if (etiquetaActual) {
        const nom = (d.smtp_from_name && d.smtp_from_name !== 'undefined') ? `${d.smtp_from_name} ` : '';
        const correo = (d.smtp_from && d.smtp_from !== 'undefined') ? d.smtp_from : 'tmontoya60@unilasallista.edu.co';
        etiquetaActual.textContent = nom ? `${nom}<${correo}>` : correo;
      }
    }
  } catch (err) {
    console.warn('No se pudo precargar configuración de correo:', err);
  }
}

/**
 * Alterna la visibilidad de la contraseña en el campo del modal
 */
function toggleVisibilidadPassword() {
  const inp = document.getElementById('cfg-input-password');
  const btn = document.getElementById('btn-toggle-pass');
  if (!inp || !btn) return;

  const esPassword = inp.type === 'password';
  inp.type = esPassword ? 'text' : 'password';

  btn.innerHTML = esPassword
    ? `<svg class="icon-svg" viewBox="0 0 24 24"><path d="M9.88 9.88a3 3 0 1 0 4.24 4.24"/><path d="M10.73 5.08A10.43 10.43 0 0 1 12 5c7 0 10 7 10 7a13.16 13.16 0 0 1-1.67 2.68"/><path d="M6.61 6.61A13.526 13.526 0 0 0 2 12s3 7 10 7a9.74 9.74 0 0 0 5.39-1.61"/><line x1="2" y1="2" x2="22" y2="22"/></svg>`
    : `<svg class="icon-svg" viewBox="0 0 24 24"><path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7Z"/><circle cx="12" cy="12" r="3"/></svg>`;
}

/**
 * Abre el modal corporativo de configuración de envíos y precarga los datos
 */
async function abrirModalConfigCorreo() {
  const modal = document.getElementById('modal-config-correo');
  const alertaBox = document.getElementById('modal-alerta-seguridad');
  const inputCorreo = document.getElementById('cfg-input-correo');
  const inputNombre = document.getElementById('cfg-input-nombre');
  const inputPass = document.getElementById('cfg-input-password');
  const badgePass = document.getElementById('cfg-password-badge');
  const etiquetaActual = document.getElementById('cfg-remitente-actual');

  if (alertaBox) alertaBox.classList.add('oculto');
  if (inputPass) {
    inputPass.value = '';
    inputPass.type = 'password';
  }

  const btnTogglePass = document.getElementById('btn-toggle-pass');
  if (btnTogglePass) {
    btnTogglePass.innerHTML = `<svg class="icon-svg" viewBox="0 0 24 24"><path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7Z"/><circle cx="12" cy="12" r="3"/></svg>`;
  }

  try {
    const r = await fetch('/api/configuracion-correo');
    const d = await r.json();
    if (d.ok) {
      if (inputCorreo) inputCorreo.value = (d.smtp_from && d.smtp_from !== 'undefined') ? d.smtp_from : '';
      if (inputNombre) inputNombre.value = (d.smtp_from_name && d.smtp_from_name !== 'undefined') ? d.smtp_from_name : '';
      if (etiquetaActual) {
        const nom = (d.smtp_from_name && d.smtp_from_name !== 'undefined') ? `${d.smtp_from_name} ` : '';
        const correo = (d.smtp_from && d.smtp_from !== 'undefined') ? d.smtp_from : 'tmontoya60@unilasallista.edu.co';
        etiquetaActual.textContent = nom ? `${nom}<${correo}>` : correo;
      }
      if (badgePass) {
        if (d.tiene_password) {
          badgePass.textContent = 'Configurada';
          badgePass.className = 'badge-password-status configurada';
          if (inputPass) inputPass.placeholder = '•••••••••••• (dejar en blanco para conservar)';
        } else {
          badgePass.textContent = 'Sin contraseña';
          badgePass.className = 'badge-password-status pendiente';
          if (inputPass) inputPass.placeholder = 'Escribe la contraseña para envíos reales';
        }
      }
    }
  } catch (err) {
    console.error('Error al consultar configuración de correo:', err);
  }

  if (modal) {
    modal.classList.remove('oculto');
    setTimeout(() => inputCorreo?.focus(), 100);
  }
}

/**
 * Cierra el modal de configuración de envíos
 */
function cerrarModalConfigCorreo() {
  const modal = document.getElementById('modal-config-correo');
  if (modal) modal.classList.add('oculto');
}

/**
 * Procesa la actualización dinámica del remitente en el backend
 */
async function guardarConfigCorreo(e) {
  e.preventDefault();
  const inputCorreo = document.getElementById('cfg-input-correo');
  const inputNombre = document.getElementById('cfg-input-nombre');
  const inputPass = document.getElementById('cfg-input-password');
  const badgePass = document.getElementById('cfg-password-badge');
  const btnGuardar = document.getElementById('btn-guardar-cfg');
  const alertaBox = document.getElementById('modal-alerta-seguridad');
  const alertaMsg = document.getElementById('modal-alerta-texto') || document.getElementById('modal-alerta-mensaje');
  const etiquetaActual = document.getElementById('cfg-remitente-actual');

  const nuevoCorreo = inputCorreo?.value.trim() || '';
  const nuevoNombre = inputNombre?.value.trim() || '';
  const nuevaClave = inputPass?.value || '';

  if (!nuevoCorreo) {
    mostrarToast('Por favor ingresa una dirección de correo válida.', 'error');
    inputCorreo?.focus();
    return;
  }

  const btnHtmlOrig = btnGuardar.innerHTML;
  btnGuardar.disabled = true;
  btnGuardar.innerHTML = '<span class="spinner"></span> Guardando…';

  try {
    const r = await fetch('/api/configuracion-correo', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        correo: nuevoCorreo,
        nombre: nuevoNombre,
        password: nuevaClave,
      }),
    });
    const d = await r.json();

    if (!r.ok || !d.ok) {
      mostrarToast(d.error || 'Error al actualizar el correo remitente.', 'error');
      btnGuardar.disabled = false;
      btnGuardar.innerHTML = btnHtmlOrig;
      return;
    }

    // Actualizar estado local y elementos visibles
    estado.remitenteActual = d.smtp_from || nuevoCorreo;
    const nom = (d.smtp_from_name && d.smtp_from_name !== 'undefined') ? `${d.smtp_from_name} ` : '';
    const correo = (d.smtp_from && d.smtp_from !== 'undefined') ? d.smtp_from : nuevoCorreo;

    if (etiquetaActual) {
      etiquetaActual.textContent = nom ? `${nom}<${correo}>` : correo;
    }

    // Actualizar estado del badge de contraseña
    if (badgePass && d.tiene_password) {
      badgePass.textContent = 'Configurada';
      badgePass.className = 'badge-password-status configurada';
      if (inputPass) {
        inputPass.value = '';
        inputPass.placeholder = '•••••••••••• (dejar en blanco para conservar)';
      }
    }

    // Actualizar la vista previa del correo si está abierta
    const remitenteVp = document.getElementById('ajuste-remitente');
    if (remitenteVp) {
      remitenteVp.textContent = nom ? `${nom}<${correo}>` : correo;
    }

    // Alerta de seguridad requerida textualmente
    const textoAdvertencia = d.mensaje_advertencia ||
      'Advertencia: El correo de envío ha sido modificado exitosamente. Todos los envíos futuros se realizarán desde esta nueva dirección.';

    // Desplegar advertencia corporativa en el modal
    if (alertaBox) {
      if (alertaMsg) alertaMsg.textContent = textoAdvertencia;
      alertaBox.classList.remove('oculto');
    }

    // Disparar notificación Toast destacada de advertencia
    mostrarToast(textoAdvertencia, 'advertencia');

    // Refrescar estado general
    consultarEstado();
  } catch (err) {
    mostrarToast(`Error de red al actualizar remitente: ${err.message}`, 'error');
  } finally {
    btnGuardar.disabled = false;
    btnGuardar.innerHTML = btnHtmlOrig;
  }
}

/* ==========================================================================
   GESTIÓN DE PLANTILLAS Y AJUSTE AL CORREO
   ========================================================================== */

async function cargarListaPlantillas() {
  try {
    const r = await fetch('/api/plantillas');
    const d = await r.json();
    if (!d.ok) return;
    plantillasDisponibles = d.plantillas || [];
    renderizarSelectPlantillas();
  } catch (err) {
    console.error('Error cargando plantillas:', err);
  }
}

function renderizarSelectPlantillas(seleccionada = null) {
  const select = document.getElementById('select-plantillas');
  if (!select) return;

  const actual = seleccionada || document.getElementById('plantilla')?.value || 'Certificados.pptx';

  select.innerHTML = plantillasDisponibles.map(p => {
    const val = p.ruta || p.archivo || p.nombre;
    const isSel = val === actual || p.archivo === actual || p.nombre === actual;
    return `<option value="${esc(val)}" ${isSel ? 'selected' : ''}>${esc(p.titulo || p.nombre)}</option>`;
  }).join('');

  actualizarBadgePlantilla(actual);
}

function actualizarBadgePlantilla(rutaOValor) {
  const hiddenInput = document.getElementById('plantilla');
  if (hiddenInput) hiddenInput.value = rutaOValor;

  const obj = plantillasDisponibles.find(p =>
    p.ruta === rutaOValor || p.archivo === rutaOValor || p.nombre === rutaOValor
  ) || {
    nombre: rutaOValor.split('/').pop().split('\\').pop(),
    tipo: rutaOValor.toLowerCase().endsWith('.pdf') ? 'pdf' : 'pptx',
    descripcion: 'Plantilla de certificado configurada.',
  };

  const nombreEl = document.getElementById('plantilla-nombre-activa');
  const tagEl = document.getElementById('plantilla-tipo-tag');
  const descEl = document.getElementById('plantilla-desc-activa');
  const iconoEl = document.getElementById('plantilla-icono');
  const fuenteAjuste = document.getElementById('ajuste-plantilla-fuente');

  const esPdf = (obj.tipo || '').toLowerCase() === 'pdf' || rutaOValor.toLowerCase().endsWith('.pdf');
  const nombreLimpio = obj.archivo || obj.nombre || rutaOValor.split('/').pop().split('\\').pop();

  if (nombreEl) nombreEl.textContent = nombreLimpio;
  if (fuenteAjuste) fuenteAjuste.textContent = nombreLimpio;
  if (tagEl) {
    tagEl.textContent = esPdf ? 'Documento PDF (.pdf)' : 'PowerPoint (.pptx)';
  }
  if (iconoEl) {
    iconoEl.innerHTML = esPdf ? ICONS.filePdf : ICONS.award;
  }
  if (descEl) {
    descEl.textContent = obj.descripcion || (esPdf
      ? 'Plantilla PDF base: el sistema aplica el fondo y ajusta nombre, rol y evento.'
      : 'Plantilla PowerPoint oficial: reemplaza dinámicamente nombre, modalidad, rol y evento.');
  }

  const btnGuia = document.getElementById('btn-descargar-guia');
  if (btnGuia) {
    const ext = esPdf ? 'pdf' : 'pptx';
    btnGuia.href = `/descargar-plantilla-guia?archivo=${encodeURIComponent(rutaOValor)}`;
    const spanTxt = btnGuia.querySelector('span:last-child');
    if (spanTxt) spanTxt.textContent = `Descargar plantilla guía (.${ext})`;
  }

  const cajaAjuste = document.getElementById('caja-ajuste-correo');
  if (cajaAjuste && !cajaAjuste.classList.contains('oculto')) {
    actualizarVistaPreviaCorreo();
  }
}

function seleccionarPlantillaExistente(valor) {
  actualizarBadgePlantilla(valor);
  const nombreLimpio = valor.split('/').pop().split('\\').pop();
  mostrarToast(`Plantilla seleccionada: ${nombreLimpio}`, 'ok');
}

async function subirNuevaPlantilla(e) {
  const file = e.target.files?.[0];
  if (!file) return;

  const ext = file.name.split('.').pop().toLowerCase();
  if (ext !== 'pptx' && ext !== 'pdf') {
    mostrarToast('Debe ser un archivo de PowerPoint (.pptx) o PDF (.pdf)', 'error');
    e.target.value = '';
    return;
  }

  const formData = new FormData();
  formData.append('plantilla_archivo', file);

  mostrarToast(`Subiendo y configurando plantilla «${file.name}»…`, 'ok');

  try {
    const r = await fetch('/api/cargar-plantilla', {
      method: 'POST',
      body: formData,
    });
    const d = await r.json();

    if (!r.ok || !d.ok) {
      mostrarToast(`Error al cargar plantilla: ${d.error || 'Archivo no válido'}`, 'error');
      return;
    }

    mostrarToast(d.mensaje || 'Plantilla cargada correctamente.', 'ok');

    await cargarListaPlantillas();
    const nuevaRuta = d.plantilla?.ruta || d.plantilla?.archivo || d.plantilla?.nombre;
    const select = document.getElementById('select-plantillas');
    if (select && nuevaRuta) {
      select.value = nuevaRuta;
    }
    actualizarBadgePlantilla(nuevaRuta);
  } catch (err) {
    mostrarToast(`Error de red al subir plantilla: ${err.message}`, 'error');
  } finally {
    e.target.value = '';
  }
}

function toggleVistaPreviaCorreo() {
  const box = document.getElementById('caja-ajuste-correo');
  if (!box) return;
  const oculta = box.classList.toggle('oculto');
  if (!oculta) {
    actualizarVistaPreviaCorreo();
    box.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  }
}

async function actualizarVistaPreviaCorreo() {
  const eventoVal = document.getElementById('evento')?.value.trim() || 'Congreso de Inteligencia Artificial 2026';
  const plantillaVal = document.getElementById('plantilla')?.value || 'Certificados.pptx';

  const eventoTxt = document.getElementById('ajuste-evento-txt');
  if (eventoTxt) eventoTxt.textContent = eventoVal;

  try {
    const r = await fetch('/api/vista-previa-correo', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        evento: eventoVal,
        plantilla: plantillaVal,
        nombre: 'Juan Pérez González',
        rol: 'Ponente',
        destinatario: 'participante@unilasallista.edu.co',
      }),
    });
    const d = await r.json();
    if (!d.ok) return;

    const vp = d.vista_previa || {};
    const remitenteEl = document.getElementById('ajuste-remitente');
    const destinatarioEl = document.getElementById('ajuste-destinatario');
    const asuntoEl = document.getElementById('ajuste-asunto');
    const adjuntoEl = document.getElementById('ajuste-adjunto');
    const emailHtmlEl = document.getElementById('ajuste-email-html');
    const fuenteEl = document.getElementById('ajuste-plantilla-fuente');

    if (remitenteEl) remitenteEl.textContent = vp.remitente || '';
    if (destinatarioEl) destinatarioEl.textContent = vp.destinatario || '';
    if (asuntoEl) asuntoEl.innerHTML = `Certificado de participación — <strong>${esc(eventoVal)}</strong>`;
    if (adjuntoEl) adjuntoEl.innerHTML = `${ICONS.filePdf} ${esc(vp.archivo_adjunto || 'Certificado.pdf')}`;
    if (fuenteEl) fuenteEl.textContent = vp.plantilla_origen || plantillaVal.split('/').pop().split('\\').pop();
    if (emailHtmlEl && vp.cuerpo_html) {
      emailHtmlEl.innerHTML = vp.cuerpo_html;
    }
  } catch (err) {
    console.warn('No se pudo cargar vista previa de correo:', err);
  }
}

/* ==========================================================================
   PROCESAMIENTO DE EVENTO Y GENERACIÓN DE CERTIFICADOS
   ========================================================================== */

async function procesarEvento(e) {
  e.preventDefault();
  const boton = document.getElementById('btn-procesar');
  const icono = document.getElementById('btn-icono');
  const texto = document.getElementById('btn-texto');
  const panel = document.getElementById('panel-resultado');
  const boxProgreso = document.getElementById('progreso-generacion');
  const txtTiempo = document.getElementById('progreso-tiempo');
  const txtTitulo = document.getElementById('progreso-titulo');
  const txtSub = document.getElementById('progreso-subtitulo');
  const barra = document.getElementById('progreso-barra');
  const formulario = new FormData(e.target);

  boton.disabled = true;
  icono.innerHTML = '<span class="spinner"></span>';
  texto.textContent = 'Procesando certificados…';
  setPaso(2);

  if (boxProgreso) {
    boxProgreso.style.display = 'block';
    if (txtTiempo) txtTiempo.innerHTML = `${ICONS.clock} 0s`;
    if (barra) barra.style.width = '15%';
    if (txtTitulo) txtTitulo.textContent = 'Llenando certificados PPTX…';
  }

  let seg = 0;
  const cronometro = setInterval(() => {
    seg++;
    if (txtTiempo) txtTiempo.innerHTML = `${ICONS.clock} ${seg}s`;
    if (barra) {
      if (seg <= 3) {
        barra.style.width = '30%';
        if (txtTitulo) txtTitulo.textContent = 'Generando presentaciones PowerPoint oficiales…';
      } else if (seg <= 12) {
        barra.style.width = '65%';
        if (txtTitulo) txtTitulo.textContent = 'PowerPoint está exportando los PDFs en alta calidad…';
        if (txtSub) txtSub.textContent = 'Renderizando diseño oficial para cada participante. Esto garantiza que el PDF sea 100% fiel al formato.';
      } else {
        barra.style.width = '88%';
        if (txtTitulo) txtTitulo.textContent = 'Casi listo: empaquetando archivos ZIP y registrando…';
      }
    }
  }, 1000);

  try {
    const r = await fetch('/procesar', { method: 'POST', body: formulario });
    let d;
    try {
      d = await r.json();
    } catch {
      const txt = await r.text();
      throw new Error(txt.slice(0, 150) || `Error del servidor (${r.status})`);
    }

    if (!r.ok || !d.ok) {
      panel.classList.remove('oculto');
      panel.innerHTML = `
        <div class="resultado-header">
          <h2>${ICONS.award} Resultado</h2>
          <button type="button" class="btn-limpiar-flotante" onclick="iniciarNuevoCertificado()">
            ${ICONS.plus} Limpiar formulario
          </button>
        </div>
        <div class="mensaje error">
          ${ICONS.error} ${esc(d?.error || 'No fue posible procesar el archivo. Revisa los datos ingresados.')}
        </div>`;
      setPaso(1);
      panel.scrollIntoView({ behavior: 'smooth', block: 'start' });
      return;
    }

    mostrarResultado(d);
    setPaso(3);
    cargarTrazabilidad();
    cargarHistorialCompleto();
  } catch (err) {
    panel.classList.remove('oculto');
    panel.innerHTML = `
      <div class="resultado-header">
        <h2>${ICONS.award} Resultado</h2>
        <button type="button" class="btn-limpiar-flotante" onclick="iniciarNuevoCertificado()">
          ${ICONS.plus} Limpiar formulario
        </button>
      </div>
      <div class="mensaje error">${ICONS.alert} Error: ${esc(err.message)}</div>`;
    setPaso(1);
    panel.scrollIntoView({ behavior: 'smooth', block: 'start' });
  } finally {
    clearInterval(cronometro);
    if (boxProgreso) boxProgreso.style.display = 'none';
    boton.disabled = false;
    icono.innerHTML = ICONS.zap;
    texto.textContent = 'Generar certificados';
  }
}

/* ── Restablecer Formulario / Nuevo Proceso ───────────────────────────────── */
function iniciarNuevoCertificado() {
  const form = document.getElementById('form-procesar');
  if (form) form.reset();

  const boxProgreso = document.getElementById('progreso-generacion');
  if (boxProgreso) boxProgreso.style.display = 'none';

  const panel = document.getElementById('panel-resultado');
  if (panel) {
    panel.classList.add('oculto');
    panel.innerHTML = '';
  }

  setPaso(1);
  mostrarToast('Formulario restablecido. Puedes generar otro certificado.', 'ok');

  const inpEvento = document.getElementById('evento');
  if (inpEvento) {
    inpEvento.focus();
    inpEvento.scrollIntoView({ behavior: 'smooth', block: 'center' });
  }

  cargarHistorialCompleto();
}

/* ── Visualización de Resultados ─────────────────────────────────────────── */
function mostrarResultado(datos) {
  const panel = document.getElementById('panel-resultado');
  panel.classList.remove('oculto');

  const det = datos.detalle || {};
  const roles = det.roles || {};
  const total = roles.total || 0;
  estado.eventoActual = det.evento || '';

  const btnZip = det.zip_url
    ? `<a href="${esc(det.zip_url)}" class="btn-zip">
         ${ICONS.packageZip} Descargar todos los certificados (.ZIP)
       </a>`
    : '';

  const btnNuevo = `
    <button type="button" class="btn-limpiar-flotante" onclick="iniciarNuevoCertificado()">
      ${ICONS.plus} Enviar otro certificado (Limpiar)
    </button>
  `;

  panel.innerHTML = `
    <div class="resultado-header">
      <h2>${ICONS.award} Certificados generados</h2>
      <div style="display:flex; gap:10px; flex-wrap:wrap; align-items:center;">
        ${btnZip}
        ${btnNuevo}
      </div>
    </div>

    <div class="mensaje exito">
      ${ICONS.check} Evento <strong>${esc(det.evento)}</strong> procesado con la plantilla <strong>${esc(det.plantilla_utilizada || 'Certificados.pptx')}</strong>.
      Se generaron <strong>${roles.ok || 0}</strong> certificado(s).
      Los datos quedaron guardados en la sección de <strong>Historial y Certificados Guardados</strong> abajo.
    </div>

    <div class="envio-hint">
      <div class="hint-icon">${ICONS.mail}</div>
      <div>
        <strong>¿Cómo enviar un certificado?</strong> En la tabla de abajo, cada fila cuenta con un campo de correo
        (ya diligenciado con el del participante). Puedes modificarlo por <em>cualquier dirección</em>
        y presionar <strong>Enviar</strong> para despachar el PDF adjunto.
      </div>
    </div>

    <div class="tarjetas">
      <div class="tarjeta">
        <div class="valor">${total}</div>
        <div class="etiqueta">Procesados</div>
      </div>
      <div class="tarjeta">
        <div class="valor">${roles.ok || 0}</div>
        <div class="etiqueta">Certificados listos</div>
      </div>
      <div class="tarjeta error">
        <div class="valor">${roles.error || 0}</div>
        <div class="etiqueta">Fallidos</div>
      </div>
      <div class="tarjeta omitido">
        <div class="valor">${roles.omitido || 0}</div>
        <div class="etiqueta">Omitidos</div>
      </div>
    </div>

    <div class="dos-columnas">
      <div>
        <h3>${ICONS.check} Certificados listos</h3>
        <div class="tabla-scroll"><table id="tabla-enviados"></table></div>
      </div>
      <div>
        <h3>${ICONS.alert} Fallidos / Omitidos</h3>
        <div class="tabla-scroll"><table id="tabla-fallidos"></table></div>
      </div>
    </div>

    <details>
      <summary>${ICONS.eye} Detalle técnico (IA: duplicados, anomalías, mapeo de encabezados)</summary>
      <pre id="detalle-tecnico"></pre>
    </details>
  `;

  pintarTablaEnviados(det.enviados || []);
  pintarTablaFallidos(det.fallidos || [], det.omitidos || []);
  document.getElementById('detalle-tecnico').textContent = JSON.stringify(
    { resumen_carga: det.resumen_carga, mapeo_encabezados: det.mapeo_encabezados,
      duplicados: det.duplicados, anomalias: det.anomalias }, null, 2
  );

  panel.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

/* ── Tabla de Certificados Listos con Acciones de Correo ──────────────────── */
function pintarTablaEnviados(lista) {
  const tabla = document.getElementById('tabla-enviados');
  if (!tabla) return;

  tabla.innerHTML = `
    <thead>
      <tr>
        <th>Rol</th>
        <th>Nombre</th>
        <th>Descargar</th>
        <th style="min-width:240px">Enviar por correo</th>
      </tr>
    </thead>
    <tbody>${
      lista.length
        ? lista.map((f, i) => {
            const rolCls = (f.rol || '').toLowerCase().replace(/\s+/g, '_');
            return `<tr>
              <td><span class="badge ${esc(rolCls)}">${esc(f.rol)}</span></td>
              <td><strong>${esc(f.nombre)}</strong></td>
              <td>
                <div style="display:flex;gap:5px;flex-wrap:wrap;">
                  ${f.descarga
                    ? `<a href="${esc(f.descarga)}" target="_blank" class="btn-descargar pdf">${ICONS.filePdf} PDF</a>`
                    : ''}
                  ${f.descarga_pptx
                    ? `<a href="${esc(f.descarga_pptx)}" target="_blank" class="btn-descargar pptx">${ICONS.filePptx} PPTX</a>`
                    : ''}
                </div>
              </td>
              <td>
                <div class="send-group">
                  <input type="email" id="email-${i}"
                         value="${esc(f.correo)}"
                         placeholder="correo@dominio.com">
                  <button type="button" class="btn-enviar"
                          id="btn-send-${i}"
                          onclick="enviarCorreo('${esc(f.archivo)}','${esc(f.nombre)}','${esc(f.rol)}','email-${i}','btn-send-${i}')">
                    ${ICONS.send} Enviar
                  </button>
                </div>
              </td>
            </tr>`;
          }).join('')
        : '<tr><td colspan="4" style="text-align:center;color:#94a3b8;padding:20px;">Sin certificados generados.</td></tr>'
    }</tbody>`;
}

/* ── Envío Individual por Correo ─────────────────────────────────────────── */
async function enviarCorreo(archivo, nombre, rol, idInput, idBoton) {
  const input  = document.getElementById(idInput);
  const boton  = document.getElementById(idBoton);
  const correo = input?.value.trim() || '';

  if (!correo) {
    mostrarToast('Escribe una dirección de correo válida.', 'error');
    input?.focus();
    return;
  }

  const textoOrig = boton.innerHTML;
  boton.disabled = true;
  boton.innerHTML = '<span class="spinner"></span> Enviando…';

  try {
    const r = await fetch('/api/enviar-individual', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        archivo,
        nombre,
        rol,
        destinatario: correo,
        evento: estado.eventoActual || 'Evento',
      }),
    });
    const d = await r.json();

    if (d.ok) {
      boton.innerHTML = `${ICONS.check} ¡Enviado!`;
      boton.classList.add('enviado');
      mostrarToast(d.mensaje || 'Certificado despachado con éxito.', 'ok');
      cargarTrazabilidad();
      cargarHistorialCompleto();
    } else {
      boton.innerHTML = `${ICONS.error} Error`;
      boton.classList.add('error-btn');
      const extra = d.error?.includes('SMTP')
        ? '\n\n💡 Configura las credenciales SMTP en Configuración de envíos o en el archivo .env'
        : '';
      mostrarToast(`${d.error}${extra}`, 'error');
      setTimeout(() => {
        boton.disabled = false;
        boton.innerHTML = textoOrig;
        boton.classList.remove('error-btn');
      }, 3500);
    }
  } catch (err) {
    boton.disabled = false;
    boton.innerHTML = textoOrig;
    mostrarToast(`Error de red: ${err.message}`, 'error');
  }
}

/* ── Tabla de Fallidos / Omitidos ────────────────────────────────────────── */
function pintarTablaFallidos(fallidos, omitidos) {
  const tabla = document.getElementById('tabla-fallidos');
  if (!tabla) return;
  const filas = [
    ...fallidos.map(f => ({ ...f, _estado: 'ERROR' })),
    ...omitidos.map(f => ({ ...f, _estado: 'OMITIDO', detalle: 'Ya registrado anteriormente' })),
  ];
  tabla.innerHTML = `
    <thead>
      <tr><th>Estado</th><th>Rol</th><th>Nombre</th><th>Correo</th><th>Motivo</th></tr>
    </thead>
    <tbody>${
      filas.length
        ? filas.map(f => `<tr>
            <td><span class="estado-badge ${esc(f._estado)}">${esc(f._estado)}</span></td>
            <td>${esc(f.rol)}</td>
            <td>${esc(f.nombre)}</td>
            <td style="font-size:11.5px">${esc(f.correo)}</td>
            <td style="font-size:12px;color:#64748b">${esc(f.detalle)}</td>
          </tr>`).join('')
        : '<tr><td colspan="5" style="text-align:center;color:#94a3b8;padding:20px;">Sin incidencias reportadas.</td></tr>'
    }</tbody>`;
}

/* ==========================================================================
   HISTORIAL Y CERTIFICADOS GUARDADOS
   ========================================================================== */

async function cargarHistorialCompleto() {
  const contenedor = document.getElementById('contenedor-historial');
  if (!contenedor) return;

  try {
    const r = await fetch('/api/historial');
    const d = await r.json();
    cacheHistorial = d.historial || [];
    renderizarHistorial(cacheHistorial);
  } catch {
    contenedor.innerHTML = '<div class="cargando-historial" style="color:#ef4444">No fue posible cargar el historial guardado.</div>';
  }
}

function filtrarHistorial() {
  const query = (document.getElementById('filtro-historial')?.value || '').toLowerCase().trim();
  if (!query) {
    renderizarHistorial(cacheHistorial);
    return;
  }
  const filtrados = cacheHistorial.filter(ev => {
    const coincideEvento = (ev.nombre || '').toLowerCase().includes(query) || (ev.dependencia || '').toLowerCase().includes(query);
    const coincidePart = (ev.participantes || []).some(p =>
      (p.nombre || '').toLowerCase().includes(query) || (p.correo || '').toLowerCase().includes(query)
    );
    return coincideEvento || coincidePart;
  });
  renderizarHistorial(filtrados);
}

function renderizarHistorial(lista) {
  const contenedor = document.getElementById('contenedor-historial');
  if (!contenedor) return;

  if (!lista.length) {
    contenedor.innerHTML = '<div class="cargando-historial">No hay eventos o certificados guardados que coincidan con la búsqueda.</div>';
    return;
  }

  contenedor.innerHTML = lista.map((ev, idx) => {
    const totalParts = ev.total_guardados || (ev.participantes ? ev.participantes.length : 0);
    const fechaFmt = ev.fecha ? ev.fecha.replace('T', ' ').slice(0, 19) : 'Sin fecha';
    const dep = ev.dependencia ? `· ${esc(ev.dependencia)}` : '';
    const btnZip = ev.zip_url
      ? `<a href="${esc(ev.zip_url)}" class="btn-zip-mini">${ICONS.packageZip} Descargar todos (.ZIP)</a>`
      : '';

    return `
      <div class="evento-card" id="evento-card-${idx}">
        <div class="evento-card__top">
          <div class="evento-card__info">
            <div class="evento-card__titulo">
              ${ICONS.award} ${esc(ev.nombre)}
            </div>
            <div class="evento-card__meta">
              <span>${ICONS.calendar} ${esc(fechaFmt)}</span>
              <span>${ICONS.building} ${dep}</span>
              <span class="badge-contador">${ICONS.check} ${ev.ok || totalParts} certificados generados</span>
            </div>
          </div>
          <div class="evento-card__acciones">
            ${btnZip}
            <button type="button" class="btn-toggle-part" onclick="toggleParticipantes(${idx})">
              ${ICONS.eye} Ver certificados (${totalParts})
            </button>
          </div>
        </div>

        <div class="evento-card__participantes" id="parts-card-${idx}" style="display:none;">
          <h4 style="font-size:13px; font-weight:700; margin-bottom:12px; color:#0f172a; display:flex; align-items:center; gap:6px;">
            ${ICONS.users} Participantes y certificados guardados:
          </h4>
          <div class="lista-part-items">
            ${
              (ev.participantes || []).map((p, pIdx) => {
                const idInput = `hist-email-${idx}-${pIdx}`;
                const idBtn = `hist-btn-${idx}-${pIdx}`;
                const btnPdf = p.descarga_pdf
                  ? `<a href="${esc(p.descarga_pdf)}" target="_blank" class="btn-enlace-descarga">${ICONS.filePdf} Ver PDF</a>`
                  : '';
                const btnPptx = p.descarga_pptx
                  ? `<a href="${esc(p.descarga_pptx)}" target="_blank" class="btn-enlace-descarga btn-enlace-pptx">${ICONS.filePptx} PPTX</a>`
                  : '';

                return `
                  <div class="participante-fila-item">
                    <div class="participante-col-info">
                      <div class="participante-nombre">
                        <strong>${esc(p.nombre)}</strong>
                        <span class="badge" style="font-size:10.5px;">${esc(p.rol || 'Participante')}</span>
                      </div>
                      <div class="participante-correo-sub">
                        ${ICONS.mail} Registrado: ${esc(p.correo)}
                      </div>
                    </div>
                    <div class="participante-acciones">
                      ${btnPdf}
                      ${btnPptx}
                      <div class="send-group" style="margin-left:6px;">
                        <input type="email" id="${idInput}" value="${esc(p.correo)}" placeholder="correo@..." style="width:165px; font-size:11.5px; padding:4px 8px;">
                        <button type="button" class="btn-enviar" id="${idBtn}" style="padding:5px 10px; font-size:11.5px;"
                                onclick="enviarCorreo('${esc(p.archivo_pdf || '')}', '${esc(p.nombre)}', '${esc(p.rol || 'Participante')}', '${idInput}', '${idBtn}')">
                          ${ICONS.send} Reenviar
                        </button>
                      </div>
                    </div>
                  </div>
                `;
              }).join('')
            }
          </div>
        </div>
      </div>
    `;
  }).join('');
}

function toggleParticipantes(idx) {
  const el = document.getElementById(`parts-card-${idx}`);
  if (!el) return;
  const isHidden = el.style.display === 'none';
  el.style.display = isHidden ? 'block' : 'none';
}

/* ==========================================================================
   TRAZABILIDAD DE ENVÍOS
   ========================================================================== */

async function cargarTrazabilidad() {
  const tabla  = document.getElementById('tabla-trazabilidad');
  const filtro = document.getElementById('filtro-evento')?.value.trim() || '';
  const url    = filtro
    ? `/api/envios?evento=${encodeURIComponent(filtro)}&limite=100`
    : '/api/envios?limite=100';

  tabla.innerHTML = '<tbody><tr><td style="text-align:center;padding:16px;color:#94a3b8">Cargando…</td></tr></tbody>';

  try {
    const r = await fetch(url);
    const d = await r.json();
    const envios = d.envios || [];

    tabla.innerHTML = `
      <thead>
        <tr>
          <th>Fecha</th><th>Evento</th><th>Rol</th>
          <th>Nombre</th><th>Correo</th><th>Estado</th>
        </tr>
      </thead>
      <tbody>${
        envios.length
          ? envios.map(f => `<tr>
              <td style="font-size:11.5px;white-space:nowrap">${esc(f.fecha)}</td>
              <td style="max-width:160px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${esc(f.evento)}</td>
              <td>${esc(f.rol)}</td>
              <td><strong>${esc(f.nombre)}</strong></td>
              <td style="font-size:11.5px">${esc(f.correo)}</td>
              <td><span class="estado-badge ${esc(f.estado)}">${esc(f.estado)}</span></td>
            </tr>`).join('')
          : '<tr><td colspan="6" style="text-align:center;padding:20px;color:#94a3b8">Sin registros de trazabilidad aún.</td></tr>'
      }</tbody>`;
  } catch {
    tabla.innerHTML = '<tbody><tr><td style="color:#ef4444;padding:12px">No fue posible consultar la trazabilidad.</td></tr></tbody>';
  }
}

/* ==========================================================================
   NOTIFICACIONES TOAST CORPORATIVAS
   ========================================================================== */

function mostrarToast(msg, tipo = 'ok') {
  const viejo = document.getElementById('toast-notif');
  if (viejo) viejo.remove();

  const div = document.createElement('div');
  div.id = 'toast-notif';

  let iconSvg = ICONS.check;
  if (tipo === 'advertencia') {
    div.className = 'toast-advertencia';
    iconSvg = ICONS.shield;
  } else if (tipo === 'error') {
    div.className = 'toast-error';
    iconSvg = ICONS.alert;
  }

  div.innerHTML = `
    <span style="flex-shrink:0; margin-top:2px;">${iconSvg}</span>
    <span style="flex:1;">${esc(msg)}</span>
  `;

  document.body.appendChild(div);

  requestAnimationFrame(() => {
    div.style.opacity = '1';
    div.style.transform = 'translateY(0)';
  });

  // Permanencia más prolongada para advertencias importantes
  const duracion = tipo === 'advertencia' ? 7000 : 4500;

  setTimeout(() => {
    div.style.opacity = '0';
    div.style.transform = 'translateY(20px)';
    setTimeout(() => div.remove(), 350);
  }, duracion);
}
