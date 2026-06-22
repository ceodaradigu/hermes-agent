# Capacidades Reales

Tabla de contexto vivo. `Estado` distingue entre repo/código/tests y validación
manual. El estado del repo no siempre equivale a validación manual en el PC de
David. Cuando exista validación conocida en el PC de David, debe indicarse
explícitamente. Si una capacidad depende del entorno local pero ya fue validada
por David tras #178/#179, no debe degradarse a "no real": debe quedar como
`REAL validado en PC de David`, con limitación de revalidación futura si cambia
el entorno.

Estados usados aquí: `REAL validado en PC de David`, `REAL en repo/código/tests`,
`REAL en Hermes/repo`, `PARCIAL`, `READINESS`, `NO HECHO` y
`[PENDIENTE: verificar]`.

| Capacidad | Estado | Evidencia | Limitacion | Proximo paso seguro |
| --- | --- | --- | --- | --- |
| `scripts/jarvis-start` | `REAL validado en PC de David` | `docs/jarvis-handoff-context.md` Phase 12: startup simple, puertos corregidos y persistencia Vosk diaria; `docs/jarvis-pr-178-phase-12-real-always-on-jarvis-mvp.md`; tests Phase 12. | Depende de puertos, procesos y entorno local; hay que revalidar si cambian deps/puertos/perfil. | Usar `scripts/jarvis-doctor` antes de cerrar cambios runtime. |
| Wake `JARVIS` | `REAL validado en PC de David` | Handoff Phase 12: `JARVIS` fue mas fiable en pruebas reales con Vosk; `jarvis/phase_12_wake_listener.py`; tests matcher/simulate. | Validado con Vosk local STT para `JARVIS`; `Hola JARVIS` sigue experimental/best-effort y no garantizado. Wake nunca aprueba ni ejecuta. | Mantener `JARVIS` como cierre real; no hacer de `Hola JARVIS` requisito hasta modelo/STT mejor. |
| Saludo escrito/hablado básico | `REAL validado en PC de David` | Handoff y #178: wake genera saludo visible/voz `Estoy aquí, David. Te escucho.` y la UI lo reclama/muestra/habla una vez; tests verifican greeting pendiente y `voice_output_requested=true`. | Depende de browser TTS, prompt de unlock o proveedor TTS local disponible. | Revalidar audio si cambia navegador, permisos o provider. |
| Voz default-on | `REAL validado en PC de David` | Handoff y #178: voz de salida activada por defecto; browser fallback y aviso de primera interacción. | Browser puede bloquear autoplay hasta primera pulsación. | Mantener aviso de unlock y smoke manual si se toca voz/UI. |
| Vosk local | `REAL validado en PC de David` + `PARCIAL/condicionado en repo` | Handoff: persistencia Vosk diaria y pruebas reales con Vosk; #178 documenta `JARVIS_WAKE_BACKEND=vosk` y `JARVIS_VOSK_MODEL_PATH`; tests cubren config. | Repo no bundlea modelo; soporte depende de `vosk`, `sounddevice`, micro y ruta local. | Revalidar `scripts/jarvis-wake-listener run` si cambia modelo, mic o profile. |
| Alta calidad de voz JARVIS/UTRON | `READINESS` | #178 documenta preferencias no-cloning y Piper/GPT-SoVITS opcionales. | Voz básica funciona, pero voz premium/cinemática de alta calidad no queda cerrada como producto. | Tratar como PR separada con provider local/API y validación manual. |
| Browser desde JARVIS | `PARCIAL` | Phase 12 abre URL/búsqueda segura con `webbrowser.open`; #179 dice que eso no equivale a browser controlado Hermes. | No hay dispatcher Hermes real desde JARVIS para snapshot/click/type/press. Abrir URL/búsqueda segura no es control Hermes. | Implementar dispatcher gobernado hacia Hermes browser tools. |
| File desde JARVIS | `PARCIAL` | `jarvis/mark_3_hermes_runtime_bridge.py` soporta `read_file` exacto; Phase 7 prueba safe read/list/write local; #179 exige resolver humanos -> Hermes file tools. | No hay lenguaje natural general via Hermes para `search_files`/`read_file`/`write_file`/`patch` end-to-end. | Dispatcher allowlisted y validacion file real por Hermes. |
| OpenRouter brain | `READINESS/PARCIAL` | Phase 11/12 tienen router/adapter seguro y tests con HTTP mock; #178 dice live calls solo con key y flag. | No probado como daily brain real; live calls bloqueadas por defecto y requieren budget/approval. | Validar con key, budget, live enabled y uso diario. `[PENDIENTE: verificar]` |
| iPhone fuera de casa | `READINESS` | Docs #178 describen Tailscale/private VPN; tests verifican status URL/kill switch/pairing. | No hay prueba repo de conexion real fuera de casa. | Probar iPhone por Tailscale en red externa. `[PENDIENTE: verificar]` |
| Dispatcher gobernado JARVIS -> Hermes | `NO HECHO` | #179 lo marca como siguiente PR: crear dispatcher con `HermesRuntimeAdapter`, `allowed_tools` y `tool_guard`. | Hay bridge estrecho y capacidades Hermes, pero no dispatcher general browser/file natural end-to-end. | Siguiente PR funcional. |
| Approvals | `REAL en repo/código/tests` | `jarvis/policy/approval_gateway.py`; Phase 7/11/12 tests de approval, exact phrase, pairing y gates. | Double/triple completo depende de canales reales. | Mantener gates y no permitir wake/memoria como permiso. |
| Hermes browser tools | `REAL en Hermes/repo` | `tools/browser_tool.py` registra `browser_navigate`, `browser_snapshot`, `browser_click`, `browser_type`, `browser_scroll`, `browser_back`, `browser_press`, `browser_get_images`, `browser_vision`, `browser_console`; `toolsets.py`; #179. | Requiere backend/agent-browser/config segun entorno. Esto no significa que JARVIS ya las despache. | Conectar desde dispatcher JARVIS con allowlist y pruebas reales. |
| Hermes filesystem tools | `REAL en Hermes/repo` | `tools/file_tools.py` registra `read_file`, `write_file`, `patch`, `search_files`; #179. | JARVIS debe resolver scope/path y pedir approval antes de mutar. Esto no significa que JARVIS ya tenga file operator natural. | Usar Hermes, no crear file operator paralelo. |
| Terminal/process tools | `REAL en Hermes/repo` | `tools/terminal_tool.py` registra `terminal`; `tools/process_registry.py` registra `process`; `toolsets.py`; #179. | Alto riesgo; no exponer raw shell desde UI. | Usar solo acciones estructuradas, guards y approval. |
| Telegram/gateway | `PARCIAL` | `gateway/platforms/telegram.py`; `tools/send_message_tool.py`; docs #179. | Real si gateway/token estan configurados; no verificado en este worktree. | Verificar token/gateway en entorno David. `[PENDIENTE: verificar]` |
| Cron | `REAL en Hermes/repo` | `tools/cronjob_tools.py`; `cron/`; `toolsets.py`; #179. | Potente y persistente; requiere scope/stop conditions. | Strong approval para automatizaciones. |
| Home Assistant | `PARCIAL` | `tools/homeassistant_tool.py` registra `ha_*` y bloquea dominios peligrosos. | Requiere `HASS_TOKEN`/`HASS_URL`; casa fisica implica riesgo. | Verificar config y policy por dominio. `[PENDIENTE: verificar]` |
| MCP | `PARCIAL` | `tools/mcp_tool.py`; `model_tools.py` llama `discover_mcp_tools()`. | Depende de servers/config externos. | Inventariar MCP activos antes de permitir acciones. `[PENDIENTE: verificar]` |
| TTS | `REAL en Hermes/repo` | `tools/tts_tool.py`; `jarvis/voice/*`; tests Phase 12 Piper/browser voice. | Provider real puede depender de navegador, binario local o API. | Validar provider elegido en maquina real si se promete audio. |
| Memory | `REAL en Hermes/repo` | `tools/memory_tool.py`; `jarvis/memory_brain_v2.py`; handoff memory commands. | Memoria nunca concede permisos ni baja riesgo. | Mantener metadata/redaction. |
| Skills | `REAL en Hermes/repo` | `tools/skills_tool.py`; `toolsets.py`. | Skills instruyen, no autorizan. | Usarlas como contexto, no como permiso. |
| Subagents | `REAL en Hermes/repo` | `tools/delegate_tool.py`; `toolsets.py` `delegate_task`. | Subagentes no saltan policy ni approvals. | Mantener aislamiento y tool allowlists. |
