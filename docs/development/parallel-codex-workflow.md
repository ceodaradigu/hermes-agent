# Parallel Codex Workflow

## Objetivo

Este documento explica como trabajar con varios Codex en paralelo usando `git worktree` sin pisarse entre ramas, tareas o pull requests.

La idea es que cada Codex trabaje en una carpeta independiente, con una rama independiente y una tarea acotada. Esto permite avanzar varias PRs a la vez sin mezclar cambios ni bloquear el directorio principal del repositorio.

## Cuando usar varios Codex

Usa varios Codex en paralelo cuando:

- Las tareas son independientes entre si.
- Cada tarea puede vivir en una rama distinta.
- Las PRs son pequenas y revisables.
- Los archivos tocados por cada tarea no se solapan, o el solape esta muy controlado.
- Quieres mantener un Codex validando una PR mientras otro prepara documentacion, pruebas manuales o cambios en otra area.

Evita este flujo cuando:

- La tarea requiere una refactorizacion grande y transversal.
- Varias ramas necesitan editar los mismos archivos criticos.
- Todavia no esta claro el alcance de cada PR.
- No hay tiempo para resolver conflictos de rebase o merge.

## Crear worktrees

Desde el repositorio principal, crea una rama y un worktree por cada tarea:

```bash
git fetch origin
git checkout main
git pull --ff-only

git worktree add -b pr-25-parallel-roadmap-doc ~/jarvis-worktrees/pr-25-parallel-roadmap-doc main
```

Para varias tareas en paralelo:

```bash
git worktree add -b pr-22-feedback-api-smoke-docs ~/jarvis-worktrees/pr-22-feedback-api-smoke-docs main
git worktree add -b pr-23-voice-runtime-cli-status ~/jarvis-worktrees/pr-23-voice-runtime-cli-status main
git worktree add -b pr-24-user-understanding-feedback-preview ~/jarvis-worktrees/pr-24-user-understanding-feedback-preview main
git worktree add -b pr-25-parallel-roadmap-doc ~/jarvis-worktrees/pr-25-parallel-roadmap-doc main
```

Ejemplo de carpetas activas:

```text
~/jarvis-worktrees/pr-22-feedback-api-smoke-docs
~/jarvis-worktrees/pr-23-voice-runtime-cli-status
~/jarvis-worktrees/pr-24-user-understanding-feedback-preview
~/jarvis-worktrees/pr-25-parallel-roadmap-doc
```

Abre un Codex distinto dentro de cada carpeta. Cada instancia debe recibir un prompt pequeno, concreto y limitado a su rama.

## Reglas para evitar conflictos

- Cada Codex trabaja en una rama distinta.
- Cada PR debe ser pequena y facil de revisar.
- No tocar los mismos archivos si se puede evitar.
- No tocar `jarvis/api/app.py` en varias ramas a la vez.
- No tocar `runtime.py` en varias ramas a la vez.
- No tocar CI ni `requirements` salvo que la tarea lo pida explicitamente.
- Correr tests antes de abrir o actualizar una PR.
- Respetar `docs/jarvis-north-star.md` como guia de producto y arquitectura.

Si dos tareas necesitan el mismo archivo critico, no las ejecutes en paralelo. Termina una, haz merge, actualiza `main` y luego continua con la otra.

## Flujo recomendado

1. Crear un worktree desde `main` actualizado.
2. Abrir Codex en la carpeta de ese worktree.
3. Dar un prompt acotado, con archivos permitidos y archivos prohibidos si aplica.
4. Validar los cambios localmente.
5. Hacer commit en esa rama.
6. Hacer push de la rama.
7. Crear la PR.
8. Revisar y ajustar la PR hasta que este lista.
9. Hacer merge.
10. Actualizar `main` en el repositorio principal.
11. Rebasear o limpiar worktrees si hace falta.

Comandos habituales:

```bash
cd ~/jarvis-worktrees/pr-25-parallel-roadmap-doc
git status --short
git diff

source venv/bin/activate
python -m pytest tests/ -q

git add docs/development/parallel-codex-workflow.md
git commit -m "docs: add parallel codex workflow"
git push -u origin pr-25-parallel-roadmap-doc
```

## Limpieza de worktrees

Lista los worktrees existentes:

```bash
git worktree list
```

Elimina un worktree que ya no se necesita:

```bash
git worktree remove <path>
```

Elimina la rama local despues de mergear:

```bash
git branch -d <branch>
```

Si un worktree quedo registrado pero la carpeta ya no existe, revisa el estado y limpia referencias obsoletas:

```bash
git worktree list
git worktree prune
```

## Riesgos

- Conflictos: aparecen cuando varias ramas modifican los mismos archivos o areas cercanas.
- Duplicar trabajo: dos Codex pueden resolver la misma necesidad de formas distintas si los prompts no estan bien delimitados.
- PRs demasiado grandes: cuanto mas grande la PR, mas dificil es revisar, testear y mergear sin efectos secundarios.
- Codex tocando arquitectura sin permiso: los prompts deben dejar claro cuando una tarea es solo documentacion, solo tests, solo UI o solo un modulo concreto.

## Checklist antes de merge

- La PR tiene un alcance pequeno y claro.
- La rama esta actualizada o no tiene conflictos relevantes con `main`.
- `git status --short` no muestra cambios inesperados.
- Los archivos modificados corresponden a la tarea.
- No se tocaron CI, `requirements` ni archivos criticos fuera del alcance.
- No se modificaron `jarvis/api/app.py` ni `runtime.py` en paralelo con otra rama activa.
- Los tests necesarios se corrieron y pasaron.
- La PR respeta `docs/jarvis-north-star.md`.
- La descripcion de la PR explica que cambia, como se valido y que queda fuera de alcance.
