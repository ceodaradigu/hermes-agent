# PR #63 - Distributed Personal OS Capabilities Backlog

## 1. Proposito

Este documento define el backlog/contrato futuro para que JARVIS pueda sentirse presente en varios dispositivos y entornos:

- movil.
- PC.
- reloj.
- coche.
- auriculares.
- altavoces.
- pantallas.
- casa.
- IDE/terminal.
- servidor.
- workers locales.
- clientes offline degradados.

Es exclusivamente documental. No implementa codigo, tests, scripts, runtime, endpoints, router, CI, requirements, clientes reales, sincronizacion real, watchers reales, notificaciones reales, device registry real, emergency continuity real, cambios en `PolicyEngine`, cambios en `ApprovalGateway`, conexion MissionControl/Hermes ni APIs externas.

La decision central es:

```text
JARVIS puede estar disponible en muchos sitios.
Los dispositivos no gobiernan.
Los clientes no son runtimes autonomos.
JARVIS Gateway recibe.
PolicyEngine decide.
Restriction Registry explica limites.
ApprovalGateway aprueba cuando aplica.
Hermes ejecuta solo lo permitido.
Audit une toda operacion distribuida.
```

El objetivo no es crear un asistente omnipresente sin control. El objetivo es fijar como JARVIS puede tener presencia distribuida, continuidad entre dispositivos, operaciones largas, briefing/debriefing, watchers prepare-only y telemetria de coste sin crear bypasses de seguridad ni multiples JARVIS inconsistentes.

## 2. Definiciones

| Concepto | Significado |
| --- | --- |
| JARVIS core | Capa de producto, intencion, policy, approval, restricciones, auditoria, memoria aprobada, modos y respuesta. |
| JARVIS Gateway | Entrada unica futura para clientes, dispositivos, workers, voz, servidor, casa e IDE. Normaliza origen, identidad, contexto y request. |
| Cliente | Interfaz ligera para voz, texto, aprobacion, notificacion, estado o handoff. No ejecuta acciones sensibles por si mismo. |
| Dispositivo | Hardware o entorno donde vive un cliente: movil, reloj, PC, coche, auricular, altavoz, pantalla, hub o IDE. |
| Worker | Entorno de ejecucion acotado y autenticado que puede realizar trabajo permitido por JARVIS bajo scope, policy y audit. |
| Presencia distribuida | Sensacion de que JARVIS acompana a David en varios canales, manteniendo una sola autoridad de decision y una sola trazabilidad. |
| Estado distribuido | Minimo estado sincronizado para continuar sesiones, aprobaciones, notificaciones, jobs, coste y conectividad sin duplicar permiso. |
| Offline degraded mode | Modo limitado cuando un cliente no puede hablar con JARVIS Gateway. Puede responder con contexto local minimo, pero no ejecutar acciones sensibles. |

## 3. Clientes no son runtimes autonomos

Un cliente futuro puede escuchar, mostrar, hablar, notificar o pedir aprobacion. Eso no lo convierte en JARVIS core.

Los clientes pueden:

- capturar voz o texto.
- mostrar respuestas naturales.
- mostrar aprobaciones pendientes.
- enviar decisiones de David al `ApprovalGateway`.
- recibir notificaciones sin secretos.
- mostrar estado de jobs, coste y conectividad.
- mantener cache local minima para offline degraded mode.
- iniciar un session handoff hacia otro dispositivo.

Los clientes no deben:

- llamar a Hermes directamente.
- llamar al runtime local directamente.
- acceder directo al filesystem local sin worker/policy.
- decidir permisos finales.
- ejecutar acciones sensibles sin `PolicyEngine`.
- degradar `requires_approval`, `strong_approval` o `denied`.
- guardar secretos amplios.
- crear una policy distinta por dispositivo.
- actuar como JARVIS paralelo.

La regla practica es simple: si una accion tiene side effects, toca datos sensibles, usa identidad, cuesta dinero, publica, cambia produccion, lee secretos, opera filesystem o afecta seguridad, debe pasar por JARVIS Gateway, `PolicyEngine`, `Restriction Registry`, `ApprovalGateway` cuando aplique y auditoria.

## 4. Arquitectura conceptual

```text
Desktop / Mobile / Watch / Car / Headphones / Speaker / Display / IDE / Home / Worker
  -> JARVIS Gateway
  -> Natural Runtime / Intent / Response Model
  -> Device and Session Context
  -> Restriction Registry
  -> PolicyEngine
  -> ApprovalGateway si aplica
  -> Orchestrator / Job Queue futura / Capability Router
  -> HermesAdapter / Worker / Connector solo si esta permitido
  -> Audit/Event Log con correlation id
  -> Notification Router / Response / Handoff
```

Reglas del flujo:

1. Todo origen entra por JARVIS Gateway.
2. La identidad de usuario, sesion y dispositivo se valida antes de actuar.
3. `PolicyEngine` decide antes de cualquier paso ejecutable.
4. `Restriction Registry` explica limites, scopes, overrides y hard boundaries.
5. `ApprovalGateway` gestiona aprobaciones con usuario, dispositivo, scope y duracion.
6. `denied` nunca se delega a worker ni llega a Hermes.
7. `requires_approval` y `strong_approval` no avanzan sin aprobacion valida y vigente.
8. Todo job, watcher, handoff, notificacion y ejecucion comparte audit correlation id.

## 5. Relacion con contratos existentes

### Local Mode, Server Mode y Hybrid Mode

Este backlog depende de PR #57.

- Local Mode puede dar acceso al PC de David y workers locales, pero no permiso global.
- Server Mode puede mantener disponibilidad 24/7, estado, colas, notificaciones y approvals, pero no acceso libre al PC ni secretos.
- Hybrid Mode combina servidor y worker local autenticado, pero el worker no es puerta trasera.

El modo de despliegue puede cambiar disponibilidad, latencia, capacidades y fallback. No puede bajar restricciones.

### Mobile Voice Command and Approval

PR #58 define el movil como interfaz, no runtime. Este documento generaliza esa regla a todos los dispositivos. El movil, reloj, coche, auriculares y pantallas pueden ser canales de entrada, salida, aprobacion y presencia, no autoridades de ejecucion.

### Home / Voice / Sensor Hardware Layer

PR #61 define casa, voz, sensores, pantallas y hardware como adapters/capabilities detras de JARVIS. La presencia distribuida usa esos canales para disponibilidad, contexto y notificacion, pero voz, presencia, rostro, sensor o habitacion no sustituyen approval.

### Personal OS / Environment Intelligence

PR #62 define el Personal OS como capa de contexto, modos, proactividad, notificaciones y atencion. Este backlog define como esa experiencia se distribuye entre dispositivos sin crear varios cerebros ni varios contratos de seguridad.

### Hermes inside JARVIS

PR #56 sigue siendo la regla base:

```text
David habla con JARVIS.
JARVIS gobierna.
Hermes ejecuta solo lo permitido.
```

Ningun cliente llama Hermes directo. Si una capacidad futura usa Hermes, entra mediante `HermesAdapter`, despues de policy, approval cuando aplique y audit.

### Future MCP, connectors y skills

MCP servers, connectors y skills futuras deben declararse como capabilities detras de JARVIS. Un cliente no puede invocar un connector por su cuenta. Cada capability debe declarar riesgo, permisos, modos soportados, coste, datos leidos, side effects, retention, logging, safe alternatives y approval esperado.

## 6. Superficies y dispositivos

| Superficie | Proposito futuro | No debe hacer |
| --- | --- | --- |
| Desktop daemon | Presencia local, estado, handoff, notificaciones, workers y control del PC bajo scope. | Ejecutar comandos sensibles sin policy/approval ni exponer filesystem directo. |
| Mobile app/client | Voz/texto, aprobaciones, notificaciones, debriefing, handoff y control rapido. | Llamar Hermes/local runtime directo o aprobar scopes vagos. |
| Watch client | Microaprobaciones, alertas criticas, estado breve y comandos cortos. | Mostrar secretos, aprobar strong actions complejas o actuar sin contexto. |
| Car mode | Agenda, navegacion conceptual, voz breve, alertas y manos libres. | Mostrar secretos, pedir decisiones complejas o ejecutar acciones sensibles conduciendo. |
| Headphones/earbuds | Alertas privadas, voz discreta, confirmaciones simples y presence routing. | Ser always listening inseguro o exponer informacion privada en voz sin contexto. |
| Smart speaker/voice satellite | Voz local, disponibilidad por habitacion y avisos domesticos. | Ejecutar acciones sensibles por wake word o guardar audio sensible por defecto. |
| Smart display/kitchen screen | Briefing matinal, estado del dia, approvals no sensibles y dashboard domestico. | Mostrar secretos ante invitados o mezclar perfiles sin privacy mode. |
| Browser extension future | Contexto web aprobado, captura de intencion y acciones prepare-only. | Leer paginas/cookies/secrets o publicar sin policy y approval fuerte. |
| IDE/terminal companion | Socio tecnico, handoff de tareas, planes, diffs conceptuales y estado de jobs. | Saltarse scope de repo, ejecutar comandos peligrosos o llamar Hermes directo. |
| Home hub | Fuente de eventos domesticos y canal local para voz/sensores. | Gobernar JARVIS, abrir red/cerraduras/camaras sin approval o actuar como bypass. |
| Local worker | Ejecucion local acotada para archivos, builds, analisis o tools permitidas. | Aceptar comandos arbitrarios o requests sin envelope/policy/scope. |
| Server orchestrator | Presencia 24/7, jobs, watchers, notificaciones, approvals y estado distribuido. | Tocar filesystem local directo, usar secretos sin vault aprobado o degradar restricciones. |
| Offline fallback client | Respuestas limitadas y cache local minima cuando no hay conectividad. | Ejecutar acciones sensibles, gastar, publicar, deployar, leer secretos o sincronizar memoria sensible. |

## 7. Capacidades acordadas

El backlog futuro debe contemplar:

- cliente always-on con indicador visible, controles y opt-in.
- cuerpo distribuido: JARVIS presente en movil, reloj, pantalla, auriculares, PC, coche y casa.
- distributed voice presence con reglas por canal.
- sincronizacion de estado entre dispositivos.
- session handoff entre dispositivos.
- multi-device approval continuity.
- notification routing por canal/dispositivo.
- fallback offline minimo y offline degraded mode.
- telemetria de coste por sesion.
- presupuesto mensual.
- throttling.
- cost/budget guard.
- briefing matinal.
- debriefing nocturno.
- schedulers y watchers.
- error watchers.
- watchers de calendario, finanzas y proyectos.
- reglas de cuando hablar y cuando callar.
- aprende a callarse: reduce interrupciones por feedback, contexto y modo.
- operaciones largas en segundo plano.
- long-running background missions.
- agentes que vuelven con informe ejecutable.
- visible status para jobs y watchers.
- cancel/pause/resume para trabajos largos.
- emergency continuity protocol.
- modo Cassandra para alertas contrarian/tempranas de riesgo.

Estas capacidades no estan implementadas por este PR. Quedan como contrato futuro.

## 8. Patrones de presencia

| Patron | Descripcion | Decision esperada |
| --- | --- | --- |
| `active_conversation` | David esta hablando o escribiendo activamente con JARVIS. | Puede responder, preparar o pedir approval segun policy. |
| `passive_availability` | JARVIS esta disponible sin interrumpir. | No actua; espera wake/input explicito. |
| `notification_only` | Solo puede avisar por prioridad configurada. | No ejecuta cambios. |
| `approval_only` | Dispositivo usado solo para aprobar/denegar/ver scope. | No inicia acciones nuevas salvo cancelar/pedir alternativa. |
| `local_worker_mode` | Worker ejecuta trabajos acotados ya autorizados. | Solo con envelope, policy, scope y audit. |
| `background_watcher` | Observa senales aprobadas y prepara avisos/propuestas. | Prepare-only por defecto. |
| `deep_focus_silence` | Modo no molestar. | No interrumpir salvo critical/emergency configurado. |
| `emergency_escalation` | Escalada por riesgo real y reglas opt-in. | Requiere configuracion previa, audit y contactos. |
| `offline_degraded` | Cliente sin gateway. | Solo respuestas locales limitadas y no sensibles. |
| `guest_privacy_mode` | Hay terceros o contexto compartido. | Ocultar datos privados y limitar capacidades. |

## 9. Estado distribuido minimo

Una implementacion futura debe definir como minimo:

| Estado | Para que sirve | Regla |
| --- | --- | --- |
| `user_identity` | Saber que David es el actor autorizado. | No sustituye approval. |
| `session_identity` | Vincular conversacion, handoff y expiracion. | Revocable. |
| `active_mode` | Deep Focus, Home, Car, Night, Guest u otro modo. | No amplia permisos. |
| `device_identity` | Saber desde que dispositivo llega o se aprueba algo. | Revocable si se pierde/roba. |
| `current_conversation_pointer` | Continuar una conversacion en otro dispositivo. | No debe incluir secretos innecesarios. |
| `pending_approvals` | Mantener decisiones pendientes entre dispositivos. | Scope, usuario, dispositivo y duracion obligatorios. |
| `pending_notifications` | Enrutar avisos por prioridad/canal. | Sin secretos. |
| `active_missions_jobs` | Seguir trabajos largos, watchers y misiones. | Cancel/pause/resume visible. |
| `last_known_capabilities` | Saber que puede hacer cada dispositivo/worker. | No usar como permiso implicito. |
| `consent_privacy_mode` | Gestionar guest/privacy/offline/retention. | Dominante sobre conveniencia. |
| `cost_budget_state` | Mostrar gasto, presupuesto, throttling y limites. | No silent spending. |
| `connectivity_state` | Saber online/offline/degraded. | Offline limita capacidades. |
| `audit_correlation_id` | Unir request, approval, job, notification y resultado. | Obligatorio para operaciones distribuidas. |

No debe sincronizarse memoria sensible, audio, video, credenciales, payloads completos privados ni contexto personal amplio sin diseno aprobado, consentimiento y retention.

## 10. Reglas de seguridad

- Ningun dispositivo ejecuta acciones sensibles sin policy.
- Ningun cliente llama Hermes directo.
- Ningun cliente accede directo al filesystem local sin worker/policy.
- Todos los dispositivos pasan por JARVIS Gateway.
- Todos los flujos ejecutables pasan por `PolicyEngine`.
- `Restriction Registry` explica limites y safe alternatives.
- `ApprovalGateway` gestiona aprobaciones normales, sensibles y fuertes.
- Approvals deben estar vinculadas a dispositivo, usuario, scope y duracion.
- Dispositivo perdido o robado puede revocarse.
- Offline fallback no puede ejecutar acciones sensibles.
- Background watchers no ejecutan cambios sensibles.
- Emergency continuity debe ser opt-in, auditado y con contactos configurados.
- No "always listening" inseguro.
- Always-on requiere indicador, control, opt-in y apagado claro.
- No secretos en notificaciones.
- No logs con audio, video, credenciales, tokens, passwords o payloads completos sensibles.
- No sincronizar memoria sensible sin diseno aprobado.
- Server, hybrid, mobile, home, watch, car e IDE no degradan restricciones.
- `denied` nunca se delega a worker ni llega a Hermes.
- Voz, presencia, rostro, reloj desbloqueado o movil personal no sustituyen approval.
- Guest/privacy mode domina sobre comodidad.
- Cost/budget guard domina sobre jobs largos y watchers.

## 11. Operaciones largas y background missions

JARVIS futuro puede preparar operaciones largas, pero no ejecutarlas como caja negra.

Permitido como prepare-only o bajo scope seguro:

- research missions.
- code/documentation planning.
- monitoring missions.
- market/opportunity scan proposals.
- report generation.
- error watcher que prepara diagnostico.
- calendario/finanzas/proyectos watcher que prepara resumen.
- background job que vuelve con informe ejecutable.

No permitido en silencio:

- no silent spending.
- no silent publication.
- no silent deploy.
- no silent identity use.
- no cambios sensibles sin approval.
- no lectura de secretos por watcher.
- no delegar denied a worker.
- no ejecutar offline actions sensibles.

Requisitos:

- estado visible.
- cancel/pause/resume.
- owner y device/source visibles.
- scope y duracion.
- coste estimado y coste real.
- budget guard y throttling.
- audit correlation id.
- resultado accionable: resumen, evidencia, riesgos, siguientes pasos y approvals necesarios.

## 12. Briefing, debriefing, watchers y silencio

### Briefing matinal

Debe agrupar agenda, foco, riesgos, oportunidades, approvals, coste, estado de jobs, estado domestico no sensible y cosas que JARVIS decidio no interrumpir. Debe ser configurable por canal: cocina, movil, PC, coche o auriculares.

### Debriefing nocturno

Debe resumir decisiones, pendientes, bloqueos, gasto, trabajos largos, watchers, oportunidades, acciones preparadas y lo que queda para manana. En Night Mode debe ser breve y no invasivo.

### Watchers

Watchers futuros observan senales aprobadas. Por defecto son prepare-only:

- error watchers.
- calendario.
- finanzas.
- proyectos.
- produccion.
- oportunidades de mercado.
- coste/presupuesto.
- seguridad/privacidad.

Un watcher puede avisar, preparar informe o pedir approval. No debe publicar, gastar, deployar, borrar, contactar, cambiar produccion ni usar identidad sin approval fuerte cuando aplique.

### Aprende a callarse

JARVIS debe aprender, de forma revisable y configurable, que no toda senal merece interrupcion. Debe poder:

- agrupar ruido.
- bajar prioridad por feedback.
- respetar Deep Focus, Night, Guest y Car Mode.
- explicar por que interrumpio.
- registrar cuando no interrumpio si es util para el briefing.
- permitir apagar categorias, canales u horarios.

## 13. Coste, presupuesto y throttling

La presencia distribuida aumenta riesgo de gasto invisible. Una implementacion futura debe incluir:

- telemetria de coste por sesion.
- coste por job/watcher/canal/modelo/capability.
- presupuesto mensual.
- alertas de umbral.
- throttling por categoria.
- bloqueo o approval fuerte cuando se exceda presupuesto.
- resumen de coste en briefing/debriefing.
- estimacion antes de operaciones largas.
- no silent spending.

El cost/budget guard es una restriccion, no una sugerencia visual.

## 14. Emergency continuity y modo Cassandra

### Emergency continuity protocol

Emergency continuity es un contrato futuro para mantener continuidad si David no responde ante situaciones definidas previamente.

Debe ser:

- opt-in.
- configurable.
- auditado.
- limitado por scope.
- con contactos definidos.
- con criterios de activacion claros.
- con expiracion o revision periodica.
- compatible con privacy mode.
- incapaz de ejecutar acciones sensibles no autorizadas.

No debe existir como default silencioso ni como excusa para contactar terceros, exponer datos, mover dinero, usar identidad, abrir casa o publicar informacion privada.

### Modo Cassandra

Modo Cassandra es un patron de alerta temprana y contrarian para riesgos que David podria ignorar.

Puede:

- advertir riesgos.
- decir "creo que estas ignorando X".
- preparar escenarios.
- escalar si el riesgo esta dentro de categorias configuradas.

No puede:

- manipular decisiones.
- usar miedo como empuje.
- saltarse Deep Focus salvo critical/emergency configurado.
- ejecutar acciones por urgencia percibida.

## 15. Ejemplos conceptuales

| Ejemplo | Comportamiento esperado | Decision |
| --- | --- | --- |
| Continuar conversacion del PC al movil. | Handoff con conversation pointer, contexto minimo y audit id; no transferir secretos innecesarios. | `allowed` |
| Aprobacion en reloj para accion no sensible. | Mostrar accion exacta, scope, duracion y origen; aprobar solo si es baja complejidad. | `requires_approval` |
| Denegar publicacion desde movil. | Registrar denegacion, bloquear ejecucion, ofrecer preparar borrador/checklist. | `denied` |
| Modo coche resume agenda sin mostrar secretos. | Voz breve, datos no sensibles, sin pantallas privadas ni approvals complejos conduciendo. | `allowed` |
| Auriculares reciben alerta critica. | Enviar alerta privada minima sin secretos y con razon de interrupcion. | `allowed` |
| Servidor detecta oportunidad y prepara informe. | Watcher prepare-only crea informe, coste visible y pide decision humana. | `prepare-only` |
| PC local apagado y servidor espera o degrada. | Job queda pendiente, expira o usa alternativa segura; no usa backdoor. | `offline_degraded` |
| Watcher detecta error de produccion y pide aprobacion. | Preparar diagnostico, impacto y propuesta; no deployar ni tocar produccion. | `requires_approval` |
| Briefing matinal en pantalla de cocina. | Mostrar agenda y foco sin secretos; activar guest/privacy si hay terceros. | `allowed` |
| Debriefing nocturno en movil. | Resumen breve de dia, coste, jobs y pendientes; no iniciar trabajos nuevos sin permiso. | `allowed` |
| Emergency continuity si David no responde. | Solo si opt-in, criterios y contactos estan configurados; registrar todo. | `future_contract` |
| Dispositivo perdido se revoca. | Invalidar sesion/device, cancelar approvals de ese device y auditar. | `strong_approval` |
| Offline client intenta enviar email como David. | Bloquear; preparar borrador local no sensible si es seguro. | `offline_degraded` |
| Altavoz oye "aprueba todo". | Rechazar por scope vago y falta de duracion. | `denied` |
| IDE companion prepara plan de refactor. | Analisis prepare-only dentro de repo autorizado; edits/commands requieren policy. | `prepare-only` |
| Browser extension quiere leer cookies. | Bloquear salvo contrato futuro explicito y approval fuerte. | `denied` |

## 16. Anti-patterns

- Cada dispositivo con su propia policy distinta.
- Movil, altavoz, IDE o extension llamando Hermes directo.
- Notificaciones con secretos.
- Approvals vagos tipo "si a todo".
- Continuidad de emergencia sin consentimiento.
- Always-on sin indicador o control.
- Watchers actuando en silencio.
- Servidor usando worker local como puerta trasera.
- Offline mode ejecutando acciones sensibles.
- Coste ilimitado sin budget guard.
- Sincronizar todo sin privacidad.
- Multiples JARVIS inconsistentes.
- Reloj aprobando acciones fuertes sin contexto.
- Coche mostrando datos privados o pidiendo decisiones complejas.
- Voice satellite guardando audio sensible por defecto.
- Browser extension leyendo paginas, cookies o formularios sin scope.
- Device trust usado como permiso global.
- Handoff copiando secretos por comodidad.
- Watchers de finanzas moviendo dinero o contratos.
- Modo Cassandra convertido en alarma constante.
- Emergency continuity usado para exponer informacion privada.

## 17. Criterios de aceptacion para futura implementacion

Una futura PR de codigo solo deberia aceptarse si:

- Existe device registry explicito.
- Las sesiones son revocables.
- Todos los clientes usan policy comun.
- Approvals incluyen device, user, scope y duration.
- Cada operacion distribuida tiene audit correlation id.
- Offline fallback esta limitado y no ejecuta acciones sensibles.
- Cost telemetry es visible por sesion/job/watcher.
- Monthly budget y throttling estan definidos.
- Notification router es configurable por canal, modo y prioridad.
- Watchers son prepare-only por defecto.
- Long-running jobs son cancelables, pausables y resumibles.
- Jobs largos muestran estado visible.
- Emergency continuity es opt-in.
- Lost/stolen device revocation cancela sesiones y approvals asociadas.
- No hay cliente que llame Hermes directo.
- No hay worker que acepte comandos sin envelope/policy/scope.
- Tests futuros cubren `allowed`, `requires_approval`, `strong_approval`, `denied`, `offline_degraded` y `no_interrupt`.
- Tests futuros cubren costo/budget guard y revocacion de dispositivo.
- Documentacion clara para David explica que esta implementado y que sigue siendo contrato futuro.

## 18. Fuera de alcance

PR #63 no implementa:

- codigo.
- tests.
- scripts.
- runtime.
- endpoints.
- router.
- CI.
- requirements.
- clientes reales.
- sincronizacion real.
- watchers reales.
- notificaciones reales.
- device registry real.
- emergency continuity real.
- cambios en `PolicyEngine`.
- cambios en `ApprovalGateway`.
- conexion MissionControl/Hermes.
- APIs externas.
- instalacion de dependencias.
- pytest.
- smoke tests.
- commit.
- PR.

Este documento solo fija el contrato que deberan respetar futuras implementaciones de Distributed Personal OS Capabilities.
