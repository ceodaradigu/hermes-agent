# PR #60 - Code Intelligence / CodeGraph evaluation contract

## 1. Proposito

Este documento define el contrato conceptual para evaluar CodeGraph como herramienta candidata de Code Intelligence para JARVIS, Codex y Hermes.

Es exclusivamente documental. No instala CodeGraph, no ejecuta CodeGraph, no crea `.codegraph`, no configura MCP, no modifica agentes, no cambia runtime, no anade endpoints, no toca router, no cambia tests, no cambia CI, no cambia requirements, no modifica `PolicyEngine`, no modifica `ApprovalGateway` y no integra MissionControl/Hermes.

La decision central es:

```text
CodeGraph puede ser una ayuda local y opcional para entender el codebase.
No es fuente de verdad.
No es dependencia obligatoria.
No gobierna permisos.
No entra en runtime critico sin contrato, medicion y aprobacion explicita de David.
```

El objetivo de esta PR es fijar como evaluar de forma segura y medible si un grafo/index semantico local del repo reduce exploracion ciega, llamadas a herramientas, tokens y tiempo en workflows de Codex/JARVIS/Hermes.

## 2. Problema que intenta resolver

En tareas de desarrollo sobre un repo grande, Codex, Hermes o un agente futuro pueden gastar demasiado tiempo en exploracion repetitiva:

- buscar con `grep`/`rg` las mismas funciones.
- leer archivos completos para localizar simbolos.
- repetir `glob`, `find`, `sed` o lecturas parciales.
- reconstruir relaciones entre imports, clases, funciones y modulos.
- inferir impacto de cambios con contexto incompleto.
- consumir tokens en navegacion en vez de razonamiento.
- aumentar tool calls antes de poder escribir un prompt cerrado o un plan seguro.

CodeGraph podria ayudar si permite consultar rapidamente:

- donde vive una funcion.
- que clases o modulos dependen de un simbolo.
- que archivos importan un modulo.
- que funciones llaman o son llamadas por otra.
- que areas pueden verse afectadas por un cambio.
- que rutas documentales o de codigo estan relacionadas.

La hipotesis a evaluar es:

```text
Un indice/grafo local puede reducir lectura repetitiva sin reducir calidad, seguridad ni trazabilidad.
```

## 3. Que no resuelve

CodeGraph no reemplaza:

- tests.
- lectura del codigo real.
- revision humana.
- `PolicyEngine`.
- `ApprovalGateway`.
- arquitectura de JARVIS.
- contratos documentales.
- auditoria.
- analisis de seguridad.
- criterio de David.
- prompts cerrados con alcance y prohibiciones.
- `rg`/read cuando el indice sea incompleto, stale o dudoso.

Un resultado de CodeGraph debe tratarse como pista. El codigo real, los tests y los contratos vigentes siguen siendo la fuente de verdad.

## 4. Por que debe ser local y opcional

CodeGraph debe evaluarse como herramienta local/opcional porque puede indexar estructura interna del repo, rutas, nombres de simbolos, comentarios, documentos, relaciones y potencialmente contenido sensible si se configura mal.

Reglas:

- No debe enviar el indice a servicios externos.
- No debe ser requisito para desarrollar JARVIS.
- No debe bloquear workflows de Codex, Hermes o humanos si no esta instalado.
- No debe modificar configuraciones globales sin aprobacion explicita.
- No debe ejecutarse contra carpetas sensibles, secretos o repos privados fuera de alcance sin diseno aprobado.
- Debe poder apagarse, limpiar artefactos y volver al baseline con `rg`/read.

El valor esperado es mejorar ergonomia y eficiencia de exploracion local, no crear una nueva dependencia de plataforma.

## 5. Por que no debe formar parte del runtime critico

El runtime critico de JARVIS debe permanecer pequeno, gobernado y auditable. Meter CodeGraph en runtime critico antes de evaluarlo crearia riesgos:

- dependencia adicional para arrancar o ejecutar JARVIS.
- fallos por indice corrupto, incompleto o desactualizado.
- coste de mantenimiento y configuracion por entorno.
- posible exposicion de rutas o contenido sensible en logs.
- confusion entre pista semantica y verdad ejecutable.
- bypass accidental de `PolicyEngine` si se usa para justificar acciones.
- cambios globales de MCP/agentes dificiles de revertir.

Si algun dia se integra, debe ser opt-in, con config explicita, detras de `ApprovalGateway` cuando implique indexacion sensible, y fuera del camino minimo de ejecucion.

## 6. Relacion con Codex, Hermes y JARVIS

### Codex

Codex podria usar CodeGraph en el futuro como ayuda de navegacion local para preparar prompts cerrados, localizar simbolos y reducir lecturas repetidas. Eso no autoriza instalarlo, ejecutarlo ni cambiar configuracion de Codex en esta PR.

### Hermes

Hermes podria exponer CodeGraph como capability o tool futura solo si una PR posterior define contrato, toolset, permisos, artefactos, errores, logs, tests y configuracion. Hermes no debe recibir acceso implicito al indice ni depender de el para funcionar.

### HermesAdapter

Segun el contrato de PR #56, Hermes queda detras de JARVIS. Si una capability futura usa CodeGraph, debe entrar por el flujo:

```text
JARVIS Gateway / Interface
  -> Natural Runtime / Intent / Response Model
  -> PolicyEngine
  -> ApprovalGateway si aplica
  -> HermesAdapter
  -> capability local opcional de Code Intelligence
  -> Audit / response
```

### Future skills

Una skill futura podria usar CodeGraph para preparar analisis de impacto, mapas de dependencias o prompts compactos. Esa skill debe declarar permisos, rutas, si necesita indice local, que artefactos crea y como se revierte.

### Developer / Stark Workshop Layer

El Developer / Stark Workshop Layer futuro puede beneficiarse de Code Intelligence para trabajar con repos grandes, pero debe mantener las mismas reglas:

- no auto-instalacion.
- no auto-config global.
- no dependencia runtime.
- no secretos en indice.
- no usar grafo para saltarse policy.
- fallback claro a `rg`/read.

## 7. Riesgos principales

### Configuracion MCP o agentes sin aprobacion

Modificar configuraciones MCP, Codex, Hermes, Claude, Cursor u otros agentes puede cambiar herramientas disponibles, permisos, prompts, servidores locales, rutas indexadas y datos expuestos.

Riesgos:

- crear un servidor MCP activo sin que David lo haya aprobado.
- exponer informacion del repo a herramientas no previstas.
- alterar el comportamiento de agentes en otros proyectos.
- romper prompt caching o toolsets.
- dejar cambios globales dificiles de detectar.
- generar permisos implicitos fuera de JARVIS.

Regla: cualquier cambio de configuracion de agentes/MCP requiere aprobacion explicita, diff revisable y rollback documentado.

### Indexar informacion sensible

Un indice semantico puede capturar mas de lo que parece:

- rutas locales.
- nombres internos.
- comentarios.
- tokens hardcodeados por error.
- `.env` si se configura mal.
- artefactos generados.
- datos de pruebas.
- documentos privados.

Regla: no usar CodeGraph con secretos, `.env`, credenciales, carpetas privadas o datos sensibles sin diseno aprobado. Los logs tampoco deben exponer secretos.

### Indice stale o incorrecto

Un grafo puede estar desactualizado, incompleto o interpretar mal un lenguaje/framework. Si el agente confia demasiado en el, puede proponer cambios equivocados.

Regla: cuando una respuesta dependa de CodeGraph, se debe verificar contra codigo real con `rg`/read antes de editar, testear o afirmar impacto.

## 8. Reglas para `.codegraph` y artefactos locales

- `.codegraph` debe quedar fuera del repo.
- No se debe commitear `.codegraph`.
- Si CodeGraph crea `.codegraph` u otros artefactos locales durante un spike futuro, deben revisarse antes de terminar.
- El spike debe confirmar si esos artefactos ya estan ignorados o deben quedar fuera por limpieza manual.
- No debe agregarse `.codegraph` al repo en esta PR.
- No debe crearse `.codegraph` en esta PR.
- Los artefactos locales deben ser limpiables con un rollback simple.
- Si una futura PR propone `.gitignore`, debe explicar por que, que patrones cubre y que no oculta cambios relevantes.

## 9. Fases de evaluacion

### Phase 0 - Documentacion/contrato

Estado de esta PR.

Objetivo:

- documentar el contrato de evaluacion.
- declarar alcance, riesgos, fases y criterios.
- no instalar ni ejecutar nada.
- no tocar runtime, tests, scripts, CI ni requirements.
- no modificar configuraciones de agentes/MCP.

### Phase 1 - Spike manual en worktree

Objetivo:

- crear un worktree dedicado.
- instalar/ejecutar CodeGraph solo con aprobacion explicita de David.
- confirmar que comandos, rutas y artefactos son locales.
- revisar que archivos crea o modifica.
- confirmar si toca configuraciones globales o locales.
- confirmar que `.codegraph` no se commitea.
- limpiar artefactos al terminar.

### Phase 2 - Medicion comparativa con tareas reales

Objetivo:

- ejecutar tareas reales comparables con y sin CodeGraph.
- medir tool calls, tiempo, archivos leidos, calidad y riesgos.
- registrar errores, ruido y falsos positivos.
- decidir si la mejora justifica mantener una guia local.

Las tareas deben incluir como minimo:

- exploracion de docs.
- analisis de codigo.
- impacto de cambio.

### Phase 3 - Guia de uso local si aporta valor

Objetivo:

- documentar uso local opt-in.
- explicar instalacion solo bajo aprobacion.
- explicar como limpiar artefactos.
- definir fallback a `rg`/read.
- declarar que no es dependencia obligatoria.

### Phase 4 - Integracion opcional futura bajo ApprovalGateway/config explicita

Objetivo:

- disenar una integracion opcional, nunca default.
- pasar por `PolicyEngine` y `ApprovalGateway` cuando aplique.
- declarar capability/tool/skill con permisos y limites.
- evitar runtime critico.
- auditar indexacion, consultas, errores y limpieza.

## 10. Spike controlado

Un spike futuro debe seguir este checklist:

1. Crear worktree dedicado para el spike.
2. Confirmar con David permiso exacto para instalar o ejecutar CodeGraph.
3. No ejecutar `npx`, installers, MCP servers ni comandos de CodeGraph antes de esa aprobacion.
4. Registrar version, comando y origen de instalacion si se aprueba.
5. Revisar que archivos crea antes y despues.
6. Confirmar si crea `.codegraph`.
7. Confirmar que `.codegraph` no se commitea.
8. Confirmar si modifica configs globales o locales.
9. Confirmar si toca configuraciones de Codex/Hermes/Claude/Cursor/MCP.
10. Medir tres tareas reales:
    - exploracion docs.
    - analisis de codigo.
    - impacto de cambio.
11. Comparar cada tarea con baseline sin CodeGraph.
12. Registrar tool calls.
13. Registrar tiempo.
14. Registrar tokens estimados si estan disponibles.
15. Registrar numero de archivos leidos.
16. Registrar precision de ubicacion de simbolos.
17. Registrar calidad de analisis de impacto.
18. Registrar errores, ruido o consultas inutiles.
19. Registrar archivos/configs modificados.
20. Limpiar artefactos al terminar.
21. No tocar runtime ni tests salvo validacion explicita.
22. No afirmar adopcion hasta decision posterior de David.

## 11. Baseline sin CodeGraph

La comparacion debe conservar un baseline normal:

- `rg` para busqueda textual.
- lectura directa de archivos relevantes.
- revision de imports reales.
- inspeccion manual de tests/documentos.
- razonamiento de impacto basado en codigo real.

El baseline no debe inflarse artificialmente. La pregunta correcta no es si CodeGraph parece comodo, sino si mejora tareas reales sin meter riesgo operativo.

## 12. Metricas

| Metrica | Como se observa | Senal positiva |
| --- | --- | --- |
| Tool calls | Numero de llamadas necesarias para llegar a contexto suficiente. | Baja clara sin perdida de calidad. |
| Tiempo | Tiempo total por tarea comparable. | Menor tiempo con respuesta igual o mejor. |
| Tokens estimados | Si el entorno los expone o permite estimarlos. | Menor contexto leido/enviado. |
| Archivos leidos | Conteo de archivos abiertos o fragmentos revisados. | Menos lectura repetitiva. |
| Precision de simbolos | Si localiza funcion/clase/import correcto. | Ubicaciones correctas y verificables. |
| Calidad de impacto | Si identifica dependencias y riesgos reales. | Mejor mapa de cambios sin omisiones graves. |
| Errores o ruido | Falsos positivos, simbolos stale, rutas erroneas. | Bajo ruido y fallback sencillo. |
| Archivos/configs modificados | `git status`, revision de home/config si aplica. | Cero cambios no aprobados. |
| Facilidad de reversion | Pasos para limpiar y volver al baseline. | Limpieza simple y verificable. |

## 13. Reglas de seguridad

- No instalar dependencias sin aprobacion explicita.
- No ejecutar MCP server sin aprobacion explicita.
- No modificar config global de Codex, Hermes, Claude, Cursor ni MCP sin aprobacion explicita.
- No commitear `.codegraph`.
- No enviar indice a servicios externos.
- No tratar el indice como fuente de verdad superior a tests o codigo real.
- No usar CodeGraph para saltarse `PolicyEngine`.
- No usar CodeGraph como runtime dependency.
- No usarlo con secretos o carpetas sensibles sin diseno aprobado.
- No exponer secretos en logs.
- No ejecutar `npx` sin aprobacion explicita.
- No configurar autostart de servidores.
- No permitir que una skill futura active CodeGraph globalmente por defecto.
- No mezclar evaluacion de CodeGraph con cambios funcionales.

## 14. Relacion con futuros contratos

### Developer / Stark Workshop Layer

Code Intelligence puede ser parte de un taller de desarrollo futuro, pero solo como ayuda local y reversible para navegar repos, no como autoridad de ejecucion.

### MCP Connector Contract

Si CodeGraph se usa via MCP, un contrato futuro debe definir servidor, permisos, lifecycle, rutas permitidas, logs, limpieza, aprobacion y configuracion por proyecto.

### Skill Registry

Una skill futura debe declarar si usa CodeGraph, que permisos necesita, si crea indice, que paths lee y como falla cuando no esta instalado.

### Hermes inside JARVIS

PR #56 sigue ganando: Hermes ejecuta solo lo permitido y detras de `HermesAdapter`. CodeGraph no crea una ruta directa a Hermes.

### Restriction Registry

PR #59 debe cubrir restricciones sobre indexacion, secretos, MCP, configuracion global, runtime dependency y logs. CodeGraph no puede crear overrides implicitos.

### Continuous Learning

El sistema de aprendizaje continuo podria proponer evaluar herramientas de Code Intelligence, pero no auto-instalar, auto-configurar ni auto-adoptar CodeGraph.

### Local / Server / Hybrid

Por defecto, CodeGraph pertenece a Local Mode. Server/Hybrid requeririan diseno adicional porque indexar repos en servidor o delegar al worker local cambia privacidad, rutas y auditoria.

### Authorized Security Research / Bug Bounty Mode

Un modo futuro de investigacion autorizada podria usar Code Intelligence defensiva para entender repos propios o targets permitidos. No debe usarse para evadir permisos, exfiltrar secretos ni saltarse scope.

## 15. Ejemplos conceptuales

### Buscar donde vive una funcion

Uso esperado:

- consultar CodeGraph para localizar candidatos.
- verificar con `rg`/read.
- citar archivo y simbolo real.

Fallo esperado:

- si CodeGraph devuelve una ruta stale, volver a `rg`/read y registrar el error.

### Analizar impacto antes de tocar PolicyEngine

Uso esperado:

- pedir dependencias de `PolicyEngine`.
- listar llamadas, tests relacionados y documentos contractuales.
- verificar contra codigo real antes de editar.

Regla:

- CodeGraph no decide que policy permite una accion. Solo ayuda a navegar.

### Encontrar imports/dependencias

Uso esperado:

- consultar que modulos importan una clase o funcion.
- confirmar en archivos reales.
- preparar un mapa de impacto compacto para Codex.

### Preparar prompt cerrado para Codex con menos lectura

Uso esperado:

- usar CodeGraph para reunir paths relevantes.
- leer solo los archivos necesarios.
- redactar prompt con alcance, prohibiciones, validacion y rollback.

### Detectar si CodeGraph se equivoca

Senales:

- simbolo no existe.
- ruta no coincide con repo actual.
- import no aparece en codigo real.
- dependencia omitida por lenguaje/framework.
- respuesta contradice tests o docs.

Respuesta:

- volver a `rg`/read.
- no usar esa salida como base de cambio.
- registrar ruido en metricas.

### Rollback del spike

Rollback esperado:

- detener cualquier proceso local aprobado.
- eliminar artefactos locales generados.
- comprobar que no quedan cambios no deseados.
- confirmar `git status --short`.
- documentar cualquier configuracion tocada y revertida.

## 16. Criterios de aceptacion para adoptar

CodeGraph solo deberia adoptarse en una fase posterior si:

- reduce tool calls de forma clara en tareas reales.
- reduce tiempo sin bajar calidad.
- mejora ubicacion de simbolos y analisis de impacto.
- no introduce riesgo de privacidad.
- no modifica configs sin control.
- los artefactos quedan ignorados o limpiables.
- no se convierte en dependencia runtime.
- aporta valor concreto a Codex, Hermes o JARVIS.
- mantiene fallback simple a `rg`/read.
- la documentacion de uso local queda clara.
- los logs no exponen secretos.
- David aprueba explicitamente la adopcion.

## 17. Criterios para rechazar o posponer

Debe rechazarse o posponerse si:

- requiere configuracion global opaca.
- crea servidores persistentes sin control.
- envia indice a servicios externos.
- produce demasiado ruido.
- no mejora tool calls o tiempo.
- baja calidad de analisis.
- complica rollback.
- indexa secretos o carpetas sensibles.
- obliga a instalar dependencias pesadas para tareas normales.
- rompe workflows existentes de Codex/Hermes/JARVIS.

## 18. Fuera de alcance

PR #60 no implementa:

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
- instalacion de CodeGraph.
- ejecucion de CodeGraph.
- ejecucion de `npx`.
- creacion de `.codegraph`.
- configuracion MCP.
- configuracion de Codex/Hermes/Claude/Cursor.
- APIs externas.
- adopcion de CodeGraph.

## 19. Resultado esperado de esta PR

Al terminar esta PR debe existir solo un contrato documental revisable para decidir como evaluar CodeGraph mas adelante.

No debe existir evidencia de instalacion, ejecucion, integracion ni adopcion. Cualquier frase futura debe distinguir entre:

- `candidato`.
- `spike aprobado`.
- `evaluado`.
- `adoptado`.

En esta PR, CodeGraph queda solo como candidato documentado.
