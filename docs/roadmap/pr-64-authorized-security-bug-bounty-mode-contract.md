# PR #64 - Authorized Security Research / Bug Bounty Mode Contract

## 1. Proposito

Este documento define el contrato conceptual para un futuro modo profesional de investigacion de seguridad autorizada en JARVIS:

- aprendizaje defensivo.
- laboratorios locales.
- CTF y retos educativos.
- auditoria defensiva de activos propios.
- diagnostico de red y dispositivos propios.
- bug bounty dentro de scope, safe harbor y rules of engagement explicitos.
- manejo responsable de evidencias.
- redaccion de reportes y mitigaciones.

Es exclusivamente documental. No implementa codigo, tests, scripts, runtime, endpoints, router, CI, requirements, scanners, target registry real, evidence locker real, integraciones bug bounty, cambios en `PolicyEngine`, cambios en `ApprovalGateway`, conexion MissionControl/Hermes ni herramientas de seguridad reales.

La decision central es:

```text
JARVIS puede ayudar con seguridad autorizada.
JARVIS no tiene un hack-anything mode.
Scope, safe harbor y rules of engagement gobiernan.
PolicyEngine decide.
ApprovalGateway aprueba cuando aplica.
Restriction Registry explica limites.
Audit registra decisiones sin secretos.
Stop conditions ganan siempre.
```

El objetivo es permitir investigacion util, legal y segura sin convertir a JARVIS en un proxy para acceso no autorizado, exfiltracion, dano, ocultacion, evasion o acciones ofensivas fuera de contrato.

## 2. Definiciones

| Categoria | Significado | Regla |
| --- | --- | --- |
| Seguridad autorizada | Trabajo con permiso explicito sobre activos propios o de un tercero que ha autorizado un programa concreto. | Debe tener scope, limites y proceso responsable. |
| Laboratorio local | Entorno controlado propiedad de David o creado para practicar. | Permitido como aprendizaje o pruebas defensivas, sin afectar terceros. |
| CTF / lab challenge | Reto educativo con reglas publicas o privadas y entorno disenhado para practica. | Permitido dentro de las reglas del reto. |
| Bug bounty | Programa con activos, tecnicas, severidades, safe harbor, reporte y reglas definidos por el propietario. | Solo dentro de scope y rules of engagement. |
| Acceso no autorizado | Interaccion con sistemas, cuentas, redes, datos o servicios sin permiso demostrable. | Denied. No se reetiqueta como bug bounty. |

Un dominio publico, una IP visible, una app accesible en internet o la curiosidad de David no son autorizacion. La autorizacion debe ser demostrable, vigente, especifica y revisable.

## 3. Por que no existe hack-anything mode

"Hack-anything mode" no esta permitido porque elimina las condiciones que hacen legal y segura una investigacion:

- no declara propietario ni autorizacion.
- no define target ni alcance.
- no respeta safe harbor.
- no limita tecnicas, volumen, horarios ni impacto.
- no protege datos personales ni credenciales.
- no garantiza disclosure responsable.
- incentiva explotar primero y justificar despues.
- convierte memoria, voz, movil o Hermes en posibles bypasses de seguridad.

JARVIS puede ensenhar conceptos, preparar checklists, ayudar a entender riesgos, redactar reportes y operar laboratorios autorizados. No debe ayudar a acceder, persistir, evadir, ocultar, danhar, exfiltrar ni extraer datos de terceros.

## 4. Scope, safe harbor y rules of engagement

Todo trabajo real de seguridad debe declarar:

- `scope`: activos exactos permitidos, activos excluidos, cuentas autorizadas, entorno, fechas y propietario.
- `safe_harbor`: proteccion ofrecida por el programa si se siguen las reglas.
- `rules_of_engagement`: tecnicas permitidas/prohibidas, rate limits, horarios, cuentas de prueba, contacto, reporte, no divulgacion y stop conditions.

Si falta cualquiera de estos elementos, JARVIS solo puede operar en `learning_only`, `prepare-only` o pedir aclaracion. No puede iniciar pruebas activas.

## 5. Controles que no se eliminan

Este modo no elimina:

- `PolicyEngine`.
- `ApprovalGateway`.
- `Restriction Registry`.
- auditoria.
- sensitive boundary.
- hard boundaries.
- mobile approval rules.
- deployment mode restrictions.
- active memory safeguards.
- stop conditions.

Un modo de seguridad es mas sensible que un modo normal, no menos. La memoria activa puede recordar que David suele trabajar en laboratorios o bug bounty, pero no puede ampliar scope, asumir permiso, bajar aprobaciones ni convertir un target desconocido en autorizado.

## 6. Relacion con contratos existentes

### Personal Defense

Este modo encaja con `Personal Defense` del Personal OS como capa defensiva para privacidad, cuentas, red domestica, configuraciones, exposicion de credenciales y respuesta a incidentes. Debe evitar paranoia, falsos positivos y acciones agresivas sin autorizacion.

### Home / Voice / Sensor Hardware Layer

El diagnostico de routers, dispositivos IoT, sensores, camaras, red domestica o Home Assistant debe tratarse como capability fisica/domestica. Voz, presencia o casa propia no sustituyen approval para cambios de red, cuarentena de dispositivos, lectura de configuraciones sensibles o acciones que puedan degradar disponibilidad.

### CodeGraph Evaluation

CodeGraph puede ayudar en el futuro a entender repos propios, dependencias y superficie de codigo local. No es scanner de terceros, no gobierna permisos y no reemplaza lectura del codigo real, tests, policy ni approval.

### Distributed Personal OS

Movil, PC, reloj, casa, IDE, servidor y workers pueden ser superficies para ver estado, aprobar, recibir alertas o preparar reportes. Ningun dispositivo ejecuta pruebas activas por si mismo ni llama a Hermes directo.

### Hermes inside JARVIS

Hermes puede preparar planes, reportes, checklists o ejecutar capabilities permitidas solo detras de JARVIS control layer, despues de policy, approvals y scope. Hermes no decide autorizacion.

### Mobile Approval Center

El movil puede mostrar scope, riesgo, target, tecnica, rate limit, stop conditions y alternativa segura. No puede usar voz como shortcut para pruebas fuertes ni aprobar acciones vagas como "escanea todo".

## 7. Capacidades futuras permitidas

| Capacidad | Proposito | Approval esperado |
| --- | --- | --- |
| Scope Parser | Extraer targets permitidos, exclusiones, fechas y restricciones desde reglas aportadas por David. | `allowed` para lectura/preparacion. |
| Safe Harbor Checker | Identificar si existe safe harbor y sus condiciones. | `allowed` para lectura/preparacion. |
| Rules-of-Engagement Checklist | Convertir reglas en checklist antes de actuar. | `allowed`. |
| Authorized Target Registry futuro | Registrar activos autorizados con propietario, evidencia, expiracion y scope. | `future_contract`. |
| Personal Cyber Defense / Authorized Red Team Lab | Practica defensiva y pruebas en activos propios/lab. | `requires_approval` o `strong_approval` segun accion. |
| Authorized IoT Diagnostics and Device Control | Revisar y controlar dispositivos propios con alcance claro. | `requires_approval` o `strong_approval`. |
| IoT Security Scanner | Revisar exposicion de dispositivos propios con controles de volumen. | `future_contract`. |
| Home Network Guardian | Alertas y diagnostico de red domestica propia. | `requires_approval`; cambios requieren `strong_approval`. |
| Credential Exposure Detector | Detectar indicios de credenciales expuestas sin almacenar secretos completos. | `requires_approval` o `strong_approval`. |
| Firmware Risk Monitor | Revisar versiones, avisos y riesgos de firmware de dispositivos propios. | `allowed` para consulta; cambios requieren approval. |
| Phishing Defense Coach | Analizar mensajes sospechosos y entrenar respuesta defensiva. | `allowed` si no expone datos sensibles; si los hay, `requires_approval`. |
| Vulnerability Lab Sandbox | Practica controlada en entorno aislado. | `requires_approval`; automatizacion avanzada es `future_contract`. |
| Incident Response Assistant | Triage, contencion propuesta, evidencia minima y mitigaciones. | `requires_approval` o `strong_approval`. |
| Device Quarantine Approval Flow | Proponer aislar un dispositivo propio de la red. | `strong_approval`. |
| Evidence Locker | Guardar evidencia minima, redactada y auditable. | `future_contract`. |
| Bug Bounty Report Writer | Redactar reporte responsable para programa autorizado. | `allowed` para borrador; envio externo requiere `strong_approval`. |
| Security Lab Mode | Modo de entrenamiento y practica local controlada. | `requires_approval` para pruebas activas. |
| Rate Limit Guard | Limitar volumen, frecuencia y horarios segun reglas. | Obligatorio para futuras pruebas activas. |
| Sensitive Data Handling | Enmascarar secretos, datos personales y muestras innecesarias. | Obligatorio. |
| Stop Conditions | Detener trabajo si aparece riesgo legal, personal, tecnico o de scope. | Gana siempre. |
| CTF / Lab Training Mode | Aprendizaje y retos permitidos por reglas del lab. | `allowed` o `requires_approval` segun entorno. |

## 8. Categorias de actividad

| Categoria | Decision base | Descripcion |
| --- | --- | --- |
| `learning_only` | `allowed` | Explicaciones, conceptos, defensas, lectura de reglas y checklists sin target real. |
| `defensive_audit` | `requires_approval` | Revision defensiva de configuraciones, activos propios o exposicion autorizada. |
| `local_lab` | `requires_approval` | Pruebas activas en entorno local aislado y propio. |
| `CTF/lab_challenge` | `allowed` / `requires_approval` | Reto educativo dentro de reglas del lab. |
| `own_asset_testing` | `requires_approval` / `strong_approval` | Activos propios con scope claro; acciones que cambian red o disponibilidad suben a strong. |
| `bug_bounty_in_scope` | `strong_approval` para pruebas activas | Programa autorizado con scope, safe harbor y rules of engagement. |
| `report_writing` | `allowed` / `strong_approval` | Borradores permitidos; envio o contacto externo requiere strong approval. |
| `incident_response` | `requires_approval` / `strong_approval` | Triage, contencion, mitigacion y evidencia minima. |
| `IoT_diagnostics` | `requires_approval` / `strong_approval` | Diagnostico de dispositivos propios; control/cuarentena requiere strong approval. |
| `credential_exposure_review` | `requires_approval` / `strong_approval` | Revisar indicios sin capturar secretos completos ni exfiltrar. |
| `out_of_scope_or_unauthorized` | `denied` | Target o tecnica sin autorizacion demostrable, fuera de scope o prohibida. |

## 9. Reglas obligatorias

- No acceso a terceros sin autorizacion explicita.
- No target sin scope definido.
- No explotacion fuera de scope.
- No robo, captura ni exfiltracion de credenciales.
- No persistencia.
- No evasion.
- No ocultar acciones a David, propietarios, programas o auditoria.
- No degradar disponibilidad.
- No DoS ni DDoS.
- No movimiento lateral.
- No extraccion de datos personales.
- No publicacion de hallazgos sin proceso responsable.
- No acciones reales desde movil sin aprobacion adecuada.
- No usar voz como shortcut para acciones fuertes.
- Active memory no puede ampliar scope.
- Hard boundaries siguen activos.
- Logs y evidencias no deben contener secretos ni datos sensibles innecesarios.
- Stop condition gana sobre cualquier mision, approval, memoria o modo.

## 10. Niveles de aprobacion

| Nivel | Permitido | Ejemplos |
| --- | --- | --- |
| `allowed` | Aprendizaje, lectura de reglas, checklist, borrador de reporte y mitigaciones conceptuales. | Explicar severidad, preparar checklist, redactar reporte sin enviar. |
| `requires_approval` | Auditoria de assets propios, escaneo local controlado, revision de configs y diagnostico defensivo. | Revisar headers de dominio propio, comprobar configuracion local, analizar router propio. |
| `strong_approval` | Pruebas activas dentro de scope, cambios de red, cuarentena de dispositivo, uso de credenciales propias, contacto o reporte externo. | Prueba activa permitida por programa, aislar dispositivo, enviar reporte. |
| `denied` | Targets no autorizados, fuera de scope, credenciales ajenas, evasion, persistencia, exfiltracion, dano u ocultacion. | Endpoint excluido, credenciales encontradas, tecnicas prohibidas. |
| `future_contract` | Automatizaciones avanzadas, scanners activos, exploit lab automation e integraciones bug bounty. | Target registry real, evidence locker real, scanner orquestado. |

## 11. Workflow conceptual

1. David aporta contexto, activo propio, laboratorio o programa.
2. JARVIS extrae scope y reglas.
3. JARVIS identifica safe harbor si existe.
4. JARVIS marca out-of-scope y tecnicas prohibidas.
5. JARVIS propone un plan `allowed` o `prepare-only`.
6. `ApprovalGateway` decide si cualquier prueba activa procede.
7. JARVIS guarda evidencias de forma segura si existe un Evidence Locker futuro aprobado.
8. JARVIS redacta reporte responsable.
9. JARVIS prepara mitigaciones.
10. JARVIS detiene si aparece cualquier stop condition.

## 12. Stop conditions

JARVIS debe detener la actividad y volver a modo explicativo/preparacion si aparece:

- target fuera de scope.
- senhal de datos personales.
- credenciales reales expuestas.
- riesgo de dano o degradacion.
- deteccion de tercero no autorizado.
- el programa prohibe la tecnica.
- rate limit alcanzado.
- incertidumbre legal.
- David no puede demostrar autorizacion.
- una herramienta pide secretos no necesarios.
- cualquier hard boundary.

Una stop condition gana aunque exista memoria activa, aprobacion previa, urgencia, modo movil, modo lab o mision en curso.

## 13. Evidence Locker futuro

Un Evidence Locker futuro debe guardar solo lo minimo necesario para reproducir, explicar y reportar responsablemente un hallazgo autorizado.

Debe incluir:

- timestamps.
- referencia de scope.
- fuente de autorizacion o programa.
- pasos reproducibles sin dano.
- observacion tecnica resumida.
- impacto.
- mitigacion.
- decision de policy y approval asociado si aplica.
- retencion y borrado configurables.

Debe aplicar:

- redaccion/masking de secretos.
- no datos personales innecesarios.
- no credenciales completas.
- no payloads sensibles completos.
- no capturas masivas.
- no logs con tokens, passwords, cookies o claves.
- exportacion solo con approval.

El Evidence Locker no existe por este PR. Cualquier implementacion futura requiere contrato, storage, retention, masking, tests, auditoria y rollback.

## 14. Ejemplos conceptuales

| Solicitud | Decision | Respuesta esperada |
| --- | --- | --- |
| "JARVIS, quiero aprender X en un CTF." | `allowed` | Explicar conceptos, reglas del reto y plan de aprendizaje sin afectar terceros. |
| "Este router es mio, auditalo." | `requires_approval` | Pedir confirmacion de propiedad, alcance, horario, impacto permitido y preparar checklist. |
| "Revisa si mi dominio tiene headers inseguros." | `requires_approval` | Confirmar dominio propio o autorizado y preparar revision defensiva de bajo impacto. |
| "Este programa bug bounty permite estos dominios, prepara plan." | `prepare-only` | Extraer scope, safe harbor, exclusiones, rate limits y plan sin pruebas activas. |
| "Prueba este endpoint que no esta en scope." | `denied` | Bloquear y explicar que queda fuera de autorizacion. |
| "Extrae credenciales encontradas." | `denied` | No extraer ni guardar credenciales; proponer masking y reporte responsable. |
| "Haz un reporte para HackerOne/Bugcrowd." | `allowed` | Redactar borrador con evidencia minima y mitigacion; envio externo requiere `strong_approval`. |
| "Aisla este dispositivo raro de mi red." | `strong_approval` | Explicar impacto, dispositivo, red afectada y pedir aprobacion fuerte antes de actuar. |
| "Desde el movil, lanza un escaneo activo." | `strong_approval` / `future_contract` | No usar voz como shortcut; mostrar scope, tecnica, rate limit y requerir capability futura. |
| "Publica el hallazgo en redes." | `denied` / `strong_approval` segun disclosure | Denegar si no hay disclosure responsable; publicacion real requiere proceso y approval fuerte. |

## 15. Anti-patterns

- Renombrar hacking no autorizado como bug bounty.
- Aceptar scope ambiguo.
- Usar memoria para asumir autorizacion.
- Explotar primero y preguntar despues.
- Guardar secretos en logs o evidencias.
- Publicar hallazgos antes de disclosure responsable.
- Usar JARVIS como proxy para acciones ocultas.
- Automatizar scanners agresivos sin rate limits.
- Confundir "mi curiosidad" con "autorizacion".
- Aceptar mobile approval vaga para acciones fuertes.
- Intentar hard boundary override.
- Tratar un laboratorio como permiso para probar internet.
- Usar cuentas o credenciales ajenas.
- Ignorar exclusiones del programa porque el target parece relacionado.

## 16. Criterios de aceptacion para futura implementacion

Una implementacion futura no debe considerarse aceptable hasta que exista:

- target registry explicito.
- scope parser revisable.
- safe harbor y rules checklist.
- out-of-scope enforcement.
- approval por categoria.
- rate limit guard.
- stop conditions probadas.
- evidence masking.
- audit con actor, target, scope, decision y resultado.
- no secretos en logs.
- tests futuros para `allowed`, `requires_approval`, `strong_approval`, `denied` y `future_contract`.
- documentacion clara para David.
- no hack-anything mode.
- no ejecucion desde movil o voz para acciones fuertes sin aprobacion adecuada.
- no forma de ampliar scope mediante active memory.
- no integracion con scanners activos sin contrato especifico.

## 17. Estado de este PR

Este PR solo crea el contrato documental.

No afirma que JARVIS ya pueda ejecutar Bug Bounty Mode, scanners, target registry, Evidence Locker, integraciones bug bounty, cuarentena real de dispositivos, diagnosticos IoT reales ni respuesta a incidentes automatizada.
