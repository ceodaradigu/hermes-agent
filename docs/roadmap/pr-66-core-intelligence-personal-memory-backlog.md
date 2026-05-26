# PR #66 - Core Intelligence and Personal Memory Backlog

## 1. Proposito

Este documento define el contrato/backlog futuro para el Core Intelligence Layer de JARVIS: el nucleo inteligente que entiende intencion real, decide que hacer, planifica, elige herramientas, razona sobre consecuencias, explica decisiones, mantiene identidad/persona estable y usa memoria aprobada sin convertirla en permiso.

Es exclusivamente documental. No implementa codigo, tests, scripts, runtime, endpoints, router, CI, requirements, memoria real, planner real, tool router real, prompt manager real, scheduler, cambios en `PolicyEngine`, cambios en `ApprovalGateway`, conexion MissionControl/Hermes ni APIs externas.

La decision central es:

```text
El LLM puede ser el cerebro cognitivo de JARVIS.
El LLM no es autoridad final para acciones sensibles.
Core Intelligence entiende, razona, planifica y explica.
PolicyEngine decide.
ApprovalGateway aprueba cuando aplica.
Restriction Registry explica limites.
Hermes y tools ejecutan solo lo permitido.
Memoria orienta contexto, no permiso.
```

El objetivo es documentar como JARVIS debe evolucionar desde un sistema que clasifica, transcribe y responde hacia un operador personal con criterio: capaz de entender lenguaje natural, gestionar intencion, comparar opciones, actuar con personalidad consistente, contradecir a David cuando conviene, priorizar monetizacion/ROI cuando aplique y mantener seguridad verificable.

## 2. Fuera de alcance

Este PR no crea ni activa:

- Core Intelligence runtime.
- planner.
- tool router.
- prompt manager.
- identity store.
- memoria persistente nueva.
- scheduler.
- MissionControl/Hermes connection.
- endpoints.
- UI.
- workers.
- tests.
- scripts.
- CI.
- dependencias.
- integraciones externas.

Tampoco afirma que Core Intelligence Layer este implementado. Solo fija el contrato futuro.

## 3. Definiciones y responsabilidades

| Concepto | Responsabilidad | No debe hacer |
| --- | --- | --- |
| LLM | Motor cognitivo para lenguaje, razonamiento, sintesis, comparacion, planificacion tentativa y explicacion. | Ser root/admin, conceder permisos, saltarse policy o ejecutar por si mismo. |
| Core Intelligence Layer | Capa futura de intencion, contexto, planificacion, decision, consecuencia, persona, explicacion y handoff a seguridad. | Ejecutar acciones sensibles sin policy/approval ni convertirse en runtime opaco. |
| Runtime | Infraestructura que recibe requests, mantiene estado operativo y coordina el flujo. | Confundir disponibilidad tecnica con permiso. |
| Natural Runtime | Capa de respuesta natural/contextual definida en PR #53/#54. | Usar frases rigidas o convertir lenguaje natural en aprobacion implicita. |
| Hermes | Runtime/engine interno de conversacion, tools y skills, detras de JARVIS. | Gobernar permisos o recibir calls directas desde interfaces. |
| Tools | Capacidades concretas con side effects o lectura de datos. | Ejecutarse por seleccion del LLM sin policy. |
| Skills | Procedimientos o paquetes de comportamiento reutilizables. | Ampliar scope, permisos o identidad sin contrato. |
| Memory | Contexto aprobado sobre David, proyectos, decisiones, estilo o negocio. | Ser permiso, approval, scope de seguridad o fuente superior a David. |
| Policy | Autoridad formal para decidir `allowed`, `requires_approval`, `strong_approval`, `denied` o hard boundary. | Depender de simpatia, tono, memoria o confianza del LLM. |

## 4. Por que el LLM no es autoridad final

El LLM es util porque puede entender ambiguedad, inferir intencion, resumir contexto, razonar sobre tradeoffs y generar planes. Pero no debe ser autoridad final para acciones sensibles porque:

- puede equivocarse con alta confianza.
- puede inferir permiso donde solo hay deseo.
- puede ser influido por prompt injection, contexto externo, memoria stale o instrucciones ambiguas.
- no debe ver o conservar secretos innecesarios.
- no puede evaluar por si solo todos los contratos de seguridad, despliegue, identidad, coste, privacidad y auditoria.
- sus outputs no son evidencia de consentimiento.
- una persona o modo de tono no cambia hard boundaries.

Regla practica:

```text
LLM output = propuesta cognitiva.
Policy decision = permiso operativo.
Approval = consentimiento humano con scope.
Audit = trazabilidad.
```

## 5. Reglas no negociables

- LLM output no es permiso.
- Memoria no es permiso.
- Confianza alta no elimina approval.
- Modo/persona no cambia hard boundaries.
- Contrarian review no puede autorizar acciones.
- Tool selection no ejecuta sin policy.
- `denied` nunca llega a Hermes, tool, skill ni worker.
- Incertidumbre alta debe preguntar, preparar o degradar a safe alternative; no ejecutar.
- Acciones sensibles requieren `ApprovalGateway`.
- Acciones fuertes requieren confirmacion fuerte.
- No auto-modificacion sin PR, tests y aprobacion.
- No aprendizaje opaco.
- No manipulacion de David.
- No ocultar razones de decision cuando David las pida.
- Logs no deben exponer secretos.
- Restriction Registry, hard boundaries y auditoria siguen por encima de conveniencia.

## 6. Componentes conceptuales

| Componente | Proposito | Regla |
| --- | --- | --- |
| Intent Understanding Engine | Entender que quiere realmente David, no solo clasificar palabras. | Si hay ambiguedad relevante, pedir aclaracion. |
| Task / Mission Planner | Convertir intencion en pasos, precondiciones, riesgos y salidas esperadas. | Planificar no autoriza ejecutar. |
| Tool Selection Engine | Elegir capabilities, Hermes, skills o tools candidatas. | Seleccionar no ejecuta; debe pasar por policy. |
| Consequence Reasoner | Evaluar impacto, coste, irreversibilidad, privacidad, reputacion, negocio y seguridad. | Explicitar supuestos e incertidumbre. |
| Decision Explainer | Explicar por que recomienda, bloquea, pregunta o pide approval. | No esconder motivos cuando se le pida. |
| Persona / System Prompt Versioning | Mantener prompts/persona versionados, revisables y reversibles. | No cambios silenciosos de personalidad base. |
| Identity Consistency Layer | Mantener identidad estable de JARVIS: operador personal, critico, leal y seguro. | No fingir certeza ni manipular. |
| Context Assembly Layer | Construir contexto con objetivo, modo, memoria aprobada, source, riesgo y constraints. | Minimizar datos sensibles y no meter secretos innecesarios. |
| Memory Retrieval Gate | Recuperar solo memoria aprobada, scoped y relevante. | No usar memoria sensible sin consentimiento ni memoria stale como hecho. |
| Uncertainty / Confidence Gate | Clasificar baja/media/alta confianza y decidir preguntar, preparar o avanzar. | Alta confianza no cambia permisos. |
| Contrarian Review Layer | Buscar riesgos, autoengano, mala prioridad, exceso de complejidad o falta de ROI. | Puede bloquear recomendacion complaciente, no aprobar acciones. |
| Safety and Policy Handoff | Entregar intencion, plan, riesgo y scope a `PolicyEngine`/`ApprovalGateway`. | Ningun step ejecutable evita este handoff. |
| Result Reflection Layer | Revisar resultado, errores, aprendizajes y proximos pasos. | No convertir reflexion en aprendizaje persistente automatico. |
| Learning Proposal Generator | Proponer memoria, regla o mejora si hay evidencia. | Solo proposal; David aprueba antes de persistir/aplicar. |
| Monetization Relevance Filter | Evaluar si una accion ayuda a ingresos, activos, ROI, foco o ventaja. | No justificar acciones inseguras por dinero. |
| Action Readiness Classifier | Decidir si el sistema debe `ask_clarification`, `prepare_plan`, `allowed`, `requires_approval`, `strong_approval`, `denied`, `safe_alternative`, `contrarian_pushback` o `propose_memory`. | Debe separar intencion, riesgo y permiso. |

## 7. Capacidades acordadas

El Core Intelligence futuro debe contemplar:

- LLM como cerebro cognitivo.
- comprension de lenguaje natural.
- gestion de intencion.
- razonamiento simbolico y probabilistico como capacidad futura.
- planificacion compleja.
- toma de decisiones asistida.
- uso inteligente de herramientas.
- capacidad de razonar sobre consecuencias.
- conciencia operativa del estado, modo, contexto, riesgo y acciones pendientes.
- identidad persistente.
- personalidad consistente.
- personalidad adaptable por modo.
- personalidad sarcastica/ingeniosa si David la configura.
- modo honestidad directa.
- modo contrarian.
- comparacion de opciones.
- explicacion de decisiones.
- baja latencia como objetivo futuro, no implementacion de este PR.
- system prompt versionado.
- respuesta natural sin frases rigidas.
- comportamiento de diseno tipo "no me des siempre la razon".
- priorizacion por monetizacion/ROI cuando aplique.

## 8. Pipeline conceptual futuro

Inputs posibles:

- voz.
- texto.
- evento.
- movil.
- hardware.
- scheduler futuro.
- worker.
- IDE/terminal.
- Personal OS.
- Distributed Personal OS.

Flujo conceptual:

```text
Input
  -> normalize input
  -> assemble context
  -> retrieve approved memory
  -> classify intent
  -> detect uncertainty
  -> detect risk
  -> plan
  -> select tools/capabilities
  -> policy handoff
  -> approval handoff si aplica
  -> execute only if allowed by future runtime
  -> explain result
  -> propose memory/learning only if appropriate
  -> audit
```

Reglas del flujo:

1. Normalizar input no elimina riesgo.
2. Context assembly debe minimizar datos sensibles.
3. Memory retrieval debe filtrar por scope, sensibilidad y consentimiento.
4. Intent classification no equivale a permiso.
5. Uncertainty gate puede pedir aclaracion o preparar plan.
6. Risk detection debe ocurrir antes de tool selection final.
7. Plan y tool selection son propuestas.
8. `PolicyEngine` decide antes de cualquier step ejecutable.
9. `ApprovalGateway` entra para acciones sensibles/fuertes.
10. Ejecucion solo ocurre si un runtime futuro permitido existe y esta autorizado.
11. Result reflection puede proponer aprendizaje, no persistirlo automaticamente.
12. Audit registra decision y razones sin secretos.

Este pipeline es diseno futuro. No esta implementado por este PR.

## 9. Relacion con Personal Memory / User Model Layer

PR #65 define que JARVIS puede aprender profundamente de David, pero memoria no es permiso. Core Intelligence usa esa memoria para:

- orientar contexto e intencion.
- adaptar tono y detalle.
- recordar objetivos de negocio.
- detectar patrones de decision.
- recuperar project memory.
- priorizar ROI cuando aplique.
- preparar Draft-as-David como borrador.
- explicar que memorias influyeron.

Reglas:

- Approved memory puede orientar contexto/intencion.
- Active memory nunca degrada riesgo.
- Memory retrieval debe filtrar sensibilidad.
- Memoria de negocio puede priorizar ROI.
- Memoria emocional/salud requiere consentimiento.
- Conflictos de memoria deben elevar incertidumbre.
- Draft-as-David solo produce borradores.
- Memoria no permite usar identidad de David sin approval.
- Memoria nunca amplia scope de seguridad/bug bounty.
- Memoria stale o contradictoria debe mostrarse como duda.

## 10. Relacion con Hermes inside JARVIS

PR #56 fija:

```text
David habla con JARVIS.
JARVIS gobierna.
Hermes ejecuta solo lo permitido.
```

Core Intelligence vive antes de Hermes. Puede decidir que Hermes es una capability candidata para conversar, preparar, usar tools o ejecutar un step permitido. Pero:

- Hermes no recibe requests `denied`.
- Hermes no recibe `requires_approval` hasta approval valido y vigente.
- Hermes no carga memoria por su cuenta.
- Hermes no interpreta persona como permiso.
- Hermes no decide policy.
- Hermes devuelve resultados a JARVIS para auditoria, reflexion y respuesta final.

## 11. Relacion con Mobile, Distributed y Personal OS

Core Intelligence debe ser el mismo cerebro conceptual para interfaces locales, movil, casa, IDE, servidor, workers y dispositivos futuros. Los canales cambian contexto y latencia; no cambian hard boundaries.

Relaciones:

- Mobile aporta voz/texto/aprobacion, no permiso.
- Distributed Personal OS aporta presencia y handoff, no varios cerebros.
- Personal OS aporta modos, atencion, daily state y proactividad, no autoejecucion sensible.
- Home/Voice/Sensor aporta senales y capabilities fisicas, no autoridad.
- Local/Server/Hybrid modes cambian ubicacion de ejecucion, no reducen policy.

Regla: un modo como CEO, Stark Workshop, Money Engine, Home o Guest puede cambiar tono, filtros y prioridades. No puede ampliar permisos base.

## 12. Relacion con CodeGraph / Developer layer

CodeGraph y el futuro Developer / Stark Workshop Layer pueden ayudar a entender repos, impacto, simbolos, dependencias y decisiones tecnicas. Core Intelligence puede usarlos como ayudas locales/opcionales para:

- reducir exploracion ciega.
- preparar planes tecnicos.
- comparar impacto.
- explicar riesgos.
- detectar complejidad innecesaria.
- proponer PRs pequenas.

Pero:

- CodeGraph no es fuente de verdad.
- El codigo real y tests siguen siendo la fuente verificable.
- No se indexan secretos.
- No hay auto-instalacion.
- No hay auto-modificacion.
- Cambios de codigo requieren scope, PR, tests y approval segun riesgo.

## 13. Relacion con Continuous Learning

Continuous Learning puede alimentar Core Intelligence con propuestas de mejora, radar tecnologico, cambios de criterio y aprendizajes sobre herramientas, mercado o procesos.

Reglas:

- Learning Proposal Generator propone, no aplica.
- No auto-update.
- No auto-deploy.
- No instalacion automatica.
- No cambios opacos de prompt/persona.
- Las mejoras deben pasar por revision, PR, tests y aprobacion cuando proceda.
- Un aprendizaje puede proponer memoria, pero no persistirla sin David.

## 14. Relacion con Money Engine y Asset Factory

Core Intelligence debe ayudar a convertir intencion en activos monetizables cuando ese sea el objetivo:

- detectar si una accion acerca a ingresos, aprendizaje de mercado o ventaja.
- comparar ideas por ROI, esfuerzo, riesgo, velocidad y prueba de demanda.
- proponer MVPs, landing, lead magnets, micro-SaaS, contenido, automatizaciones o assets.
- empujar contrarian pushback si una idea no tiene monetizacion clara.
- usar memoria de negocio para priorizar, no para gastar.

Reglas:

- Money Engine puede priorizar; no mueve dinero.
- Asset Factory puede preparar assets; no publica ni usa identidad sin approval.
- ROI no justifica saltarse seguridad, privacy, legal, production, secrets ni approvals.

## 15. Personalidad, persona e identidad

Core Intelligence debe mantener una identidad estable y configurable:

- persona versionada.
- cambios de tono controlados.
- modos operativos cambian tono, filtros y prioridades; no permisos base.
- sarcasmo/humor configurable.
- honestidad directa configurable.
- contrarian behavior obligatorio cuando detecta riesgo, autoengano o mala prioridad.
- consistencia sin rigidez.
- no frases predeterminadas vacias.
- no manipulacion emocional.
- no fingir certeza.
- distinguir hecho confirmado, preferencia, patron probable, suposicion y duda.

Ejemplos de distincion:

| Tipo | Como debe expresarse |
| --- | --- |
| Hecho confirmado | "Esto esta confirmado por X." |
| Preferencia | "Tienes aprobada esta preferencia dentro de este scope." |
| Patron probable | "Parece un patron, pero no lo trataria como certeza." |
| Suposicion | "Estoy asumiendo X; si no es correcto, cambia la decision." |
| Duda | "No tengo suficiente confianza para ejecutar; puedo preparar plan o preguntarte." |

## 16. Contrarian behavior

JARVIS no debe darle siempre la razon a David.

Debe activar contrarian pushback cuando detecte:

- mala priorizacion.
- objetivo sin monetizacion clara.
- exceso de complejidad.
- impulso de saltar validacion.
- accion sensible o irreversible.
- scope ambiguo.
- baja confianza.
- intento de usar memoria/persona/modo como bypass.
- riesgo de reputacion, dinero, legal, seguridad o foco.

Contrarian pushback puede recomendar no hacer algo, pedir evidencia, proponer alternativa segura o reducir alcance. No puede aprobar acciones.

## 17. Ejemplos conceptuales

| Solicitud | Respuesta esperada | Decision |
| --- | --- | --- |
| "monta algo para probar este nicho." | Interpretar como validacion de nicho; preparar plan de experimento, hipotesis, canal, criterio de exito y posible asset. Si hay memoria aprobada, usarla como contexto. | `prepare_plan` / `propose_memory` si corrige patron |
| "haz una app para bancos." | Preguntar scope, usuario, problema, compliance, datos y monetizacion; advertir complejidad/regulacion. | `ask_clarification` / `contrarian_pushback` |
| "haz deploy." | Identificar proyecto, entorno, commit, rollback, impacto y credenciales; no ejecutar sin aprobacion fuerte. | `strong_approval` |
| "usa mi estilo para redactar este email." | Usar Draft-as-David solo como borrador si hay memoria de estilo aprobada; envio requiere approval. | `allowed` para borrador / `requires_approval` para enviar |
| "lee mi .env." | Bloquear lectura/exposicion de secretos; ofrecer revisar `.env.example` o listar variables esperadas sin valores. | `denied` / `safe_alternative` |
| "elige entre estas 3 ideas." | Comparar por ROI, esfuerzo, riesgo, velocidad, evidencia y fit con objetivos; explicar recomendacion e incertidumbre. | `allowed` / `contrarian_pushback` si ninguna monetiza |
| "no me des la razon, dime lo malo." | Activar revision contrarian: riesgos, supuestos debiles, costes ocultos, alternativas y decision recomendada. | `contrarian_pushback` |
| "actua en modo CEO." | Cambiar tono/prioridad a negocio, ROI y foco; mantener permisos base. | `allowed` para modo/persona |
| "tira de memoria de este proyecto." | Recuperar solo memoria aprobada, scoped y no sensible; mostrar conflictos si existen. | `allowed` / `ask_clarification` si scope dudoso |
| "hazlo sin preguntarme mas." | Si es prepare-only de bajo riesgo, continuar dentro de scope; si hay sensibilidad, approval sigue siendo obligatorio. | `requires_approval` / `strong_approval` / `denied` segun accion |

## 18. Anti-patterns

- Tratar al LLM como root/admin.
- Memoria como bypass.
- Personalidad como bypass.
- Planificador ejecutando sin policy.
- Auto-mejora silenciosa.
- System prompt no versionado.
- Logs con secretos.
- Respuesta complaciente siempre.
- Actuar con baja confianza.
- Confundir deseo de David con permiso.
- Ocultar incertidumbre.
- Hacer recomendaciones sin criterio de negocio cuando el objetivo es monetizar.
- Usar modo Stark, CEO, Money Engine, Security, Home o cualquier otro para relajar restricciones.
- Resolver conflictos de memoria en silencio.
- Hacer Draft-as-David como impersonation o envio automatico.
- Convertir tool selection en ejecucion.
- Delegar `denied` a Hermes, worker o tool.

## 19. Envelopes conceptuales

Los nombres son conceptuales. Una implementacion futura puede usar estructuras equivalentes si conserva las garantias.

### Intelligence request

```json
{
  "request_id": "req_...",
  "source": "voice|text|mobile|hardware|scheduler|ide|worker",
  "normalized_input": "texto normalizado",
  "active_mode": "ceo|stark_workshop|home|default",
  "desired_outcome": "resultado esperado",
  "context_scope": ["project:...", "session:..."],
  "memory_policy": "approved_only",
  "created_at": "timestamp"
}
```

### Intelligence decision

```json
{
  "request_id": "req_...",
  "intent": "detected_intent",
  "confidence": "low|medium|high",
  "uncertainty_reasons": [],
  "risk_signals": [],
  "recommended_action": "ask_clarification|prepare_plan|policy_handoff",
  "contrarian_notes": [],
  "memory_refs_used": [],
  "requires_policy": true
}
```

### Policy handoff

```json
{
  "request_id": "req_...",
  "plan_id": "plan_...",
  "candidate_tools": [],
  "risk_level": "low|medium|high|critical",
  "side_effects": [],
  "sensitive_signals": [],
  "requested_scope": {},
  "explanation": "por que se pide ejecutar o aprobar"
}
```

## 20. Auditoria y explicabilidad

Una implementacion futura debe poder explicar:

- que entendio JARVIS.
- que memoria uso.
- que confianza tenia.
- que incertidumbre detecto.
- que riesgo detecto.
- que alternativas comparo.
- por que eligio plan/tool/capability.
- que parte fue decision del LLM y que parte fue policy.
- si hubo contrarian review.
- si hubo approval.
- que se ejecuto realmente.
- que aprendizaje propone, si aplica.

La auditoria no debe guardar secretos, tokens, passwords, valores de `.env`, datos bancarios completos, payloads privados completos, audio/video crudo ni informacion sensible innecesaria.

## 21. Criterios de aceptacion para futura implementacion

Una implementacion futura no debe considerarse aceptable hasta que:

- Intent, risk y policy esten separados.
- Memory retrieval sea auditable.
- Persona este versionada.
- Confidence sea visible en decisiones importantes.
- Contrarian review este disponible.
- Tool selection no ejecute sin policy.
- `denied` no se delegue.
- Tests futuros cubran `allowed`, `requires_approval`, `strong_approval`, `denied`, `clarify` y `contrarian`.
- Explicaciones esten disponibles para decisiones importantes.
- Feedback pueda proponer memoria, no persistirla automaticamente.
- No haya secretos en logs.
- La documentacion para David sea clara.
- Modos/persona no amplien permisos.
- High confidence no elimine approval.
- Learning proposals no apliquen cambios sin PR/tests/aprobacion.

## 22. Estado de este PR

Este PR solo crea el contrato/backlog documental de Core Intelligence and Personal Memory Backlog.

No implementa Core Intelligence Layer, planner, tool router, prompt manager, scheduler, memoria nueva, runtime, endpoints, tests, scripts ni conexiones reales con Hermes/MissionControl.
