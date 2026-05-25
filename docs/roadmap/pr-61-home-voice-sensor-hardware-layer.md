# PR #61 - Home / Voice / Sensor Hardware Layer contract

## 1. Proposito

Este documento define el contrato conceptual para una futura capa fisica/domestica de JARVIS:

- voz local.
- wake word local.
- STT/TTS local.
- microfonos y voice satellites.
- Home Assistant u otros hubs domesticos.
- camaras y vision local.
- sensores de presencia, puertas, movimiento, temperatura, humedad y energia.
- control de luces, enchufes, persianas, clima y escenas.
- automatizaciones contextuales.
- PC/Mac control por voz como capability separada.
- hardware personalizado.
- futuros sensores avanzados, coche, salud limitada, robotics y fabrication.

Es exclusivamente documental. No implementa codigo, tests, scripts, runtime, endpoints, router, CI, requirements, cambios en `PolicyEngine`, cambios en `ApprovalGateway`, conexion MissionControl/Hermes, adapters reales, Home Assistant, dispositivos, puertos, APIs externas ni dependencias.

La decision central es:

```text
David puede hablar con JARVIS en casa.
La casa no gobierna.
El hardware no gobierna.
Home Assistant no gobierna.
JARVIS Gateway recibe.
PolicyEngine decide.
Restriction Registry explica limites.
ApprovalGateway aprueba cuando aplica.
Las capabilities fisicas ejecutan solo lo permitido.
```

El objetivo es fijar como JARVIS puede evolucionar hacia un sistema fisico/domestico realista, local-first y privado sin crear bypasses peligrosos. La capa domestica debe ampliar la presencia de JARVIS en el entorno de David, no convertir sensores, camaras, wake word o hubs en caminos paralelos de ejecucion.

## 2. Interfaz fisica/domestica vs runtime principal

La capa Home / Voice / Sensor Hardware es una interfaz y un conjunto de capabilities. No es el runtime principal de JARVIS.

Puede:

- capturar voz local.
- detectar wake word local.
- transcribir audio mediante STT local cuando sea posible.
- sintetizar respuesta con TTS local cuando sea posible.
- recibir eventos de sensores.
- consultar estado domestico.
- preparar automatizaciones.
- ejecutar cambios fisicos de bajo riesgo si policy lo permite.
- pedir aprobacion para acciones sensibles.
- responder por altavoz, movil, smart display, espejo o notificacion.

No debe:

- llamar a Hermes directamente.
- saltarse JARVIS Gateway.
- decidir permisos finales.
- ejecutar acciones sensibles solo por wake word.
- tratar presencia, voz o rostro como aprobacion universal.
- usar Home Assistant como backdoor.
- exponer red domestica sin auth/audit.
- enviar audio, video, imagenes, biometricos o eventos sensibles a nube por defecto.
- guardar logs con audio/video/rostros/secretos por defecto.

El runtime principal sigue siendo JARVIS: natural runtime, intent, policy, approvals, restrictions, capability routing, auditoria y respuesta final. El hardware solo aporta entradas, salidas y capacidades acotadas.

## 3. Regla de seguridad no negociable

Ningun hardware puede saltarse:

- `JARVIS Gateway`.
- Natural Runtime / Intent.
- `PolicyEngine`.
- `Restriction Registry`.
- `ApprovalGateway`.
- Capability Router.
- Audit/Event Log.

Esto aplica a:

- Home Assistant.
- hubs Zigbee/Z-Wave/Matter/Thread.
- altavoces.
- microfonos.
- camaras.
- sensores.
- cerraduras.
- alarmas.
- router/red domestica.
- PC/Mac control.
- robots/drones futuros.
- cualquier adapter o skill de hardware.

La presencia fisica de David en casa no baja el riesgo. La voz de David no baja el riesgo por si sola. Un rostro reconocido no baja el riesgo por si solo. Un dispositivo de confianza no baja el riesgo por si solo.

Las senales de presencia, voz, speaker identity o rostro pueden aumentar confianza contextual, pero no sustituyen policy ni approval cuando la accion es sensible, fuerte, irreversible, publica, de coste relevante, de seguridad, de salud o de credenciales.

## 4. Home Assistant como adapter, no bypass

Home Assistant puede ser una pieza muy util para integrar dispositivos domesticos porque ya soporta entidades, escenas, automatizaciones, dashboards y protocolos de hogar.

Pero dentro de JARVIS debe vivir como adapter/capability:

```text
JARVIS -> Capability Router -> HomeAssistantAdapter -> Home Assistant -> Device
```

No como:

```text
Wake word / Movil / Sensor -> Home Assistant -> accion sensible directa
```

Home Assistant u otros hubs pueden:

- exponer entidades y estados.
- ejecutar servicios domesticos acotados.
- recibir comandos ya autorizados.
- reportar eventos a JARVIS.
- mantener automatizaciones propias de bajo riesgo si David las configura manualmente fuera de JARVIS.

No deben:

- conceder permisos de JARVIS.
- ejecutar cerraduras, alarmas, camaras privadas, red, gasto relevante o acciones destructivas sin policy/approval.
- tratar una automatizacion de Home Assistant como autorizacion implicita de JARVIS.
- llamar a Hermes directo.
- ocultar acciones del audit log de JARVIS cuando la accion nace desde JARVIS.

Si una automatizacion externa a JARVIS existe en Home Assistant, JARVIS debe tratarla como entorno observado o capability externa, no como permiso para replicarla sin evaluacion.

## 5. Relacion con modos de despliegue

Este contrato depende de PR #57.

### Local Mode

Uso recomendado:

- voz local en el PC o en un dispositivo local.
- STT/TTS local.
- control de PC/Mac bajo scope.
- Home Assistant accesible en red local.
- camaras y sensores procesados localmente.
- pruebas domesticas manuales y opt-in.

Reglas:

- no streaming externo por defecto.
- no puertos publicos para control remoto.
- no accion sensible sin approval.
- no lectura de secretos ni credenciales de dispositivos sin diseno aprobado.

### Server Mode

Uso recomendado:

- notificaciones.
- estado read-only no sensible.
- Mobile Approval Center.
- colas o eventos que pueden esperar.
- dashboards seguros.

Reglas:

- el servidor no obtiene control libre del hogar.
- el servidor no debe recibir audio/video domestico sensible por defecto.
- acciones fisicas sensibles requieren approval y, cuando aplique, confirmacion local.
- si una capability local no esta disponible, JARVIS debe esperar, rechazar o pedir alternativa segura.

### Hybrid Mode

Uso recomendado:

- servidor 24/7 como gateway y notificador.
- worker local en casa para voz, sensores, vision y Home Assistant.
- movil como interfaz de aprobacion.
- ejecucion local de acciones domesticas ya autorizadas.

Reglas:

- el worker local no es una puerta trasera.
- el servidor no manda comandos arbitrarios al hogar.
- todo job trae envelope, source, device, policy, approval si aplica, scope y audit.
- local/server/hybrid comparten el mismo policy contract.

## 6. Relacion con Mobile Approval Center

PR #58 define que el movil es interfaz, no runtime. En la capa domestica, el movil puede:

- recibir aprobaciones de cerraduras, alarmas, camaras, red o gasto.
- mostrar origen: habitacion, dispositivo, sensor o voz.
- mostrar accion exacta, riesgo, alcance, duracion y alternativa segura.
- permitir aprobar, denegar, cancelar o pedir prepare-only.

El movil no debe:

- llamar Home Assistant directo como bypass de JARVIS para acciones sensibles.
- aprobar acciones ambiguas como "hazlo todo".
- convertir reconocimiento de cara/voz en aprobacion global.
- aprobar hard boundaries.

## 7. Relacion con Hermes inside JARVIS

PR #56 establece que Hermes es runtime interno, no autoridad de seguridad.

En este contrato:

- Hermes puede ayudar a interpretar intenciones, preparar planes o ejecutar capabilities permitidas si JARVIS lo solicita.
- Hermes no debe recibir eventos crudos de hardware como autoridad directa.
- Hermes no decide si se abre una puerta, se publica un clip, se cambia la red o se activa una alarma.
- Si una skill futura usa hardware, debe entrar como capability declarada, con riesgo, policy, approvals, scope y audit.

Flujo valido:

```text
Home / Voice / Sensor source
  -> JARVIS Gateway
  -> Natural Runtime / Intent
  -> PolicyEngine
  -> Restriction Registry
  -> ApprovalGateway si aplica
  -> Capability Router
  -> Adapter fisico autorizado
  -> Audit/Event Log
  -> Response / Notification
```

## 8. Relacion con Restriction Registry

PR #59 define restricciones explicables, overrides acotados y hard boundaries.

La capa Home / Voice / Sensor necesita restricciones especificas para:

- dispositivos permitidos.
- habitaciones.
- camaras privadas.
- biometria.
- invitados.
- voz autorizada.
- presencia.
- red domestica.
- gasto energetico.
- acciones fisicas.
- robots/drones futuros.
- salud/seguridad.
- retention de audio/video/eventos.

David debe poder preguntar por que una accion domestica fue bloqueada y recibir:

- que restriccion se activo.
- que protege.
- que riesgo evita.
- que approval seria necesaria, si aplica.
- que alternativa segura existe.
- si se puede pedir override temporal.
- si es hard boundary.

Un override domestico debe tener scope estricto: dispositivo, habitacion, accion, coste, duracion, source, modo y rollback. No existe "aprueba toda la casa para siempre".

## 9. Relacion con skills y hardware capabilities futuras

Las futuras skills/hardware capabilities deben declarar:

- `capability_id`.
- adapter requerido.
- dispositivos o entidades que puede tocar.
- datos que puede leer.
- acciones que puede ejecutar.
- categorias de riesgo.
- modos soportados: local, server, hybrid, mobile.
- approval esperado.
- retention y logging.
- safe alternatives.
- rollback o apagado.
- si usa audio, video, biometria, presencia, red, energia, salud o accion fisica.

Una skill domestica no recibe permisos por estar instalada. Instalar una skill no autoriza usar cerraduras, camaras, red, electricidad, identidad, sensores de salud ni robots.

## 10. Capacidades realistas documentadas

### Voz local

- Wake word local preferido para "Hola JARVIS" o equivalente.
- STT local preferido para datos sensibles.
- TTS local preferido para respuestas privadas.
- Microfono array o voice satellites para cobertura por habitacion.
- Barge-in para interrumpir TTS o corregir una accion pendiente.
- Speaker identity / authorized speaker identity como senal contextual, no como permiso absoluto.

### Domotica

- Luces.
- Enchufes.
- Persianas.
- Clima.
- Escenas.
- Automatizaciones contextuales.
- Simulacion de presencia.
- Modo trabajo profundo.
- Red de invitados auto-expirable.
- Optimizacion electrica por tarifas.

### Sensores

- Puertas y ventanas.
- Movimiento.
- Presencia.
- Temperatura.
- Humedad.
- Energia.
- Deteccion de presencia por habitacion.
- Sensores personalizados.
- Alertas basadas en sensores.
- Recordatorios contextuales.

### Vision local

- Camaras con vision local.
- Deteccion de objetos en tiempo real.
- Reconocimiento facial autorizado.
- Entrada/puerta principal.
- Smart mirror / projection layer.

La vision local debe minimizar salida externa. Una captura, clip o inferencia biometrica no debe salir de casa sin approval explicita.

### PC y entorno

- Control de PC/Mac por voz como capability separada.
- Abrir aplicaciones, ventanas o documentos bajo scope.
- Preparar workflows locales.
- No ejecutar comandos peligrosos por voz sin policy/approval.

### Futuro avanzado

- Inventario de nevera / recetas.
- Deteccion de caidas con limites claros.
- OBD-II / carga de coche.
- Robots/drones.
- Fabrication layer.

Estas capacidades requieren contratos posteriores. Salud, caidas, coche, robots, drones y fabricacion no deben implementarse como automatizaciones ligeras.

## 11. Categorias de riesgo

| Categoria | Significado | Ejemplos |
| --- | --- | --- |
| `read-only sensor/status` | Consulta de estado sin side effects ni datos sensibles. | Temperatura, luz encendida, consumo agregado. |
| `local notification` | Aviso local o privado sin accion fisica. | "La puerta lleva abierta 10 minutos." |
| `low-risk environment change` | Cambio reversible y local de bajo impacto. | Encender luz, escena simple, ajustar brillo. |
| `physical access/security` | Control de acceso o seguridad domestica. | Cerradura, puerta, garaje, alarma. |
| `camera/biometric` | Imagen, video, rostro, huella, biometria o inferencias visuales. | Mostrar camara, detectar rostro, clip de entrada. |
| `identity recognition` | Identificar quien habla, entra o aparece. | Speaker identity, face recognition autorizado. |
| `home network change` | Router, WiFi, VLAN, invitados, firewall. | Crear red invitado, bloquear dispositivo. |
| `cost/energy spending` | Acciones con coste electrico o economico. | Clima intensivo, carga coche, electrodomesticos. |
| `irreversible/destructive physical action` | Accion fisica dificil de revertir o con dano potencial. | Cortar energia critica, abrir valvula, fabricacion. |
| `health/safety critical` | Salud, caidas, emergencia, medicacion, fuego, gas. | Deteccion de caidas, alerta medica, estufa/gas. |
| `secrets/credentials` | Claves de hubs, router, tokens, contrasenas. | Credenciales Home Assistant/router/camaras. |
| `external/public exposure` | Enviar datos fuera o hacerlos publicos. | Subir clip, enviar foto, exponer dashboard. |

## 12. Approval esperado

| Accion | Decision esperada |
| --- | --- |
| Consultar estado de sensor no sensible. | `allowed` si policy lo permite. |
| Consultar estado con datos privados o presencia sensible. | `allowed` o `requires_approval` segun scope. |
| Encender una luz o escena simple. | `allowed` o `normal approval` segun configuracion. |
| Apagar todas las luces. | `allowed` o `normal approval` segun hora, presencia y contexto. |
| Abrir cerradura, puerta, garaje o desactivar alarma. | `sensitive approval` o `strong approval`. |
| Mostrar camara privada o biometria. | `sensitive approval` o `strong approval` segun contexto. |
| Publicar imagen/video o enviarlo fuera de casa. | `strong approval`. |
| Cambiar router, WiFi, VLAN o firewall. | `sensitive approval` o `strong approval`. |
| Crear red de invitados auto-expirable. | `sensitive approval` si cambia red real. |
| Accion con gasto energetico relevante. | `normal approval` o `sensitive approval` segun coste. |
| Acciones medicas/salud. | No ejecutar sin diseno profesional; `denied` o `future_contract`. |
| Robots/drones. | `strong approval` o `future_contract`. |
| Accion fisica irreversible. | `strong approval` o `denied`. |
| Leer secretos/credenciales de hubs o router. | `denied` o `strong approval` solo con contrato futuro. |

## 13. Reglas de privacidad

- No audio continuo a nube por defecto.
- Wake word local preferido.
- STT local preferido para datos sensibles.
- TTS local preferido para respuestas privadas.
- Camaras y biometria requieren consentimiento, finalidad y scope.
- No reconocimiento facial de terceros sin autorizacion explicita.
- No speaker identity de invitados sin aviso y consentimiento.
- No enviar clips, capturas, audio o transcripts sensibles fuera sin approval.
- Logs no deben guardar audio/video sensible por defecto.
- Logs no deben guardar rostros, biometricos, secretos ni payloads completos sensibles por defecto.
- Retention debe ser configurable.
- Invitados deben tener modo privacy-aware.
- No usar datos emocionales o de salud sin consentimiento explicito.
- No usar sensores para vigilancia oculta.
- No inferir salud, estado emocional, relaciones o comportamiento privado como hecho sin base y consentimiento.
- No convertir presencia en autorizacion automatica.
- No convertir "usuario esta en casa" en permiso para acciones sensibles.

## 14. Arquitectura conceptual

```text
Mobile / Local Voice / Smart Display / Sensor Event
  -> JARVIS Gateway
  -> Natural Runtime / Intent
  -> PolicyEngine
  -> Restriction Registry
  -> ApprovalGateway si aplica
  -> Capability Router
  -> HomeAssistantAdapter / VoiceAdapter / VisionAdapter / SensorAdapter / PCControlAdapter
  -> Audit/Event Log
  -> Response / Notification
```

Reglas del flujo:

1. Todo origen se normaliza en JARVIS Gateway.
2. El natural runtime interpreta intencion, confianza, contexto y riesgo.
3. `PolicyEngine` evalua antes de ejecutar.
4. `Restriction Registry` explica limites, scopes, overrides y hard boundaries.
5. `ApprovalGateway` gestiona approvals normales, sensibles o fuertes cuando aplica.
6. Capability Router solo enruta acciones permitidas.
7. Cada adapter ejecuta una capability acotada, no permisos globales.
8. Audit registra origen, dispositivo, accion, riesgo, decision y resultado.
9. La respuesta vuelve a David por voz, movil, smart display o notificacion.

## 15. Adapters conceptuales

| Adapter | Responsabilidad | No debe hacer |
| --- | --- | --- |
| `HomeAssistantAdapter` | Consultar entidades y ejecutar servicios domesticos permitidos. | Ejecutar cerraduras, alarmas, red o camaras sensibles sin policy/approval. |
| `VoiceAdapter` | Wake word, STT, TTS, voice satellites y barge-in. | Convertir voz en permiso o mandar audio sensible a nube por defecto. |
| `VisionAdapter` | Vision local, objetos, camaras y biometria autorizada. | Enviar clips/capturas fuera ni reconocer terceros sin consentimiento. |
| `SensorAdapter` | Eventos de sensores, presencia, energia, temperatura y custom sensors. | Vigilar de forma oculta o inferir salud sin contrato. |
| `PCControlAdapter` | Control local de PC/Mac bajo scope. | Ejecutar comandos peligrosos, leer secretos o actuar como Hermes directo. |
| `NetworkAdapter` futuro | Red invitados, router, VLAN y dispositivos. | Cambiar red sin approval reforzado y rollback. |
| `VehicleAdapter` futuro | OBD-II, carga coche y estado. | Controlar coche o carga critica sin contrato especifico. |
| `RoboticsAdapter` futuro | Robots, drones o fabrication. | Operar sin kill switch, strong approval y contrato propio. |

## 16. Anti-patterns

- Home Assistant ejecutando acciones sensibles sin JARVIS policy.
- Camaras enviando video a nube por defecto.
- Wake word ejecutando acciones reales automaticamente.
- Movil o home hub llamando Hermes directo.
- Sensores de salud usados para decisiones fuertes sin consentimiento.
- Reconocimiento facial para visitantes sin aviso.
- Red domestica expuesta a internet sin auth.
- Logs con audio, video, rostros, secretos o transcripts sensibles.
- Robots/drones sin kill switch ni approval.
- Modo "casa inteligente" como excusa para autoejecucion peligrosa.
- Voice satellite con token amplio guardado localmente sin vault/diseno.
- Automatizaciones que degradan `strong_approval` a `allowed` por presencia.
- Borrar clips o logs para ocultar acciones a David.
- Publicar capturas domesticas por conveniencia.
- Usar biometria como unica confirmacion para acciones irreversibles.

## 17. Ejemplos conceptuales

| Solicitud | Respuesta esperada | Decision | Safe alternative |
| --- | --- | --- | --- |
| "Hola JARVIS, activa modo cine." | Preparar escena: bajar luces, cerrar persianas, ajustar TV/clima si esta configurado. | `allowed` o `requires_approval` | Mostrar plan de escena sin ejecutar. |
| "Apaga todas las luces." | Verificar alcance por habitaciones y presencia; apagar si policy permite. | `allowed` | Apagar solo luces de habitaciones vacias. |
| "Abre la puerta." | Identificar puerta, origen y riesgo; pedir confirmacion reforzada. | `strong_approval` | Mostrar estado de la puerta o avisar al movil. |
| "Ensename quien esta en la entrada." | Mostrar camara local de entrada si esta autorizada. | `requires_approval` o `strong_approval` | Describir sensor de timbre/movimiento sin mostrar imagen. |
| "Deje la estufa encendida?" | Consultar sensor/enchufe/energia si existe; no inventar certeza. | `allowed` o `requires_approval` | Decir que no hay sensor fiable y sugerir comprobacion manual. |
| "Estoy entrando en modo trabajo profundo." | Activar escena de foco: no molestar, luces, recordatorios y bloqueos suaves. | `allowed` o `requires_approval` | Preparar checklist de foco sin cambiar dispositivos. |
| "Da WiFi a una visita durante 2 horas." | Crear red invitado con expiracion si NetworkAdapter futuro lo soporta y policy aprueba. | `requires_approval` o `strong_approval` | Mostrar instrucciones manuales del router sin cambiarlo. |
| "Optimiza la lavadora para la tarifa barata." | Programar o sugerir ventana de bajo coste si dispositivo lo permite. | `requires_approval` | Recordatorio local cuando empiece la tarifa barata. |
| "Revisa si hay dispositivos raros en mi red." | Consultar inventario si hay NetworkAdapter autorizado; no bloquear sin approval. | `requires_approval` | Preparar lista de pasos manuales para revisar el router. |
| "Reconoce si soy yo por voz." | Usar speaker identity autorizado como senal contextual, no permiso final. | `requires_approval` | Responder que puede comparar voz solo si esta configurado con consentimiento. |
| "Si me caigo, avisa." | Capacidad de salud/seguridad critica; requiere contrato profesional y limites. | `future_contract` | Preparar checklist de opciones y contactos de emergencia sin activar nada. |
| "Controla el PC y abre el informe de ayer." | Abrir documento local bajo scope si PCControlAdapter lo permite. | `allowed` o `requires_approval` | Decir ruta/candidatos y pedir confirmacion antes de abrir. |
| "Publica el video de la camara de entrada." | Bloquear publicacion sin approval fuerte y scope exacto. | `strong_approval` o `denied` | Guardar clip local o describir evento sin publicar. |
| "Activa la alarma aunque haya alguien dentro." | Riesgo de seguridad/presencia; requiere aclaracion y approval fuerte. | `strong_approval` | Activar modo parcial o pedir confirmacion local. |
| "Apaga la nevera para ahorrar energia." | Riesgo de dano/perdida; probablemente denegar. | `denied` | Sugerir revisar consumo o temperatura. |
| "Haz que el drone revise el tejado." | Robotics/drone requiere contrato futuro, kill switch y approval fuerte. | `future_contract` | Preparar checklist manual de inspeccion. |

## 18. Eventos y auditoria

Cada accion o decision domestica futura debe registrar:

- request id.
- source: mobile, local voice, smart display, sensor event, automation.
- user o speaker si esta autorizado.
- device id.
- room o zona si aplica.
- adapter/capability.
- accion solicitada.
- accion ejecutada o bloqueada.
- risk category.
- policy decision.
- restriction activada si existe.
- approval id si aplica.
- modo: local, server o hybrid.
- resultado.
- errores.
- timestamp.

La auditoria no debe guardar por defecto:

- audio crudo.
- video crudo.
- imagenes completas.
- rostros.
- biometricos.
- secretos.
- passwords.
- tokens.
- payloads completos de sensores sensibles.

Cuando sea necesario guardar evidencia, debe existir retention, scope, razon, consentimiento y deletion path.

## 19. Criterios de aceptacion para futura implementacion

Una futura PR de codigo solo deberia aceptarse si:

- No hay hardware bypass de `PolicyEngine`.
- Home Assistant u otros hubs son adapters/capabilities detras de JARVIS.
- Adapters separados y testeables.
- Ningun streaming externo por defecto.
- Wake word local no ejecuta acciones sensibles por si solo.
- STT/TTS local se prefiere para datos sensibles.
- Camara, biometria y salud requieren consentimiento y policy.
- Audit registra origen, dispositivo, accion, riesgo, decision y resultado.
- Restricciones se muestran en lenguaje humano.
- Safe alternatives se devuelven para acciones denegadas.
- Tests cubren `allowed`, `requires_approval`, `strong_approval`, `denied` y `future_contract`.
- Local, server y hybrid comparten el mismo policy contract.
- Mobile Approval Center muestra scope, riesgo, duracion y alternativa segura.
- Logs no guardan audio/video/rostros/secretos por defecto.
- Retention es configurable.
- Invitados tienen modo privacy-aware.
- Speaker identity y face recognition no sustituyen approvals fuertes.
- Home network changes tienen rollback o alternativa manual.
- Robots/drones futuros tienen shutdown/kill switch, strong approval y contrato propio.
- Documentacion clara para David.

## 20. Fuera de alcance

PR #61 no implementa:

- codigo.
- tests.
- scripts.
- runtime.
- endpoints.
- router.
- CI.
- requirements.
- cambios en `PolicyEngine`.
- cambios en `ApprovalGateway`.
- conexion MissionControl/Hermes.
- Home Assistant.
- adapters reales.
- dispositivos.
- puertos.
- APIs externas.
- dependencias.
- pytest.
- smoke tests.
- `.jarvis`.
- `.codegraph`.
- commit.
- PR.

Este documento solo fija el contrato que deberan respetar futuras implementaciones de Home / Voice / Sensor Hardware Layer.

## 21. Resultado esperado de esta PR

Al terminar esta PR debe existir solo un contrato documental revisable para decidir como evolucionar JARVIS hacia una presencia fisica/domestica segura.

No debe existir evidencia de integracion real, instalacion, configuracion de dispositivos, adapters, puertos, endpoints, cambios de runtime ni automatizacion fisica.

En esta PR, Home / Voice / Sensor Hardware Layer queda como contrato futuro documentado, no como feature implementada.
