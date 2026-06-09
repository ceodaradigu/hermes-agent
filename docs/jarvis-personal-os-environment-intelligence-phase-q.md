# JARVIS Phase Q - Personal OS / Environment Intelligence

Phase Q crea una base **prepare-only** para coordinar contexto autorizado, atención,
entorno y rutinas. La implementación transforma únicamente datos incluidos en cada
request en previews revisables. No conecta fuentes, no ejecuta acciones y no persiste
estado.

## Qué permite

- Consultar el estado seguro y la política de privacidad.
- Preparar consentimiento por fuente y alcance.
- Preparar daily state usando exclusivamente datos proporcionados.
- Describir señales de PC/entorno proporcionadas sin monitorización.
- Previsualizar awareness de calendario, email, documentos y archivos locales.
- Previsualizar cambios de contexto manteniendo separación personal/profesional.
- Preparar protección de atención, rutinas y apoyo de energía/foco.
- Preparar modo invitado, razones visibles y requisitos de approval.
- Mostrar readiness prepare-only en Command Center y Operator Console.

## Qué NO permite

- Leer calendario, email o documentos reales.
- Escanear archivos, procesos, pantalla o estado real del PC.
- Activar cámara, micrófono, sensores, tracking o vigilancia.
- Hacer inferencias sensibles o conclusiones médicas.
- Mezclar contexto personal y profesional.
- Enviar notificaciones, mensajes o emails.
- Modificar calendario, email, documentos, archivos o ajustes del sistema.
- Llamar servicios externos, Hermes, ApprovalGateway, misiones o tasks.
- Leer secretos, persistir estado o crear auditoría persistente.

`prepare_only=true` es obligatorio. Los flags de lectura, captura, vigilancia,
ejecución, llamadas externas y persistencia permanecen en `false`, incluso al
deserializar input que intente habilitarlos.

## Consentimiento y approval

Cada fuente necesita consentimiento independiente. Calendar, email, documentos,
archivos privados, cuentas externas y cruces de contexto requieren strong approval.
Enviar, actuar o activar cámara, micrófono o pantalla también requiere strong
approval. Phase Q solo calcula y expone ese requisito; nunca crea ni concede approval.

La minimización de datos es obligatoria. Una aprobación futura no debe ampliar el
scope más allá de la fuente y alcance revisados.

## Endpoints

| Método | Endpoint | Resultado |
|---|---|---|
| GET | `/personal-os/status` | Capabilities deshabilitadas |
| GET | `/personal-os/privacy-policy` | Política default-deny |
| POST | `/personal-os/source-consent-preview` | Consentimiento y scope por fuente |
| POST | `/personal-os/daily-state` | Daily state con datos proporcionados |
| POST | `/personal-os/pc-environment-state` | Señales proporcionadas, sin monitorización |
| POST | `/personal-os/awareness-source-preview` | Awareness bloqueado pendiente de approval |
| POST | `/personal-os/local-files-scope` | Scope de archivos sin scan/index/store |
| POST | `/personal-os/context-switch` | Cambio revisable sin mezclar contextos |
| POST | `/personal-os/attention-protection` | Política de interrupciones sin actuar |
| POST | `/personal-os/personal-routine` | Rutina sin schedule/execute/notify |
| POST | `/personal-os/energy-focus-support` | Recomendación sin inferencia sensible |
| POST | `/personal-os/guest-mode` | Memoria y contexto privado bloqueados |
| POST | `/personal-os/visible-reason-audit` | Razón, fuentes, approvals e incertidumbre |
| POST | `/personal-os/approval-requirements` | Requisitos sin crear approval |

No existen rutas para leer fuentes, escanear, capturar, activar sensores, enviar o
actuar. No existe WebSocket de Personal OS.

## Ejemplos

### Consentimiento por fuente

```json
POST /personal-os/source-consent-preview
{
  "source_name": "Work calendar",
  "source_type": "calendar",
  "access_requested": true,
  "scope_preview": ["provided date range"]
}
```

Respuesta resumida:

```json
{
  "prepare_only": true,
  "consent_status": "missing",
  "would_read_source": false,
  "would_store_data": false,
  "would_cross_context": false,
  "approval_required": true,
  "strong_approval_required": true,
  "visible_reason": "Source access remains blocked until explicit consent and approval."
}
```

### Daily state

```json
POST /personal-os/daily-state
{
  "date": "2026-06-09",
  "timezone": "Europe/Madrid",
  "mode": "focus",
  "priorities": ["Review highest ROI action"],
  "source_data": "provided"
}
```

El resultado conserva prioridades proporcionadas, declara que no leyó calendario,
email o documentos y mantiene `would_notify=false` y `would_execute=false`.

### PC y entorno

```json
POST /personal-os/pc-environment-state
{
  "device_state_summary": "Provided by user",
  "environment_signals": ["quiet room"],
  "interruption_risk": "low"
}
```

Las señales son texto proporcionado. El preview garantiza no screen capture, process
scan, file scan, cámara, micrófono, monitorización, tracking ni persistencia.

### Awareness y archivos locales

`/personal-os/awareness-source-preview` puede reflejar que se solicitó awareness,
pero mantiene todas las lecturas en `false`, exige consentimiento, approval y
minimización. `/personal-os/local-files-scope` muestra paths proporcionados como
preview, bloquea secretos y paths privados, y nunca escanea, indexa o almacena.

### Context switching y atención

`/personal-os/context-switch` nunca realiza el cambio ni mezcla contextos. Un cruce
personal/profesional marca `approval_required=true` y expone una razón visible.

`/personal-os/attention-protection` prepara ventanas de foco y políticas de
interrupción. No silencia apps, cambia ajustes, contacta personas ni envía
notificaciones. Esas acciones futuras requerirían strong approval.

### Rutinas y energía/foco

Las rutinas son listas revisables de pasos y triggers. No se programan, ejecutan,
notifican ni persisten.

Energy/focus support acepta un estado declarado y prepara una recomendación. No
infiere salud, no emite conclusión médica, no notifica y no ejecuta.

### Guest mode

Guest mode se presenta con memoria deshabilitada, contexto personal oculto, fuentes
sensibles bloqueadas y cruce de contexto bloqueado. Nunca usa contexto privado ni
persiste datos.

### Razones visibles y auditoría

```json
POST /personal-os/visible-reason-audit
{
  "action_or_preview_name": "daily state",
  "visible_reason": "Protect focus using only provided data.",
  "data_sources_used": ["provided priorities"],
  "data_sources_blocked": ["calendar", "email"],
  "approvals_needed": ["calendar source approval"],
  "uncertainty_notes": ["No live context was read"]
}
```

El endpoint explica razones, fuentes usadas/bloqueadas, approvals e incertidumbre.
No afirma revelar razonamiento oculto y no persiste auditoría.

## Privacidad y separación

Phase Q prohíbe vigilancia opaca e inferencias sensibles sin consentimiento. Las
razones visibles y la explicación auditable forman parte del contrato. El modo
invitado impide memoria y contexto privado. La separación personal/profesional es
obligatoria y un cruce futuro necesitaría strong approval.

## Integraciones

- **Daily Operator:** puede consumir en el futuro daily state revisado; Phase Q no
  programa ni ejecuta tareas.
- **Continuous Learning:** puede proponer mejoras de foco; no aprende información
  sensible ni modifica Phase Q automáticamente.
- **Mission Core:** sigue siendo la frontera de ejecución; los previews no crean
  misiones ni tasks.
- **Command Center / Operator Console:** exponen
  `personal_os_environment_intelligence=prepare_only`, status y policy placeholders.
  No habilitan lectura, vigilancia, captura, inferencia, envío o actuación.

## Foco humano y ROI

La foundation permite ordenar prioridades proporcionadas, hacer visible el riesgo de
interrupción y preparar protección de foco. El objetivo de monetización es proteger
tiempo humano y priorizar acciones de mayor ROI, sin inventar métricas ni convertir
ROI en permiso para acceder a datos o actuar.
