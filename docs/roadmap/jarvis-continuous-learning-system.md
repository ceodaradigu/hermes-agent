# JARVIS Continuous Learning System

## 1. Objetivo

Esta fase documenta el diseño futuro de un sistema de aprendizaje continuo supervisado para que JARVIS no se quede estancado frente a novedades tecnológicas relevantes.

El objetivo es que JARVIS pueda:

- mantenerse actualizado con tecnología nueva relevante.
- evitar quedarse obsoleto o rígido.
- convertir novedades útiles en mejoras concretas para JARVIS.
- filtrar ruido, moda y hype antes de proponer cambios.
- mantener siempre supervisión humana.
- alinearse con `docs/jarvis-north-star.md`.

Continuous Learning debe reforzar la visión de JARVIS como operador personal de David: más capaz, más útil, más seguro, más enfocado en monetización y con pensamiento crítico.

## 2. Qué NO implementa esta fase

Esta fase es solo documentación. No implementa:

- código.
- tests.
- scripts.
- búsquedas reales.
- scheduling real.
- scraping.
- APIs externas.
- agentes reales.
- auto-update.
- auto-modificación.
- instalación de dependencias.
- cambios automáticos en runtime.
- endpoints.
- router.
- ejecución real.
- tareas reales.
- misiones reales.
- conexión con MissionControl.
- conexión con Hermes runtime.
- automatizaciones reales.

Nada de este documento autoriza a JARVIS a buscar, descargar, instalar, ejecutar, modificar o publicar cambios por sí solo.

## 3. Principios

El principio central es:

JARVIS nunca debe auto-modificarse ni aplicar cambios sin aprobación explícita de David.

Principios obligatorios:

- David aprueba antes de aplicar cualquier cambio.
- Los cambios deben pasar por PRs revisables.
- Los tests son obligatorios antes de mergear.
- Todo cambio debe poder revertirse o aislarse.
- `PolicyEngine` y `ApprovalGateway` siempre ganan.
- `Contrarian Agent` revisa si algo es hype, distracción o mala prioridad.
- Monetización y utilidad práctica pesan más que novedad.
- Seguridad por encima de velocidad.
- No instalar dependencias sin aprobación explícita.
- No guardar secretos.
- No enviar datos privados a servicios externos sin diseño aprobado.
- Preferir PRs pequeñas, medibles y reversibles.

## 4. Componentes futuros

### Tech Radar Agent

Componente futuro encargado de buscar novedades tecnológicas relevantes para JARVIS.

Fuera de esta fase, podría revisar fuentes sobre IA, agentes, voz, automatización, frameworks, modelos, APIs, seguridad, infra local, herramientas de desarrollo y monetización.

No debe ejecutar código, instalar dependencias ni aplicar cambios.

### Relevance Filter

Filtra ruido y detecta qué novedades podrían servir realmente a JARVIS.

Debe separar:

- novedades aplicables.
- novedades interesantes pero no prioritarias.
- hype sin impacto claro.
- riesgos de seguridad o mantenimiento.
- cambios que requieren investigación adicional.

### Contrarian Review

Evalúa si una novedad aporta dinero, velocidad, seguridad o capacidad real, o si es una distracción.

Debe poder decir claramente: "no merece la pena".

Preguntas clave:

- ¿Aporta una capacidad real?
- ¿Reduce coste o tiempo?
- ¿Mejora seguridad?
- ¿Ayuda a monetizar?
- ¿Introduce deuda técnica?
- ¿Es estable o solo hype?

### Learning Proposal

Convierte una novedad en una propuesta concreta para JARVIS.

Una propuesta debe explicar:

- qué se ha detectado.
- por qué importa.
- qué impacto tendría en JARVIS.
- qué impacto tendría en negocio o monetización.
- riesgos.
- dependencias nuevas si existen.
- plan incremental posible.
- tests esperados.
- decisión recomendada.

### Approval Workflow

JARVIS debe preguntar a David antes de aplicar cualquier aprendizaje.

Opciones futuras:

- ignorar.
- investigar más.
- crear propuesta.
- crear issue.
- crear PR experimental.

Sin confirmación explícita, no hay cambios de código, runtime, dependencias ni configuración.

### Implementation Planner

Cuando David apruebe investigar o aplicar una mejora, este componente futuro convertiría la propuesta en plan, issue o PRs pequeñas.

El plan debe mantener:

- alcance pequeño.
- criterios de aceptación.
- pruebas necesarias.
- riesgos.
- rollback.
- dependencias.
- impacto esperado.

### Test and Rollback Gate

Ningún cambio debe aplicarse si rompe tests o seguridad.

El gate futuro debe exigir:

- tests relevantes.
- revisión de seguridad.
- rollback definido.
- PR revisable.
- no degradar `PolicyEngine`.
- no saltarse `ApprovalGateway`.

### Memory/Roadmap Update

Documenta lo aprendido, lo aceptado, lo rechazado y por qué.

Puede proponer nuevas memorias o items de roadmap, pero no debe persistir aprendizaje ni activar memoria sin aprobación explícita de David.

## 5. Categorías que debe vigilar

El radar tecnológico futuro debe vigilar:

- IA y modelos nuevos.
- agentes autónomos.
- frameworks de agentes.
- herramientas de desarrollo.
- voz, STT, TTS y wake word.
- automatización local.
- seguridad y permisos.
- GitHub, Codex y workflows de desarrollo.
- browsers y tools.
- bases de datos y vector stores.
- monetización, SaaS, afiliados y funnels.
- infra local y despliegue.
- cambios importantes en OpenAI, APIs y tools.

## 6. Formato de informe semanal futuro

Ejemplo conceptual de informe semanal:

```json
{
  "week": "2026-W21",
  "items_reviewed": 42,
  "high_signal_items": 5,
  "recommended_for_jarvis": 2,
  "rejected_as_hype": 8,
  "proposals": [
    {
      "title": "Mejorar coordinación de subagentes con planificación explícita",
      "why_it_matters": "Reduce solapamiento entre agentes y mejora trazabilidad.",
      "jarvis_impact": "Podría hacer que MissionControl coordine planes futuros con más claridad.",
      "business_impact": "Acelera construcción de activos y reduce tiempo perdido en iteraciones confusas.",
      "risk": "medium",
      "estimated_prs": 2,
      "requires_approval": true
    }
  ]
}
```

Este formato es solo diseño. No implica scheduling, scraping, llamadas externas ni generación real de informes en esta fase.

## 7. Flujo de aprobación

Flujo obligatorio futuro:

1. investigar.
2. filtrar.
3. resumir.
4. proponer.
5. pedir aprobación.
6. crear issue, plan o PR.
7. pasar tests.
8. documentar aprendizaje.
9. aplicar solo tras merge.

Reglas:

- JARVIS presenta un resumen.
- David elige: ignorar, investigar más, crear propuesta, crear issue o crear PR experimental.
- JARVIS no cambia código sin confirmación.
- JARVIS no mergea sin tests.
- JARVIS documenta la decisión.
- JARVIS no instala dependencias sin aprobación explícita.
- JARVIS no convierte una propuesta en cambio aplicado sin PR revisable.

## 8. Criterios de priorización

Cada novedad debe evaluarse con preguntas concretas:

- ¿Aumenta capacidad real de JARVIS?
- ¿Reduce tiempo de desarrollo?
- ¿Mejora seguridad?
- ¿Ayuda a monetizar?
- ¿Reduce coste?
- ¿Evita deuda técnica?
- ¿Es estable o puro hype?
- ¿Tiene coste de mantenimiento?
- ¿Requiere dependencias nuevas?
- ¿Rompe privacidad o local-first?
- ¿Respeta `PolicyEngine` y `ApprovalGateway`?
- ¿Puede implementarse como PR pequeña y reversible?

## 9. Reglas anti-hype

Reglas obligatorias:

- No perseguir cada framework nuevo.
- No instalar librerías por moda.
- No cambiar arquitectura sin beneficio claro.
- Comparar beneficio, coste y riesgo.
- Preferir PRs pequeñas y reversibles.
- `Contrarian Agent` debe poder decir "no merece la pena".
- Una novedad no es prioridad solo porque sea reciente.
- Si no hay impacto claro en capacidad, monetización, seguridad o velocidad, debe rechazarse o posponerse.

## 10. Seguridad

Continuous Learning debe tratar cualquier novedad externa como no confiable hasta revisión.

Reglas de seguridad:

- No ejecutar código de fuentes externas sin revisión.
- No copiar snippets inseguros.
- No guardar secretos.
- No enviar memoria privada a servicios externos sin diseño aprobado.
- No dar permisos a herramientas externas sin `ApprovalGateway`.
- No actualizar dependencias críticas sin tests.
- No usar APIs externas sin aprobación y diseño de privacidad.
- No instalar herramientas que requieran credenciales sin revisión explícita.
- No degradar controles sensibles para ganar velocidad.

## 11. Roadmap propuesto de PRs futuras

Roadmap incremental propuesto:

- PR A: docs: add continuous learning design.
- PR B: tech radar source model.
- PR C: weekly technology scan report model.
- PR D: relevance scoring for JARVIS.
- PR E: learning proposal model.
- PR F: approval workflow for learning proposals.
- PR G: create implementation plan from approved learning.
- PR H: create GitHub issue from approved learning proposal.
- PR I: create PR from approved learning proposal.
- PR J: memory integration for accepted learnings.
- PR K: scheduled weekly tech radar.
- PR L: dashboard/report view.

Cada PR futura debe mantener alcance pequeño, revisión humana, tests y compatibilidad con `docs/jarvis-north-star.md`.

## 12. Ejemplo narrativo

JARVIS:

"He detectado 5 novedades relevantes esta semana. Dos podrían mejorar JARVIS. Una mejora voice runtime, otra mejora coordinación de subagentes. ¿Quieres que cree propuesta?"

David:

"Sí, crea propuesta para la de subagentes."

JARVIS:

"Creo propuesta revisable. No cambio código todavía."

## 13. Límites claros

Continuous Learning no significa auto-modificación.

Continuous Learning no significa auto-deploy.

Continuous Learning no significa instalar dependencias solo.

Continuous Learning no significa saltarse PRs.

Continuous Learning no significa conectar con MissionControl o Hermes runtime sin una PR futura aprobada.

Continuous Learning es investigación y propuesta supervisada.

La regla final es simple: JARVIS puede aprender, resumir y proponer; David decide, revisa y aprueba antes de aplicar.
