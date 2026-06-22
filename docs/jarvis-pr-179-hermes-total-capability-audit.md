# PR #179 - Hermes Total Capability Audit + JARVIS Control Map

Fecha: 2026-06-22

## Resumen para David

Hermes ya es el motor que sabe ejecutar muchas acciones reales: navegador,
archivos, terminal, procesos, mensajes, tareas programadas, Home Assistant,
TTS, memoria, skills, MCP y subagentes.

JARVIS no debe reconstruir esas manos dentro de `jarvis/`. JARVIS debe escuchar,
entender, clasificar riesgo, pedir aprobación cuando toque, llamar a una
capacidad Hermes concreta, auditar el resultado y responder en español.

La causa del problema de PR #179 no era solo "Amazon". El problema era que
Phase 12 estaba usando rutas locales estrechas como `webbrowser.open` y
respuestas conversacionales, en vez de mandar acciones básicas al runtime real
de Hermes. Por eso podía abrir una web, pero no podía controlar bien la página.

## Etiquetas usadas

| Etiqueta | Significado |
| --- | --- |
| REAL | Hay código ejecutable y se puede probar con un comando o test concreto. |
| PARCIAL | Una parte funciona, pero falta una pieza importante para que sea producto completo. |
| READINESS | Hay contrato, endpoint, estado, preview o mock, pero no ejecución real. |
| NO HECHO | No se encontró capacidad real en el repo auditado. |

## Cómo se organiza Hermes

Hermes funciona con un registro central de herramientas:

```text
tools/registry.py
  -> tools/*.py registran herramientas
  -> model_tools.py descubre herramientas
  -> toolsets.py decide qué toolsets están disponibles
  -> run_agent.py / cli.py / gateway/run.py ejecutan conversaciones
```

JARVIS ya tiene un puente correcto hacia Hermes en
`jarvis/runtime/hermes_adapter.py`: `HermesRuntimeAdapter` crea `AIAgent` con
`allowed_tools`, `tool_guard`, `enabled_toolsets` y `governed_mode`.

Ese puente es la pieza que JARVIS debe usar para ejecutar capacidades Hermes de
forma gobernada.

## Inventario total

| Capacidad | Existe dónde | Qué hace | Cómo se invoca | Estado | Riesgo | Aprobación | Cómo debería usarlo JARVIS |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Abrir URL con navegador controlado | `tools/browser_tool.py::browser_navigate` | Abre una URL con `agent-browser`, backend cloud o Camofox si está configurado. Devuelve resultado y snapshot. | Tool `browser_navigate` del toolset `browser`. | REAL | Bajo si es web pública segura. | No para abrir web pública segura. | Intent `browser.open` -> policy -> `HermesRuntimeAdapter(allowed_tools=["browser_navigate"])`. |
| Leer página / snapshot | `tools/browser_tool.py::browser_snapshot` | Devuelve texto/elementos de la página actual. | Tool `browser_snapshot`. | REAL | Bajo/medio según web. | No para lectura normal; sí si puede exponer secretos. | Usarlo para "qué pone", "qué botones ves" y auditoría después de navegar. |
| Clic en página | `tools/browser_tool.py::browser_click` | Hace clic por referencia de elemento del snapshot. | Tool `browser_click`. | REAL | Bajo/medio; alto si confirma compra, pago, envío o legal. | Sí si el clic puede enviar/modificar/comprar. | JARVIS debe resolver texto visible -> snapshot ref -> policy -> click. |
| Escribir en campo | `tools/browser_tool.py::browser_type` | Escribe texto en un elemento interactivo. | Tool `browser_type`. | REAL | Medio/alto si son credenciales, datos personales o pago. | Sí para credenciales, tarjetas, datos sensibles o formularios externos. | JARVIS debe pedir preview para datos sensibles y no usar comando crudo del usuario. |
| Pulsar tecla | `tools/browser_tool.py::browser_press` | Pulsa una tecla como Enter. | Tool `browser_press`. | REAL | Bajo/medio; alto si envía formulario o confirma acción. | Sí si puede enviar datos o aceptar condiciones. | Usarlo después de clasificar el efecto de la tecla. |
| Scroll | `tools/browser_tool.py::browser_scroll` | Desplaza la página. | Tool `browser_scroll`. | REAL | Bajo. | No normalmente. | Ruta directa de navegador gobernado. |
| Volver atrás | `tools/browser_tool.py::browser_back` | Vuelve a la página anterior. | Tool `browser_back`. | REAL | Bajo. | No normalmente. | Usarlo para "atrás" y "vuelve". |
| Avanzar / recargar | No se encontró tool público `browser_forward` ni `browser_reload`. | Puede existir como acción posible del backend, pero no está expuesta en Hermes. | No hay tool registrada. | NO HECHO | Bajo. | No normalmente. | Añadir como capacidad Hermes, no como ejecutor JARVIS paralelo. |
| Cerrar página controlada | `tools/browser_tool.py::cleanup_browser`, `tools/browser_camofox.py::camofox_close` | Cierra sesión/navegador interno por `task_id`; Camofox también cierra. | Función interna, no tool pública. | PARCIAL | Bajo si la página la abrió Hermes. | No para páginas controladas por Hermes. | Añadir tool Hermes `browser_close` o endpoint gobernado; JARVIS no debe fingir cierre. |
| Manejar pestañas | Estado de sesión en `tools/browser_tool.py` y backend. | Mantiene sesión por `task_id`, pero no hay API de pestañas completa. | Interno. | PARCIAL | Bajo/medio. | Depende de acción. | Añadir capacidades Hermes si el producto necesita pestañas. |
| Buscar en web | `tools/web_tools.py`, `tools/browser_tool.py` | Búsqueda web de investigación o navegación a URL de búsqueda. | `web_search`, `web_extract`, `browser_navigate`. | REAL | Bajo para búsqueda normal. | No normalmente. | Para "busca X", JARVIS puede usar `browser_navigate` con URL segura o `web_search` si quiere resultados textuales. |
| Buscar producto en Amazon | Browser tools permiten escribir/click; Phase 12 tenía alias/webbrowser. | No hay router determinista de producto Amazon en Hermes. | Combinación de `browser_navigate`, `browser_snapshot`, `browser_type`, `browser_press`. | PARCIAL | Bajo para buscar; alto para comprar. | No para buscar; sí para comprar/pagar/pedido. | JARVIS debe orquestar herramientas Hermes. Fallback seguro: URL `https://www.amazon.es/s?k=...`. |
| Rellenar formularios | Browser `click/type/press` lo permite técnicamente. | No hay política semántica completa de formularios en Hermes. | Browser tools. | PARCIAL | Medio/alto. | Sí para enviar; preview para datos sensibles. | JARVIS debe controlar la política antes de `type` y antes de enviar. |
| Leer archivo | `tools/file_tools.py::read_file_tool` | Lee archivos, evita binarios/dispositivos, redacción de secretos. | Tool `read_file`. | REAL | Bajo/medio; alto si secretos. | Sí para secretos o fuera de scope. | JARVIS debe resolver path permitido y llamar `read_file`. |
| Buscar archivos | `tools/file_tools.py::search_files_tool` | Busca por glob/patrón con límites. | Tool `search_files`. | REAL | Medio si enumera datos privados. | Según scope. | Usarlo para "busca en mi escritorio X" con raíces permitidas. |
| Escribir archivo | `tools/file_tools.py::write_file_tool` | Escribe contenido con protecciones de paths sensibles. | Tool `write_file`. | REAL | Alto porque modifica datos. | Sí, con preview/diff. | JARVIS debe preparar diff y pedir aprobación antes de escribir. |
| Aplicar patch | `tools/file_tools.py::patch_tool` | Aplica cambios a archivos con comprobaciones. | Tool `patch`. | REAL | Alto. | Sí, con preview/diff. | Ruta correcta para "cambia X por Y" tras aprobación. |
| Backup/checkpoint | `tools/checkpoint_manager.py` | Crea checkpoints shadow-git para mutaciones cuando está activado. | Infra interna de agente, no tool directa. | PARCIAL | Bajo/medio. | No como acción aislada. | JARVIS debe exigir rollback/checkpoint en acciones de alto riesgo cuando aplique. |
| Leer Desktop/Descargas por nombre natural | No hay resolver JARVIS->Hermes completo. Hermes puede leer path explícito. | Falta capa de resolución segura Desktop/Downloads/Documents. | `read_file` si JARVIS entrega path. | PARCIAL | Medio. | Sí si fuera de zonas permitidas o secreto. | Implementar en JARVIS como resolución/política, no como lector nuevo. |
| PDF/DOCX/XLSX | No se encontró tool local dedicada estable. | Podría abrirse con terminal/libs externas si se instalan. | No hay tool registrada. | NO HECHO | Medio/alto. | Según documento. | Añadir soporte Hermes o fallback honesto. |
| Abrir carpeta/app | Phase 11/12 tienen pilotos locales con allowlist y `webbrowser.open`. | Abre `/jarvis`, URLs seguras y algunas apps conocidas si resueltas. | `LocalControllerPilot`, `Phase12ActionRouter`. | PARCIAL | Bajo/medio; alto para apps sensibles. | Sí para apps sensibles. | Conservar como controlador local acotado o mover a Hermes como tool estructurada. |
| Terminal local | `tools/terminal_tool.py` | Ejecuta comandos en entorno local/docker/ssh/modal/etc. con guards. | Tool `terminal`. | REAL | Alto. | Sí para comandos peligrosos o escritura/sistema. | JARVIS nunca debe exponer comando crudo desde UI; debe generar acción estructurada y usar guards. |
| Procesos en background | `tools/process_registry.py` | Lista, lee logs, espera, mata y escribe a procesos. | Tool `process`. | REAL | Medio/alto. | Sí para matar/escribir procesos sensibles. | Usarlo para procesos que Hermes inició o que estén en scope. |
| Sandbox / code execution | `tools/code_execution_tool.py` | Ejecuta Python aislado con acceso limitado a tools Hermes. | Tool `execute_code`. | REAL | Alto. | Sí. | Solo para tareas técnicas con aprobación/scope; no para acciones de navegador básicas. |
| Web research/extract | `tools/web_tools.py` | Busca y extrae páginas con proveedores configurados. | `web_search`, `web_extract`. | REAL | Bajo/medio. | Según sitio/datos. | Útil para leer web sin control visual de navegador. |
| Mensajería remota | `tools/send_message_tool.py`, `gateway/` | Envía/lista canales en Telegram, Slack, WhatsApp, Signal, email, SMS y otros si están configurados. | Tool `send_message` y gateway. | REAL | Alto si envía como David. | Sí con preview. | JARVIS debe pedir confirmación antes de enviar/publicar. |
| Telegram | `gateway/platforms/telegram.py` | Adaptador real para mensajes, media, voz y approvals con botones. | Gateway configurado con token. | REAL | Medio/alto. | Sí para acciones sensibles. | JARVIS puede usar Telegram como interfaz/aprobación, no como permiso automático. |
| iPhone/mobile companion | `jarvis/phase_11_real_provider_controller_iphone_companion.py`, docs mobile | Pairing/state/read model. No ejecución Hermes directa. | Endpoints JARVIS mobile. | PARCIAL | Medio. | Sí para approvals fuertes. | Usarlo como interfaz confiable si hay device trust y challenge. |
| Cron / automatización | `tools/cronjob_tools.py`, `cron/` | Crea y ejecuta tareas programadas con prompt/toolsets. | Tool `cronjob`, gateway tick. | REAL | Alto. | Sí fuerte. | JARVIS debe exigir scope, duración, stop conditions, presupuesto y audit. |
| Home Assistant | `tools/homeassistant_tool.py` | Lista entidades, lee estado y llama servicios permitidos. | Tools `ha_*`. | REAL si está configurado. | Medio/alto por mundo físico. | Sí para acciones que cambien estado. | JARVIS debe clasificar casa/seguridad antes de `ha_call_service`. |
| MCP/plugins | `tools/mcp_tool.py`, plugin discovery | Descubre y registra tools externas. | Registro dinámico MCP. | REAL si servers/config existen. | Variable. | Según tool. | JARVIS debe tratar cada capability externa con policy propia. |
| Skills/memoria/todo/session search | `tools/skills_tool.py`, `tools/memory_tool.py`, `tools/todo_tool.py`, `tools/session_search_tool.py` | Gestiona skills, memoria, tareas y búsqueda de sesión. | Tools Hermes. | REAL | Bajo/medio. | Según contenido. | Útil para contexto; nunca como permiso. |
| TTS | `tools/tts_tool.py` | Genera audio por Edge/OpenAI/ElevenLabs/MiniMax/Mistral/local según config. | Tool `text_to_speech`. | REAL | Bajo. | No normalmente. | JARVIS puede hablar resultados vía su flujo de voz. |
| STT / transcripción | `tools/transcription_tools.py`, tests, voice runtime JARVIS | Funciones y contratos de transcripción; no apareció como tool central registrada. | Runtime/utility, no tool LLM central. | PARCIAL | Medio por audio. | Sí para grabación persistente o envío externo. | JARVIS lo usa para entrada de voz; wake no aprueba. |
| Wake phrase / Always-on | `jarvis/phase_12_real_always_on_jarvis_mvp.py`, scripts `jarvis-wake-*` | Wake local opcional, saludo y sesión activa. | `scripts/jarvis-start`, `scripts/jarvis-wake-listener`. | REAL opcional | Bajo/medio. | Wake nunca aprueba. | Solo activa escucha/conversación. |
| JARVIS conversación Phase 12 | `jarvis/phase_12_real_always_on_jarvis_mvp.py` | Responde local/OpenRouter según config. | `/mark-3/phase-12/conversation/turn`. | REAL para conversación; PARCIAL para acciones. | Variable. | Según intención. | Debe enrutar comandos básicos a Hermes antes de depender de OpenRouter. |
| JARVIS Mark 2 adapters | `jarvis/mark_2_*_adapter.py`, `jarvis/tool_invocation_layer.py` | Previews y readiness para browser/files/GitHub/tools. | APIs internas JARVIS. | READINESS | Bajo porque no ejecuta. | No ejecuta. | Mantener como contratos/política o retirar duplicación. |
| Mark 3 Hermes runtime bridge | `jarvis/mark_3_hermes_runtime_bridge.py` | Bridge gobernado muy estrecho: solo `read_file` aprobado exacto. | Endpoint/servicio Mark 3. | REAL pero estrecho | Medio. | Sí por approval exacto. | Ampliar patrón a más tools Hermes con allowlist y guards. |
| GitHub remoto | JARVIS adapter es preview; Hermes no tiene tool GitHub nativa local en registro base. | Puede operar repo local con file/terminal; GitHub remoto depende de MCP/plugin/CLI configurado. | File/terminal/MCP externo. | PARCIAL | Alto para push/PR/merge. | Sí fuerte. | No duplicar; conectar MCP/GitHub o terminal allowlisted con approval. |
| Deploy/pagos/Stripe | JARVIS tiene control planes/preview; no se encontró ejecución nativa base en Hermes. | Puede existir vía plugin/config externa, no base auditada. | No base local estable. | READINESS | Muy alto. | Sí fuerte. | Solo preview hasta conector gobernado real. |
| OS GUI humano completo | No se encontró control de mouse/teclado global de escritorio. | Browser está cubierto; escritorio general no. | No tool base. | NO HECHO | Alto. | Sí. | Futuro Hermes capability, no JARVIS paralelo. |

## Capacidades reales encontradas

- Navegador real: abrir, leer snapshot, clicar, escribir, scroll, atrás, teclas,
  imágenes, visión y consola con `tools/browser_tool.py`.
- Archivos reales: leer, buscar, escribir y aplicar patch con `tools/file_tools.py`.
- Terminal real con guards y aprobación en `tools/terminal_tool.py` y
  `tools/approval.py`.
- Procesos reales en `tools/process_registry.py`.
- Ejecución de código real y limitada en `tools/code_execution_tool.py`.
- Búsqueda/extracción web real en `tools/web_tools.py`.
- Mensajería real mediante gateway y `tools/send_message_tool.py`.
- Telegram real si está configurado en `gateway/platforms/telegram.py`.
- Cron/automatización real en `tools/cronjob_tools.py` y `cron/`.
- Home Assistant real si está configurado en `tools/homeassistant_tool.py`.
- MCP/plugins reales si hay servidores configurados en `tools/mcp_tool.py`.
- TTS real en `tools/tts_tool.py`.
- Wake/always-on JARVIS real opcional en Phase 12.

## Capacidades parciales

- Cerrar páginas: Hermes puede cerrar sesiones internamente, pero no hay tool
  pública `browser_close` para JARVIS.
- Pestañas: hay sesión por `task_id`, pero no API completa de tabs.
- Buscar productos dentro de Amazon: se puede hacer con browser tools, pero falta
  router determinista de intención a secuencia segura.
- Formularios: se puede clicar/escribir, pero JARVIS debe añadir política de
  preview/aprobación antes de enviar o usar datos sensibles.
- Desktop/Downloads/Documents por lenguaje natural: Hermes puede leer paths,
  pero JARVIS todavía debe resolver nombres de forma segura.
- Apps locales: Phase 11/12 abren algunas rutas/apps, pero no es operador de
  escritorio completo.
- iPhone/mobile: pairing y estado existen; ejecución remota gobernada sigue
  limitada.
- GitHub remoto: el repo local se puede editar/testear; push/PR/merge dependen
  de herramientas externas y aprobación.
- STT local: hay runtime/contratos y scripts de voz; no es una tool central de
  Hermes como `text_to_speech`.

## Readiness encontrada

- `jarvis/tool_invocation_layer.py` y `jarvis/tool_registry.py`: contratos
  prepare-only, sin ejecución.
- `jarvis/mark_2_browser_adapter.py`: preview de navegador, sin browser real.
- `jarvis/mark_2_filesystem_adapter.py`: preview/path policy, sin leer/escribir.
- `jarvis/mark_2_github_adapter.py`: preview GitHub, sin llamadas GitHub reales.
- Varias fases de producto/dinero/deploy/email en JARVIS preparan candidatos,
  pero no ejecutan acciones externas por defecto.

## No hecho o no encontrado

- `browser_close` público como tool Hermes.
- `browser_forward` y `browser_reload` públicos.
- Resolver natural completo para "archivo del escritorio llamado X".
- Lector dedicado estable de PDF/DOCX/XLSX.
- Operador GUI general de escritorio con mouse/teclado global.
- Compras/pagos/publicaciones automáticas. Correcto que no existan sin strong
  approval.
- n8n nativo en repo auditado. [PENDIENTE: verificar si David lo tiene fuera de
  este repo.]

## Duplicaciones detectadas

| Código nuevo o existente en JARVIS | Capacidad Hermes equivalente | Decisión | Motivo |
| --- | --- | --- | --- |
| `Phase12ActionRouter` abriendo URLs con `webbrowser.open` | `tools/browser_tool.py::browser_navigate` | Reconectar | `webbrowser.open` abre, pero no controla ni cierra. Hermes ya tiene browser tool. |
| Alias web "Amazon/Google/YouTube" dentro de JARVIS | `browser_navigate` con URL resuelta por JARVIS | Mantener solo resolución, no ejecución | JARVIS puede mapear intención a URL; Hermes debe abrir/controlar. |
| Browser Operator nuevo dentro de `jarvis/` | `browser_navigate/snapshot/click/type/press/back/scroll` | Borrar o reducir | Sería otro Hermes dentro de JARVIS. |
| File Operator nuevo dentro de `jarvis/` | `read_file/write_file/patch/search_files` | Reconectar | Hermes ya tiene lectura/escritura/búsqueda/patch con guards. |
| `mark_2_*_adapter.py` como ejecución futura | Hermes tools reales | Mantener como política/preview o simplificar | No deben convertirse en ejecutores paralelos. |
| Tool registry JARVIS prepare-only | `tools/registry.py` Hermes | Alinear | Hermes ya tiene registro real. JARVIS debe tener mapa de control, no registro duplicado. |
| GitHub adapter JARVIS | MCP/plugin/terminal/file tools | Mantener preview o conectar externo | No hay que inventar otro cliente GitHub si Hermes/MCP ya lo puede aportar. |

## Mapa correcto JARVIS -> Hermes

Flujo único:

```text
David habla o escribe
  -> JARVIS normaliza texto/voz
  -> JARVIS clasifica intención
  -> JARVIS clasifica riesgo
  -> JARVIS pide aprobación si toca
  -> JARVIS llama a una capability Hermes allowlisted
  -> Hermes ejecuta
  -> Hermes devuelve resultado
  -> JARVIS audita
  -> JARVIS responde en español y, si viene por voz, habla
```

### Navegador

JARVIS debe resolver frases como "abre Amazon", "busca freidora de aire en
Amazon", "haz clic en aceptar" o "qué botones ves" a tools Hermes:

- `browser_navigate`
- `browser_snapshot`
- `browser_click`
- `browser_type`
- `browser_press`
- `browser_scroll`
- `browser_back`
- futuro `browser_close`
- futuro `browser_forward`
- futuro `browser_reload`

JARVIS debe bloquear o pedir aprobación antes de comprar, pagar, iniciar sesión,
usar tarjeta, publicar, enviar formularios o aceptar condiciones legales.

### Archivos

JARVIS debe resolver nombres humanos a paths permitidos y luego usar:

- `search_files`
- `read_file`
- `write_file`
- `patch`

Leer `.txt`, `.md`, `.json`, `.csv` y `.log` puede ser bajo riesgo dentro de
zonas permitidas. Modificar, borrar, leer secretos o salir de zonas permitidas
requiere aprobación fuerte o bloqueo.

### Apps y sistema local

JARVIS no debe enviar shell cruda desde el frontend. Para tareas de sistema:

- usar pilotos locales allowlisted cuando existan;
- usar `terminal` solo cuando JARVIS haya generado una acción concreta,
  revisada por policy y approval;
- usar `process` solo para procesos en scope.

### Remoto y Telegram

Telegram/gateway son interfaces y canales de entrega. No son permiso. Enviar
mensajes, archivos o acciones remotas requiere preview y aprobación.

### Automatización

`cronjob` es real y potente. JARVIS debe exigir scope, duración, presupuesto,
stop conditions, auditoría y strong approval antes de crear o activar rutinas.

### Dinero, deploy y publicaciones

Por defecto deben quedar en preview. Solo se ejecutan si hay capability real,
policy específica, presupuesto, rollback cuando aplique y strong approval.

## Qué debe corregirse después

1. Crear un dispatcher gobernado JARVIS -> Hermes que use
   `HermesRuntimeAdapter` con `allowed_tools` y `tool_guard`.
2. Conectar comandos básicos sin OpenRouter: navegador, archivos simples y
   estado.
3. Reemplazar `webbrowser.open` por `browser_navigate` cuando se necesite control
   real; dejar `webbrowser.open` solo como fallback honesto `controlled:false`.
4. Añadir en Hermes herramientas públicas faltantes: `browser_close`,
   `browser_forward`, `browser_reload`.
5. Implementar resolver seguro de Desktop/Downloads/Documents en JARVIS, pero
   ejecutar lectura/escritura con Hermes file tools.
6. Convertir acciones de Amazon en secuencia gobernada: navegar, snapshot,
   escribir/buscar o fallback URL segura; compra siempre bloqueada/aprobación.
7. Reducir o borrar código JARVIS que duplique ejecución Hermes.
8. Añadir tests de ruta común voz/texto -> intención -> policy -> Hermes tool ->
   respuesta.

## Pruebas y comandos de verificación

Comandos útiles para comprobar capacidades reales:

```bash
source venv/bin/activate
PYTHONPATH=. python3 - <<'PY'
import model_tools
from tools.registry import registry
model_tools._discover_tools()
for name in registry.get_all_tool_names():
    print(name, registry.get_toolset_for_tool(name))
PY
```

Pruebas por área:

```bash
source venv/bin/activate
PYTHONPATH=. python3 -m pytest tests/tools/test_browser_cleanup.py -q
PYTHONPATH=. python3 -m pytest tests/tools/test_file_tools.py -q
PYTHONPATH=. python3 -m pytest tests/tools/test_terminal_tool.py -q
PYTHONPATH=. python3 -m pytest tests/tools/test_send_message_tool.py -q
PYTHONPATH=. python3 -m pytest tests/tools/test_cronjob_tools.py -q
PYTHONPATH=. python3 -m pytest tests/tools/test_homeassistant_tool.py -q
```

Validación pedida para esta PR de auditoría:

```bash
source venv/bin/activate
PYTHONPATH=. python3 -m pytest tests/jarvis -q -n 0
git diff --check
```

`npm --prefix web run build` solo es necesario si esta PR toca frontend. Esta
auditoría no debe tocar frontend.

## Conclusión

PR #179 debe cerrar como auditoría y mapa de control, no como Browser Operator
nuevo dentro de JARVIS.

La siguiente PR debería ser: **JARVIS Governed Hermes Dispatcher MVP**.

Objetivo de esa siguiente PR:

- JARVIS entiende comandos básicos sin OpenRouter.
- JARVIS decide riesgo.
- JARVIS llama a Hermes tools reales.
- Hermes ejecuta.
- JARVIS audita y responde.
- Nada peligroso se ejecuta sin aprobación fuerte.
