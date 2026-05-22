# PR #58 - Mobile voice command and approval contract

## 1. Proposito

Este documento define el contrato conceptual para que el movil sea una interfaz remota segura de JARVIS.

Es exclusivamente documental. No implementa app movil, wake word, background listening, push notifications, auth, endpoints, router, runtime, worker, `PolicyEngine`, `ApprovalGateway`, HermesAdapter, tests, scripts, CI ni requirements.

La decision central es:

```text
David puede hablar con JARVIS desde el movil.
El movil no gobierna.
JARVIS Gateway recibe.
PolicyEngine decide.
ApprovalGateway aprueba cuando aplica.
Hermes ejecuta solo lo permitido.
```

El objetivo es permitir una experiencia futura tipo "Hola JARVIS" o acceso equivalente, con voz/texto, respuestas y aprobaciones desde el movil, sin convertir el movil en un bypass del runtime ni de los limites sensibles.

## 2. Que significa hablar con JARVIS desde el movil

"Hablar con JARVIS desde el movil" significa que David puede usar el movil como canal de entrada, salida y aprobacion:

- enviar voz o texto.
- recibir respuesta por texto o voz.
- ver aprobaciones pendientes.
- aprobar, denegar o pedir una alternativa segura.
- cancelar una mision o una intencion pendiente.

No significa que el movil ejecute JARVIS, Hermes, tools, scripts, comandos locales, acceso al filesystem, deploys, publicaciones ni acciones sensibles por si mismo.

El movil es interfaz. No es runtime.

## 3. Movil como interfaz, no como runtime

El movil puede:

- capturar voz o texto.
- normalizar la interaccion a una request para JARVIS Gateway.
- mostrar respuestas naturales de JARVIS.
- mostrar aprobaciones con riesgo, alcance, modo y duracion.
- enviar decisiones de David al `ApprovalGateway`.
- recibir notificaciones sin secretos.
- actuar como canal de presencia, estado y control humano.

El movil no debe:

- llamar a Hermes directamente.
- llamar al runtime local directamente.
- leer o escribir el filesystem local.
- guardar tokens de Hermes, del worker local o de servicios sensibles.
- decidir si una accion esta permitida.
- degradar `requires_approval` a `allowed`.
- ejecutar por wake word.
- desbloquear hard boundaries por voz.

## 4. Por que el movil no llama a Hermes directamente

Hermes es runtime interno de JARVIS. Segun el contrato de PR #56, Hermes debe quedar detras de `HermesAdapter` y de la capa de control de JARVIS.

Permitir `Mobile -> Hermes` crearia:

- dos caminos de ejecucion con reglas distintas.
- riesgo de saltarse `PolicyEngine`.
- aprobaciones ad hoc fuera de `ApprovalGateway`.
- exposicion accidental de tools, filesystem, credenciales o identidad.
- auditoria incompleta.
- permisos vagos desde una interfaz robable o comprometible.

El flujo valido es:

```text
Mobile Client futuro
  -> JARVIS Gateway
  -> Natural Runtime / Intent / Response Model
  -> PolicyEngine
  -> ApprovalGateway si aplica
  -> Orchestrator / Local Worker / HermesAdapter segun modo
  -> Hermes solo si esta permitido
  -> Audit / respuesta
```

## 5. Relacion con Local Mode, Server Mode y Hybrid Mode

Este contrato depende del contrato de PR #57.

### Local Mode

El movil puede enviar una request a JARVIS, pero Local Mode solo puede actuar si el entorno local esta disponible y la policy lo permite. El movil no accede al filesystem local ni manda comandos directos al PC.

### Server Mode

El movil puede hablar con un JARVIS Gateway en servidor para estado, respuestas, notificaciones, jobs pendientes y aprobaciones. Server Mode no obtiene acceso libre al PC local ni a secretos. Si una accion requiere contexto local, debe esperar, rechazar o delegar mediante un mecanismo futuro seguro.

### Hybrid Mode

El movil habla con JARVIS Gateway. El servidor puede orquestar y, si hace falta, delegar a un Local Worker autenticado. El worker solo acepta jobs con envelope, policy, scope, expiracion y audit. El movil no se convierte en mando remoto ilimitado del PC.

## 6. Relacion con natural runtime

PR #54 define que JARVIS debe responder de forma natural, contextual y segura. El movil hereda ese contrato.

Una frase de voz puede sonar informal, incompleta o urgente. Eso no baja el riesgo.

El natural runtime debe:

- interpretar intencion y confianza.
- separar entender, preparar, pedir aprobacion y ejecutar.
- responder con tono adecuado.
- pedir aclaracion cuando haya baja confianza.
- explicar aprobaciones con accion, riesgo, alcance y alternativa segura.
- mantener que memoria activa nunca degrada riesgo.
- garantizar que wake word o voz natural no implican autoejecucion.

## 7. Relacion con Hermes inside JARVIS

PR #56 establece:

```text
David habla con JARVIS.
JARVIS gobierna.
Hermes ejecuta solo lo permitido.
```

El movil no cambia esa regla. El movil es otra interfaz de JARVIS Gateway. Si una capacidad futura usa Hermes, debe hacerlo mediante `HermesAdapter`, despues de policy y approval cuando aplique.

## 8. Experiencia objetivo

Flujo conceptual:

1. David dice "Hola JARVIS" o usa un acceso equivalente seguro.
2. El movil captura voz o texto.
3. El movil envia la intencion a JARVIS Gateway.
4. JARVIS interpreta, evalua policy y responde por voz/texto.
5. Si la accion requiere aprobacion, JARVIS explica:
   - que hara.
   - por que lo hara.
   - riesgo.
   - alcance.
   - cuenta, proyecto o datos afectados.
   - modo de ejecucion: local, server o hybrid.
   - capacidad de Hermes implicada si aplica.
   - alternativa segura.
6. David puede:
   - aprobar una vez.
   - denegar.
   - pedir alternativa segura.
   - pedir plan/preparar sin ejecutar.
   - aprobar temporalmente si policy lo permite.
7. Toda aprobacion, denegacion, expiracion y ejecucion queda auditada.

## 9. Niveles de interaccion movil

| Nivel | Descripcion | Estado de este PR |
| --- | --- | --- |
| Mobile Text v1 | David escribe desde el movil y recibe respuesta. | Contrato futuro, no implementado. |
| Push-to-talk voice v1 | David pulsa para hablar; el movil envia transcript o audio procesado segun diseno futuro. | Contrato futuro, no implementado. |
| Voice response v1 | JARVIS responde con texto y opcionalmente voz. | Contrato futuro, no implementado. |
| Mobile approval center v1 | Pantalla de aprobaciones pendientes con riesgo, scope, duracion y acciones. | Contrato futuro, no implementado. |
| Wake word / "Hola JARVIS" v2 | Activacion por frase o mecanismo equivalente seguro. | Futuro, no implementado. |
| Background listening v2/v3 | Escucha en segundo plano solo donde el OS lo permita de forma segura. | Futuro condicionado, no implementado. |
| Offline/local mobile mode | Ejecucion local en el movil. | Fuera de alcance salvo diseno posterior. |

## 10. Limites por plataforma

### Android

Wake word y background listening podrian ser posibles dependiendo de permisos del sistema operativo, version, fabricante, bateria, politicas de privacidad e implementacion. Este PR no implementa nada de eso y no afirma disponibilidad.

### iOS

Un wake word siempre activo tipo Siri puede estar restringido por el sistema. Shortcuts, widgets, apertura de app, push-to-talk o acciones explicitas pueden ser caminos mas seguros para primeras versiones. Este PR no implementa nada de eso y no afirma disponibilidad.

### Regla comun

No debe afirmarse que existe app movil, wake word, escucha en segundo plano, push notifications ni approval center hasta que una PR futura lo implemente y valide.

## 11. Approval Center movil

Cada aprobacion movil debe mostrar, como minimo:

- accion solicitada.
- razon.
- riesgo.
- datos, cuentas o proyectos afectados.
- modo de ejecucion: local, server o hybrid.
- herramienta o Hermes capability implicada si aplica.
- duracion del permiso.
- alcance: una vez, temporal, proyecto o skill.
- alternativa segura.
- boton aprobar.
- boton denegar.
- boton pedir plan/preparar sin ejecutar.
- estado de auditoria.

Una aprobacion vaga como "si a todo" no es valida. Una aprobacion debe tener scope, duration, risk y audit event.

## 12. Tipos de aprobacion

| Tipo | Significado | Comportamiento movil |
| --- | --- | --- |
| `none` | No requiere aprobacion. | Puede responder o preparar si policy permite. |
| `normal approval` | Requiere consentimiento explicito para accion acotada. | Mostrar alcance, riesgo, duracion y auditar. |
| `sensitive approval` | Toca datos, cuentas, identidad, red o entorno sensible. | Mostrar explicacion reforzada y alternativa segura. |
| `strong approval` | Publicacion, dinero, deploy, contratos, secretos o irreversible. | Requiere confirmacion extra futura y scope exacto. |
| `not allowed from mobile` | La interfaz movil no puede aprobar ni ejecutar esa categoria. | Denegar en movil y ofrecer alternativa segura. |
| `requires desktop/local confirmation` | Debe confirmarse desde entorno local o desktop. | Mantener pendiente o pedir confirmacion local. |
| `requires config-file/manual confirmation` | Requiere cambio manual o archivo de config revisable. | No ejecutar desde movil; explicar procedimiento seguro. |

## 13. Acciones por categoria

| Categoria | Comportamiento movil esperado | Regla |
| --- | --- | --- |
| Consultar estado | allowed | Si no expone secretos ni datos sensibles. |
| Preparar plan | allowed | Prepare-only, sin side effects. |
| Crear PR documental | prepare-only / requires approval | Preparar o editar docs puede ser permitido por scope; commit, push o PR requieren policy especifica. |
| Ejecutar tests | requires approval | Code execution acotado; no desde wake word. |
| Escribir archivos | requires approval | Scope de rutas, diff/audit y duracion. |
| Usar GitHub | requires approval / strong approval | Leer puede ser allowed; push, merge, release o PR real requieren aprobacion. |
| Usar navegador | requires approval | Red externa y datos enviados deben estar claros. |
| Subir borrador a YouTube | sensitive approval | Uso de identidad/plataforma; no publicar. |
| Publicar en YouTube/redes | strong approval | Publicacion real como David. |
| Leer `.env`/secrets | denied / not allowed from mobile | Preferir alternativa segura: variables esperadas sin valores. |
| Hacer deploy | strong approval | Alcance exacto, rollback y confirmacion reforzada. |
| Gastar dinero | strong approval | Scope, importe, proveedor y expiracion. |
| Aceptar contratos | not allowed from mobile / strong approval futuro | Preferir revision manual; no voz como unico control. |
| Borrar archivos | strong approval / denied | Borrado amplio o irreversible debe bloquearse o requerir confirmacion local. |
| Usar identidad de David | sensitive/strong approval | Enviar, publicar, contratar o representar a David requiere control reforzado. |

## 14. Reglas de seguridad

- Mobile -> JARVIS Gateway only.
- Mobile -> Hermes directo prohibido.
- Mobile -> local filesystem directo prohibido.
- `PolicyEngine` evalua antes de cualquier ejecucion.
- `ApprovalGateway` decide aprobaciones.
- Sensitive boundary siempre gana.
- Active memory nunca degrada riesgo.
- `denied` nunca llega a Hermes ni worker.
- No secrets in push notifications.
- No logs con secretos.
- No autoejecucion por wake word.
- No publicacion, gasto, deploy ni contratos sin aprobacion fuerte.
- No lectura de `.env` desde movil salvo flujo fuerte futuro y seguro; preferir alternativa segura.
- Movil perdido o robado debe poder revocar sesiones.
- Approvals deben expirar.

## 15. Seguridad de sesion futura

Una implementacion futura debe disenar, como minimo:

- pairing device.
- autenticacion.
- identidad de dispositivo.
- expiracion de sesion.
- revocacion de dispositivo/sesion.
- unlock local biometrico opcional como refuerzo, no como sustituto de policy.
- rate limiting.
- replay protection.
- confirmation phrases o segundo factor para strong approval.
- audit trail de request, policy, approval, denial, expiry y execution.

Push notifications no deben incluir secretos, tokens, rutas sensibles completas ni payloads que permitan reconstruir credenciales.

## 16. Ejemplos conceptuales

### "Hola JARVIS, como va el proyecto?"

Respuesta esperada: responder estado read-only si la fuente no es sensible. Si necesita leer archivos locales o estado privado no disponible, explicar que requiere Local/Hybrid Mode y pedir scope o esperar worker.

Decision: `allowed` o `prepare-only` segun datos.

### "Crea una PR documental para X."

Respuesta esperada: proponer plan documental y, si policy lo permite, preparar cambios limitados a `docs/**`. Crear commit, push o PR real requiere evaluacion adicional y aprobacion.

Decision: `prepare-only` / `requires approval`.

### "Sube este video a YouTube como borrador."

Respuesta esperada: explicar titulo, descripcion, cuenta afectada, archivo, privacidad, riesgo de identidad y pedir aprobacion sensible antes de cualquier subida futura.

Decision: `sensitive approval`.

### "Publica este video."

Respuesta esperada: no publicar por voz directa. Mostrar publicacion, cuenta, audiencia, irreversible/impacto, alternativa de dejarlo en borrador y pedir aprobacion fuerte.

Decision: `strong approval`.

### "Lee mi .env."

Respuesta esperada: denegar exposicion de secretos desde movil. Ofrecer alternativa segura: listar variables esperadas, revisar plantilla `.env.example` o comprobar presencia sin mostrar valores si una future policy lo permite.

Decision: `denied` / `not allowed from mobile`.

### "Haz deploy."

Respuesta esperada: pedir contexto, preparar plan, riesgos y rollback. Ejecucion requiere approval fuerte con entorno, commit, proyecto, proveedor y duracion.

Decision: `prepare-only` antes de `strong approval`.

### "Crea una app para bancos."

Respuesta esperada: contrarian/estrategico. Preparar discovery, riesgos regulatorios, nicho, monetizacion y scope inicial. No crear integraciones bancarias ni manejar credenciales.

Decision: `prepare-only`.

### "Cancela la mision."

Respuesta esperada: si cancelar es reversible y esta dentro de scope, puede pedir confirmacion normal o ejecutar segun policy. Si afecta jobs en ejecucion o recursos externos, requiere aprobacion.

Decision: `allowed` / `requires approval`.

### "Aprueba durante 30 minutos esta restriccion."

Respuesta esperada: solo si policy permite override temporal. Debe mostrar restriccion exacta, scope, riesgo, expiracion, actor, modo y auditoria. Hard boundaries no pueden desbloquearse por voz.

Decision: `normal/sensitive/strong approval` o `denied` segun restriccion.

## 17. Anti-patterns prohibidos

- Abrir API publica para el movil sin auth.
- Meter tokens en la app movil.
- Enviar secretos por push.
- Mobile llamando Hermes directo.
- Wake word ejecutando acciones reales.
- Aprobacion vaga tipo "si a todo".
- Permisos permanentes sin expiracion.
- Logs con credenciales.
- Servidor usando movil como bypass de policy.
- Permitir que voz desbloquee hard boundaries.
- Duplicar `PolicyEngine` en la app movil.
- Reintentar acciones sensibles automaticamente tras fallo.
- Tratar un dispositivo pareado como permiso global.

## 18. Criterios de aceptacion para futura implementacion

Una futura PR de codigo solo deberia aceptarse si:

- mobile requests usan el mismo policy contract que local/server.
- aprobacion movil comparte `ApprovalGateway`.
- toda aprobacion tiene scope, duration, risk y audit event.
- denials se respetan.
- pending approvals no ejecutan.
- strong approvals tienen confirmacion extra.
- no hay secretos en notificaciones.
- tests cubren `allowed`, `requires_approval`, `strong`, `denied` y `not_allowed_from_mobile`.
- wake word no ejecuta por si sola.
- app movil puede revocarse.
- logs no exponen secretos.
- mobile no llama Hermes directo.
- mobile no accede al filesystem local directo.
- approvals expiran y no se reutilizan fuera de scope.

## 19. Fuera de alcance

PR #58 no implementa:

- codigo.
- tests.
- scripts.
- runtime.
- endpoints.
- router.
- CI.
- requirements.
- app movil.
- wake word.
- background listening.
- push notifications.
- auth real.
- pairing real.
- approval center real.
- cambios en `PolicyEngine`.
- cambios en `ApprovalGateway`.
- conexion MissionControl/Hermes.
- APIs externas.
- instalacion de dependencias.
- pytest.
- smoke tests.
- commit.
- PR.

Este documento solo fija el contrato que deberan respetar futuras implementaciones de mobile voice command and approval.
