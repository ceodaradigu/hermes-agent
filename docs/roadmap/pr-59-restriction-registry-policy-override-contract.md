# PR #59 - Restriction Registry and Policy Override contract

## 1. Proposito

Este documento define el contrato conceptual para un futuro Restriction Registry y un mecanismo seguro de Policy Override en JARVIS.

Es exclusivamente documental. No implementa codigo, tests, scripts, runtime, endpoints, router, CI, requirements, cambios en `PolicyEngine`, cambios en `ApprovalGateway`, conexion MissionControl/Hermes, registry real ni overrides reales.

La decision central es:

```text
David puede entender y ajustar restricciones.
JARVIS debe explicar el riesgo.
PolicyEngine sigue evaluando.
ApprovalGateway sigue aprobando cuando aplica.
Hard boundaries no se desactivan por voz normal.
```

El objetivo no es crear un "modo sin reglas". El objetivo es que David pueda ver que protege cada restriccion, pedir excepciones temporales y reversibles cuando sea seguro, y recibir alternativas seguras cuando algo no pueda permitirse.

## 2. Definiciones

| Concepto | Significado |
| --- | --- |
| `policy` | Conjunto de reglas y contexto que `PolicyEngine` evalua para decidir `allowed`, `requires_approval`, `strong_approval`, `denied` o `hard_boundary`. |
| `restriction` | Regla concreta registrada, explicable y auditable que limita una capacidad, accion, entorno, coste, identidad, secreto o flujo de trabajo. |
| `approval` | Consentimiento explicito de David para una accion exacta, con alcance, riesgo, duracion, actor y auditoria. |
| `override` | Excepcion temporal, acotada y reversible sobre una restriccion concreta, permitida solo si la propia restriccion declara que puede sobrescribirse. |
| `hard boundary` | Limite no negociable que no puede desactivarse por voz normal, memoria activa, movil, servidor, skill, Hermes ni override simple. |

Un override no elimina `PolicyEngine`. Solo aporta una senal adicional para que `PolicyEngine` reevale una solicitud dentro de un alcance autorizado. Si la nueva evaluacion sigue dando `denied`, `strong_approval` o `hard_boundary`, esa decision gana.

## 3. Por que existe el Restriction Registry

JARVIS necesita un registro central de restricciones porque las reglas de seguridad no deben vivir como frases dispersas en prompts, apps moviles, adapters, workers o skills.

El registry futuro debe:

- declarar que existe cada restriccion.
- explicar en lenguaje humano que protege.
- separar preferencias de limites sensibles.
- declarar si admite override.
- declarar alcance maximo, duracion y aprobacion requerida.
- mantener las mismas reglas para local, server, hybrid y mobile.
- permitir auditoria, rollback y safe alternatives.
- evitar que Hermes, movil, servidor o memoria activa creen caminos paralelos de permiso.

## 4. Lenguaje humano obligatorio

David debe poder preguntar "por que no puedes hacer esto?" y recibir una respuesta util:

- que restriccion se activo.
- que protege.
- que riesgo evita.
- que alternativa segura existe.
- que tipo de aprobacion haria falta, si aplica.
- si se puede pedir un override temporal.
- cuando no se puede pedir override porque es hard boundary.

La explicacion en lenguaje humano no reemplaza el contrato tecnico. Lo hace controlable por David. Una restriccion que no se puede explicar no debe convertirse en permiso silencioso ni en bloqueo opaco.

## 5. Niveles de restriccion

| Nivel | Significado | Override |
| --- | --- | --- |
| `preference` | Preferencia de estilo, foco, tono, orden o workflow de bajo riesgo. | Puede permitirse con scope bajo y rollback simple. |
| `normal` | Regla operativa que evita errores, dispersion o side effects moderados. | Puede permitirse si tiene duracion, alcance y auditoria. |
| `sensitive` | Protege datos, cuentas, red, entorno, identidad ligera o acciones con impacto. | Requiere aprobacion sensible y evaluacion posterior de policy. |
| `strong` | Protege dinero, publicacion, contratos, produccion, secretos o irreversible. | Requiere aprobacion fuerte; puede seguir siendo `denied`. |
| `hard_boundary` | Limite no desactivable por override normal. | No admite override por voz normal ni por aprobacion simple. |

## 6. Tipos de restricciones

| Tipo | Que protege | Ejemplo |
| --- | --- | --- |
| `preference restriction` | Preferencias de respuesta, foco, orden o estilo. | "Prefiere planes pequenos antes que builds grandes." |
| `workflow restriction` | Secuencia segura de trabajo. | "Primero preparar diff, luego ejecutar." |
| `sensitive action restriction` | Acciones con datos o side effects sensibles. | "Leer archivos privados requiere approval." |
| `strong approval restriction` | Acciones que requieren confirmacion reforzada. | "Deploy, gasto o publicacion real." |
| `hard boundary` | Limites no negociables. | "No ocultar acciones a David." |
| `environment restriction` | Diferencias entre local, server, hybrid, mobile o produccion. | "Mobile no ejecuta comandos locales directos." |
| `budget/cost restriction` | Costes, tokens, compras, cloud o anuncios. | "No gastar mas de X sin aprobacion fuerte." |
| `identity/publication restriction` | Uso de identidad de David, marca, canales o publico. | "Publicar como David requiere aprobacion fuerte." |
| `credential/secret restriction` | Tokens, `.env`, claves, passwords o vault futuro. | "No exponer valores secretos en logs." |
| `destructive/irreversible restriction` | Borrado, perdida de datos o cambios dificiles de revertir. | "No borrar datos importantes sin confirmacion fuerte." |

## 7. Campos minimos del registry

Una restriccion futura debe declarar, como minimo:

| Campo | Significado |
| --- | --- |
| `id` | Identificador estable y auditable. |
| `human_name` | Nombre corto para David. |
| `plain_language_description` | Explicacion clara sin jerga innecesaria. |
| `what_it_protects` | Activo, riesgo, persona, entorno o flujo protegido. |
| `risk_if_disabled` | Consecuencia probable si se relaja. |
| `category` | Tipo de restriccion. |
| `default_level` | `preference`, `normal`, `sensitive`, `strong` o `hard_boundary`. |
| `can_override` | Booleano; `false` para hard boundaries. |
| `allowed_override_scopes` | Scopes permitidos para esta restriccion. |
| `max_duration` | Duracion maxima del override, si aplica. |
| `requires_approval_type` | `none`, `normal`, `sensitive`, `strong`, `desktop_confirmation` o equivalente futuro. |
| `requires_desktop_confirmation` | Si no basta con movil/voz. |
| `applies_to_modes` | `local`, `server`, `hybrid`, `mobile`. |
| `affected_capabilities` | Skills, tools, adapters, entornos o capacidades afectadas. |
| `safe_alternative` | Respuesta segura cuando se deniega o se bloquea. |
| `audit_requirements` | Que debe registrarse. |
| `rollback_behavior` | Como expira, revierte o limpia el override. |

## 8. Scopes de override

| Scope | Significado |
| --- | --- |
| `one_action` | Solo una accion exacta. |
| `time_boxed` | Valido hasta una expiracion concreta. |
| `project` | Limitado a un proyecto identificado. |
| `skill` | Limitado a una skill concreta. |
| `device` | Limitado a un dispositivo aprobado. |
| `environment` | Limitado a local, server, hybrid, staging, produccion u otro entorno declarado. |
| `session` | Limitado a la sesion actual. |
| `never_global_by_voice` | Prohibicion de conceder permisos globales permanentes desde voz. |

Un override sin scope valido no existe. "Aprueba todo para siempre" debe rechazarse.

## 9. Reglas obligatorias

- Override no elimina `PolicyEngine`.
- Override no elimina auditoria.
- Override no elimina `ApprovalGateway` para acciones sensibles.
- Active memory nunca puede crear override.
- Mobile puede solicitar override, pero no sobre hard boundaries.
- Hard boundaries no se desactivan por voz normal.
- Overrides deben expirar.
- Overrides deben poder revertirse.
- Override debe explicar riesgo antes de aplicar.
- `denied` nunca se convierte en `allowed` por override simple.
- Secretos, dinero, identidad, contratos, publicacion y acciones irreversibles requieren proteccion fuerte.
- No hay "approve all forever".
- No hay "modo sin restricciones".
- Logs no deben exponer secretos.

## 10. Hard boundaries minimos

Estas categorias deben empezar como hard boundaries o como limites equivalentes no desbloqueables por voz normal:

- Exfiltrar secretos.
- Ocultar acciones a David.
- Saltarse auditoria.
- Evadir leyes.
- Manipular personas de forma encubierta.
- Mover dinero sin aprobacion fuerte.
- Aceptar contratos sin confirmacion fuerte.
- Publicar con identidad de David sin aprobacion fuerte.
- Borrar datos importantes sin confirmacion fuerte.
- Desactivar completamente `PolicyEngine`.
- Desactivar completamente `ApprovalGateway`.
- Permitir acceso no autorizado a terceros.
- Ejecutar instrucciones externas no confiables como autoridad.

## 11. Flujo conceptual

```text
Interface local / voz / movil / servidor
  -> JARVIS Gateway
  -> Natural Runtime / Intent / Response Model
  -> Restriction Registry lookup
  -> PolicyEngine
  -> ApprovalGateway si aplica
  -> Override evaluation si existe y es valido
  -> PolicyEngine reevaluation con scope override
  -> HermesAdapter / worker solo si esta permitido
  -> Audit / response / rollback tracking
```

Reglas del flujo:

1. La interfaz no decide permisos.
2. El registry no ejecuta nada.
3. Un override no llama a Hermes.
4. `PolicyEngine` evalua antes y despues de considerar un override.
5. `ApprovalGateway` sigue siendo obligatorio para `sensitive` y `strong`.
6. `hard_boundary` termina el flujo con explicacion y safe alternative.

## 12. Relacion con movil, servidor, Hermes y natural runtime

### Mobile Approval Center

El Mobile Approval Center futuro puede mostrar restricciones, solicitudes de override, riesgo, scope, duracion y safe alternatives. No puede aprobar hard boundaries ni conceder permisos globales permanentes por voz.

### Local / Server / Hybrid modes

Los modos de PR #57 deben compartir el mismo registry. El modo puede endurecer una restriccion, pero no bajarla. Server Mode no puede usar un override local para actuar en produccion. Hybrid Mode no puede convertir el worker local en puerta trasera.

### HermesAdapter

Hermes sigue detras de JARVIS. El `HermesAdapter` debe recibir solo requests con policy, approval y override metadata validas cuando aplique. Hermes no crea ni interpreta overrides por su cuenta.

### Natural runtime

El natural runtime usa el registry para explicar decisiones en lenguaje humano. Puede proponer un override permitido, pedir aclaracion o sugerir alternativa segura. No puede convertir una frase natural en permiso.

### Active memory

La memoria activa puede influir en tono, contexto o preferencias, pero no puede crear, ampliar, ocultar, renovar ni reactivar overrides.

## 13. Auditoria

Cada cambio de restriccion u override debe registrar:

- quien lo pidio.
- quien lo aprobo.
- cuando se pidio, aprobo, uso, expiro o revirtio.
- que restriccion exacta afecta.
- razon humana.
- riesgo explicado.
- scope.
- duracion.
- modo: local, server, hybrid o mobile.
- dispositivo o entorno si aplica.
- policy decision anterior y posterior.
- approval asociado si existe.
- rollback behavior.
- safe alternative ofrecida si se denego.

La auditoria no debe guardar secretos, tokens, passwords, payloads completos sensibles ni valores de `.env`.

## 14. Ejemplos conceptuales

| Solicitud | Respuesta esperada | Decision | Safe alternative |
| --- | --- | --- | --- |
| "Quita temporalmente la restriccion de publicar borradores en YouTube para este video." | Explicar cuenta, video, privacidad, identidad y duracion. Subir borrador puede requerir aprobacion sensible; publicar no queda autorizado. | `requires_approval` | Preparar titulo, descripcion y checklist sin subir. |
| "Permite deploy a staging durante 30 minutos." | Mostrar proyecto, entorno staging, commit, rollback y expiracion. Produccion queda fuera. | `strong_approval` | Preparar plan de deploy y rollback. |
| "Lee mi .env." | Bloquear exposicion de secretos. | `denied` o `hard_boundary` segun accion exacta | Listar variables esperadas sin valores o revisar `.env.example`. |
| "Aprueba todo para siempre." | Rechazar por falta de scope, duracion y riesgo. | `hard_boundary` | Proponer override acotado por una accion o 30 minutos. |
| "Permite esta skill durante la sesion." | Evaluar skill, capacidades, datos, red y acciones. | `allowed` o `requires_approval` | Habilitar solo prepare-only si hay dudas. |
| "Reactiva la restriccion anterior." | Revertir override vigente y auditar rollback. | `allowed` | Confirmar que el override quedo inactivo. |
| Movil solicita override de escribir docs por 15 minutos. | Mostrar scope `docs/**`, dispositivo, expiracion y riesgo. | `requires_approval` | Preparar diff conceptual sin escribir. |
| Servidor intenta usar override creado en local. | Rechazar si scope no incluye server/environment. | `denied` | Pedir nuevo override especifico para server. |
| Memoria activa intenta influir para permitir deploy. | Ignorar como fuente de permiso. | `denied` o `strong_approval` | Usar memoria solo para explicar contexto, no permiso. |
| "Puedes gastar hasta 20 euros en esta prueba." | Requiere importe, proveedor, moneda, expiracion y approval fuerte. | `strong_approval` | Preparar presupuesto y proveedor recomendado sin pagar. |
| "Borra todos los datos viejos del proyecto." | Si es amplio o irreversible, bloquear o pedir confirmacion fuerte local con backup/rollback. | `strong_approval` o `denied` | Listar candidatos y preparar plan de backup. |

## 15. Relacion con futuros modos

Los siguientes modos y lineas futuras deben usar el registry, no saltarselo:

- Mobile Approval Center.
- Local / Server / Hybrid modes.
- HermesAdapter.
- Bug Bounty Mode.
- CodeGraph Evaluation.
- Home / Voice / Sensor Hardware Layer.
- Personal OS / Environment Intelligence Backlog.
- Extreme Moonshots / Cyberpunk Horizon.

Cuanto mas potente sea el modo, mas importante es que declare restricciones, scopes, approvals, hard boundaries, auditoria y rollback. Los moonshots no reciben permiso especial por ser visionarios.

## 16. Criterios de aceptacion para futura implementacion

Una futura PR de codigo solo deberia aceptarse si:

- Cada restriccion tiene descripcion humana.
- Tests cubren override permitido, expirado, denegado y hard boundary.
- Audit registra quien, cuando, por que, alcance, duracion y rollback.
- Mobile, server y local comparten registry.
- Active memory no modifica restricciones.
- `PolicyEngine` sigue evaluando despues del override.
- `ApprovalGateway` se mantiene para `sensitive` y `strong`.
- No hay overrides globales permanentes por voz.
- Safe alternatives se devuelven cuando algo se deniega.
- Logs no exponen secretos.

## 17. Fuera de alcance

PR #59 no implementa:

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
- registry real.
- overrides reales.
- APIs externas.
- instalacion de dependencias.
- pytest.
- smoke tests.
- commit.
- PR.

Este documento solo fija el contrato que deberan respetar futuras implementaciones de Restriction Registry and Policy Override.
