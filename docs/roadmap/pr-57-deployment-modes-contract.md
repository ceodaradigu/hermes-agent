# PR #57 - JARVIS deployment modes contract

## 1. Proposito

Este documento define el contrato conceptual para futuros modos de despliegue de JARVIS:

- Local Mode.
- Server Mode.
- Hybrid Mode.

Es exclusivamente documental. No implementa despliegue, servidores, movil, endpoints, router, runtime nuevo, worker local, colas, vault, auth, CI, scripts, tests, `PolicyEngine`, `ApprovalGateway` ni conexion efectiva con Hermes.

El objetivo es fijar como JARVIS podra vivir en el ordenador de David, en un servidor 24/7 o en un modo hibrido sin cambiar la regla central:

```text
David habla con JARVIS.
JARVIS gobierna.
PolicyEngine decide.
ApprovalGateway aprueba cuando aplica.
Hermes ejecuta solo lo permitido.
```

El modo de despliegue puede cambiar donde vive la ejecucion, la disponibilidad y las capacidades disponibles. No puede reducir seguridad, saltarse approvals ni convertir a Hermes, al servidor o al worker local en una puerta trasera.

## 2. Por que disenar esto antes del movil

El movil sera una interfaz potente porque permite voz, aprobaciones, notificaciones y comandos remotos. Precisamente por eso no debe disenarse antes de tener claro donde se ejecutan las acciones y que limites aplican.

Antes de movil hay que definir:

- si una peticion se resuelve en local, servidor o worker privado.
- que capacidades existen en cada perfil.
- que datos puede ver cada entorno.
- como se autentica cada origen.
- donde se evalua policy.
- como se pide aprobacion.
- como se audita una accion remota.
- que pasa si el PC esta apagado o el worker falla.
- que nunca debe llegar a Hermes.

Sin este contrato, el movil podria acabar llamando al runtime directo, exponiendo un servidor sin auth, delegando comandos al PC por SSH ilimitado o duplicando reglas de policy por interfaz. Este documento evita esa arquitectura antes de que exista.

## 3. Principio comun

Todos los modos comparten el mismo contrato de seguridad:

- `PolicyEngine` se evalua antes de cualquier paso ejecutable.
- `ApprovalGateway` se usa para acciones sensibles, sin excepcion por modo.
- El sensitive boundary gana siempre.
- `denied` nunca se delega a worker ni llega a Hermes.
- `requires_approval` no se ejecuta hasta tener aprobacion valida y vigente.
- La memoria activa no cambia `requires_approval` a `allowed`.
- La memoria activa no cambia `denied` a una decision menos restrictiva.
- El servidor y el modo hibrido no degradan restricciones.
- El movil futuro no obtiene permiso especial por ser personal.
- Hermes sigue detras de JARVIS control layer mediante `HermesAdapter`.
- Los logs no deben exponer secretos.

## 4. Modos de despliegue

### Local Mode

Local Mode corre en el ordenador de David.

Uso recomendado:

- desarrollo.
- Codex/worktrees.
- terminal local.
- pruebas controladas.
- herramientas del PC.
- acceso a archivos/proyectos locales bajo policy.
- smoke tests manuales.
- trabajo documental o codigo acotado.

Puede:

- leer contexto local permitido.
- editar archivos dentro de rutas aprobadas por policy.
- ejecutar comandos locales acotados si policy lo permite.
- usar Hermes como runtime interno detras de JARVIS.
- operar sin exposicion publica.
- mantener memoria local solo por accion explicita.

No debe:

- abrir acciones sensibles sin aprobacion.
- leer secretos como `.env` sin decision explicita de policy y approval fuerte si una futura policy lo permite.
- instalar dependencias, hacer deploy, publicar, gastar o borrar de forma irreversible sin approval.
- exponer puertos publicos como forma de control remoto.
- tratar el acceso local como permiso global.
- hacer autoload de memoria.
- autoejecutar comandos peligrosos.

### Server Mode

Server Mode corre 24/7 en un servidor.

Uso recomendado:

- movil futuro.
- notificaciones.
- colas.
- dashboards.
- tareas no dependientes del PC local.
- estado read-only.
- orquestacion de trabajos diferidos.
- aprobaciones remotas.

Puede:

- recibir peticiones autenticadas desde interfaces futuras.
- mantener estado de orquestacion.
- guardar eventos de auditoria.
- encolar jobs.
- resolver tareas read-only o prepare-only dentro de su alcance.
- pedir aprobacion por canales configurados.
- decidir esperar o rechazar cuando una capacidad local no esta disponible.

No debe:

- tener acceso libre a todo el ordenador local.
- montar el filesystem local de David como si fuera propio.
- guardar secretos sin vault/diseno aprobado.
- ejecutar acciones sensibles sin `ApprovalGateway`.
- exponer endpoints publicos sin auth, rate limit y audit.
- llamar a Hermes directo saltandose JARVIS control layer.
- usar SSH ilimitado al PC como sustituto de worker autenticado.
- publicar, deployar, gastar o usar identidad sin aprobacion.

### Hybrid Mode

Hybrid Mode combina un servidor siempre vivo con el ordenador local como worker privado cuando este disponible.

Flujo conceptual:

```text
Mobile Client futuro / Interface
  -> JARVIS Gateway en servidor
  -> Server Orchestrator
  -> PolicyEngine
  -> ApprovalGateway si aplica
  -> Job Queue futura
  -> Local Worker autenticado cuando sea necesario
  -> HermesAdapter local o servidor segun alcance
  -> Audit/Event Log
```

Uso recomendado:

- movil hablando con servidor/JARVIS Gateway.
- servidor resolviendo lo que pueda de forma segura.
- delegacion al PC solo para steps que requieren contexto local.
- builds/tests locales bajo scope.
- trabajo en repos privados no disponibles en servidor.
- jobs que pueden esperar hasta que el PC este disponible.

Puede:

- decidir si resuelve en servidor, espera o delega a worker local.
- ejecutar en local solo steps permitidos y auditados.
- mantener colas y estado de jobs.
- registrar identidad de worker, origen, decision de policy y resultado.
- cancelar o expirar trabajos futuros.
- notificar aprobaciones pendientes.

No debe:

- convertir el worker local en puerta trasera.
- permitir que el servidor mande cualquier comando arbitrario al PC.
- delegar requests `denied`.
- ejecutar `requires_approval` antes de aprobacion valida.
- ampliar permisos locales por estar en modo hibrido.
- saltarse limites de ruta, red, credenciales o tiempo.
- ocultar fallos del worker como si fueran permisos.

## 5. Componentes conceptuales

| Componente | Responsabilidad conceptual | No debe hacer |
| --- | --- | --- |
| JARVIS Gateway | Entrada unica para interfaces futuras, normaliza origen, usuario, request y contexto. | Exponer JARVIS publico sin auth/audit ni llamar Hermes directo. |
| Deployment Profile | Declara modo activo, capacidades, limites, ubicacion de ejecucion y defaults seguros. | Usarse como excusa para bajar restricciones. |
| PolicyEngine | Decide `allowed`, `requires_approval` o `denied` antes de ejecutar. | Duplicarse por modo con reglas divergentes. |
| ApprovalGateway | Gestiona aprobaciones normales/fuertes con alcance, expiracion y auditoria. | Ser reemplazado por confirmaciones ad hoc del movil o servidor. |
| HermesAdapter | Unica puerta conceptual hacia Hermes. | Aceptar requests sin policy/approval o ampliar capacidades. |
| Local Worker | Worker privado del PC de David para steps locales permitidos. | Ejecutar comandos arbitrarios ni actuar como backdoor. |
| Server Orchestrator | Coordina requests, jobs, estado, retries limitados y delegacion. | Tocar filesystem local directo o ejecutar sensibles sin approval. |
| Mobile Client futuro | Interfaz de voz/comando/aprobacion para David. | Llamar Hermes/runtime directo o conceder permisos implicitos. |
| Audit/Event Log | Registra origen, modo, usuario, policy, approval, worker y resultado. | Guardar secretos, tokens o payloads completos sensibles. |
| Job Queue futura | Mantiene trabajos pendientes, diferidos, cancelables o delegables. | Convertir pending en autoejecucion peligrosa. |
| Capability Registry futura | Declara capacidades, riesgos, permisos y modos soportados. | Permitir capacidades vagas o no clasificadas. |
| Vault futuro | Guarda secretos si un diseno aprobado lo permite. | Ser sustituido por variables sueltas sin control ni auditoria. |
| Notification/Approval channel futuro | Notifica estado y solicita aprobacion con alcance claro. | Aprobar acciones ambiguas o sin registrar decision. |

## 6. Enrutamiento desde interfaces futuras

Ninguna interfaz futura debe decidir ejecucion por si sola.

Flujo minimo:

```text
Interface local / voz / movil / dashboard
  -> JARVIS Gateway
  -> Request envelope con source, user, deployment_profile y desired_outcome
  -> PolicyEngine
  -> ApprovalGateway si aplica
  -> Server Orchestrator o Local runtime segun modo
  -> HermesAdapter solo si la accion esta permitida
  -> Audit/Event Log
  -> Respuesta a David
```

Reglas:

1. Mobile no llama a Hermes directo.
2. Mobile no llama al runtime local directo.
3. Server no accede a archivos locales sin worker autenticado y policy.
4. Local Worker no acepta jobs sin envelope, policy y scope.
5. `denied` termina en JARVIS con alternativa segura si existe.
6. `requires_approval` crea approval request y queda pendiente.
7. `allowed` se ejecuta solo dentro del alcance declarado.
8. Si una capacidad no existe en el modo activo, JARVIS responde, espera, delega o rechaza segun policy.

## 7. PolicyEngine unico

Debe existir un contrato unico de policy para todos los modos.

El Deployment Profile puede aportar contexto:

- `mode`: `local`, `server` o `hybrid`.
- `source`: `cli`, `voice`, `mobile`, `dashboard`, `gateway`, `job`.
- `capabilities_available`.
- `allowed_paths`.
- `network_policy`.
- `credential_policy`.
- `worker_identity`.
- `approval_channel`.

Pero la decision sigue siendo del mismo `PolicyEngine`.

Ejemplo conceptual:

```json
{
  "request_id": "req_...",
  "deployment_profile": "hybrid",
  "source": "mobile",
  "capability": "code-execution",
  "target_environment": "local_worker",
  "policy_decision": "requires_approval",
  "reason": "mobile-originated local code execution requires explicit approval"
}
```

El modo puede hacer una accion mas restrictiva. No puede hacerla menos restrictiva.

## 8. ApprovalGateway unico

`ApprovalGateway` debe ser compartido por local, servidor, hibrido y movil futuro.

Una aprobacion debe declarar:

- accion exacta.
- origen.
- modo de despliegue.
- usuario.
- riesgo.
- scope.
- worker o entorno destino si aplica.
- expiracion.
- fuerza de aprobacion: normal o strong.

El movil futuro puede ser un canal de aprobacion, pero no un sistema separado de permisos.

Reglas:

- deploy, gasto, publicacion, identidad, secretos y acciones irreversibles requieren approval fuerte o `denied`.
- aprobacion pendiente no ejecuta.
- aprobacion expirada no ejecuta.
- aprobacion para servidor no autoriza automaticamente worker local.
- aprobacion para prepare-only no autoriza ejecucion real.

## 9. Hermes detras de JARVIS control layer

Hermes sigue siendo runtime/engine interno. No se convierte en interfaz publica ni en autoridad de seguridad.

En todos los modos:

- JARVIS recibe la request.
- JARVIS evalua policy.
- JARVIS solicita approval cuando aplica.
- JARVIS crea execution envelope.
- `HermesAdapter` valida envelope.
- Hermes ejecuta solo el step permitido.
- JARVIS audita resultado y responde a David.

Anti-bypass:

- no `Mobile -> Hermes`.
- no `Server -> Hermes` directo.
- no `Worker -> Hermes` sin envelope.
- no `Tool/Skill -> accion` sin policy.
- no retry automatico de acciones sensibles.

## 10. Capacidades por modo

| Categoria | Modo recomendado | Aprobacion esperada | Regla |
| --- | --- | --- | --- |
| read-only status | Server o Hybrid | none/normal segun datos | Permitido si no expone secretos ni datos sensibles. |
| documentation/design | Local o Server | none/normal | Seguro para preparar; file-write requiere scope. |
| code generation | Local o Hybrid | normal si escribe archivos | Generar codigo no autoriza ejecutarlo ni deployarlo. |
| local file access | Local o Hybrid via worker | normal/sensitive segun ruta | Server no accede directo al filesystem local. |
| code execution | Local o Hybrid via worker | normal/strong segun comando | Requiere comandos acotados, audit y limites. |
| external network | Server o Local controlado | normal/sensitive | Requiere policy explicita sobre destino y datos. |
| GitHub operations | Local, Server o Hybrid | normal/strong segun impacto | Leer puede ser allowed; push/merge/release requiere approval. |
| mobile voice command | Server/Hybrid | none para interpretar, approval para sensibles | Movil es interfaz, no permiso. |
| notifications | Server | none/normal | No deben incluir secretos ni permitir accion sensible sin approval. |
| background jobs | Server/Hybrid | normal/strong segun accion | Jobs deben ser auditables, cancelables y con scope. |
| deployment | Local/Server/Hybrid segun infra | strong | Requiere rollback, alcance exacto y aprobacion fuerte. |
| publication | Server/Hybrid | strong | Subir, enviar o publicar como David requiere approval. |
| money/payment | Server/Hybrid | strong o denied | Gastar, cobrar, contratar o cambiar precios reales requiere approval fuerte. |
| identity/credentials | Local/Server con vault futuro | strong o denied | No exponer secretos completos; vault requerido para servidor. |
| destructive actions | Local/Hybrid acotado | strong o denied | Borrado amplio/irreversible debe bloquearse o aprobarse fuerte. |

## 11. Reglas de seguridad

- No direct public exposure sin auth.
- No mobile -> Hermes directo.
- No mobile -> runtime local directo.
- No server -> local files directo sin worker/policy.
- No server secrets sin vault aprobado.
- No deploy, gasto o publicacion sin approval.
- No autoload de memoria.
- No autoejecucion peligrosa.
- No acciones irreversibles sin aprobacion fuerte.
- Server/Hybrid no degrada restricciones.
- Mobile approval futura debe usar el mismo `ApprovalGateway`.
- `denied` nunca se delega a worker ni llega a Hermes.
- Logs no deben exponer secretos.
- Endpoints publicos futuros requieren auth, rate limit, audit y modelo de abuso.
- Worker local requiere identidad, scope, expiracion y revocacion.
- Capabilities futuras deben declararse antes de usarse.
- Permisos temporales deben expirar y quedar auditados.

## 12. Ejemplos conceptuales

### Movil pide estado del proyecto

`Mobile Client futuro -> JARVIS Gateway -> PolicyEngine`.

Si pide estado read-only no sensible, Server Mode puede responder desde estado auditado. Si necesita leer archivos locales recientes, Hybrid Mode puede esperar o delegar a Local Worker con scope read-only.

### Movil pide crear PR documental

JARVIS clasifica como documentation/design + posible file-write + GitHub operation. Puede preparar plan y cambios documentales si policy lo permite. Crear commit, push o PR requiere policy especifica y approval si el contrato futuro lo exige.

### Movil pide subir video a YouTube

Es publication/identity. JARVIS puede preparar titulo, descripcion y checklist. No sube ni publica sin `ApprovalGateway` fuerte.

### Movil pide leer `.env`

Es identity/credentials o credential-touching. JARVIS debe bloquear exposicion de secretos completos o exigir approval fuerte solo para una operacion muy acotada si una futura policy la permite. Alternativa segura: listar variables esperadas sin valores.

### Servidor detecta oportunidad

Server Mode puede crear una propuesta, resumen o notification. No puede iniciar ejecucion real, gastar, publicar o modificar proyectos sin policy y approval cuando aplique.

### Servidor delega build/test al PC local

Hybrid Mode crea job con comando acotado, repo/ruta permitida, timeout y audit. Local Worker autenticado acepta solo si policy/approval son validos y el scope coincide.

### PC local apagado

Server Orchestrator no inventa ejecucion. Puede dejar job pendiente, expirar, pedir confirmacion, ofrecer alternativa server-safe o responder que requiere worker local disponible.

### Worker local falla

El fallo se registra. No se reintenta una accion sensible automaticamente. JARVIS puede proponer diagnostico o pedir aprobacion para un retry acotado.

### Aprobacion pendiente

El job queda `pending_approval`. No llega a Hermes ni al worker hasta que `ApprovalGateway` conceda aprobacion valida y vigente.

### Permiso temporal activado/desactivado

Un permiso temporal debe tener alcance, expiracion, actor, modo y audit. Al expirar o revocarse, nuevos jobs deben volver a `requires_approval` o `denied` segun policy.

## 13. Criterios de aceptacion para implementacion futura

Una futura PR de codigo solo deberia aceptarse si:

- el perfil de despliegue es explicito.
- ninguna ruta publica existe sin auth.
- policy se evalua antes de ejecucion.
- approval es compartido por local, server y mobile.
- audit registra origen, modo, usuario, policy decision y worker.
- worker local esta autenticado.
- server no accede directamente al filesystem local.
- secrets estan protegidos por diseno aprobado, idealmente vault.
- tests cubren `denied`, `requires_approval` y `allowed` por modo.
- rollback/cancelacion esta disenada para jobs.
- capabilities estan declaradas antes de usarse.
- `denied` no llega a Hermes ni worker.
- `requires_approval` no ejecuta antes de aprobacion valida.
- logs redaccionan secretos.
- documentacion explica claramente a David que puede hacer cada modo y que no.

## 14. Anti-patterns prohibidos

- Exponer `uvicorn` a internet tal cual.
- Meter tokens en variables sin vault/diseno aprobado para servidor.
- Movil llamando runtime directo.
- Movil llamando Hermes directo.
- Servidor con SSH ilimitado al PC.
- Worker local ejecutando cualquier comando.
- Server bypass de `ApprovalGateway`.
- Duplicar logica de policy por modo.
- "Modo servidor" como excusa para autoejecucion.
- Logs con secretos.
- Endpoint publico sin auth/rate limit/audit.
- Job queue que ejecuta pendientes sin revalidar policy.
- Approval por mensaje ambiguo tipo "ok" sin scope.
- Capability registry con permisos vagos.
- Worker local que acepta instrucciones fuera de JARVIS Gateway.

## 15. Fuera de alcance

PR #57 no implementa:

- codigo.
- tests.
- scripts.
- runtime.
- endpoints.
- router.
- CI.
- requirements.
- despliegue.
- servidor real.
- worker local real.
- movil.
- colas.
- vault.
- auth.
- rate limit.
- cambios en `PolicyEngine`.
- cambios en `ApprovalGateway`.
- conexion MissionControl/Hermes.
- APIs externas.
- instalacion de dependencias.
- pytest.
- smoke tests.
- commit.
- PR.

Este documento solo fija el contrato que deberan respetar futuras implementaciones de Local Mode, Server Mode y Hybrid Mode.
