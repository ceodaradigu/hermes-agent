# PR #69 - Mission Autonomy / Self-Improvement / Revenue Execution Contract

## 1. Proposito

Este documento define el contrato/backlog futuro para que JARVIS pueda recibir misiones con objetivo, operar por bloques aprobados, mejorar resultados genericos, evaluar herramientas externas, crear activos de negocio y perseguir objetivos de ingresos con supervision, limites, auditoria y metricas.

Es exclusivamente documental. No implementa codigo, tests, scripts, runtime, endpoints, router, CI, requirements, Mission Envelope real, planner real, tool adoption real, Money Engine real, Asset Factory real, cambios en `PolicyEngine`, cambios en `ApprovalGateway`, conexion MissionControl/Hermes ni APIs externas.

La decision central es:

```text
David puede dar una mision.
JARVIS puede planificar, preparar, mejorar, medir e iterar.
JARVIS opera solo dentro de un Mission Envelope aprobado.
PolicyEngine decide.
ApprovalGateway aprueba cuando aplica.
Restriction Registry explica limites.
Audit registra objetivo, acciones, costes, approvals y resultados.
JARVIS maximiza probabilidad; no promete ingresos garantizados.
```

El objetivo es cerrar la fase documental general antes de empezar implementacion: JARVIS debe poder evolucionar hacia un operador emprendedor supervisado, no quedarse en "sugerir ideas" ni convertirse en un sistema sin control.

## 2. Fuera de alcance

PR #69 no crea ni activa:

- Mission Envelope real.
- Mission planner real.
- tool adoption pipeline real.
- Open Design instalado o ejecutado.
- CodeGraph instalado o ejecutado.
- Money Engine real.
- Asset Factory real.
- revenue execution runtime.
- landing/deck/funnel generator real.
- endpoints.
- router.
- runtime.
- tests.
- scripts.
- CI.
- requirements.
- deploy.
- checkout/pagos.
- emails reales.
- publicaciones reales.
- gastos reales.
- cambios en `PolicyEngine`.
- cambios en `ApprovalGateway`.
- conexion MissionControl/Hermes.

Tampoco afirma que Mission Autonomy, Self-Improvement o Revenue Execution esten implementados. Solo fija el contrato futuro.

## 3. Definiciones

| Concepto | Significado | Regla |
| --- | --- | --- |
| `task` | Unidad pequena de trabajo con resultado acotado. | Puede formar parte de una mision; no implica autonomia amplia. |
| `mission` | Trabajo orientado a un objetivo medible, con limites, canales, herramientas, presupuesto, reporting y stop conditions. | Requiere Mission Envelope antes de operar. |
| `objective` | Resultado deseado expresado en lenguaje humano. | Debe traducirse a metricas y limites. |
| `success_metric` | Criterio observable para decidir si la mision avanza o cumple. | No debe ser ambiguo. |
| `experiment` | Prueba acotada para reducir incertidumbre. | Debe declarar hipotesis, coste, plazo, medicion y decision siguiente. |
| `asset` | Entregable reutilizable o monetizable: web, landing, deck, email sequence, script, prototype, offer, prompt, brief, funnel o documento. | Puede prepararse; publicar o vender requiere policy/approval. |
| `tool` | Capacidad interna o externa que puede ayudar a producir, medir, analizar o ejecutar. | No se adopta silenciosamente como dependencia core. |
| `approval` | Consentimiento explicito de David con scope, duracion, coste maximo, rollback y auditoria. | No existe "approve all forever". |
| `execution` | Accion con side effects: escribir, correr comandos, instalar, publicar, contactar, gastar, desplegar o tocar datos. | Pasa por `PolicyEngine` y `ApprovalGateway` cuando aplique. |

## 4. Sugerir vs operar

Sugerir significa:

- pensar.
- comparar.
- explicar.
- preparar borradores.
- crear planes.
- estimar ROI.
- listar riesgos.
- proponer herramientas.
- recomendar siguiente accion.

Operar significa:

- modificar archivos.
- ejecutar comandos.
- instalar dependencias.
- lanzar servidores, daemons o docker.
- contactar personas.
- publicar.
- gastar dinero.
- usar identidad de David.
- desplegar.
- crear pagos o checkout.
- tocar produccion.

JARVIS puede sugerir dentro de un scope amplio de bajo riesgo. JARVIS solo puede operar dentro de un Mission Envelope aprobado y despues de policy/approval cuando la accion lo requiera.

## 5. Microaccion vs Mission Envelope

Autonomia por microaccion significa pedir permiso para cada paso pequeno. Es segura pero puede volver inutil una mision larga: David no quiere aprobar cada busqueda, comparativa, borrador o variante si ya aprobo un marco claro.

Autonomia por Mission Envelope significa que David aprueba un marco con objetivo, limites, presupuesto, herramientas, canales, acciones permitidas, acciones que requieren approval, stop conditions y reporting. Dentro de ese marco, JARVIS puede avanzar sin pedir permiso para cada microaccion de bajo riesgo.

Regla:

- No pedir permiso para cada microaccion si existe un marco aprobado y la accion esta dentro de `allowed_actions`.
- Pedir aprobacion si la accion entra en `requires_approval_actions`.
- Pedir aprobacion fuerte si entra en `strong_approval_actions`.
- Bloquear si entra en `denied_actions`, hard boundary o fuera de scope sin alternativa segura.

Esto mantiene velocidad sin convertir autonomia en ausencia de control.

## 6. Riesgo real siempre requiere aprobacion

JARVIS debe pedir aprobacion cuando existe riesgo real:

- coste economico.
- reputacion.
- identidad publica.
- datos sensibles.
- secretos.
- contacto externo.
- publicacion.
- produccion.
- contratos.
- acciones irreversibles.
- instalacion o ejecucion de software no evaluado.
- permisos de red, daemon, docker o puertos.

Un Mission Envelope reduce friccion operativa, no elimina `PolicyEngine`, `ApprovalGateway`, Restriction Registry, hard boundaries ni auditoria.

## 7. Ingresos medibles vs ingresos garantizados

"Genera 1000 euros limpios este mes" es un objetivo medible. No es un ingreso garantizado.

JARVIS puede:

- convertir el objetivo en hipotesis, ofertas, assets, canales, experimentos y metricas.
- estimar probabilidad, esfuerzo, coste y ROI esperado.
- preparar activos y campanas.
- medir senales.
- iterar hacia la siguiente mejor accion.
- separar revenue confirmado de revenue proyectado.

JARVIS no puede:

- prometer ingresos garantizados.
- afirmar ventas no confirmadas.
- ocultar incertidumbre.
- tratar proyecciones como dinero real.
- gastar, publicar, contactar o cobrar sin approval.

La obligacion futura de JARVIS sera maximizar la probabilidad de alcanzar el objetivo dentro de limites aprobados, no prometer resultados que dependen del mercado.

## 8. Relacion con contratos existentes

### Core Intelligence

PR #66 define que Core Intelligence entiende intencion, planifica, selecciona herramientas y razona sobre consecuencias. Mission Autonomy usa ese nucleo para convertir "crea una web y mejorala" o "este mes genera 1000 euros limpios" en mision, hipotesis, plan, riesgos, herramientas candidatas y metricas.

Core Intelligence no autoriza acciones. Entrega intencion, plan y riesgo a `PolicyEngine`.

### Personal Memory / User Model Layer

PR #65 define que memoria no es permiso. Mission Autonomy puede usar memoria aprobada para conocer estilo, objetivos, preferencias, nichos, ideas descartadas, tolerancia al riesgo y criterios de calidad de David.

Memoria puede orientar prioridades y tono. No autoriza gasto, identidad, publicacion, contacto, deploy, instalacion ni acceso a datos.

### Developer / Stark Workshop Layer

PR #67 define el modo tecnico para construir software. Mission Autonomy puede crear misiones developer: landing, micro-SaaS, prototype, automation, PR planning, code review, tool spike o deploy prepare-only.

El modo developer no baja riesgo: comandos, instalaciones, docker, deploy, produccion y secrets siguen requiriendo approvals.

### Personal Knowledge / RAG Layer

PR #68 define que documentos y RAG no son permiso. Mission Autonomy puede usar conocimiento aprobado para briefs, propuestas, research, ofertas y assets con fuentes.

Si una fuente documental sugiere una accion, esa accion sigue pasando por policy/approval. RAG ayuda a preparar contexto, no a ejecutar.

### CodeGraph Evaluation

PR #60 define CodeGraph como herramienta local/opcional candidata para Code Intelligence. Mission Autonomy puede proponer CodeGraph para entender codigo, reducir tool calls, tiempo o tokens, y preparar un spike.

Reglas:

- no instalar ni ejecutar sin aprobacion.
- `.codegraph` fuera del repo.
- medir reduccion real de tool calls, tiempo y tokens.
- no sustituye tests, revision humana ni codigo real.
- no se convierte en dependencia core por defecto.

### Open Design candidato futuro

Open Design puede ser una herramienta candidata para Design Artifact Studio: landing pages, decks, dashboards, prototypes y marketing assets. Debe tratarse como herramienta externa no adoptada.

Reglas:

- local-first/open-source candidate si su licencia y arquitectura lo permiten.
- no instalar sin aprobacion.
- no ejecutar daemon sin aprobacion.
- no permitir Write/Bash/WebFetch sin policy/sandbox.
- no usar como runtime dependency por defecto.
- evaluar en spike separado.
- medir calidad de outputs, tiempo, coste, riesgos y reversibilidad.

### Money Engine / Asset Factory

Mission Autonomy es la capa que convierte objetivos en trabajo supervisado. Money Engine futuro prioriza oportunidades, coste, ROI y metricas. Asset Factory futura crea activos: landing, offers, decks, emails, funnels, scripts, prompts, briefs y prototypes.

Ninguna de estas capas mueve dinero, publica, contacta clientes, usa identidad ni crea pagos sin approval fuerte.

### PolicyEngine, ApprovalGateway, Restriction Registry y auditoria

`PolicyEngine` decide permiso operativo. `ApprovalGateway` gestiona aprobaciones. Restriction Registry explica limites y hard boundaries. Audit registra objetivo, acciones, approvals, costes, resultados, errores y rollback.

Mission Autonomy no es un bypass. Es un contrato para operar mas tiempo dentro de limites claros.

## 9. Mission Envelope

Un Mission Envelope futuro debe declarar como minimo:

| Campo | Significado |
| --- | --- |
| `mission_id` | Identificador estable y auditable. |
| `objective` | Resultado deseado en lenguaje humano. |
| `success_metric` | Medida concreta de avance o exito. |
| `net_target` | Objetivo neto opcional, especialmente para revenue missions. |
| `deadline` | Fecha o ventana temporal. |
| `budget_limit` | Presupuesto total maximo autorizado. |
| `cost_limit_per_action` | Coste maximo por accion antes de pedir approval. |
| `allowed_actions` | Acciones que JARVIS puede realizar dentro del envelope. |
| `requires_approval_actions` | Acciones que requieren approval normal antes de ejecutar. |
| `strong_approval_actions` | Acciones fuertes que requieren confirmacion reforzada. |
| `denied_actions` | Acciones prohibidas aunque parezcan utiles. |
| `allowed_tools` | Herramientas ya aprobadas para esa mision. |
| `candidate_tools` | Herramientas que se pueden investigar/proponer, no usar todavia. |
| `channels` | Canales permitidos: local, docs, web research, email prepare-only, landing, ads prepare-only, etc. |
| `identity_use_policy` | Como se puede o no usar la identidad de David. |
| `publication_policy` | Que puede prepararse, publicar como borrador o publicar realmente. |
| `spending_policy` | Moneda, presupuesto, proveedores, limites y approval requerido. |
| `external_contact_policy` | Si se permite preparar, revisar o enviar mensajes externos. |
| `data_access_scope` | Fuentes, repos, docs o datos permitidos. |
| `install_dependency_policy` | Si se permite proponer, instalar o ejecutar dependencias. |
| `runtime_execution_policy` | Comandos, daemons, servers, docker, red, puertos y sandbox. |
| `reporting_frequency` | Cada cuanto debe reportar progreso, coste, riesgo y siguiente accion. |
| `stop_conditions` | Condiciones que obligan a parar o pedir decision. |
| `rollback_plan` | Como revertir cambios, gastos, publicaciones, installs o artefactos. |
| `audit_requirements` | Eventos y datos que deben registrarse sin secretos. |

Ejemplo conceptual:

```json
{
  "mission_id": "mission_...",
  "objective": "Crear y mejorar una landing para vender X",
  "success_metric": "landing publicada como borrador revisable y 3 variantes comparadas",
  "net_target": null,
  "deadline": "2026-06-15",
  "budget_limit": 0,
  "cost_limit_per_action": 0,
  "allowed_actions": ["research", "draft", "variant_generation", "quality_review"],
  "requires_approval_actions": ["file_write", "local_tool_use"],
  "strong_approval_actions": ["deploy", "spend_money", "public_identity_use"],
  "denied_actions": ["spam", "misrepresentation", "hidden_actions"],
  "allowed_tools": ["approved_local_editor"],
  "candidate_tools": ["Open Design"],
  "channels": ["local", "docs"],
  "identity_use_policy": "draft_only",
  "publication_policy": "prepare_only",
  "spending_policy": "no_spend",
  "external_contact_policy": "prepare_only",
  "data_access_scope": ["project_docs"],
  "install_dependency_policy": "propose_only",
  "runtime_execution_policy": "no_daemon_no_docker_no_ports",
  "reporting_frequency": "daily_or_on_blocker",
  "stop_conditions": ["risk_increase", "approval_needed", "cost_exceeds_expected_value"],
  "rollback_plan": "revert generated files and document discarded variants",
  "audit_requirements": ["objective", "actions", "approvals", "costs", "results"]
}
```

## 10. Tipos de mision

Tipos futuros soportados por contrato:

- `build_asset`.
- `improve_existing_asset`.
- `revenue_mission`.
- `tool_adoption_mission`.
- `research_mission`.
- `marketing_experiment`.
- `product_validation`.
- `lead_generation`.
- `content_to_product_loop`.
- `website_creation`.
- `landing_page_optimization`.
- `offer_creation`.
- `client_outreach_prepare_only`.
- `business_metric_monitoring`.
- `self_improvement_mission`.
- `developer_mission`.

Cada tipo puede compartir el mismo Mission Envelope, pero con defaults distintos de riesgo, metricas, canales, approvals y stop conditions.

## 11. Capacidades acordadas

JARVIS futuro debe poder:

- convertir "crea una web" en algo util, especifico y alineado con objetivo, no generico.
- detectar si un resultado parece generico y buscar como mejorarlo.
- proponer herramientas externas como Open Design.
- proponer CodeGraph para entender codigo.
- crear landing pages, assets, decks, emails, funnels, scripts, prompts, briefs y prototypes.
- crear variantes y compararlas.
- medir calidad, coste, tiempo y ROI esperado.
- preparar campanas y ofertas.
- proponer instalacion o evaluacion de herramientas.
- operar misiones largas con status visible.
- iterar sobre resultados.
- pedir approval por bloques.
- parar si hay riesgo, coste excesivo o falta de evidencia.
- reportar progreso y proximos pasos.

Estas capacidades son futuras. Este PR no las implementa.

## 12. Tool Adoption Pipeline

Una herramienta externa futura debe pasar por este pipeline antes de adoptarse:

1. Discover tool.
2. Explain why it may help.
3. Check license.
4. Check repo health.
5. Check dependencies.
6. Check runtime requirements.
7. Check security risks.
8. Check privacy/data flow.
9. Check local/sandbox feasibility.
10. Propose spike.
11. Ask approval.
12. Install only in approved sandbox/worktree.
13. Measure value.
14. Compare baseline.
15. Keep/rollback decision.
16. Document result.
17. Never silently adopt as core dependency.

Tool adoption no es un permiso para saltarse seguridad. Si una herramienta pide permisos excesivos, secretos, red amplia, daemon persistente, Write/Bash/WebFetch sin sandbox o cambios globales, JARVIS debe parar y pedir decision.

## 13. Open Design como ejemplo explicito

Open Design puede evaluarse como candidata futura para Design Artifact Studio.

Podria ayudar en:

- landing pages.
- decks.
- dashboards.
- prototypes.
- marketing assets.
- comparacion visual de variantes.

Contrato:

- tratarla como local-first/open-source candidate solo tras revisar licencia, repo, dependencias, runtime y flujo de datos.
- no instalar sin aprobacion explicita.
- no ejecutar daemon sin aprobacion explicita.
- no permitir Write/Bash/WebFetch sin policy y sandbox.
- no usar como runtime dependency por defecto.
- evaluar en spike separado.
- medir calidad de outputs, tiempo, coste, riesgos y reversibilidad.
- documentar keep/rollback.

Decision base: `candidate_tool`, no `allowed_tool`.

## 14. CodeGraph como ejemplo explicito

CodeGraph puede evaluarse como candidata futura para Code Intelligence.

Contrato:

- usar solo bajo el contrato de PR #60.
- no instalar ni ejecutar sin aprobacion.
- no crear `.codegraph` en el repo.
- mantener `.codegraph` fuera del repo si un spike futuro la crea.
- medir reduccion real de tool calls, tiempo y tokens.
- verificar contra codigo real.
- no sustituir tests, revision humana ni lectura directa.
- no convertirlo en dependencia obligatoria.

Decision base: `candidate_tool`, no `allowed_tool`.

## 15. Revenue Mission

Una revenue mission futura debe declarar:

| Campo | Significado |
| --- | --- |
| `economic_objective` | Objetivo economico en lenguaje humano. |
| `net_target` | Objetivo limpio despues de gastos. |
| `gross_target` | Ingreso bruto objetivo. |
| `deadline` | Fecha limite. |
| `budget` | Gasto maximo aprobado. |
| `expected_ROI` | Retorno esperado con supuestos. |
| `channels` | Canales: inbound, outbound prepare-only, marketplace, content, ads prepare-only, etc. |
| `offer` | Oferta concreta. |
| `assets_needed` | Landing, deck, emails, demo, checkout draft, scripts, lead magnet. |
| `pricing` | Precio o rangos propuestos. |
| `funnel` | Pasos desde trafico hasta conversion. |
| `traffic_source` | Fuente de leads o visitas. |
| `conversion_assumptions` | Supuestos explicitos de conversion. |
| `experiment_plan` | Hipotesis, pasos, metrica, decision siguiente. |
| `daily_weekly_reporting` | Cadencia de reporte. |
| `revenue_confirmed` | Ingreso cobrado o confirmado. |
| `revenue_projected` | Ingreso esperado o estimado. |
| `expenses` | Gastos reales y proyectados. |
| `net_result` | Resultado neto confirmado. |
| `uncertainty` | Nivel de incertidumbre y razones. |
| `next_iteration` | Siguiente experimento o ajuste. |
| `stop_loss_limit` | Punto de parada por coste, tiempo o senal baja. |

Revenue confirmado y revenue proyectado deben estar separados siempre.

## 16. Acciones por nivel

### Allowed

- investigar.
- resumir.
- crear borradores.
- generar variantes.
- preparar assets.
- crear planes.
- comparar herramientas.
- preparar mensajes.
- estimar ROI.
- organizar tareas.
- reportar progreso.

### Requires approval

- escribir archivos.
- crear ramas/PRs.
- ejecutar comandos seguros.
- usar herramientas locales aprobadas.
- contactar personas si el texto esta aprobado.
- publicar borradores no sensibles.
- iniciar spike de herramienta.
- acceder a datos de proyecto.

### Strong approval

- instalar dependencias.
- ejecutar docker/daemon/server.
- gastar dinero.
- abrir puertos.
- usar identidad de David publicamente.
- enviar emails/mensajes externos.
- publicar contenido comercial.
- crear pagos/checkout.
- desplegar.
- firmar/aceptar contratos.
- tocar produccion.
- usar datos sensibles.
- cambios destructivos.

### Denied

- spam.
- engano.
- suplantacion.
- scraping abusivo o ilegal.
- usar credenciales/secretos sin flujo seguro.
- contratos/pagos sin aprobacion.
- prometer ingresos garantizados.
- ocultar acciones.
- evadir limites.
- acciones fuera de scope.
- hack-anything mode.

## 17. Approval por bloques

David puede aprobar un marco de mision. JARVIS opera dentro de ese marco.

Reglas:

- Si aparece una accion fuera de scope, JARVIS pide aprobacion.
- Cada aprobacion debe tener scope, duracion, coste maximo y rollback.
- No hay "approve all forever".
- No hay "haz todo lo necesario" sin limites.
- Approvals vagos deben convertirse en Mission Envelope concreto.
- Mobile approvals siguen el mismo `ApprovalGateway`.
- Una aprobacion expirada no se renueva sola.
- Una aprobacion para preparar no autoriza publicar.
- Una aprobacion para investigar no autoriza instalar.
- Una aprobacion para crear draft no autoriza usar identidad de David.

## 18. Self-Improvement

JARVIS puede detectar limitaciones propias:

- falta de herramienta.
- output generico.
- exceso de tool calls.
- baja calidad visual.
- falta de contexto.
- prompt debil.
- workflow repetitivo.
- coste alto.
- baja conversion.

Puede proponer:

- herramientas.
- skills.
- prompts.
- docs.
- cambios de codigo futuros.
- planes de mejora.
- PRs futuras.
- metricas para medir valor.

No puede:

- auto-modificar runtime sin PR, checks y approval.
- auto-merge.
- auto-deploy.
- relajar `PolicyEngine`.
- cambiar hard boundaries.
- instalar o activar herramientas privilegiadas sin aprobacion.
- ocultar que una mejora fallo.
- convertir self-improvement en cambios silenciosos de personalidad, seguridad o permisos.

## 19. Metricas

Metricas futuras obligatorias o candidatas:

- `revenue_confirmed`.
- `revenue_projected`.
- `gross_revenue`.
- `net_revenue`.
- `expenses`.
- `time_spent`.
- `cost_per_session`.
- `tool_cost`.
- `conversion_rate`.
- `response_rate`.
- `leads_created`.
- `assets_created`.
- `experiments_run`.
- `confidence`.
- `risk_level`.
- `ROI_expected`.
- `ROI_actual`.
- `next_best_action`.

Las metricas deben distinguir dato confirmado, estimacion, proyeccion, supuesto e incertidumbre.

## 20. Stop conditions

JARVIS debe parar, pedir decision o degradar a safe alternative si aparece:

- presupuesto agotado.
- riesgo legal.
- riesgo reputacional.
- datos sensibles no autorizados.
- baja confianza en una accion irreversible.
- mercado no responde tras limite definido.
- herramienta exige permisos excesivos.
- dependencia sospechosa.
- coste supera beneficio esperado.
- David no aprueba accion fuerte.
- cambio requiere secreto/credencial.
- se detecta spam/engano.
- hard boundary.

Una stop condition gana sobre mision, memoria, modo, urgencia, revenue target o approval anterior.

## 21. Ejemplos conceptuales

| Solicitud | Decision esperada | Respuesta segura |
| --- | --- | --- |
| "Crea una web para vender X." | `requires_approval` para escribir archivos; `allowed` para plan/brief/estructura. | Preparar estrategia, copy, estructura, variantes y pedir scope para crear archivos. |
| "La web parece generica, mejorala." | `allowed` para evaluar y proponer; `requires_approval` para editar. | Auditar diferenciacion, oferta, visual, pruebas sociales, CTA y variantes. |
| "Evalua Open Design para mejorar esta landing." | `allowed` research/compare; `requires_approval` para spike; `strong_approval` para install/daemon. | Revisar licencia, repo, runtime, riesgos y proponer spike. |
| "Instala Open Design para este proyecto." | `strong_approval`. | Pedir scope, worktree/sandbox, comandos, coste, rollback y confirmar que no sera dependency core. |
| "Este mes tienes que generar 1000 euros limpios." | `future_contract` / revenue mission; no garantia. | Crear Mission Envelope con net target, oferta, canales, presupuesto, experimentos y reporting. |
| "Crea 3 ofertas y elige la mejor." | `allowed`. | Generar ofertas, comparar por ROI, esfuerzo, riesgo, evidencia y canal. |
| "Prepara emails para potenciales clientes." | `allowed` / `prepare_only`. | Redactar emails y lista de criterios; no enviar. |
| "Envia esos emails." | `strong_approval`. | Mostrar destinatarios, texto exacto, identidad, canal, limite y rollback/cancelacion si existe. |
| "Crea checkout de pago." | `strong_approval` / `future_contract`. | Preparar requisitos, copy y flujo; no crear pagos reales sin approval. |
| "Haz deploy." | `strong_approval`. | Pedir proyecto, entorno, commit, dominio, rollback y confirmacion reforzada. |
| "Gasta 50 euros en ads." | `strong_approval`. | Pedir plataforma, moneda, presupuesto, campaña, stop-loss, audience, creatividad y reporting. |
| "Haz lo que haga falta sin preguntarme." | `denied` como permiso vago. | Convertir en Mission Envelope concreto con limites y approvals por nivel. |
| "Auto-mejorate para hacerlo mejor." | `allowed` para diagnostico/propuesta; `requires_approval` o `strong_approval` para cambios. | Crear plan de mejora, metricas y PR futura; no auto-modificar runtime. |

## 22. Anti-patterns

- mision sin limites.
- objetivo economico tratado como garantia.
- pedir permiso por cada microaccion.
- aprobar todo para siempre.
- instalar herramientas por moda.
- usar tool adoption para saltarse seguridad.
- publicar sin revision.
- gastar sin presupuesto.
- contactar clientes sin aprobacion.
- usar identidad de David sin approval.
- prometer resultados falsos.
- ocultar fallos.
- esconder costes.
- auto-mejora silenciosa.
- cambiar policy para avanzar mas rapido.
- confundir autonomia con ausencia de control.

## 23. Criterios de aceptacion para futura implementacion

Una implementacion futura no debe considerarse aceptable hasta que:

- Mission Envelope existe y es validable.
- approvals por bloque tienen scope, duracion y coste.
- revenue missions separan confirmado/proyectado.
- tool adoption requiere evaluacion y approval.
- install, daemon, docker, deploy, spend y contact requieren strong approval.
- reporting visible.
- stop conditions probadas.
- audit registra objetivo, acciones, approvals, costes, resultados y rollback.
- no secrets in logs.
- no auto-merge, auto-deploy ni self-modification.
- future tests cubren `allowed`, `requires_approval`, `strong`, `denied`, `stop_condition`, `tool_adoption` y `revenue_projection`.
- documentacion clara para David.
- este documento marca el cierre de la fase documental general antes de iniciar PRs de codigo.

## 24. Transition to implementation

Despues de PR #69, la siguiente PR recomendada debe ser codigo.

Siguiente PR recomendada:

```text
PR #70 - Mission Envelope v1
```

PR #70 debe ser la primera implementation PR de esta nueva fase. No debe seguir ampliandose el backlog general salvo necesidad concreta. Nuevas ideas deben entrar como misiones, spikes o envelopes acotados, no como arquitectura infinita.

## 25. Estado de este PR

Este PR solo crea el contrato/backlog documental de Mission Autonomy / Self-Improvement / Revenue Execution.

No implementa Mission Envelope, planner, tool adoption, revenue execution, Open Design, CodeGraph, Money Engine, Asset Factory, runtime, endpoints, tests, scripts ni conexiones reales con Hermes/MissionControl.
