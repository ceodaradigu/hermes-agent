# Estado Actual

Estado despues de PR #179: auditoria/documentacion completada, sin
funcionalidad nueva. Esta PR #180 solo crea contexto vivo.

## REAL validado en PC de David

- `scripts/jarvis-start` como arranque local Phase 12, con puertos corregidos y
  lectura de configuracion Vosk persistida segun handoff.
- Wake principal `JARVIS` con Vosk local STT. `Hola JARVIS` queda experimental,
  no garantizado.
- Saludo escrito/hablado basico: `Estoy aquí, David. Te escucho.` El handoff
  documenta que wake crea saludo visible/voz, la UI lo reclama y lo muestra/
  habla una sola vez.
- Voz default-on: salida de voz activada por defecto, con limitacion de unlock
  del navegador si `speechSynthesis` bloquea autoplay.
- Vosk configurado localmente para el camino real de wake tras #178/#179. Si
  cambia microfono, modelo, profile o dependencias, hay que revalidar.

## REAL en repo/Hermes

- Separacion doctrinal JARVIS gobierna/Hermes ejecuta esta documentada.
- Hermes tiene tools reales de browser, filesystem, terminal/procesos, web,
  cron, Home Assistant, TTS, memoria, skills y subagentes en `tools/` y
  `toolsets.py`.
- Phase 12 tiene codigo/tests/docs para `jarvis-start`, `jarvis-stop`,
  `jarvis-doctor`, `jarvis-wake-listener` y `jarvis-wake-setup`.
- Hermes browser tools existentes: `browser_navigate`, `browser_snapshot`,
  `browser_click`, `browser_type`, `browser_press`, `browser_scroll` y
  `browser_back`, entre otras.
- Hermes filesystem tools existentes: `read_file`, `write_file`, `patch` y
  `search_files`.
- Hermes terminal/process tools existentes: `terminal` y `process`.
- Cron, TTS, memory, skills y subagents tienen evidencia en repo/Hermes.
- `HermesRuntimeAdapter` existe como wrapper gobernable sobre `AIAgent`.

## PARCIAL

- JARVIS todavía no despacha browser natural a Hermes end-to-end. Phase 12 abre
  URL/busqueda segura, pero eso no es snapshot/click/type por Hermes.
- File desde JARVIS existe como bridge estrecho `read_file` y pilotos locales,
  pero no como dispatcher general a Hermes file tools.
- Telegram, Home Assistant y MCP son capacidades reales de Hermes condicionadas
  a configuracion externa.

## READINESS

- iPhone fuera de casa via Tailscale/private VPN como camino recomendado, sin
  prueba repo de red externa real.
- OpenRouter como brain diario: hay router/adapter y mocks, pero no validacion
  de uso diario real.
- Alta calidad de voz JARVIS/UTRON: hay voz basica y providers opcionales, pero
  no una voz premium validada como capacidad final.
- Browser form fill, compras, pagos, publicaciones, credenciales y vault.
- Double/triple confirmation completa si faltan canales reales.
- Dispatcher gobernado JARVIS -> Hermes para acciones browser/file generales.

## NO HECHO

- No hay `browser_close`, `browser_forward` ni `browser_reload` publicos como
  tools Hermes segun auditoria #179.
- No hay operador GUI general de escritorio.
- No hay lector dedicado estable PDF/DOCX/XLSX confirmado en la auditoria #179.
- No hay compras/pagos/publicaciones automaticas sin strong approval; correcto
  que no existan.
- No hay dispatcher general JARVIS -> Hermes cerrado como `REAL`; sigue siendo
  siguiente PR, no capacidad terminada.

## Siguiente PR recomendada

La siguiente PR funcional deberia ser el dispatcher gobernado JARVIS -> Hermes:
JARVIS entiende intencion, clasifica riesgo, pide aprobacion, llama tools Hermes
allowlisted, audita y responde. Debe validar una accion browser real y una
accion file real por Hermes, sin duplicar Hermes.
