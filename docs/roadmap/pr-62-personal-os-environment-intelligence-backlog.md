# PR #62 - Personal OS / Environment Intelligence Backlog

## 1. Proposito

Este documento define el backlog/contrato futuro para que JARVIS evolucione de asistente/agente a sistema operativo personal de David:

```text
JARVIS organiza contexto, prioridades, decisiones, entorno y herramientas.
David conserva control.
PolicyEngine decide.
ApprovalGateway aprueba cuando aplica.
Restriction Registry explica limites.
Hermes ejecuta solo lo permitido.
```

Es exclusivamente documental. No implementa codigo, tests, scripts, runtime, endpoints, router, CI, requirements, UI, Command Center real, memoria real, scheduler, notificaciones reales, cambios en `PolicyEngine`, cambios en `ApprovalGateway`, conexion MissionControl/Hermes ni APIs externas.

El objetivo es fijar como debe evolucionar JARVIS hacia una capa de Personal OS / Environment Intelligence: una experiencia que coordina vida, trabajo, proyectos, rutinas, conocimiento, notificaciones, modos operativos, entorno fisico y criterio tecnico sin convertirse en autoejecucion peligrosa.

## 2. Definicion

Personal OS / Environment Intelligence es la capa que convierte capacidades sueltas en una experiencia coherente:

- entiende estado actual, contexto y objetivos.
- organiza la atencion de David.
- mantiene memoria viva, revisable y reversible.
- separa vida personal y trabajo cuando corresponde.
- coordina herramientas, proyectos, casa, movil y Hermes mediante reglas comunes.
- sugiere antes de que David pida, pero explica por que.
- prepara y agrupa informacion con poca friccion.
- pide aprobacion antes de acciones sensibles.
- permite apagar, ajustar o limitar proactividad por categoria.

No es una pantalla bonita. Es una capa de gobierno de experiencia, contexto y prioridades.

## 3. Chatbot vs agente vs dashboard vs sistema operativo personal

| Capa | Que hace | Limite |
| --- | --- | --- |
| Chatbot | Responde a mensajes. | Espera prompts y suele olvidar contexto operativo. |
| Agente | Usa tools para completar tareas. | Puede ejecutar pasos, pero no necesariamente organiza vida, atencion ni permisos globales. |
| Dashboard | Muestra estado visual. | Puede ser decorativo si no guia decisiones ni controla acciones. |
| Sistema operativo personal | Organiza contexto, prioridades, modos, decisiones, notificaciones, memoria y entorno. | Debe estar gobernado por policy, approval, consentimiento y auditoria. |

JARVIS debe poder usar chat, agentes y dashboards, pero no debe quedar reducido a ninguno de ellos. El Personal OS es la capa que decide que importa, que debe esperar, que requiere aprobacion, que conviene agrupar y que no merece interrumpir a David.

## 4. Reglas no negociables

- `PolicyEngine` sigue por encima de memoria, modo operativo, proactividad, voz, movil, dashboard, servidor, hardware, Hermes y preferencias.
- `ApprovalGateway` sigue siendo obligatorio para acciones sensibles, fuertes, irreversibles, publicas, financieras, de identidad, produccion, secretos o seguridad.
- `Restriction Registry` debe explicar limites en lenguaje humano y no puede convertirse en permiso silencioso.
- La auditoria registra decisiones, razones, cambios de modo, aprobaciones, denegaciones, interrupciones y acciones relevantes.
- La memoria puede orientar contexto, tono y prioridades, pero nunca saltarse policy ni approval.
- La proactividad puede sugerir, preparar, agrupar y avisar; no puede ejecutar acciones sensibles por iniciativa propia.
- David debe poder ajustar frecuencia, canales, categorias, prioridades y apagado de proactividad.
- El Personal OS no debe afirmar capacidades implementadas hasta que una PR futura las implemente y valide.

## 5. Relacion con contratos existentes

### Mobile Approval Center

El movil futuro puede ser el centro de aprobaciones, notificaciones y control rapido. Debe mostrar prioridad, razon, riesgo, alcance, modo, duracion, alternativa segura y audit status. No llama a Hermes ni al runtime local directamente.

### Local / Server / Hybrid modes

El Personal OS debe funcionar en Local Mode, Server Mode y Hybrid Mode con las mismas reglas. El modo puede cambiar disponibilidad, ubicacion de ejecucion y canales de notificacion; no puede bajar restricciones ni ampliar permisos.

### Home / Voice / Sensor Hardware Layer

La capa domestica aporta voz local, sensores, presencia, estado de casa y control fisico acotado. Es fuente de contexto y capability, no autoridad. Voz, presencia, rostro o dispositivo de confianza no sustituyen approval.

### Hermes inside JARVIS

Hermes sigue siendo runtime interno. JARVIS gobierna la experiencia, policy, approvals, memoria, modos y auditoria. Hermes prepara o ejecuta solo mediante adapter/control layer y solo lo permitido.

### Memoria local y natural runtime

La memoria local empieza explicita, revisable, aprobada y reversible. El natural runtime convierte contexto en respuestas utiles, criticas y humanas, sin frases rigidas ni complacencia. Memoria activa no degrada riesgo.

### Command Center futuro

El Command Center / Personal Control Center sera la interfaz visual futura del Personal OS: HUD, dashboard, daily state, aprobaciones, riesgos, decisiones, notificaciones agrupadas, modos, estado de sistema, proyectos y entorno. No debe ser solo una UI decorativa.

## 6. Capas principales

| Capa | Proposito | Reglas |
| --- | --- | --- |
| Command Center / Personal Control Center | Panel visual tipo HUD y pantalla/dashboard para estado, control personal, riesgos, aprobaciones y decisiones. | Read/control first; acciones sensibles pasan por policy/approval. |
| Personal Context & Memory Layer | Preferencias, proyectos, rutinas, decisiones, contexto conversacional y memoria viva. | Propuestas revisables/aprobables/reversibles; no salta policy. |
| Supervised Proactive Layer | Sugerencias, preparacion, agrupacion y avisos de riesgo u oportunidad. | Configurable, auditable, reversible y silenciable. |
| Operational Modes System | Modos como CEO, Deep Focus, Home, Travel o Emergency. | Cambian tono, filtros y defaults; no amplian permisos por si solos. |
| Environment Control Layer | Casa, voz, sensores, dispositivos, PC/Mac y ambiente. | Hardware es adapter/capability, no bypass. |
| Daily State / Life Dashboard | Estado general del dia, foco recomendado, pendientes y proximos pasos. | Distingue hechos, inferencias, consentimiento y datos faltantes. |
| Notification and Attention Router | Decide hablar, callar, agrupar, escalar o pedir accion humana. | Cada notificacion tiene prioridad y razon. |
| Life/Work Coordination Layer | Coordina vida y trabajo sin mezclarlos indebidamente. | Separacion por contexto, consentimiento y permisos. |
| Technical Partner / Builder Copilot Layer | Socio tecnico para construir, revisar, priorizar, monetizar y reducir complejidad. | Puede contradecir; no ejecuta cambios sensibles sin approval. |
| Decision and Consequence Layer | Compara opciones, consecuencias, riesgos, coste de oportunidad y tradeoffs. | No manipula decisiones; explicita supuestos e incertidumbre. |
| Personal Knowledge and File Context Layer | Contexto de archivos, notas, proyectos, docs y conocimiento personal/profesional. | Acceso por scope; secretos y datos privados protegidos. |
| Privacy / Consent / Audit Layer | Control, consentimiento, privacidad, borrado, reversibilidad y trazabilidad. | Debe ser visible y dominante sobre conveniencia. |

## 7. Capacidades acordadas

El Personal OS futuro debe contemplar:

- panel visual tipo HUD y dashboard visual.
- centro de notificaciones unificado.
- estado general del dia.
- sistema de control personal y conciencia operativa.
- poca friccion sin perder control.
- proactividad elegida, sugerencias anticipadas y accion anticipada con limites.
- lealtad, consistencia y personalizacion profunda.
- sincronizacion entre vida y trabajo.
- experiencia de socio tecnico.
- memoria de preferencias, aprendizaje de preferencias, memoria viva y contexto de conversacion.
- aprendizaje de contexto emocional solo con consentimiento explicito.
- modo proactivo, invisible, sombra, estratega, taller, creador, seguridad y multiple.
- varios perfiles y separacion de contextos.
- modo silencioso, urgente o nocturno.
- comparacion de opciones y razonamiento sobre consecuencias.
- adaptacion a vida y trabajo.
- operacion como sistema operativo personal con privacidad y control.

## 8. Operational Modes

Los modos operativos son perfiles de experiencia. Ajustan tono, filtros, proactividad, permisos esperados y notificaciones permitidas. No son permisos globales.

| Modo | Proposito | Tono | Proactividad | Permisos esperados | Notificaciones permitidas | Riesgos | Approval esperado |
| --- | --- | --- | --- | --- | --- | --- | --- |
| CEO Mode | Priorizar negocio, decisiones, ROI, foco y delegacion. | Directo, estrategico, contrarian. | Alta para riesgos/oportunidades. | Read/prepare; ejecucion limitada por scope. | Critico, urgente, dinero, oportunidades, aprobaciones. | Sobreoptimizar dinero o ignorar energia personal. | Normal/sensitive/strong segun accion. |
| Stark Workshop | Construccion tecnica, prototipos, arquitectura y debugging. | Tecnico, pragmatico, preciso. | Media-alta en bloqueos y mejoras. | Repo/docs/tools permitidos por scope. | Fallos, riesgos tecnicos, approvals, avances. | Cambios grandes, complejidad, tocar runtime sin contrato. | Normal para edits; strong para deploy/produccion. |
| Deep Focus | Proteger concentracion y reducir ruido. | Breve, silencioso, protector. | Baja; solo interrupciones justificadas. | Prepare-only y filtros de atencion. | Critico, requiere accion humana, seguridad. | Ocultar informacion importante por exceso de silencio. | Approval normal para cambiar reglas; sensitive si toca datos. |
| Shadow Operator | Observar, agrupar y preparar sin molestar. | Invisible, resumido cuando se pida. | Media en preparacion, baja en interrupcion. | Read/prepare dentro de fuentes autorizadas. | Digest, riesgo critico, approval pendiente. | Convertirse en autoejecucion silenciosa. | Approval antes de cualquier side effect. |
| Money Engine | Detectar monetizacion, costes, ingresos y oportunidades. | ROI-first, frio, comparativo. | Alta para oportunidades/risgos financieros. | Analisis y preparacion; gasto bloqueado. | Oportunidad de monetizacion, riesgo financiero, approval. | Sesgo a dinero, decisiones impulsivas. | Strong para gasto, contratos, pagos o inversion. |
| Personal Defense | Seguridad personal, privacidad, cuentas y superficie de riesgo. | Cauto, explicativo, firme. | Alta para seguridad real. | Read/prepare; acciones defensivas acotadas. | Critico, urgente, riesgo de seguridad. | Paranoia, falsos positivos, bloqueo excesivo. | Sensitive/strong segun impacto. |
| Learning Engine | Aprendizaje, investigacion, curriculo y practica. | Didactico, exigente, claro. | Media. | Lectura/preparacion; cambios solo aprobados. | Digest, oportunidades de aprendizaje, bloqueos. | Aprender sin aplicar o dispersarse. | Normal; sensitive si usa datos privados. |
| Creator Mode | Contenido, activos, marca, ideas y produccion creativa. | Creativo, editorial, orientado a publicar con control. | Media-alta en ideas y borradores. | Draft/prepare; publicacion bloqueada. | Ideas, deadlines, aprobaciones de publicacion. | Publicar o usar identidad sin control. | Strong para publicacion real. |
| Home Mode | Casa, voz, sensores, comodidad y presencia domestica. | Natural, contextual, tranquilo. | Media para entorno; alta para seguridad. | Control domestico bajo riesgo; sensibles aprobados. | Hogar critico, seguridad, dispositivos, digest. | Camaras, cerraduras, privacidad, invitados. | Normal/sensitive/strong segun dispositivo. |
| Travel Mode | Viajes, movilidad, itinerarios, riesgos y coordinacion. | Practico, anticipatorio. | Alta en tiempos, riesgos y logistica. | Preparar rutas/checklists; compras bloqueadas. | Urgente, critico, cambios de agenda, seguridad. | Exponer ubicacion, gastos o datos personales. | Sensitive/strong para compras, identidad o cambios reales. |
| Night Mode | Descanso, silencio y proteccion nocturna. | Minimo, calmado, no invasivo. | Muy baja. | Solo estado, alarmas y seguridad. | Critico, emergencia, seguridad domestica. | Interrumpir descanso o silenciar demasiado. | Strong para acciones sensibles fuera de rutina. |
| Emergency Mode | Gestionar situaciones urgentes. | Claro, corto, prioritario. | Muy alta en triage y avisos. | Preparar/llamar atencion; acciones criticas segun policy. | Critico y urgente. | Panico, falsas emergencias, acciones precipitadas. | Sensitive/strong salvo instrucciones seguras de bajo riesgo. |
| Guest Mode | Limitar datos y capacidades cuando hay terceros. | Formal, discreto, limitado. | Baja. | Sin contexto privado salvo permiso explicito. | Solo informacion no sensible o aprobaciones privadas. | Filtrar informacion personal/profesional. | Approval para revelar o actuar con datos privados. |
| Family/Shared Context Mode futuro | Coordinar contexto compartido con familia o personas autorizadas. | Respetuoso, claro, multiusuario. | Media con consentimiento. | Solo datos compartidos y permisos por persona. | Compartido, urgente, hogar, aprobaciones. | Mezclar identidades, privacidad o consentimiento. | Approval por actor/contexto; strong para datos sensibles. |

## 9. Reglas de proactividad

JARVIS puede:

- sugerir siguientes pasos.
- preparar planes, borradores, comparativas y checklists.
- agrupar informacion para reducir ruido.
- avisar si detecta riesgo, bloqueo u oportunidad.
- anticipar acciones no sensibles como preparar contexto o resumir.
- decir que decidio no interrumpir y por que.

JARVIS no debe:

- molestar por ruido.
- ejecutar acciones sensibles solo por proactividad.
- manipular decisiones ni empujar a David ocultando tradeoffs.
- usar estado emocional/salud sin consentimiento.
- ampliar permisos por estar en modo proactivo, invisible o sombra.
- ocultar que preparo algo o por que interrumpio.

Toda proactividad debe ser configurable, auditable y reversible. David debe poder ajustar frecuencia, canales, prioridades, categorias, horas, modos y apagado total. Cada interrupcion debe explicar por que merece atencion ahora.

## 10. Daily State

El Daily State futuro debe responder a "como va mi dia?" con una vista compacta y accionable:

- agenda.
- tareas.
- proyectos.
- energia/estado solo si hay datos y consentimiento.
- foco recomendado.
- riesgos.
- oportunidades.
- aprobaciones pendientes.
- notificaciones agrupadas.
- metricas de negocio.
- estado del sistema.
- estado de casa/dispositivos si aplica.
- proximos pasos sugeridos.
- cosas que JARVIS decidio no interrumpir.

Debe separar confirmado, inferido, pendiente, sensible y no disponible. Si falta consentimiento para energia, salud, emocion o datos privados, debe decirlo y no inferir certezas.

## 11. Notification and Attention Router

El router de atencion decide cuando hablar y cuando callar. No todas las senales son notificaciones.

| Prioridad | Significado | Comportamiento |
| --- | --- | --- |
| `critical` | Riesgo inmediato, seguridad, perdida importante o emergencia. | Interrumpir salvo hard no-disturb configurado con excepcion documentada. |
| `urgent` | Requiere atencion pronta para evitar coste, bloqueo o perdida. | Notificar por canal activo. |
| `important` | Importa, pero puede esperar. | Agrupar o mostrar en Daily State. |
| `informational` | Contexto util sin accion inmediata. | Digest o dashboard. |
| `digest` | Varias senales agrupadas. | Resumen periodico. |
| `silenced` | Categoria apagada temporalmente. | No interrumpir; registrar si aplica. |
| `do_not_disturb` | No molestar salvo excepciones. | Solo critical/emergency segun config. |
| `requires_approval` | No puede avanzar sin decision humana. | Mostrar en Approval Center. |
| `requires_human_action` | JARVIS no puede actuar o no debe actuar. | Explicar siguiente accion de David. |
| `monetization_opportunity` | Puede generar dinero o ventaja. | Escalar segun Money Engine y modo activo. |
| `security_risk` | Riesgo de seguridad, privacidad o acceso. | Escalar con razon y alternativa segura. |
| `discarded_noise` | Ruido descartado. | No interrumpir; opcionalmente listar en "no interrumpido". |

La decision de hablar/callar debe considerar modo activo, hora, energia consentida, agenda, riesgo, oportunidad, coste de interrupcion, canal, urgencia, aprobaciones pendientes y preferencias. La razon debe ser visible: "te interrumpo porque..." o "lo deje para digest porque...".

## 12. Memoria y contexto

El Personal OS necesita memoria, pero memoria no es permiso.

Debe poder representar:

- preferencias explicitas.
- habitos y rutinas.
- proyectos activos y pausados.
- decisiones tomadas y razones.
- ideas descartadas.
- estilo de trabajo.
- nivel de detalle preferido.
- contexto personal/profesional separado.
- limites de privacidad.
- memorias propuestas, revisadas y aprobadas.
- conflictos de memoria.
- borrado, reversibilidad y expiracion.
- contexto de conversacion.
- aprendizaje de preferencias y memoria viva.

Reglas:

- Toda memoria persistente relevante empieza como propuesta revisable.
- David puede aprobar, rechazar, editar, borrar o revertir.
- Conflictos de memoria deben mostrarse, no resolverse en silencio si afectan decisiones.
- Contexto personal y profesional debe poder separarse por perfil, proyecto, fuente y modo.
- Memoria emocional, salud, energia o relaciones requiere consentimiento explicito y scope.
- Memoria nunca salta `PolicyEngine`, `ApprovalGateway`, `Restriction Registry` ni auditoria.

## 13. Ejemplos conceptuales

| Solicitud | Respuesta esperada | Comportamiento |
| --- | --- | --- |
| "JARVIS, como va mi dia?" | Daily State con agenda, foco, riesgos, approvals, oportunidades, estado de sistema y lo no interrumpido. | Agrupa y sugiere. |
| "Ponme en modo trabajo profundo." | Cambia a Deep Focus, silencia ruido, deja pasar critico/approvals definidos y explica excepciones. | Cambia de modo; no amplia permisos. |
| "Resume todo lo importante de hoy." | Digest priorizado por importancia, no por volumen. | Agrupa. |
| "Estoy saturado, prioriza por mi." | Propone 1-3 prioridades, tradeoffs y que quedara para despues. | Sugiere; no manipula. |
| "Coordina mi vida y trabajo sin mezclarlo mal." | Separa contextos, pide consentimiento si necesita cruzar datos y propone reglas. | Prepara y pide approval si toca datos sensibles. |
| "Activa modo invitado." | Oculta contexto privado, limita capacidades y confirma que no revelara datos sin permiso. | Cambia de modo. |
| "No me molestes salvo cosas criticas." | Activa filtro no molestar y define que cuenta como critico. | Cambia router de atencion. |
| "Dime que estoy ignorando que puede hacerme ganar dinero." | Lista oportunidades con evidencia, impacto, esfuerzo y riesgo. | Sugiere y compara. |
| "Hazme de socio tecnico para este proyecto." | Entra en Stark Workshop, revisa contexto permitido, pregunta scope si falta y propone plan tecnico. | Prepara; pide approval antes de edits/ejecucion. |
| "Ensename por que me recomiendas esto." | Explica supuestos, memoria usada, riesgos, alternativas y consecuencias. | Justifica y permite revision. |

## 14. Anti-patterns

- Convertir Personal OS en dashboard decorativo.
- Notificar demasiado o por ruido.
- Proactividad sin explicacion.
- Mezclar contexto personal/profesional sin permiso.
- Memoria opaca.
- Manipular decisiones.
- Actuar en nombre de David sin aprobacion.
- Usar estado emocional, salud o energia sin consentimiento.
- Saltarse `ApprovalGateway` por confianza.
- Convertir modo invisible en autoejecucion peligrosa.
- Usar modos como excusa para ampliar permisos.
- Ocultar acciones, fuentes, decisiones o preparaciones.
- Guardar todo para siempre.
- Tratar voz, presencia, movil o casa como autorizacion universal.
- Hacer que Hermes, dashboard, hardware o notificaciones sean bypasses.

## 15. Criterios de aceptacion para futura implementacion

Una implementacion futura del Personal OS / Environment Intelligence solo debe aceptarse si:

- Los modos estan documentados y son configurables.
- Cada notificacion tiene prioridad y razon.
- La proactividad es auditable.
- La memoria es explicita, revisable y reversible.
- El contexto personal/profesional es separable.
- No hay autoejecucion sensible.
- `PolicyEngine` y `ApprovalGateway` siguen por encima.
- `Restriction Registry` explica limites en lenguaje humano.
- Mobile, Local, Server y Hybrid comparten reglas.
- Command Center muestra estado, riesgos, aprobaciones y decisiones.
- Tests futuros cubren `allowed`, `requires_approval`, `denied` y `no_interrupt`.
- David puede ajustar o apagar proactividad por categoria.
- El sistema registra cosas que decidio no interrumpir cuando sea util.
- Los perfiles multiples no mezclan datos ni permisos sin consentimiento.
- Cualquier dato emocional, salud, hogar, familia o ubicacion requiere consentimiento y scope.

## 16. Fases futuras sugeridas

1. Contrato de envelopes para Daily State, Operational Mode y Attention Event.
2. Config documental de modos y categorias de notificacion.
3. Read-only Daily State local con datos no sensibles.
4. Mobile Approval Center y Notification Router con audit.
5. Command Center read-only.
6. Memoria de preferencias revisable conectada a modos.
7. Integracion limitada con Home / Voice / Sensor layer.
8. Personal OS multi-perfil con separacion personal/profesional.

Cada fase debe ser una PR pequena, con scope claro, policy/approval antes de runtime y sin afirmar capacidades hasta estar implementadas y validadas.
