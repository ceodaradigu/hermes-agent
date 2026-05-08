# Roadmap futuro: Dominion / Overdrive Mode (Command Center)

## Estado
Este documento describe una **capacidad futura** para JARVIS y no forma parte del alcance actual del Command Center base.

## Objetivo del modo
Definir una capa visual y conversacional opcional para Command Center que permita operar con una estética más intensa y un estilo de comunicación más agresivo, sin cambiar el modelo de seguridad ni las garantías de supervisión humana.

## Contexto
- Mission Control ya está mergeado.
- JARVIS es un operador personal privado para David (no un SaaS público).
- Las acciones sensibles siguen requiriendo Approval Gate.
- Dominion / Overdrive Mode es una capa futura de experiencia (UX/tono), no un bypass de seguridad.

## Nombres posibles
- Overdrive Mode
- Dominion Mode
- Shadow Command Mode

## Nombre recomendado
**Dominion Mode**

Se recomienda este nombre porque comunica control estratégico y dirección táctica sin ambigüedad funcional sobre la capa de seguridad.

## Qué cambia al activarlo
Al activar Dominion Mode, cambia únicamente la experiencia visible y el estilo conversacional:

- Diseño oscuro con acentos rojo/neón.
- Tono más frío, arrogante, estratégico y teatralmente malvado.
- Narrativa más dramática para status, planes y ejecución.

## Qué no cambia
Dominion Mode **no** modifica ni debilita:

- `PolicyEngine`
- `ApprovalGateway`
- Logs de ejecución
- Auditoría
- Confirmación humana previa en acciones sensibles

## Regla central
**JARVIS puede sonar peligroso, pero no puede actuar de forma peligrosa.**

La personalidad percibida puede cambiar; la seguridad operativa y el control humano no.

## Protocolo de confirmación para dinero real
Para cualquier acción con impacto económico real, el flujo mantiene confirmación explícita humana antes de ejecutar:

1. JARVIS propone el plan.
2. Se evalúa policy/riesgo.
3. Se genera solicitud de aprobación con monto, destino y alcance.
4. Solo tras confirmación humana explícita se ejecuta.

## Ejemplo: campaña Meta Ads de 20 €
Escenario de referencia en Dominion Mode:

1. JARVIS sugiere una campaña de Meta Ads de **20 €** con objetivo y audiencia definidos.
2. El sistema marca la acción como sensible por involucrar dinero real.
3. Se emite `ApprovalRequest` con detalle del gasto (20 €), alcance y duración.
4. Sin aprobación humana: no se publica ni se gasta.
5. Con aprobación humana: se autoriza la ejecución bajo los límites aprobados.

## Límites (no negociables)
- No saltarse aprobaciones.
- No mover dinero sin permiso explícito.
- No usar credenciales sin aprobación.
- No publicar contenido sin confirmación humana.
- No ejecutar acciones ilegales.

## Plan de implementación
Dominion Mode se implementará **después** del Command Center base, como una fase posterior enfocada en UX/tono y sin introducir bypasses sobre controles de seguridad existentes.
