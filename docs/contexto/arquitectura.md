# Arquitectura JARVIS/Hermes

Este paquete resume el contexto operativo para futuras sesiones de Codex. No
implementa runtime, endpoints ni dispatcher.

## Separacion

JARVIS gobierna:

- Intencion, conversacion, UI, persona y memoria visible.
- Clasificacion de riesgo y policy.
- Approval gate, strong approval y auditoria metadata-only.
- Scope, limites, rollback/stop plan y respuesta final a David.

Hermes ejecuta:

- Browser controlado, filesystem, terminal/procesos, gateway/Telegram, cron,
  Home Assistant, MCP, TTS, memoria, skills, subagentes y otras tools locales
  existentes.
- Registro real de tools en `tools/registry.py`, descubierto por
  `model_tools.py` y agrupado por `toolsets.py`.

## Prohibido duplicar

- No crear otro browser operator dentro de `jarvis/` si Hermes ya tiene
  `browser_navigate`, `browser_snapshot`, `browser_click`, `browser_type`,
  `browser_press`, `browser_scroll` y `browser_back`.
- No crear otro file operator dentro de JARVIS si Hermes ya tiene `read_file`,
  `write_file`, `patch` y `search_files`.
- No exponer `/execute`, shell arbitrario desde UI/mobile, ni frontend directo a
  Hermes.
- No llamar READINESS a DONE ni cerrar una PR funcional solo por tests.

## Flujo correcto

```text
David habla o escribe
  -> JARVIS normaliza intencion
  -> JARVIS clasifica riesgo
  -> JARVIS pide aprobacion si toca
  -> JARVIS llama capability Hermes allowlisted
  -> Hermes ejecuta
  -> JARVIS audita metadata-only
  -> JARVIS responde en espanol
```

## Evidencia base

- `docs/jarvis-pr-179-hermes-total-capability-audit.md`: auditoria total Hermes
  y mapa correcto JARVIS -> Hermes.
- `docs/JARVIS_MASTER_BUILD_MAP.md`: contrato maestro JARVIS gobierna/Hermes
  ejecuta y Phase 12.
- `jarvis/runtime/hermes_adapter.py`: wrapper fino sobre `AIAgent` con
  `allowed_tools`, `tool_guard` y `governed_mode`.
- `jarvis/mark_3_hermes_runtime_bridge.py`: bridge real estrecho para
  `read_file`, no dispatcher general.
