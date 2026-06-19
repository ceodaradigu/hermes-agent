# JARVIS Phase 3 Local Runtime Daemon + Trusted Approval Report

Fecha: 2026-06-19

## Resultado Ejecutivo

Phase 3 queda implementada como macro-fase coherente sobre Phase 2. JARVIS tiene
daemon local embebido, readiness de tray, trusted approval channels, double
approval real, stop/rollback observable, execution history v2, local doctor,
pilot checklist y readiness de Telegram/mobile futuro deshabilitada.

No se crea otro Hermes. No se duplica runtime de ejecucion. El frontend nunca
ejecuta Hermes directamente.

## Implementacion Por Bloque

### A - Local Runtime Daemon

Implementado en `jarvis/phase_3_local_runtime.py`.

El daemon local es el proceso API local embebido: local-only, bind seguro
`127.0.0.1:9119`, no autostart, no background listening, no auto
mic/camera/wake, heartbeat auditable y stop/restart unsupported honesto.

### B - Tray / Local Controller Readiness

Readiness preparada sin instalar tray nativo. El contrato declara controles que
un tray futuro deberia soportar y deja `tray_installed=false`.

### C - Trusted Approval Channels

Canales implementados como contrato gobernado: UI local, terminal local, tray
not installed, voice readback only, wake disabled, Telegram/mobile future
disabled. Voice y wake no pueden aprobar. Telegram/mobile no estan activos.

### D - Strong / Double / Triple Approval

Strong se mantiene backend-gated.

Double es realista: dos pasos, frases distintas, caducidad por paso, readback
obligatorio, canales separados, anti-reuse y audit por paso.

Triple queda bloqueado por falta de tres canales independientes reales.

### E - Stop / Rollback Observable

Stop y rollback exponen metadata estructurada y no fingen capacidades. Read-only
no requiere rollback. Prepare-only descarta preview. Acciones futuras con side
effects deben traer rollback plan.

### F - Execution History v2

Historial metadata-only con filtros, export preview y campos nuevos de approval,
channel, stop y rollback. Persiste en SQLite si hay state dir local.

### G - Runtime Health / Doctor Local

Doctor local seguro: comprueba imports y entorno, dirs escribibles, DBs locales,
bind local y package lock, sin leer `.env`, sin exponer secretos, sin instalar
dependencias y sin scanners pesados.

### H - Browser / Local Pilot

El pilot se documenta en
`docs/jarvis-phase-3-local-runtime-pilot-report.md`. Distingue pruebas
automatizadas, build, pending manual pilot y unsupported honesto.

### I - UI `/jarvis`

Drawer actualizado con secciones Phase 3 sin saturar el centro ni mostrar JSON
gigante.

### J - API / Backend

Se agregan endpoints Phase 3 GET/POST gobernados. No hay `/execute`, shell libre
ni comandos arbitrarios.

### K - Telegram / Mobile Future

Readiness deshabilitada con remote approval false, remote execution false,
trusted pairing required, tokens no cargados y no llamadas externas.

### L - External Adoption

Se revisaron repos externas para patrones. No se copio codigo externo ni se
instalaron dependencias.

## Acciones Que Ejecuta Realmente

Se mantienen las acciones allowlisted de Phase 2:

- status/control-plane local reads;
- comandos git fijos sin shell libre;
- pytest target allowlisted;
- lectura segura via Hermes bridge existente cuando hay approval valido;
- preview/read-only/history/audit/status.

Phase 3 agrega control-plane runtime/approval metadata, no nuevos ejecutores
libres.

## Denied / Unsupported

Denied:

- credenciales, `.env`, tokens, passwords, cookies, session material;
- wake approval;
- voice approval;
- frontend Hermes directo;
- `/execute`;
- shell libre;
- comandos arbitrarios;
- dinero, Stripe, deploy, email, publicacion.

Unsupported honesto:

- triple approval sin tercer canal real;
- stop/restart de servicio externo;
- tray nativo;
- Telegram/mobile remoto activo;
- browser capability checks server-side.

## Validacion

Validado por tests automatizados:

- Phase 3 dedicated suite;
- full `tests/jarvis`;
- py_compile;
- diff check;
- frontend build.

Los comandos exactos y salidas se recogen en la respuesta final de Codex.

## Riesgos Pendientes

- Falta tray nativo opt-in.
- Falta tercer canal independiente para critical triple.
- Stop real de procesos largos depende del bridge futuro.
- Browser pilot manual aun debe ejecutarse visualmente.
- Remote bridge debe seguir disabled hasta pairing fuerte.

## Siguiente Macro-Fase

Phase 4: tray/local controller opt-in real, tercer canal confiable para triple
approval, stop cooperativo observable para procesos largos y pairing remoto
preparado pero no abierto por defecto.
