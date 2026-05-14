# User Understanding Persistent Memory

## 1. Objetivo

Esta fase diseña la futura memoria persistente segura de User Understanding para pasar de reglas temporales en memoria a memoria persistente revisada, aprobada, auditable y reversible.

El diseño debe mantenerse alineado con `docs/jarvis-north-star.md`: JARVIS debe aprender de David de forma progresiva sin perder privacidad, transparencia, pensamiento critico, seguridad ni control humano.

La memoria futura debe permitir aprender de David de forma amplia:

- comunicacion y tono.
- intencion real detras de frases incompletas o indirectas.
- contexto personal, tecnico y de negocio.
- ejecucion y ritmo de trabajo preferido.
- monetizacion, foco y retorno esperado.
- frustracion, bloqueos y patrones de decision.
- prioridades, limites y estilo de decision.

## 2. Que NO implementa esta fase

Esta fase es solo documentacion. No implementa:

- persistencia.
- base de datos.
- archivos de memoria.
- aprendizaje automatico opaco.
- ejecucion real.
- conexion con MissionControl.
- conexion con Hermes runtime.
- memoria sensible sin consentimiento explicito.

Tampoco crea misiones reales, tareas reales, threads, background services, audio, wake word, STT, reproduccion de audio, autoarranque, dependencias, CI ni cambios de runtime.

## 3. Principios de seguridad

La memoria persistente futura debe obedecer estos principios:

- Privacidad local: las memorias deben permanecer bajo control local por defecto.
- Transparencia: David debe poder ver que se propone recordar, por que y desde que feedback nace.
- Auditabilidad: cada cambio de estado debe dejar rastro revisable.
- Reversibilidad: una memoria debe poder desactivarse, eliminarse o expirar sin efectos ocultos.
- Revision humana: ninguna memoria persistente debe activarse sin aprobacion explicita.
- ApprovalGateway obligatorio para acciones sensibles.
- PolicyEngine sigue ganando ante cualquier conflicto.
- Los terminos sensibles no pueden ser degradados por memoria aprendida.
- La memoria nunca puede usarse para saltarse aprobaciones.

Una preferencia aprendida puede orientar estilo, interpretacion o priorizacion, pero no puede autorizar acciones sensibles ni reducir limites de seguridad.

## 4. Tipos de memoria futura

Tipos conceptuales de memoria:

- `communication_preferences`: tono, idioma, longitud, nivel de detalle y formato preferido.
- `intent_aliases`: frases de David que suelen mapear a intenciones conocidas.
- `business_goals`: objetivos de negocio, productos, nichos o lineas de trabajo.
- `monetization_preferences`: preferencias sobre ROI, modelos de ingreso, pricing, validacion y foco comercial.
- `execution_preferences`: tamano de PR, pasos pequenos, validacion frecuente, aversion a romper flujos existentes.
- `decision_style`: como decide David, que evidencia pide y cuando prefiere velocidad frente a analisis.
- `contrarian_triggers`: patrones que deben activar contradiccion o revision critica.
- `sensitive_boundaries`: limites explicitos sobre privacidad, identidad, datos, acciones o temas.
- `project_context`: contexto estable de proyectos, objetivos, restricciones y estado conceptual.
- `rejected_assumptions`: interpretaciones o suposiciones que David ya rechazo.
- `learning_notes`: notas revisadas que todavia no encajan en un tipo mas especifico.

## 5. Ciclo propuesto

Flujo futuro propuesto:

1. `feedback-preview`: mostrar como se interpretaria el feedback antes de aplicarlo.
2. `feedback-add`: registrar feedback temporal para revision.
3. `feedback-apply-reviewed`: aplicar reglas revisadas temporales.
4. `memory-proposal`: generar una propuesta explicita de memoria persistente.
5. Human approval: David revisa y aprueba, edita, rechaza o pospone.
6. Persist reviewed memory: guardar solo la memoria revisada y aprobada.
7. Audit log: registrar origen, aprobacion, cambios y estado.
8. Reversible delete/disable: permitir desactivar o eliminar el efecto de la memoria.
9. Runtime loads approved memory: el runtime carga solo memorias aprobadas, activas y no expiradas.

El paso de feedback temporal a memoria persistente debe ser deliberado. El sistema no debe convertir patrones observados en memoria activa sin una propuesta visible y aprobacion humana.

## 6. Estados de una memoria

Estados conceptuales:

- `proposed`: propuesta generada, todavia sin revision.
- `reviewed`: revisada por un flujo humano o semi-asistido, pero no aprobada.
- `approved`: aprobada por David para persistir.
- `active`: aprobada, no expirada y cargable por runtime.
- `disabled`: conservada para auditoria, pero sin efecto.
- `deleted`: eliminada como memoria aplicable; puede quedar un rastro minimo de auditoria si el diseno de privacidad lo permite.
- `expired`: ya no aplicable por fecha o politica de caducidad.

## 7. Modelo de datos conceptual

Ejemplo JSON conceptual, no codigo productivo:

```json
{
  "id": "mem_01HYPOTHETICAL",
  "type": "intent_alias",
  "source": "feedback_apply_reviewed",
  "alias": "probar este nicho",
  "target_intent": "create_mission",
  "confidence": "reviewed",
  "scope": "voice_runtime",
  "approved_by": "David",
  "created_at": "2026-05-14T10:00:00Z",
  "expires_at": null,
  "sensitive": false,
  "active": true,
  "audit": [
    {
      "at": "2026-05-14T10:00:00Z",
      "event": "proposed",
      "source": "feedback_apply_reviewed"
    },
    {
      "at": "2026-05-14T10:05:00Z",
      "event": "approved",
      "by": "David"
    }
  ]
}
```

Campos como `id`, `created_at`, `expires_at`, `scope`, `sensitive`, `active` y `audit` son conceptuales. La forma final debe definirse en una PR posterior antes de implementar persistencia.

## PR #32 — Memory proposal model

Se añade un modelo local en memoria para propuestas futuras de User Understanding memory.

Alcance:

- No persiste propuestas.
- No escribe memoria en disco.
- No aplica propuestas al router.
- No carga propuestas en runtime.
- No cambia la conducta de JARVIS.
- Mantiene propuestas revisables, auditables, reversibles y serializables.

Este paso prepara la siguiente fase: una API de proposals en memoria. La persistencia real sigue fuera de alcance hasta que exista un flujo explicito de revision, aprobacion, auditoria y reversibilidad.

## 8. Reglas anti-autoengano

La memoria no debe convertir a JARVIS en un sistema que siempre confirma a David.

Reglas futuras:

- La memoria no debe confirmar siempre a David ni reforzar decisiones malas solo porque coinciden con preferencias pasadas.
- Contrarian Agent debe revisar patrones dudosos, especialmente cuando haya perdida de foco, complejidad innecesaria, monetizacion debil o riesgo tecnico.
- Si una preferencia aprendida entra en conflicto con seguridad, gana seguridad.
- Si una preferencia aprendida entra en conflicto con monetizacion o foco, JARVIS debe pedir aclaracion o contradecir con argumentos concretos.
- El sistema debe distinguir hecho confirmado, preferencia explicita, patron probable y suposicion.
- Las memorias deben conservar incertidumbre cuando aplique; no deben convertirse en certezas falsas.

## 9. Reglas de privacidad

La memoria persistente futura no debe guardar:

- secretos.
- credenciales.
- contenido de `.env`.
- datos bancarios.
- audio bruto salvo consentimiento explicito futuro.
- datos sensibles sin consentimiento y sin diseno especifico.

Tampoco debe enviar memorias a APIs externas sin un diseno explicito, aprobado y documentado. Cualquier exportacion, sincronizacion o uso externo debe tratarse como una capacidad nueva con revision de seguridad propia.

## 10. Endpoints futuros propuestos

Solo propuestos, no implementar en esta fase:

- `GET /voice/runtime/memory/proposals`
- `POST /voice/runtime/memory/proposals`
- `POST /voice/runtime/memory/proposals/{id}/approve`
- `POST /voice/runtime/memory/proposals/{id}/disable`
- `DELETE /voice/runtime/memory/proposals/{id}`
- `GET /voice/runtime/memory/audit`

Estos endpoints deberian exponer propuestas, aprobaciones, desactivaciones, eliminaciones y auditoria sin ejecutar acciones reales ni saltarse `PolicyEngine` o `ApprovalGateway`.

## 11. CLI futuro propuesto

Solo propuesto, no implementar en esta fase:

- `memory-propose`
- `memory-list`
- `memory-approve`
- `memory-disable`
- `memory-delete`
- `memory-audit`

El CLI futuro debe priorizar revision clara, diffs legibles, origen de cada propuesta, estado actual, efecto esperado y capacidad de revertir.

## 12. Tests futuros

Casos futuros a cubrir cuando exista implementacion:

- No persistir sin aprobacion.
- No cargar memoria sensible sin consentimiento y politica explicita.
- `PolicyEngine` gana siempre.
- Eliminar memoria desactiva su efecto.
- Memoria expirada no se aplica.
- Audit log se conserva segun la politica definida.
- Nuevas instancias cargan solo memorias aprobadas, activas y no expiradas.
- Memoria aprendida no degrada terminos sensibles.
- Memoria aprendida no salta `ApprovalGateway`.

## 13. Roadmap incremental

PRs futuras propuestas:

- PR A: memory proposal model sin persistencia.
- PR B: in-memory memory proposal API.
- PR C: local JSON persistence opt-in.
- PR D: audit log local.
- PR E: load approved memory at startup.
- PR F: UI/CLI review workflow.
- PR G: encryption/vault design if needed.

Cada PR debe mantener el alcance pequeno, revisable y compatible con `docs/jarvis-north-star.md`. La persistencia real no debe aparecer hasta que exista un flujo claro de propuesta, aprobacion, auditoria y reversibilidad.
