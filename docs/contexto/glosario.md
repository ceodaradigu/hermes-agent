# Glosario

| Termino | Significado |
| --- | --- |
| JARVIS | Capa de gobierno: intencion, conversacion, UI, policy, approvals, riesgo, memoria y auditoria. |
| Hermes | Runtime de ejecucion: tools, agentes, browser, filesystem, terminal, gateway, cron, MCP, TTS, skills, memoria y subagentes. |
| Dispatcher gobernado | Futuro puente JARVIS -> Hermes que convierte una intencion aprobada en llamada allowlisted a tool Hermes y audita el resultado. |
| Approval gate | Paso obligatorio que bloquea o pide aprobacion antes de ejecutar acciones sensibles. |
| Strong confirmation | Aprobacion reforzada para alto riesgo con readback, scope, expiracion, frase exacta y auditoria. |
| Double confirmation | Dos confirmaciones/canales para riesgo superior. Estado completo actual: `[PENDIENTE: verificar]`. |
| Triple confirmation | Tres pasos/canales para riesgo critico. Documentado como readiness en fases previas si faltan canales reales. |
| Wake phrase | Frase de activacion. En Phase 12 la garantia es `JARVIS`; `Hola JARVIS` queda como alias experimental. Nunca aprueba ni ejecuta. |
| `REAL` | Hay codigo ejecutable y evidencia concreta. |
| `PARCIAL` | Funciona una parte, falta integracion o producto completo. |
| `READINESS` | Contrato, preview, status, endpoint o mock sin ejecucion real completa. |
| `NO HECHO` | No encontrado como capacidad real en el repo auditado. |
| Manual validation | Prueba humana de flujo real, no solo unit tests o mocks. |
| Safe path | Ruta permitida por scope/policy, sin traversal, symlinks peligrosos, secretos ni zonas sensibles. |
| Audit metadata-only | Auditoria que guarda IDs, estado, riesgo, hashes o resumen seguro; no guarda secretos, audio bruto, frames ni contenido sensible completo. |
