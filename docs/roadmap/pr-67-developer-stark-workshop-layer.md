# PR #67 - Developer / Stark Workshop Layer

## 1. Proposito

Este documento define el contrato/backlog futuro para el Developer / Stark Workshop Layer de JARVIS: la capa orientada a construir software con David como socio tecnico, pair programmer, reviewer, planificador de PRs, asistente de IDE/terminal/PC, triage de errores, analista de codebase y preparador de deploys seguros.

Es exclusivamente documental. No implementa codigo, tests, scripts, runtime, endpoints, router, CI, requirements, sandbox real, IDE companion real, tool router real, CodeGraph real, watchers reales, cambios en `PolicyEngine`, cambios en `ApprovalGateway`, conexion MissionControl/Hermes ni APIs externas.

La decision central es:

```text
David puede construir software con JARVIS.
El modo developer no es un modo sin reglas.
JARVIS Gateway recibe.
Core Intelligence entiende y planifica.
PolicyEngine decide.
ApprovalGateway aprueba cuando aplica.
Restriction Registry explica limites.
Hermes, Codex, IDE, terminal, sandbox y CodeGraph ejecutan o informan solo dentro de scope aprobado.
Audit registra decisiones sin secretos.
```

El objetivo es fijar como JARVIS debe evolucionar hacia un "Stark Workshop" para desarrollo: una presencia tecnica que ayuda a pensar, planificar, revisar, estimar, buscar, probar, preparar PRs, explicar errores y operar herramientas de desarrollo sin saltarse seguridad, aprobacion, auditoria ni control humano.

## 2. Que problema resuelve

David trabaja con repos, PRs, errores, ideas de producto, documentacion, infra, dependencias, despliegues y herramientas locales. JARVIS debe poder ayudar como socio tecnico, no solo como chatbot:

- entender un repo.
- localizar donde tocar.
- convertir una idea en plan de implementacion.
- preparar prompts cerrados para Codex.
- revisar PRs.
- planificar tests.
- explicar errores.
- vigilar fallos y preparar triage.
- estimar coste, tiempo y riesgo.
- preparar rollback.
- generar playbooks reutilizables.
- conectar decisiones tecnicas con monetizacion y activos.

Pero estas capacidades son potentes porque pueden tocar filesystem, terminal, dependencias, secretos, cuentas, CI, deploys, produccion y reputacion. Por eso la capa developer debe nacer como contrato gobernado, no como bypass.

## 3. Definiciones

| Concepto | Significado | No debe hacer |
| --- | --- | --- |
| `Developer / Stark Workshop Layer` | Capa futura de JARVIS para desarrollo de software, arquitectura, debugging, PRs, review, IDE/terminal y builder copilot. | Ejecutar cambios, comandos o deploys sin policy/approval. |
| Asistencia de desarrollo | Leer, explicar, planificar, revisar, estimar y preparar artefactos tecnicos. | Producir side effects sin scope. |
| Ejecucion real | Cualquier accion que modifica archivos, corre comandos, instala dependencias, usa red, cambia cuentas o despliega. | Tratarse como "solo desarrollo" para bajar riesgo. |
| Sandbox futuro | Entorno aislado para ejecutar comandos o pruebas con limites de red, secretos, tiempo, coste y filesystem. | Acceder al host, secretos o produccion por defecto. |
| IDE companion futuro | Interfaz en editor/terminal para contexto, planes, diffs conceptuales, revisiones y aprobaciones. | Llamar Hermes directo o ejecutar comandos como puerta trasera. |
| Hermes capability | Tool/skill/runtime interno que JARVIS puede usar mediante control layer despues de policy. | Gobernar permisos o ampliar scope por su cuenta. |
| CodeGraph | Ayuda local/opcional de code intelligence para encontrar simbolos, dependencias e impacto. | Ser fuente de verdad, dependencia obligatoria o permiso operativo. |
| Prompt cerrado para Codex | Instruccion acotada con objetivo, alcance, prohibiciones, validacion y formato de respuesta. | Autorizar por si mismo cambios sensibles. |
| Project memory | Memoria aprobada del proyecto, decisiones, patrones y restricciones. | Ser permiso para escribir, ejecutar, instalar o desplegar. |

## 4. Fuera de alcance

PR #67 no crea ni activa:

- sandbox real.
- IDE companion real.
- terminal companion real.
- PC/Mac control real.
- screen reader real.
- OCR real.
- watchers reales.
- error monitoring real.
- CodeGraph real.
- semantic code search real.
- Hermes capability nueva.
- Codex integration nueva.
- deploy automation.
- code review automation.
- tool router.
- endpoints.
- runtime.
- tests.
- scripts.
- CI.
- requirements.
- cambios en `PolicyEngine`.
- cambios en `ApprovalGateway`.
- permisos nuevos.

Tampoco afirma que Developer / Stark Workshop Layer este implementado. Solo fija el contrato futuro.

## 5. Regla de seguridad no negociable

Ninguna superficie developer puede saltarse:

- `JARVIS Gateway`.
- Core Intelligence / Natural Runtime / Intent.
- `PolicyEngine`.
- `Restriction Registry`.
- `ApprovalGateway`.
- Capability Router futuro.
- HermesAdapter.
- Audit/Event Log.

Esto aplica a:

- IDE.
- terminal.
- Codex.
- Hermes.
- CodeGraph.
- sandbox.
- PC/Mac control.
- screen reading.
- OCR.
- mobile approvals.
- workers locales.
- watchers.
- deploy tools.
- GitHub/Git providers.
- CI/CD.
- external services.

El hecho de que una accion sea "de desarrollo" no la vuelve segura. Leer codigo no es lo mismo que ejecutar codigo. Preparar deploy no es desplegar. Proponer una dependencia no es instalarla. Generar un prompt para Codex no autoriza a Codex a ignorar policy.

## 6. Relacion con contratos existentes

### Core Intelligence

PR #66 define que Core Intelligence entiende intencion, planifica, selecciona herramientas, razona sobre consecuencias y entrega a policy. Developer / Stark Workshop Layer es una especializacion tecnica de ese nucleo.

Core Intelligence puede:

- entender el objetivo tecnico real.
- detectar ambiguedad.
- separar lectura, plan, escritura, ejecucion y deploy.
- preparar prompts cerrados.
- hacer contrarian review tecnico.
- estimar coste/tiempo/riesgo.
- elegir CodeGraph, Hermes, Codex o lectura directa como capacidades candidatas.

No puede convertir planificacion tecnica en permiso operativo.

### Personal Memory / User Model Layer

PR #65 define que memoria no es permiso. En desarrollo, project memory puede recordar:

- decisiones de arquitectura.
- estilo de PRs pequenas.
- comandos de validacion preferidos.
- riesgos conocidos.
- rutas importantes.
- restricciones de repo.
- criterio de David para calidad, monetizacion y velocidad.

Pero project memory no autoriza escribir archivos, leer secretos, ejecutar tests, instalar dependencias, modificar CI, hacer commit, abrir PR, mergear ni desplegar. Puede informar decisiones tecnicas; no puede aprobarlas.

### CodeGraph Evaluation

PR #60 define CodeGraph como ayuda local/opcional, no fuente de verdad. En esta capa, CodeGraph puede ayudar a:

- localizar simbolos.
- explorar dependencias.
- sugerir impacto.
- reducir lecturas repetidas.
- preparar prompts compactos.

Reglas:

- No auto-instalacion.
- No `.codegraph` en repo por defecto.
- No indexar secretos.
- No confiar ciegamente.
- Verificar contra codigo real con lectura directa y tests.
- Fallback a `rg`/read si falta, esta stale o genera duda.

### Hermes inside JARVIS

PR #56 fija que Hermes es runtime interno. En desarrollo, Hermes puede aportar tools, skills, terminal o capacidades de agente, pero solo mediante JARVIS:

```text
IDE / Terminal / Mobile / Voice
  -> JARVIS Gateway
  -> Core Intelligence / Intent
  -> PolicyEngine
  -> ApprovalGateway si aplica
  -> HermesAdapter / Codex / Sandbox / Worker solo dentro de scope
  -> Audit / response
```

Ninguna interfaz developer llama Hermes directo.

### Authorized Security Research / Bug Bounty Mode

Si una tarea developer se vuelve seguridad ofensiva, auditoria activa, bug bounty, scanner, exploit, credenciales, incidente de seguridad o target externo, debe enrutar a PR #64.

Ejemplos:

- revisar dependencias vulnerables de un repo propio puede ser developer/security defensivo.
- probar un endpoint externo requiere scope.
- escanear un dominio requiere autorizacion.
- explotar una vulnerabilidad requiere Bug Bounty Mode o laboratorio autorizado.

El modo Stark Workshop no es un hack-anything mode.

### Distributed Personal OS y Mobile Approval Center

PR #63 y PR #58 permiten presencia en movil, PC, IDE y otros dispositivos. En desarrollo:

- el movil puede pedir plan, revisar approval, cancelar o aprobar acciones con scope.
- el IDE puede mostrar contexto, diff conceptual, riesgos y validaciones.
- el PC puede ser worker local futuro.
- ningun cliente ejecuta acciones sensibles por si mismo.
- approvals moviles usan el mismo `ApprovalGateway`.
- deploys, dependencias, secretos y produccion requieren aprobacion fuerte aunque David lo diga por voz.

### Continuous Learning

Continuous Learning puede proponer mejoras de tooling, librerias, frameworks, prompts, playbooks o arquitectura developer.

Reglas:

- No auto-update.
- No instalacion automatica.
- No cambios opacos de prompt/persona.
- No modificar CI/requirements por novedad.
- Las mejoras deben convertirse en issue/plan/PR revisable, con tests y rollback cuando aplique.

### Money Engine / Asset Factory

Developer / Stark Workshop Layer debe ayudar a convertir trabajo tecnico en activos monetizables:

- MVPs.
- micro-SaaS.
- automatizaciones.
- templates.
- docs.
- internal tools.
- playbooks.
- pruebas de mercado.
- PRs pequenas que desbloquean valor.

Money Engine puede priorizar por ROI; Asset Factory puede preparar activos. Ninguno autoriza gasto, publicacion, deploy, uso de identidad, contratos, cambios en produccion ni shortcuts inseguros.

## 7. Capacidades acordadas

El Developer / Stark Workshop Layer futuro debe contemplar:

- pair programming por voz.
- code review automatico de PRs.
- watchers de errores.
- error watcher / incident triage.
- deploy por voz con doble confirmacion.
- sandbox execution contract.
- busqueda semantica de codebase.
- integracion futura con CodeGraph.
- control de PC/Mac por voz.
- lectura de pantalla.
- OCR y lectura de documentos.
- IDE / terminal companion.
- PR planning.
- prompt cerrado para Codex.
- test planning.
- rollback planning.
- impact analysis.
- dependency risk review.
- cost/time estimation.
- implementation plan generation.
- code/documentation refactor planning.
- reusable templates/playbooks for development.
- project memory use for engineering decisions.
- technical partner / builder copilot.

Todas estas capacidades son futuras salvo las piezas ya existentes en otros contratos. Este documento no implementa ninguna.

## 8. Categorias de actividad

| Categoria | Decision base | Descripcion |
| --- | --- | --- |
| `read_only_code_analysis` | `allowed` | Leer codigo/docs dentro de scope no sensible, explicar arquitectura, buscar referencias y resumir. |
| `documentation_planning` | `allowed` | Preparar contratos, READMEs, PRDs, checklists y docs sin side effects fuera del archivo aprobado. |
| `prompt_generation` | `allowed` | Generar prompt cerrado para Codex/Hermes/humano, con alcance, prohibiciones y validacion. |
| `test_planning` | `allowed` | Disenar estrategia de tests, casos, comandos sugeridos y criterios sin ejecutar. |
| `local_sandbox_execution_future` | `future_contract` | Ejecutar comandos en sandbox aislado con limites definidos. |
| `code_modification_future` | `requires_approval` | Escribir o modificar codigo/docs/config dentro de scope aprobado. |
| `PR_review_future` | `allowed` / `requires_approval` | Revisar diff read-only puede ser allowed; comentar, solicitar cambios o aprobar en GitHub requiere approval. |
| `deploy_prepare_only` | `allowed` | Preparar checklist, comandos, rollback y riesgos sin ejecutar deploy. |
| `deploy_to_staging` | `strong_approval` | Desplegar a staging con scope, revision y audit. |
| `deploy_to_production` | `strong_approval` | Produccion requiere confirmacion explicita reforzada, rollback y estado claro. |
| `dependency_change` | `strong_approval` | Instalar, actualizar, quitar o cambiar lockfiles/requirements/package manifests. |
| `secrets_or_env_access` | `strong_approval` / `denied` | Leer `.env`, tokens o secretos queda bloqueado por defecto salvo flujo seguro futuro. |
| `external_service_action` | `strong_approval` | GitHub writes, releases, cloud, CI, tickets, publicaciones o APIs externas con side effects. |
| `incident_response` | `requires_approval` / `strong_approval` | Triage puede preparar; contencion, cambios o produccion suben a strong. |
| `security_research_related` | `route_to_bug_bounty_mode` | Cualquier prueba activa, scanner, exploit, bug bounty o target externo usa PR #64. |

## 9. Approval esperado por accion

| Accion | Decision esperada | Regla |
| --- | --- | --- |
| Read-only code/docs analysis | `allowed` | Dentro de repo/scope permitido y sin secretos. |
| PR planning / prompt generation | `allowed` | Prepare-only, sin side effects. |
| Running tests | `requires_approval` o `allowed` segun modo futuro | Ejecucion de comandos; requiere scope, coste y entorno. |
| Writing files | `requires_approval` / `future_contract` | Scope de rutas, diff revisable y audit. |
| Dependency install/change | `strong_approval` | Explicar paquete, version, origen, riesgo, lockfile y rollback. |
| Reading `.env` / secrets | `strong_approval` / `denied` | Denied por defecto salvo flujo seguro disenado; preferir `.env.example` o nombres sin valores. |
| Deploy staging | `strong_approval` | Scope exacto, target, commit, rollback y audit. |
| Deploy production | `strong_approval` + confirmacion explicita | No por voz sola; requiere doble confirmacion y rollback. |
| Deleting files/branches | `strong_approval` | Especialmente si es irreversible o amplio. |
| External publication/release | `strong_approval` | Releases, posts, docs publicas, packages o uso de identidad. |
| Security testing | `route_to_bug_bounty_mode` | Scope, safe harbor y rules of engagement si aplica. |
| Code execution in sandbox | `future_contract` | Solo con limites de sandbox definidos y aprobados. |
| PC control | `requires_approval` / `strong_approval` | Sensible si toca archivos, apps, cuentas, credenciales o acciones externas. |

## 10. Reglas de seguridad

- No tool execution without policy.
- No direct Hermes calls from IDE, terminal, mobile, worker or PC control.
- No reading secrets by default.
- No logging secrets.
- No dependency install without explicit approval.
- No deploy without strong approval.
- No production changes by voice alone.
- No destructive git commands without strong approval.
- No auto-merge without explicit approval.
- No automatic code execution outside sandbox.
- No agent config changes without approval.
- CodeGraph optional/local, not source of truth.
- Tests/review remain required.
- `denied` never reaches worker, tool, Hermes, Codex, sandbox or connector.
- Active memory cannot downgrade risk.
- Project memory can inform but not authorize.
- IDE/terminal/mobile are interfaces, not authority.
- A prompt closed for Codex constrains work; it does not bypass JARVIS policy.
- Logs, reports and PR summaries must redact tokens, passwords, cookies, private keys and `.env` values.
- External calls require explicit scope, destination and data handling.

## 11. Sandbox futuro

Una futura sandbox de desarrollo debe ser un contrato de ejecucion aislada, no una excusa para ejecutar cualquier cosa.

Debe incluir:

- aislamiento del host.
- sin secretos por defecto.
- red restringida por defecto.
- limites de tiempo.
- limites de coste.
- limites de CPU/memoria si aplica.
- scope de filesystem.
- artefactos revisables antes de moverlos al host.
- allowlist/denylist de comandos.
- audit log.
- cleanup al terminar.
- sin credenciales de produccion.
- sin acceso destructivo al host.
- aprobacion explicita antes de llamadas externas.
- salida resumida sin secretos.
- cancel/pause/timeout visible para David.

Reglas:

- Sandbox no puede montar `$HOME` completo por defecto.
- Sandbox no puede leer `.env` salvo flujo seguro futuro.
- Sandbox no puede instalar dependencias globales en el host.
- Sandbox no puede hacer deploy.
- Sandbox no puede escribir fuera de su workspace permitido.
- Pasar en sandbox no sustituye review ni tests relevantes en entorno real cuando aplique.

## 12. Developer workflow conceptual

1. David describes goal.
2. JARVIS clarifies intent/risk.
3. JARVIS uses approved project memory and code intelligence.
4. JARVIS prepares plan.
5. JARVIS asks approval for write/execute/deploy if needed.
6. Codex/Hermes/tools operate only inside approved scope.
7. Tests and checks are run if approved.
8. JARVIS summarizes diff, risks, validation.
9. PR is created only when instructed.
10. Merge/deploy requires explicit approval.

## 13. Ejemplos conceptuales

| Solicitud | Decision | Respuesta esperada |
| --- | --- | --- |
| "Explicame este repo." | `allowed` | Leer docs/codigo permitido, resumir arquitectura, riesgos y zonas clave sin ejecutar nada. |
| "Prepara una PR para X." | `prepare_only` / `requires_approval` | Preparar plan y prompt cerrado; escribir archivos requiere approval; commit/push/PR real requiere instruccion explicita. |
| "Escribe tests para este archivo." | `requires_approval` | Proponer casos y diff; editar archivos solo dentro de scope aprobado. |
| "Ejecuta pytest." | `requires_approval` | Explicar comando, alcance, coste/tiempo y entorno; ejecutar solo si policy/mode lo permite. |
| "Instala esta dependencia." | `strong_approval` | Explicar paquete, version, origen, riesgo, lockfile, alternativa y rollback antes de instalar. |
| "Lee mi .env para configurar esto." | `denied` / `strong_approval` futuro | Bloquear por defecto; proponer revisar `.env.example`, nombres de variables o flujo seguro sin valores. |
| "Haz deploy a staging." | `strong_approval` | Preparar checklist, target, commit y rollback; ejecutar solo con approval fuerte. |
| "Haz deploy a produccion." | `strong_approval` | Requiere doble confirmacion explicita, estado de checks, rollback y no por voz sola. |
| "Revisa este PR antes de mergear." | `allowed` / `requires_approval` | Review read-only permitido; comentar/aprobar/mergear requiere approval segun accion. |
| "Usa CodeGraph para encontrar donde tocar." | `future_contract` / `allowed` si ya existe aprobado | Usarlo solo si esta instalado/aprobado; verificar contra codigo real; fallback a `rg`/read. |
| "Corrige el error de produccion." | `requires_approval` / `strong_approval` | Triage prepare-only; cambios, comandos, deploy o contencion requieren approval fuerte. |
| "Haz esto desde el movil." | `allowed` / `requires_approval` / `strong_approval` segun accion | Movil es interfaz; approvals pasan por `ApprovalGateway`; no ejecuta directo ni baja riesgo. |
| "Escanea este dominio para fallos." | `route_to_bug_bounty_mode` | Pedir scope, autorizacion y rules of engagement; sin eso, prepare-only o denied. |
| "Borra esta rama y limpia archivos viejos." | `strong_approval` | Mostrar impacto, backups/rollback y confirmacion exacta antes de borrar. |
| "Genera un prompt cerrado para Codex." | `allowed` | Crear objetivo, alcance, prohibiciones, validacion y formato sin ejecutar. |

## 14. Anti-patterns

- IDE/terminal como bypass de policy.
- "Developer mode" como modo sin reglas.
- Autoejecutar comandos destructivos.
- Leer secretos para ahorrar tiempo.
- Instalar dependencias por moda.
- Mergear sin checks.
- Desplegar por voz sin confirmacion fuerte.
- Confiar ciegamente en CodeGraph.
- Usar memoria de proyecto como permiso.
- Modificar CI/requirements sin aprobacion.
- Logs con tokens.
- Agentes paralelos tocando el mismo archivo sin coordinacion.
- Prometer que algo funciona sin tests.
- Tratar "solo es staging" como permiso implicito.
- Usar un prompt cerrado como sustituto de approval.
- Hacer que Codex/Hermes actuen fuera del scope aprobado.
- Ocultar validaciones no ejecutadas.
- Confundir preparar rollback con tener rollback probado.

## 15. Outputs esperados

Una mision developer futura deberia producir salidas claras:

- objetivo entendido.
- supuestos y dudas.
- categoria de actividad.
- decision de policy esperada.
- scope de archivos/rutas.
- plan de implementacion.
- plan de tests.
- riesgos.
- impacto probable.
- dependencias afectadas.
- coste/tiempo estimado.
- rollback plan.
- prompts cerrados si se delega a Codex/Hermes.
- resumen de diff si hubo cambios.
- validacion ejecutada.
- validacion no ejecutada.
- aprobaciones usadas.
- siguientes pasos.

No debe decir "funciona" si no se ejecuto la validacion relevante.

## 16. Criterios de aceptacion para futura implementacion

Una implementacion futura del Developer / Stark Workshop Layer solo debe aceptarse si:

- Activity categories map to policy decisions.
- Sandbox boundaries are documented and tested.
- No secrets in logs.
- Deploy requires strong approval.
- Dependency changes require strong approval.
- Project memory use is auditable.
- CodeGraph use is optional and verified.
- Tests/checks are first-class outputs.
- PR summary includes files, risks, validation and validation not run.
- Mobile developer approvals use the same `ApprovalGateway`.
- Future tests cover `allowed`, `requires_approval`, `strong_approval`, `denied` and `future_contract`.
- David can cancel/pause long developer missions.
- Documentation is clear for David.
- IDE/terminal clients cannot call Hermes direct.
- `denied` requests never reach worker/tool/Hermes.
- Active memory cannot downgrade risk.
- Production deploy needs explicit strengthened confirmation.
- Dependency risk review exists before install/change.
- Sandbox never receives production credentials by default.
- Code execution outside sandbox is explicitly approved and scoped.

## 17. Estado de este PR

Este PR solo crea el contrato documental.

No implementa Developer / Stark Workshop Layer, sandbox, IDE companion, terminal companion, CodeGraph integration, watchers, PC control, deploy automation, code review automation, Hermes capability, Codex connector, tool router, runtime, tests, scripts, endpoints, CI ni requirements.
