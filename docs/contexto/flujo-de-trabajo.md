# Flujo de Trabajo

## Como trabaja David con Codex

1. Verificar `main` antes de empezar.
2. Crear una rama/worktree por PR bajo `~/jarvis-worktrees`.
3. Abrir Codex dentro del worktree.
4. Pasar un prompt cerrado con objetivo, alcance, prohibiciones, validacion y
   formato final.
5. Activar venv antes de Python.
6. Codex implementa o documenta dentro del alcance.
7. Codex valida lo tocado.
8. David revisa, valida manualmente si aplica y decide commit/push/PR/merge.

## Comandos base documentados

```bash
git checkout main
git pull
git status --short

mkdir -p ~/jarvis-worktrees
git worktree add -b pr-XX-nombre ~/jarvis-worktrees/pr-XX-nombre main
cd ~/jarvis-worktrees/pr-XX-nombre
```

Para este repo, `AGENTS.md` exige:

```bash
source venv/bin/activate
```

## Prohibido para Codex salvo instruccion explicita

- Hacer commit.
- Hacer push.
- Abrir PR.
- Mergear.
- Ejecutar `jarvis-finish-pr`.
- Cambiar `main` directamente.
- Anadir runtime peligroso, `/execute` o shell arbitrario desde UI.

## Cierre

David pega el resumen de Codex donde corresponda. Una PR solo se cierra cuando
la validacion requerida paso de verdad. Si la PR promete capacidad de usuario,
los tests no bastan: hace falta validacion manual real o declarar el cierre como
`READINESS`.
