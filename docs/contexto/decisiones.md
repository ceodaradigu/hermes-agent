# Decisiones

## Confirmadas

- JARVIS gobierna y Hermes ejecuta.
- JARVIS no debe reconstruir herramientas Hermes dentro de `jarvis/`.
- El frontend y el iPhone no ejecutan Hermes directamente.
- Wake phrase nunca aprueba y memoria nunca concede permisos.
- Acciones peligrosas requieren readback, scope, expiracion, auditoria y approval
  adecuado.
- No se anade `/execute`, shell libre ni endpoints peligrosos desde UI/mobile.

## Decisiones de PR #179

- PR #179 fue auditoria/documentacion, no funcionalidad nueva.
- Hermes ya tiene capacidades reales amplias: browser, filesystem, terminal,
  procesos, web, gateway/mensajeria, cron, Home Assistant, MCP/plugins, TTS,
  memoria, skills y subagentes.
- La siguiente PR funcional recomendada por #179 es un dispatcher gobernado
  JARVIS -> Hermes.
- `webbrowser.open` puede abrir una URL, pero no sustituye browser controlado
  Hermes.
- `jarvis/mark_2_*_adapter.py` y capas similares deben quedar como politica,
  preview o contratos si no llaman ejecucion Hermes real.

## Pendientes

- Disenar e implementar dispatcher gobernado JARVIS -> Hermes con allowlist,
  `tool_guard`, auditoria y approvals.
- Validar manualmente una accion browser real por Hermes desde JARVIS.
  `[PENDIENTE: verificar]`
- Validar manualmente una accion file real por Hermes desde JARVIS.
  `[PENDIENTE: verificar]`
- Confirmar si David tiene n8n fuera de este repo.
  `[PENDIENTE: verificar]`
- Confirmar configuracion real del entorno de David para Vosk, Tailscale,
  Home Assistant, Telegram, MCP y OpenRouter live.
  `[PENDIENTE: verificar]`
