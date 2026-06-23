# Convenciones

## Estilo observado

- Documentos breves, con secciones explicitas: que es real, que queda fuera,
  validacion y limites.
- Estado de capacidades siempre clasificado distinguiendo `REAL en
  repo/código/tests`, `REAL validado en PC de David`, `PARCIAL`, `READINESS`,
  `NO HECHO` y `[PENDIENTE: verificar]`.
- Evidencia por ruta concreta: docs, tests, codigo o commits.
- Seguridad escrita como invariante, no como detalle opcional.

## Branches y PRs

- Branch/worktree observado: `pr-180-jarvis-context-pack-reality-audit`.
- Patron reciente en commits: `Phase N ... (#PR)` o descripcion concreta de PR,
  por ejemplo `Hermes Total Capability Audit + JARVIS Control Map (#179)`.
- Worktrees bajo `~/jarvis-worktrees/<branch-name>` segun
  `docs/jarvis-handoff-context.md`.

## Clasificacion

| Estado | Uso |
| --- | --- |
| `REAL en repo/código/tests` | Hay codigo ejecutable y evidencia en repo/tests/docs/commits. |
| `REAL validado en PC de David` | Ademas de evidencia documental, hay validacion manual/local conocida en el entorno de David. |
| `PARCIAL` | Una parte funciona, pero falta integracion, cobertura o flujo producto. |
| `READINESS` | Hay contrato, preview, status, endpoint o plan, pero no ejecucion real completa. |
| `NO HECHO` | No se encontro capacidad real en el repo auditado. |

Si algo no esta verificado en repo/tests/docs/commits, escribir
`[PENDIENTE: verificar]`.

No degradar una capacidad ya validada en PC de David a `READINESS` solo porque
dependa de entorno local. Documentar la validacion y la condicion de
revalidacion futura si cambia ese entorno.

## Como documentar limites

- Separar "lo que hace" de "lo que no hace".
- Si depende de entorno externo, decirlo: tokens, modelos locales, Tailscale,
  mic, browser TTS, Home Assistant, MCP servers.
- No usar "done", "terminado" o "funciona" para capacidades que solo tienen
  preview o status.

## Evitar fake progress

- Tests no sustituyen validacion manual cuando la PR promete capacidad de
  usuario.
- `simulate`, `mock`, `dry-run`, `preview`, `status` y `read model` no prueban
  ejecucion real completa.
- OpenRouter no debe ser excusa para acciones basicas de navegador/archivo; esas
  deben ir por dispatcher gobernado hacia Hermes.
