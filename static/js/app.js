/* =====================================================
   Certificado Unilasallista — app.js (Premium UI)
   ===================================================== */

'use strict';

const estado = { eventoActual: '', eventos: [] };
let cacheHistorial = [];

/* ── Init ──────────────────────────────────────────── */
document.addEventListener('DOMContentLoaded', () => {
  consultarEstado();
  cargarTrazabilidad();
  cargarHistorialCompleto();
  document.getElementById('form-procesar')?.addEventListener('submit', procesarEvento);
  document.getElementById('btn-trazabilidad')?.addEventListener('click', cargarTrazabilidad);
});

/* ── Escape HTML ───────────────────────────────────── */
function esc(t) {
  return String(t === null || t === undefined ? '' : t)
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

/* ── Indicador de pasos ────────────────────────────── */
function setPaso(n) {
  for (let i = 1; i <= 3; i++) {
    document.getElementById(`paso-${i}`)?.classList.toggle('activo', i === n);
  }
}

/* ── Estado SMTP ───────────────────────────────────── */
async function consultarEstado() {
  const el = document.getElementById('estado-sistema');
  try {
    const r = await fetch('/api/estado');
    const d = await r.json();
    const smtp = d.smtp || {};
    const sim = smtp.simulacion;
    const ok = smtp.configurado;
    const cls = ok ? 'ok' : 'alerta';
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

/* ── PROCESAR FORMULARIO ───────────────────────────── */
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
    if (txtTiempo) txtTiempo.textContent = '⏱️ 0s';
    if (barra) barra.style.width = '15%';
    if (txtTitulo) txtTitulo.textContent = 'Llenando certificados PPTX…';
  }

  let seg = 0;
  const cronometro = setInterval(() => {
    seg++;
    if (txtTiempo) txtTiempo.textContent = `⏱️ ${seg}s`;
    if (barra) {
      if (seg <= 3) {
        barra.style.width = '30%';
        if (txtTitulo) txtTitulo.textContent = 'Generando presentaciones PowerPoint oficiales…';
      } else if (seg <= 12) {
        barra.style.width = '65%';
        if (txtTitulo) txtTitulo.textContent = 'PowerPoint está exportando los PDFs en alta calidad…';
        if (txtSub) txtSub.textContent = 'Renderizando diseño oficial INCIETEC para cada participante. Esto garantiza que el PDF sea 100% fiel al formato.';
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
          <h2>📋 Resultado</h2>
          <button type="button" class="btn-limpiar-flotante" onclick="iniciarNuevoCertificado()">
            ➕ Limpiar formulario
          </button>
        </div>
        <div class="mensaje error">
          ❌ ${esc(d?.error || 'No fue posible procesar el archivo. Revisa los datos ingresados.')}
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
        <h2>📋 Resultado</h2>
        <button type="button" class="btn-limpiar-flotante" onclick="iniciarNuevoCertificado()">
          ➕ Limpiar formulario
        </button>
      </div>
      <div class="mensaje error">⚠️ Error: ${esc(err.message)}</div>`;
    setPaso(1);
    panel.scrollIntoView({ behavior: 'smooth', block: 'start' });
  } finally {
    clearInterval(cronometro);
    if (boxProgreso) boxProgreso.style.display = 'none';
    boton.disabled = false;
    icono.textContent = '⚡';
    texto.textContent = 'Generar certificados';
  }
}

/* ── NUEVO CERTIFICADO / LIMPIAR FORMULARIO ────────── */
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
  mostrarToast('✨ Formulario restablecido. Puedes generar otro certificado.', 'ok');

  const inpEvento = document.getElementById('evento');
  if (inpEvento) {
    inpEvento.focus();
    inpEvento.scrollIntoView({ behavior: 'smooth', block: 'center' });
  }

  cargarHistorialCompleto();
}

/* ── MOSTRAR RESULTADO ─────────────────────────────── */
function mostrarResultado(datos) {
  const panel = document.getElementById('panel-resultado');
  panel.classList.remove('oculto');

  const det = datos.detalle || {};
  const roles = det.roles || {};
  const total = roles.total || 0;
  estado.eventoActual = det.evento || '';

  const btnZip = det.zip_url
    ? `<a href="${esc(det.zip_url)}" class="btn-zip">
         📦 Descargar todos los certificados (.ZIP)
       </a>`
    : '';

  const btnNuevo = `
    <button type="button" class="btn-limpiar-flotante" onclick="iniciarNuevoCertificado()">
      ➕ Enviar otro certificado (Limpiar)
    </button>
  `;

  panel.innerHTML = `
    <div class="resultado-header">
      <h2>🏅 Certificados generados</h2>
      <div style="display:flex; gap:10px; flex-wrap:wrap; align-items:center;">
        ${btnZip}
        ${btnNuevo}
      </div>
    </div>

    <div class="mensaje exito">
      ✅ Evento <strong>${esc(det.evento)}</strong> procesado con la plantilla <strong>Certificados.pptx</strong>.
      Se generaron <strong>${roles.ok || 0}</strong> certificado(s).
      Los datos quedaron guardados en la sección de <strong>Historial y Certificados Guardados</strong> abajo.
    </div>

    <div class="envio-hint">
      <div class="hint-icon">📨</div>
      <div>
        <strong>¿Cómo enviar un certificado?</strong> En la tabla de abajo, cada fila tiene un campo de correo
        (ya pre-relleno con el del participante). Puedes cambiarlo por <em>cualquier dirección</em>
        y presionar <strong>Enviar</strong> para mandar el PDF adjunto.
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
        <h3>✅ Certificados listos</h3>
        <div class="tabla-scroll"><table id="tabla-enviados"></table></div>
      </div>
      <div>
        <h3>⚠️ Fallidos / Omitidos</h3>
        <div class="tabla-scroll"><table id="tabla-fallidos"></table></div>
      </div>
    </div>

    <details>
      <summary>🔬 Detalle técnico (IA: duplicados, anomalías, mapeo de encabezados)</summary>
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

/* ── TABLA ENVIADOS (con botones de correo) ────────── */
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
                    ? `<a href="${esc(f.descarga)}" target="_blank" class="btn-descargar pdf">📄 PDF</a>`
                    : ''}
                  ${f.descarga_pptx
                    ? `<a href="${esc(f.descarga_pptx)}" target="_blank" class="btn-descargar pptx">📊 PPTX</a>`
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
                    ✉️ Enviar
                  </button>
                </div>
              </td>
            </tr>`;
          }).join('')
        : '<tr><td colspan="4" style="text-align:center;color:#94a3b8;padding:20px;">Sin certificados generados.</td></tr>'
    }</tbody>`;
}

/* ── ENVÍO INDIVIDUAL POR CORREO ───────────────────── */
async function enviarCorreo(archivo, nombre, rol, idInput, idBoton) {
  const input  = document.getElementById(idInput);
  const boton  = document.getElementById(idBoton);
  const correo = input?.value.trim() || '';

  if (!correo) {
    mostrarToast('⚠️ Escribe una dirección de correo válida.', 'error');
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
      boton.innerHTML = '✅ ¡Enviado!';
      boton.classList.add('enviado');
      mostrarToast(`✅ ${d.mensaje}`, 'ok');
      cargarTrazabilidad();
      cargarHistorialCompleto();
    } else {
      boton.innerHTML = '❌ Error';
      boton.classList.add('error-btn');
      const extra = d.error?.includes('SMTP')
        ? '\n\n💡 Para envíos reales, configura SMTP_PASS en el archivo .env'
        : '';
      mostrarToast(`⚠️ ${d.error}${extra}`, 'error');
      setTimeout(() => {
        boton.disabled = false;
        boton.innerHTML = textoOrig;
        boton.classList.remove('error-btn');
      }, 3500);
    }
  } catch (err) {
    boton.disabled = false;
    boton.innerHTML = textoOrig;
    mostrarToast(`❌ Error de red: ${err.message}`, 'error');
  }
}

/* ── TABLA FALLIDOS / OMITIDOS ─────────────────────── */
function pintarTablaFallidos(fallidos, omitidos) {
  const tabla = document.getElementById('tabla-fallidos');
  if (!tabla) return;
  const filas = [
    ...fallidos.map(f => ({ ...f, _estado: 'ERROR' })),
    ...omitidos.map(f => ({ ...f, _estado: 'OMITIDO', detalle: 'Ya enviado anteriormente' })),
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
        : '<tr><td colspan="5" style="text-align:center;color:#94a3b8;padding:20px;">Sin incidencias 🎉</td></tr>'
    }</tbody>`;
}

/* ── HISTORIAL Y CERTIFICADOS GUARDADOS ────────────── */
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
    contenedor.innerHTML = '<div class="cargando-historial">No hay eventos o certificados guardados que coincidan.</div>';
    return;
  }

  contenedor.innerHTML = lista.map((ev, idx) => {
    const totalParts = ev.total_guardados || (ev.participantes ? ev.participantes.length : 0);
    const fechaFmt = ev.fecha ? ev.fecha.replace('T', ' ').slice(0, 19) : 'Sin fecha';
    const dep = ev.dependencia ? `· ${esc(ev.dependencia)}` : '';
    const btnZip = ev.zip_url
      ? `<a href="${esc(ev.zip_url)}" class="btn-zip-mini">📦 Descargar todos (.ZIP)</a>`
      : '';

    return `
      <div class="evento-card" id="evento-card-${idx}">
        <div class="evento-card__top">
          <div class="evento-card__info">
            <div class="evento-card__titulo">
              🎓 ${esc(ev.nombre)}
            </div>
            <div class="evento-card__meta">
              <span>📅 ${esc(fechaFmt)}</span>
              <span>🏢 ${dep}</span>
              <span class="badge-contador">✅ ${ev.ok || totalParts} certificados generados</span>
            </div>
          </div>
          <div class="evento-card__acciones">
            ${btnZip}
            <button type="button" class="btn-toggle-part" onclick="toggleParticipantes(${idx})">
              👁️ Ver certificados (${totalParts})
            </button>
          </div>
        </div>

        <div class="evento-card__participantes" id="parts-card-${idx}" style="display:none;">
          <h4 style="font-size:13px; font-weight:700; margin-bottom:12px; color:#1e293b;">
            👥 Participantes y certificados guardados:
          </h4>
          <div class="lista-part-items">
            ${
              (ev.participantes || []).map((p, pIdx) => {
                const idInput = `hist-email-${idx}-${pIdx}`;
                const idBtn = `hist-btn-${idx}-${pIdx}`;
                const btnPdf = p.descarga_pdf
                  ? `<a href="${esc(p.descarga_pdf)}" target="_blank" class="btn-enlace-descarga">📄 Ver PDF</a>`
                  : '';
                const btnPptx = p.descarga_pptx
                  ? `<a href="${esc(p.descarga_pptx)}" target="_blank" class="btn-enlace-descarga btn-enlace-pptx">📊 PPTX</a>`
                  : '';

                return `
                  <div class="participante-fila-item">
                    <div class="participante-col-info">
                      <div class="participante-nombre">
                        <strong>${esc(p.nombre)}</strong>
                        <span class="badge" style="font-size:10.5px;">${esc(p.rol || 'Participante')}</span>
                      </div>
                      <div class="participante-correo-sub">
                        📧 Registrado: ${esc(p.correo)}
                      </div>
                    </div>
                    <div class="participante-acciones">
                      ${btnPdf}
                      ${btnPptx}
                      <div class="send-group" style="margin-left:6px;">
                        <input type="email" id="${idInput}" value="${esc(p.correo)}" placeholder="correo@..." style="width:165px; font-size:11.5px; padding:4px 8px;">
                        <button type="button" class="btn-enviar" id="${idBtn}" style="padding:5px 10px; font-size:11.5px;"
                                onclick="enviarCorreo('${esc(p.archivo_pdf || '')}', '${esc(p.nombre)}', '${esc(p.rol || 'Participante')}', '${idInput}', '${idBtn}')">
                          ✉️ Reenviar
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

/* ── TRAZABILIDAD ──────────────────────────────────── */
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

/* ── TOAST NOTIFICATIONS ───────────────────────────── */
function mostrarToast(msg, tipo = 'ok') {
  const viejo = document.getElementById('toast-notif');
  if (viejo) viejo.remove();

  const div = document.createElement('div');
  div.id = 'toast-notif';
  Object.assign(div.style, {
    position: 'fixed',
    bottom: '28px',
    right: '28px',
    background: tipo === 'ok' ? '#166534' : '#991b1b',
    color: '#fff',
    padding: '14px 22px',
    borderRadius: '12px',
    fontSize: '13.5px',
    fontWeight: '600',
    fontFamily: 'Inter, Segoe UI, sans-serif',
    maxWidth: '400px',
    lineHeight: '1.5',
    boxShadow: '0 8px 30px rgba(0,0,0,.25)',
    zIndex: '9999',
    opacity: '0',
    transform: 'translateY(20px)',
    transition: 'all .3s ease',
    whiteSpace: 'pre-wrap',
  });
  div.textContent = msg;
  document.body.appendChild(div);

  requestAnimationFrame(() => {
    div.style.opacity = '1';
    div.style.transform = 'translateY(0)';
  });

  setTimeout(() => {
    div.style.opacity = '0';
    div.style.transform = 'translateY(20px)';
    setTimeout(() => div.remove(), 350);
  }, 5500);
}
