# PR #65 - Personal Memory / User Model Layer

## 1. Proposito

Este documento define el contrato/backlog futuro para la capa Personal Memory / User Model Layer de JARVIS.

Es exclusivamente documental. No implementa codigo, tests, scripts, runtime, endpoints, router, CI, requirements, base de datos, UI, CLI, scheduler, memoria real, activacion de memoria, cambios en `PolicyEngine`, cambios en `ApprovalGateway`, conexion MissionControl/Hermes ni APIs externas.

La decision central es:

```text
JARVIS puede aprender profundamente de David.
La memoria debe ser visible, aprobada, reversible y auditable.
Memoria no es permiso.
PolicyEngine decide.
ApprovalGateway aprueba cuando aplica.
Restriction Registry explica limites.
Hermes ejecuta solo lo permitido.
```

El objetivo es que JARVIS construya con el tiempo un modelo transparente de preferencias, habitos, decisiones, proyectos, estilo de trabajo, contexto personal/profesional, memoria episodica, conflictos, borrado, consentimiento y auditoria, sin convertir la memoria en vigilancia, manipulacion ni bypass de seguridad.

## 2. Que problema resuelve

JARVIS necesita recordar mas que comandos aislados:

- como piensa, decide, habla y trabaja David.
- que proyectos estan activos, pausados o descartados.
- que preferencias se repiten y cuales fueron corregidas.
- que decisiones se tomaron, por que y con que resultado.
- que oportunidades o ideas se descartaron y bajo que razon.
- que tono, nivel de detalle y ritmo ayudan mas.
- que contexto personal y profesional debe mantenerse separado.
- que datos son sensibles, caducan o requieren consentimiento reforzado.

Sin una capa explicita de memoria, JARVIS corre dos riesgos opuestos: olvidar demasiado y repetir errores, o recordar demasiado y volverse opaco. Este contrato fija el camino intermedio: memoria util, revisable, consentida, con incertidumbre explicita y borrado real.

## 3. Fuera de alcance

Este PR no crea ni activa:

- memoria persistente nueva.
- base de datos.
- store vectorial.
- endpoints.
- comandos CLI.
- UI de memoria.
- scheduler.
- autoload.
- aprendizaje automatico.
- sincronizacion entre dispositivos.
- HermesAdapter real.
- target registry, vault, evidence locker o audit log real.
- nuevos permisos.

Tampoco afirma que Personal Memory / User Model Layer este implementado. Solo define el contrato futuro.

## 4. Definiciones principales

| Concepto | Significado |
| --- | --- |
| Memoria temporal | Contexto de conversacion o sesion que ayuda mientras dura el flujo actual y no se persiste como modelo estable. |
| Memoria aprobada | Memoria propuesta, revisada y aprobada explicitamente por David para uso futuro dentro de un scope. |
| Memoria episodica | Registro resumido de eventos, decisiones, razones, resultados y aprendizajes, con retencion limitada. |
| Preferencia | Eleccion explicita o confirmada sobre tono, formato, herramientas, ritmo, validacion o estilo de trabajo. |
| Habito | Patron observado o confirmado de comportamiento, rutina o preferencia repetida. Debe distinguirse de una certeza. |
| Decision | Eleccion tomada por David o JARVIS con David, junto con razon, evidencia, alternativas y resultado esperado. |
| Suposicion | Inferencia no confirmada. Debe mostrarse como candidata, no como hecho. |
| Memoria personal | Contexto de vida personal, rutinas, relaciones, preferencias privadas o estados no estrictamente profesionales. |
| Memoria de proyecto | Contexto acotado a un proyecto, repo, producto, PR, activo o linea de trabajo. |
| Memoria de negocio | Objetivos, oportunidades, monetizacion, experimentos, metricas, riesgo y patrones comerciales. |
| Memoria sensible | Informacion privada, emocional, salud, identidad, finanzas, legal, credenciales o datos que requieren consentimiento reforzado. |

## 5. Memoria no equivale a permiso

Que JARVIS recuerde una preferencia no significa que pueda actuar sin controles.

Ejemplos:

- Recordar que David prefiere PRs pequenas no autoriza hacer commit, push o abrir PR.
- Recordar que David suele validar nichos con misiones no autoriza crear misiones reales si la policy lo bloquea.
- Recordar que un dominio pertenece a David no autoriza pruebas de seguridad activas sin scope y approval.
- Recordar un estilo de email no autoriza enviar emails importantes como David.
- Recordar una restriccion temporal no autoriza renovarla ni ampliarla.

La memoria puede orientar interpretacion, tono, priorizacion, borradores, explicaciones y propuestas. No puede degradar riesgo, saltarse `PolicyEngine`, evitar `ApprovalGateway`, ignorar `Restriction Registry`, ocultar auditoria ni acceder a secretos.

## 6. Relacion con contratos existentes

### Natural runtime

El natural runtime debe usar memoria para responder con mas contexto, criterio y humanidad. Debe distinguir hecho, preferencia, inferencia y duda. Si una memoria activa aporta contexto pero la intencion es ambigua o sensible, debe preguntar, explicar riesgo o pedir approval.

La memoria no debe crear frases rigidas ni personalidad prefabricada. Debe ayudar a que JARVIS responda como operador contextual, critico y seguro.

### Mobile Approval Center

El Mobile Approval Center futuro puede mostrar memorias usadas en una decision, propuestas de memoria pendientes, conflictos y solicitudes de consentimiento. No puede convertir una memoria en approval. Toda aprobacion movil debe seguir mostrando accion, riesgo, scope, duracion y alternativa segura.

### Personal OS / Environment Intelligence

El Personal OS necesita memoria para daily state, modos, proactividad, notificaciones, vida/trabajo y criterio tecnico. Esta capa define como esa memoria debe ser consentida, separable y reversible. El Personal OS puede sugerir y preparar, pero no ejecutar acciones sensibles por memoria.

### Distributed Personal OS

La presencia distribuida puede necesitar sincronizar estado minimo, pending approvals o contexto de sesion. No debe sincronizar memoria sensible, audio, video, credenciales, payloads privados ni contexto personal amplio sin contrato, consentimiento y retention. Los dispositivos no son fuentes de permiso.

### Hermes inside JARVIS

Hermes puede usar memoria solo cuando JARVIS se la entregue mediante control layer, despues de policy y dentro de scope. Hermes no debe cargar memoria por su cuenta, decidir permisos, resolver conflictos en silencio ni usar memoria para ejecutar tools no autorizadas.

### Local memory quickstart actual

El quickstart actual ya fija el baseline seguro:

- `memory-save-local` escribe solo por accion explicita.
- `memory-load-local` lee solo por accion explicita.
- `memory-review` y `memory-approve` no activan runtime por si solos.
- `memory-activate` es explicito y de sesion.
- no hay autoload.
- sensitive boundary gana siempre.

Personal Memory / User Model Layer debe extender ese principio, no debilitarlo.

### Continuous Learning

Continuous Learning puede proponer nuevas memorias, cambios de roadmap o aprendizajes sobre herramientas, negocio o procesos. No puede persistir aprendizaje ni activar memoria sin aprobacion explicita de David. Un aprendizaje rechazado debe poder quedar como `rejected_memory` o item de roadmap descartado con razon.

### Authorized Security Research / Bug Bounty Mode

La memoria puede recordar laboratorios, preferencias de reporte o programas autorizados solo como contexto. No puede asumir autorizacion, ampliar scope, ignorar safe harbor, saltarse stop conditions ni convertir un target desconocido en in-scope. Active memory no puede rebajar security policy.

## 7. Tipos de memoria

| Tipo | Uso futuro | Regla |
| --- | --- | --- |
| `short_term_context` | Contexto inmediato del turno o interaccion. | No persistir como modelo estable sin propuesta. |
| `session_memory` | Estado temporal de una sesion local. | Caduca al cerrar o limpiar sesion. |
| `approved_user_preference` | Preferencia explicita o confirmada por David. | Persistencia solo con aprobacion. |
| `working_style_memory` | Ritmo, formato, PRs pequenas, validacion frecuente, detalle tecnico. | Orienta ejecucion, no permisos. |
| `business_goal_memory` | Objetivos de monetizacion, foco, ROI, productos o nichos. | No convierte oportunidad en accion. |
| `project_memory` | Estado, decisiones, constraints y contexto de un proyecto. | Scope por proyecto obligatorio. |
| `decision_memory` | Decision, razones, alternativas, evidencia y resultado. | Debe conservar incertidumbre y fecha. |
| `idea_graveyard_memory` | Ideas descartadas, pausa, razon y condiciones para reactivar. | Reactivacion requiere revision visible. |
| `episodic_memory` | Eventos importantes, briefings, debriefings y aprendizajes. | No guardar todo para siempre. |
| `emotional_context_memory` | Estado emocional, energia o frustracion si David consiente. | Consentimiento explicito y expiracion recomendada. |
| `relationship_context_memory` | Contexto sobre personas o relaciones. | Alta privacidad; consentimiento y scope claros. |
| `personal_life_context` | Vida personal, rutinas, hogar, familia, salud no clinica, preferencias privadas. | Separado de trabajo por defecto. |
| `professional_context` | Trabajo, repos, clientes, proyectos, productos, partners, oportunidades. | No mezclar con personal sin permiso. |
| `sensitive_memory` | Salud, identidad, finanzas, legal, secretos o datos privados fuertes. | Consentimiento reforzado; algunas categorias no deben almacenarse. |
| `inferred_memory_candidate` | Inferencia propuesta con evidencia y confianza. | No usar como hecho; requiere review. |
| `rejected_memory` | Memoria propuesta o inferencia rechazada por David. | Sirve para no repetir la suposicion; no se reactiva sola. |
| `expired_memory` | Memoria caducada por fecha, stale o cambio de contexto. | No aplica salvo revalidacion. |

## 8. Campos minimos de una memoria

Toda memoria futura debe declarar como minimo:

| Campo | Significado |
| --- | --- |
| `id` | Identificador estable y auditable. |
| `type` | Tipo de memoria de la taxonomia. |
| `plain_language_summary` | Resumen claro para David. |
| `source` | Origen: feedback, conversacion, documento, approval, debrief, decision, import, etc. |
| `evidence` | Evidencia concreta y minimizada que justifica la memoria. |
| `confidence` | Nivel de confianza. |
| `sensitivity` | Nivel de sensibilidad. |
| `scope` | Donde aplica: sesion, proyecto, modo, dispositivo, vida personal, trabajo, negocio, seguridad, etc. |
| `created_at` | Fecha de creacion. |
| `updated_at` | Fecha de ultima modificacion. |
| `expires_at` | Opcional; fecha de caducidad. |
| `approval_status` | Propuesta, en revision, aprobada, rechazada, activa, desactivada, borrada o expirada. |
| `user_visible` | Si David puede verla en UI/CLI/export. Debe ser `true` salvo casos de audit tecnico minimizado. |
| `applies_to_modes` | Modos donde puede orientar respuesta: local, mobile, server, hybrid, CEO, Deep Focus, etc. |
| `related_projects` | Proyectos, repos o activos relacionados. |
| `conflict_group` | Grupo usado para detectar contradicciones. |
| `allowed_uses` | Usos permitidos: tono, priorizacion, borrador, resumen, recomendacion, pregunta. |
| `forbidden_uses` | Usos prohibidos: permiso, approval, secretos, manipulacion, identidad, publicacion, gasto. |
| `deletion_behavior` | Que se borra, que queda como audit minimizado y como se revierte activacion. |
| `audit_requirements` | Eventos que deben registrarse sin secretos. |

## 9. Niveles de confianza

| Nivel | Significado | Uso permitido |
| --- | --- | --- |
| `explicit` | David lo dijo directamente como preferencia, decision o instruccion de memoria. | Puede proponerse o aprobarse segun sensibilidad. |
| `confirmed` | David confirmo una propuesta o correccion. | Puede usarse dentro de scope aprobado. |
| `inferred_low_confidence` | Patron debil o inferencia tentativa. | Solo como candidato o pregunta. |
| `inferred_high_confidence` | Patron repetido con evidencia, pero no confirmado. | Proponer memoria; no presentar como hecho privado. |
| `stale` | Puede estar obsoleto por fecha o contexto. | Pedir revalidacion antes de aplicar. |
| `contradicted` | Existe memoria o evidencia opuesta. | Resolver conflicto de forma visible. |
| `rejected` | David lo rechazo. | No aplicar; puede evitar repetir la inferencia. |

## 10. Niveles de sensibilidad

| Nivel | Regla |
| --- | --- |
| `public_or_low_risk` | Baja sensibilidad; aun asi requiere visibilidad si se persiste. |
| `personal_preference` | Preferencias de tono, formato o workflow; aprobacion explicita para persistir. |
| `business_sensitive` | Objetivos, proyectos, metricas, oportunidades o estrategia; proteger scope y logs. |
| `private_personal` | Vida personal privada; consentimiento y separacion personal/profesional. |
| `health_or_emotional` | Salud, energia, emocion o estados mentales; consentimiento explicito y expiracion. |
| `identity` | Identidad, documentos, cuentas, firma, representacion publica; controles fuertes. |
| `financial` | Dinero, pagos, bancos, inversiones, precios o presupuestos sensibles; approval fuerte para acciones. |
| `credential_or_secret` | Tokens, passwords, `.env`, claves, cookies o secretos. No guardar como memoria normal. |
| `legal_or_contractual` | Contratos, terminos, obligaciones, claims o riesgo legal; manejar como sensible. |
| `never_store_without_design` | Categoria que no debe almacenarse hasta tener diseno especifico, retention, masking y approval fuerte. |

## 11. Reglas obligatorias

- No autoload opaco.
- No memoria persistente sin aprobacion explicita.
- No memoria sensible sin consentimiento explicito.
- No inferencias privadas presentadas como hechos.
- No usar memoria para manipular decisiones.
- No usar memoria para saltarse approval.
- No usar memoria para ampliar scope de seguridad.
- No usar memoria para acceder a secretos.
- No guardar credenciales, tokens, `.env` ni datos bancarios como memoria normal.
- Active memory nunca degrada riesgo.
- Un conflicto de memoria debe resolverse de forma visible.
- David puede ver, corregir, borrar y revertir memoria.
- Memoria personal y profesional deben poder separarse.
- Memoria emocional, salud o energia requiere consentimiento explicito.
- Memoria debe poder expirar.
- Logs no deben exponer secretos.
- Una memoria rechazada no se reactiva sola.
- Un modo operativo no amplia permisos de memoria.
- Una memoria de proyecto no aplica globalmente sin scope explicito.
- Una memoria usada en una recomendacion debe poder explicarse.
- La memoria nunca es fuente de verdad superior al usuario.

## 12. Componentes futuros

| Componente | Responsabilidad | No debe hacer |
| --- | --- | --- |
| Memory Proposal Engine | Convertir feedback, correcciones y eventos en propuestas visibles. | Persistir o activar sin approval. |
| Memory Review Queue | Bandeja de propuestas, conflictos y caducidades pendientes. | Ocultar inferencias sensibles. |
| Memory Approval Workflow | Aprobar, editar, rechazar, posponer o pedir expiracion. | Aprobar scopes vagos o globales por voz. |
| Memory Activation Layer | Cargar memoria aprobada dentro de scope y sesion/modo. | Autoload opaco o degradar policy. |
| Memory Conflict Resolver | Detectar preferencias contradictorias, stale o sensibles. | Resolver en silencio si afecta decisiones. |
| Memory Decay / Expiration | Caducar memoria por fecha, uso, contradiccion o sensibilidad. | Mantener todo para siempre. |
| Memory Deletion / Reversal | Borrar, desactivar, revertir activaciones y limpiar derivados. | Impedir borrado o dejar efectos ocultos. |
| User Model Profile | Vista legible del modelo de David: preferencias, estilo, objetivos, limites. | Ser una caja negra. |
| Project Memory Store | Memoria scoped por proyecto, repo, producto o cliente. | Mezclar proyectos sin scope. |
| Decision Memory | Registro de decisiones, razones, supuestos, evidencia y resultados. | Reescribir historia sin audit. |
| Idea Graveyard | Ideas descartadas, por que, cuando reabrir y condiciones. | Convertir descarte en bloqueo permanente. |
| Context Compression Engine | Resumir contexto manteniendo decisiones, riesgos y memoria relevante. | Perder aprobaciones, restricciones o incertidumbre. |
| Draft-as-David Mode | Redactar borradores en estilo de David bajo control humano. | Impersonar, enviar, publicar o firmar sin approval. |
| Memory Audit Log | Registrar proposal, review, approve, activate, conflict, delete, revert. | Guardar secretos o payloads sensibles completos. |
| Memory Export / Portability | Exportar memorias visibles y auditables para backup/revision. | Exfiltrar datos sensibles sin approval. |
| Sensitive Memory Guard | Clasificar, bloquear o pedir consentimiento reforzado para memoria sensible. | Tratar salud, emociones, identidad o secretos como low risk. |

## 13. Draft-as-David Mode

Draft-as-David Mode es la version segura y controlada de una idea tipo "Shadow-You".

Puede:

- redactar borradores en el estilo de David.
- adaptar tono, idioma, longitud y estructura segun memoria aprobada.
- preparar emails, mensajes, propuestas, respuestas, posts o notas.
- indicar que es un borrador.
- explicar que memorias de estilo uso.
- permitir revision, edicion y descarte.

No debe:

- hacerse pasar por David sin aprobacion.
- enviar mensajes importantes sin aprobacion.
- firmar contratos.
- publicar.
- usar identidad de David sin aprobacion fuerte.
- comprometer dinero, legal, reputacion o relaciones.
- ocultar que el contenido fue redactado por JARVIS.
- convertir borrador en accion automatica.

Regla practica: Draft-as-David puede preparar. David decide, edita y aprueba antes de cualquier envio, publicacion, firma o compromiso.

## 14. Memoria de negocio

La memoria de negocio debe representar:

- objetivos de monetizacion.
- proyectos activos.
- proyectos pausados.
- ideas descartadas y por que.
- experimentos realizados.
- metricas aprendidas.
- preferencias de PRs pequenas.
- estilo de validacion.
- tolerancia al riesgo.
- patrones de bloqueo.
- oportunidades recurrentes.
- restricciones de foco, tiempo, presupuesto o energia.

Reglas:

- Una oportunidad recordada no se convierte en accion sin approval.
- Un objetivo de monetizacion no justifica manipulacion, gasto, publicacion ni deploy.
- Una idea descartada puede reabrirse si cambian las condiciones, pero debe mostrarse el conflicto.
- Las metricas deben conservar fuente, fecha y limitaciones.
- El Money Engine futuro puede usar memoria de negocio para priorizar, no para gastar.

## 15. Memoria episodica

La memoria episodica registra eventos relevantes, no todo lo que ocurre.

Debe poder guardar:

- eventos importantes.
- decisiones tomadas.
- razones.
- resultados esperados y reales.
- aprendizajes.
- estados contextuales si hay consentimiento.
- briefings y debriefings.
- cambios de proyecto, bloqueo o foco.

Relacion con "diario propio":

- Puede parecer un diario operativo de JARVIS, pero debe ser visible para David.
- No debe registrar todo para siempre.
- Debe separar privado, profesional, sensible e inferido.
- Debe permitir borrar episodios y caducar detalles.
- Los debriefings pueden proponer memorias, no persistirlas automaticamente.

Limites de privacidad:

- No guardar conversaciones completas si basta un resumen minimizado.
- No guardar emociones, salud o relaciones sin consentimiento.
- No usar episodios antiguos para juzgar o manipular decisiones.
- No compartir episodios entre dispositivos o modos sin scope.

## 16. Conflictos de memoria

Conflictos esperados:

- preferencia antigua vs nueva.
- proyecto descartado vs reactivado.
- contexto personal vs profesional.
- suposicion vs hecho confirmado.
- baja confianza vs alta confianza.
- memoria sensible detectada.
- memoria global vs memoria de proyecto.
- decision vieja vs resultado nuevo.

Respuesta esperada:

- preguntar a David cuando el conflicto afecta una decision.
- proponer actualizacion de memoria.
- desactivar memoria vieja si fue reemplazada.
- mantener ambas con scope claro si aplican en contextos distintos.
- rebajar confianza a `stale` o `contradicted`.
- bloquear activacion si aparece sensibilidad no consentida.
- auditar resolucion sin exponer secretos.

Un conflicto no debe resolverse por conveniencia silenciosa si cambia tono, decision, permisos, proyecto, identidad, dinero, seguridad o datos privados.

## 17. Ejemplos conceptuales

| Escenario | Decision esperada | Respuesta |
| --- | --- | --- |
| David corrige una clasificacion de intencion. | `propose_memory` | Crear propuesta visible con evidencia y scope; no activar sola. |
| David dice "prefiero PRs pequenas". | `propose_memory` / `requires_approval` | Proponer `working_style_memory`; aprobar antes de persistir. |
| David cambia de opinion sobre una idea descartada. | `requires_review` | Mostrar idea graveyard, razon vieja y propuesta de reactivacion. |
| JARVIS infiere algo con baja confianza. | `requires_review` | Guardar solo como `inferred_memory_candidate` o preguntar. |
| JARVIS recuerda una preferencia de tono aprobada. | `allowed` | Usarla para adaptar respuesta dentro de scope. |
| JARVIS intenta usar memoria para evitar approval. | `denied` | Bloquear: memoria no degrada risk ni approval. |
| JARVIS detecta conflicto entre vida personal y trabajo. | `requires_review` | Preguntar si se puede cruzar contexto o mantener separado. |
| JARVIS redacta como David un email importante. | `requires_approval` | Draft-as-David permitido como borrador; envio requiere approval fuerte si importante. |
| JARVIS recuerda datos emocionales sin consentimiento. | `denied` / `safe_alternative` | No persistir; ofrecer guardar solo si David consiente con scope/expiracion. |
| David pide borrar una memoria. | `delete/revert` | Borrar o desactivar, revertir activacion y registrar audit minimizado. |

## 18. Anti-patterns

- Guardar todo por defecto.
- Memoria opaca.
- Inferir certezas privadas.
- Recordar secretos.
- Usar memoria para manipular.
- Usar memoria para aprobar acciones sensibles.
- Mezclar vida/trabajo sin permiso.
- Hacer impersonation de David.
- Convertir Draft-as-David en envio automatico.
- No permitir borrar.
- Logs con datos sensibles.
- Memoria como excusa para no preguntar.
- Memoria como fuente de verdad superior al usuario.
- Guardar `.env`, tokens, cookies, passwords o datos bancarios como memoria normal.
- Presentar baja confianza como certeza.
- Usar memoria vieja sin revisar caducidad.
- Sincronizar memoria sensible a dispositivos sin contrato.
- Usar emociones o salud para empujar decisiones.

## 19. Auditoria, borrado y portabilidad

Una implementacion futura debe auditar:

- propuesta creada.
- fuente y evidencia minimizada.
- revision.
- aprobacion, rechazo o edicion.
- activacion y desactivacion.
- conflicto detectado.
- conflicto resuelto.
- expiracion.
- borrado.
- reversibilidad aplicada.
- exportacion.

La auditoria no debe guardar secretos, tokens, passwords, valores de `.env`, datos bancarios completos, payloads privados completos, audio/video crudo ni informacion sensible innecesaria.

Borrado debe significar:

- la memoria deja de aplicarse.
- cualquier activacion se revierte.
- derivados aplicables se invalidan o marcan stale.
- queda como maximo audit minimizado si el contrato de privacidad lo permite.
- David puede saber que se borro y por que.

Export/portability debe permitir a David revisar que recuerda JARVIS y moverlo o limpiarlo, con especial cuidado sobre memoria sensible.

## 20. Criterios de aceptacion para futura implementacion

Una implementacion futura no debe considerarse aceptable hasta que:

- La memoria sea visible y revisable.
- Existan propuestas antes de persistencia.
- La persistencia requiera aprobacion explicita.
- Exista borrado/reversion.
- Los conflictos sean detectables.
- `confidence` y `sensitivity` sean obligatorios.
- Exista separacion personal/profesional.
- Active memory no degrade policy.
- No haya secretos en logs.
- Tests futuros cubran propose, review, approve, activate, conflict, delete y denied.
- Una Memory UI o CLI muestre que recuerda JARVIS y por que.
- La documentacion para David sea clara.
- Las memorias sensibles requieran consentimiento explicito.
- Las memorias puedan expirar.
- Draft-as-David no pueda enviar, publicar, firmar ni usar identidad sin approval.
- Bug Bounty Mode no pueda ampliar scope por memoria.
- Mobile Approval Center no pueda aprobar scopes vagos por memoria.

## 21. Estado de este PR

Este PR solo crea el contrato/backlog documental de Personal Memory / User Model Layer.

No implementa memoria profunda, no activa memoria, no crea almacenamiento nuevo, no modifica runtime, no anade UI/CLI, no toca `PolicyEngine`, no toca `ApprovalGateway` y no conecta Hermes.
