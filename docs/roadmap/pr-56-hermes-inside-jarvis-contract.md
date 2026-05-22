# PR #56 - Hermes inside JARVIS integration contract

## 1. Proposito

Este documento define el contrato conceptual para integrar Hermes dentro de JARVIS.

Es exclusivamente documental. No implementa runtime, endpoints, router, MissionControl, `PolicyEngine`, `ApprovalGateway`, adapter real, herramientas, skills, tests, scripts, CI, requirements ni conexion efectiva con Hermes.

La decision central es:

```text
David habla con JARVIS.
JARVIS gobierna.
Hermes ejecuta solo lo permitido.
```

Hermes debe ser el runtime/engine interno que JARVIS aprovecha para conversacion, tools y skills. No debe convertirse en una interfaz paralela, un monolito magico ni un bypass de seguridad.

## 2. Rol de Hermes dentro de JARVIS

Hermes aporta capacidades que JARVIS no debe duplicar sin necesidad:

- conversacion con modelos.
- orquestacion de tools.
- skills.
- terminal y herramientas de desarrollo cuando esten disponibles.
- ejecucion controlada de pasos.
- integraciones futuras reutilizables.
- experiencia de agente ya existente.

JARVIS no debe reescribir esas piezas si Hermes ya las resuelve. Duplicarlas aumentaria superficie de bugs, divergencia de comportamiento, coste de mantenimiento y riesgo de que existan dos caminos de ejecucion con reglas distintas.

Hermes, sin embargo, no decide por si solo que esta permitido dentro de JARVIS. Hermes no conoce por completo la North Star, el sensitive boundary de David, el estado de approvals, la politica por interfaz, el contexto de mision ni la auditoria de JARVIS. Por eso Hermes debe quedar detras de un adapter/control layer.

## 3. Responsabilidades de JARVIS

JARVIS es la capa de producto, decision, seguridad y experiencia de David.

JARVIS debe:

- recibir la interaccion desde gateway, voz, movil, servidor, CLI o interfaces futuras.
- interpretar intencion mediante el natural runtime / intent / response model.
- distinguir entender, preparar, pedir aprobacion y ejecutar.
- priorizar negocio, foco, monetizacion y riesgo.
- aplicar `PolicyEngine` antes de cualquier paso ejecutable.
- aplicar `ApprovalGateway` cuando la politica lo requiera.
- hacer que el sensitive boundary gane siempre.
- impedir que memoria activa degrade riesgo o elimine aprobacion.
- planificar steps mediante MissionControl o una capa equivalente futura.
- llamar a Hermes solo mediante `HermesAdapter`.
- auditar decision, aprobacion, ejecucion, resultado y errores.
- responder a David como JARVIS, no como una consola directa de Hermes.

## 4. Responsabilidades de Hermes

Hermes es runtime interno, no autoridad de seguridad.

Hermes puede:

- ejecutar prompts, tools y skills permitidos por JARVIS.
- preparar borradores, planes, diffs conceptuales o artefactos seguros.
- operar dentro de limites de ruta, red, credenciales, entorno y modo declarados por JARVIS.
- devolver resultados estructurados, errores y metadatos utiles para auditoria.
- declarar capacidades disponibles, permisos requeridos y riesgos conocidos.

Hermes no debe:

- recibir llamadas directas desde UI, movil, servidor, memoria, agentes, tools o skills externas.
- decidir su propio permiso final.
- ejecutar un step que `PolicyEngine` haya marcado como `denied`.
- ejecutar una accion `requires_approval` antes de aprobacion.
- saltarse `ApprovalGateway` por confianza alta, memoria activa o urgencia.
- tocar secretos, identidad, dinero, produccion o acciones irreversibles sin el contrato de JARVIS.
- ocultar riesgos bajo errores genericos.

## 5. Arquitectura conceptual

El flujo conceptual obligatorio es:

```text
JARVIS Gateway / Interfaces
  -> Natural Runtime / Intent / Response Model
  -> PolicyEngine
  -> ApprovalGateway si aplica
  -> MissionControl / Step planner
  -> HermesAdapter
  -> Hermes runtime/tools/skills
  -> Audit / result / response
```

Reglas del flujo:

1. Ninguna interfaz llama a Hermes directamente.
2. Todo paso ejecutable pasa antes por `PolicyEngine`.
3. Toda accion sensible pasa por `ApprovalGateway`.
4. `denied` nunca llega a Hermes.
5. `requires_approval` solo llega a Hermes despues de aprobacion valida, si sigue siendo seguro.
6. `allowed` no significa libre de auditoria; significa permitido dentro de limites concretos.
7. El resultado vuelve a JARVIS para auditoria, interpretacion y respuesta final.

## 6. Contrato HermesAdapter

`HermesAdapter` es la unica puerta conceptual entre JARVIS y Hermes.

Debe aceptar solo requests ya evaluadas por policy y, cuando aplique, por approval. Debe rechazar cualquier request que no traiga decision de policy, alcance de ejecucion, categoria de riesgo y metadata de auditoria.

Contrato minimo:

- validar que existe `request_id`.
- validar que existe `policy_decision`.
- validar que `policy_decision.status` no es `denied`.
- validar que una decision `requires_approval` trae approval concedido y vigente.
- validar limites de ruta, red, credenciales, identidad, entorno y modo.
- ejecutar una sola unidad de trabajo por envelope.
- devolver resultado estructurado.
- registrar errores sin convertirlos en permiso.
- no ampliar capacidades mas alla de lo declarado.

## 7. Envelopes

Los nombres y campos son conceptuales. Una futura implementacion puede usar estructuras equivalentes si conserva las garantias.

### Request envelope

```json
{
  "request_id": "req_...",
  "source": "local|server|mobile|voice|gateway|mission",
  "user_id": "david",
  "transcript": "texto original o normalizado",
  "intent": "detected_intent",
  "confidence": "low|medium|high",
  "desired_outcome": "que quiere conseguir David",
  "execution_mode": "read_only|prepare_only|execute_step",
  "active_memory_refs": ["mem_..."],
  "sensitive_signals": [".env", "deploy"],
  "created_at": "timestamp"
}
```

### Policy decision envelope

```json
{
  "request_id": "req_...",
  "step_id": "step_...",
  "status": "allowed|requires_approval|denied",
  "risk_category": "file-write|production/deploy",
  "risk_level": "low|medium|high|critical",
  "allowed_scope": {
    "paths": ["docs/**"],
    "network": false,
    "credentials": false,
    "production": false
  },
  "reason": "auditable reason",
  "sensitive_boundary_triggered": false
}
```

### Approval envelope

```json
{
  "approval_id": "appr_...",
  "request_id": "req_...",
  "step_id": "step_...",
  "status": "approved|rejected|expired",
  "approval_strength": "normal|strong",
  "approved_action": "accion exacta autorizada",
  "approved_scope": {
    "paths": ["docs/**"],
    "network": false,
    "production": false
  },
  "approved_by": "david",
  "expires_at": "timestamp"
}
```

### Execution envelope

```json
{
  "execution_id": "exec_...",
  "request_id": "req_...",
  "step_id": "step_...",
  "policy_decision_id": "pol_...",
  "approval_id": "appr_... or null",
  "hermes_capability": "capability_name",
  "call_category": "prepare-only|file-write|code-execution",
  "inputs": {
    "prompt": "instruccion acotada",
    "constraints": ["no network", "docs only"]
  },
  "limits": {
    "timeout_seconds": 120,
    "max_files": 3,
    "allowed_paths": ["docs/**"]
  }
}
```

### Result envelope

```json
{
  "execution_id": "exec_...",
  "status": "succeeded|failed|blocked",
  "summary": "resultado breve",
  "outputs": [],
  "changed_resources": [],
  "errors": [],
  "risk_observations": [],
  "requires_followup_policy": false
}
```

### Audit event envelope

```json
{
  "audit_id": "audit_...",
  "request_id": "req_...",
  "event_type": "policy_decision|approval_requested|approval_granted|execution_started|execution_finished|execution_blocked",
  "actor": "jarvis|david|hermes_adapter|hermes",
  "decision": "allowed|requires_approval|denied|null",
  "reason": "auditable reason",
  "timestamp": "timestamp",
  "metadata": {}
}
```

### Capability declaration envelope

```json
{
  "capability_id": "cap_...",
  "name": "hermes.skill.or.tool",
  "description": "que puede hacer",
  "call_categories": ["read-only", "prepare-only"],
  "required_permissions": ["filesystem:read"],
  "risk_level": "low|medium|high|critical",
  "sensitive_boundaries": ["credentials", "production"],
  "default_mode": "prepare-only",
  "requires_policy": true,
  "requires_approval_for": ["file-write", "external-network"]
}
```

## 8. Categorias de llamadas a Hermes

Cada llamada debe clasificarse antes de llegar a Hermes.

| Categoria | Significado | Regla |
| --- | --- | --- |
| `read-only` | Leer informacion no sensible o resumir contexto permitido. | Puede ser `allowed` si policy lo permite y la fuente esta dentro de alcance. |
| `prepare-only` | Preparar plan, borrador, checklist, propuesta o diff conceptual sin accion real. | No ejecuta acciones reales ni produce side effects. |
| `local-safe` | Accion local de bajo riesgo dentro de sandbox o alcance no sensible. | Requiere limites explicitos y auditoria. |
| `external-network` | Cualquier llamada a internet, API externa o servicio remoto. | Requiere politica explicita; puede requerir approval segun destino y datos. |
| `file-write` | Crear, editar o borrar archivos locales. | Requiere limites de ruta, alcance, diff/auditoria y bloqueo de rutas sensibles. |
| `code-execution` | Ejecutar comandos, scripts, tests o codigo generado. | Requiere contexto controlado, limites, auditoria y tests cuando aplique. |
| `credential-touching` | Leer, escribir, transformar o usar secretos. | Requiere approval fuerte o debe estar bloqueado; secretos completos no deben exponerse. |
| `identity/publication` | Publicar, enviar mensajes, subir contenido o actuar como David. | Requiere approval. |
| `money/payment` | Gastar, cobrar, mover dinero, comprar, contratar o cambiar precios reales. | Requiere approval fuerte. |
| `production/deploy` | Cambiar produccion, deployar, migrar, configurar infra real. | Requiere approval fuerte y rollback/observabilidad cuando aplique. |
| `destructive/irreversible` | Borrado amplio, cambios no recuperables o acciones de alto impacto. | Requiere approval fuerte o `denied`. |

## 9. Reglas obligatorias

- `read-only` puede ser `allowed` si policy lo permite.
- `prepare-only` no ejecuta acciones reales.
- `file-write` requiere limites de ruta y auditoria.
- `code-execution` requiere contexto controlado y tests cuando el objetivo sea validar codigo.
- `external-network` requiere politica explicita.
- `credential-touching` requiere approval fuerte o debe estar bloqueado.
- `identity/publication` requiere approval.
- `money/payment` requiere approval fuerte.
- `production/deploy` requiere approval fuerte.
- `destructive/irreversible` requiere approval fuerte o `denied`.
- `denied` nunca llega a Hermes.
- La memoria activa nunca cambia `requires_approval` a `allowed`.
- La memoria activa nunca cambia `denied` a `requires_approval` ni a `allowed`.
- Un error de Hermes no oculta el riesgo original.
- Un tool o skill no decide su propio permiso final.

## 10. Anti-patterns prohibidos

- UI -> Hermes directo.
- Mobile -> Hermes directo.
- Server -> Hermes directo.
- Memory -> Hermes directo.
- Agent -> tool sin policy.
- Tool que decide su propio permiso final.
- Skill que declara capacidades vagas para ejecutar mas de lo aprobado.
- Natural runtime ejecutando porque la frase suena natural.
- Bypass de `ApprovalGateway` por confianza alta.
- Bypass de `ApprovalGateway` por memoria activa.
- Desactivar restricciones sin auditoria.
- Usar Hermes como monolito magico.
- Tratar `allowed` como permiso global sin alcance.
- Reintentar automaticamente una accion sensible tras fallo.
- Convertir una accion `prepare-only` en ejecucion real durante el mismo paso.

## 11. Como escalar el sistema

Nuevas skills:

- deben declarar capacidades, permisos, categorias y riesgos antes de usarse.
- deben tener default seguro, preferiblemente `prepare-only` cuando haya dudas.
- no deben pedir mas alcance del necesario.

Nuevas interfaces:

- no llaman a Hermes.
- llaman a JARVIS Gateway o capa equivalente.
- heredan el mismo `PolicyEngine`, `ApprovalGateway`, auditoria y sensitive boundary.

Nuevos agentes:

- no ejecutan tools sin step policy.
- no convierten confianza o memoria en permiso.
- devuelven propuestas o execution envelopes para evaluacion.

Nuevos modos local/server/hybrid:

- usan el mismo contrato.
- pueden cambiar capacidades disponibles, pero no saltarse policy.
- deben declarar donde viven datos, ejecucion, red y auditoria.

Movil:

- usa el mismo `ApprovalGateway`.
- no obtiene permiso especial por ser una interfaz personal.
- debe mostrar acciones sensibles con alcance, riesgo y alternativa segura.

Restricciones configurables futuras:

- se integran con policy.
- no sustituyen `PolicyEngine`.
- no desactivan sensitive boundary.
- deben quedar auditadas cuando cambien.

## 12. Ejemplos conceptuales seguros

### Crear PR documental

JARVIS puede clasificarlo como `file-write` limitado a `docs/**` y `prepare-only`/`local-safe` si el cambio no toca runtime. Si policy devuelve `allowed`, JARVIS puede llamar a Hermes mediante adapter para editar documentacion. Debe auditar decision y resultado.

### Crear app

JARVIS debe separar plan, archivos, dependencias, ejecucion local y posible deploy. Puede preparar arquitectura y primeros archivos si policy lo permite. Instalar dependencias, llamar APIs externas o hacer deploy requiere evaluacion adicional y posiblemente approval.

### Subir video a YouTube

Es `identity/publication`. JARVIS puede preparar titulo, descripcion, checklist y borrador. No debe publicar ni subir contenido mediante Hermes sin `ApprovalGateway`.

### Leer `.env`

Es `credential-touching`. JARVIS debe denegar lectura/exposicion de secretos completos o exigir approval fuerte para una operacion muy acotada si una futura policy la permite. Alternativa segura: revisar plantilla sin valores o lista de variables esperadas.

### Hacer deploy

Es `production/deploy`. JARVIS puede preparar plan, resumen de cambios, riesgos y rollback. La ejecucion requiere approval fuerte y envelope con alcance exacto.

### Borrar archivos

Puede ser `file-write` o `destructive/irreversible`. Borrado acotado y reversible podria requerir approval normal/fuerte segun ruta. Borrado amplio, sensible o irreversible debe ser approval fuerte o `denied`.

### Crear landing de validacion

JARVIS puede recomendar validar oferta, comprador y senal antes de construir. Puede preparar copy, estructura y archivos dentro de alcance si policy lo permite. Publicarla requiere approval si implica identidad, dominio, red o produccion.

### Investigar nicho

Puede ser `prepare-only` si usa contexto local o conocimiento ya disponible. Si requiere internet o APIs externas, pasa a `external-network` y necesita politica explicita. JARVIS debe separar supuestos de hechos confirmados.

### Ejecutar tests

Es `code-execution`. JARVIS puede hacerlo si policy permite ejecucion local controlada, con comandos acotados y auditoria. Si los tests escriben fuera de alcance, descargan dependencias o tocan secretos, requieren policy/approval adicional.

## 13. Criterios de aceptacion para futura implementacion

Una futura PR de codigo solo deberia aceptarse si:

- no hay caminos directos a Hermes fuera de `HermesAdapter`.
- tests cubren `denied`, `requires_approval` y `allowed`.
- audit registra decision de policy antes de ejecucion.
- prompts sensibles nunca llegan como ejecucion `allowed`.
- active memory no cambia `requires_approval` a `allowed`.
- active memory no cambia `denied` a una decision menos restrictiva.
- mobile, server y local comparten policy contract.
- Hermes errors no ocultan riesgos.
- capabilities se declaran antes de usarse.
- `denied` no invoca Hermes.
- `requires_approval` no invoca Hermes hasta aprobacion valida.
- file writes estan acotados por ruta.
- external network esta desactivado salvo politica explicita.
- production/deploy y money/payment requieren approval fuerte.
- audit permite reconstruir request, policy, approval, execution y result.

## 14. Fuera de alcance

PR #56 no implementa:

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
- adapter real.
- APIs externas.
- instalacion de dependencias.
- pytest.
- smoke tests.
- commit.
- PR.

Este documento solo fija el contrato que deberan respetar futuras implementaciones.
