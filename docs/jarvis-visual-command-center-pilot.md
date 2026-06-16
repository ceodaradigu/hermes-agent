# JARVIS Visual Command Center Pilot

PR #153 valida el cockpit local `/jarvis` como Visual Command Center read-only.
La regla central no cambia:

```text
JARVIS gobierna.
Hermes ejecuta.
```

## 1. Que valida este piloto

- `/jarvis` carga como dashboard local.
- `/jarvis` consume `GET /mark-3/dashboard/status`.
- El backend expone `visual_command_center_pilot` en el read model.
- Todos los paneles esperados siguen visibles: Header, Voice Core, Wake Word
  Local Safe Flow, Mission Control, Approval Console, Hermes Execution, Agent /
  Module Radar, Camera / Vision, Mobile Companion, Finance / ROI, Product
  Builder Adaptativo, Frontend Pilot / Hardening, Live Timeline / Audit y Kill
  Switch.
- Los estados sin evidencia degradan a `unknown`, `disabled`,
  `not_connected`, `preview` o `future_gated`.
- Los botones criticos permanecen disabled.
- El timeline es read-only y no afirma ejecucion real.
- Finance / ROI conserva no fake metrics.

## 2. Que NO valida

- no Hermes execution;
- no real approvals;
- no real mission submit;
- no real voice;
- no real wake listener;
- no sensors;
- no camera capture;
- no mobile runtime;
- no money, Stripe, checkout or payment movement;
- no deploy;
- no email send;
- no credentials;
- no production readiness;
- no browser/manual pilot result claimed by code or docs.

## 3. Como arrancar backend

```bash
source ~/venvs/hermes-agent/bin/activate
export PYTHONPATH=.
python -m uvicorn jarvis.api.app:app --host 127.0.0.1 --port 9119
```

## 4. Como abrir `/jarvis`

En otra terminal:

```bash
cd web
npm ci
npm run dev
```

Abrir la URL local del frontend y navegar a `/jarvis`. El proxy de Vite apunta
`/mark-3` a `http://127.0.0.1:9119`.

## 5. Checklist manual

1. Arrancar backend.
2. Abrir `/jarvis`.
3. Comprobar estado general.
4. Comprobar panels.
5. Comprobar `unknown`/`disabled`/`not_connected`/`preview`/`future_gated`.
6. Comprobar que botones criticos estan disabled.
7. Comprobar que no hay permisos de navegador.
8. Comprobar que no hay ejecucion Hermes.
9. Comprobar que Finance / ROI no inventa datos.
10. Comprobar timeline read-only.

## 6. Checklist de seguridad

- Dashboard route: `/jarvis`.
- Status endpoint: `/mark-3/dashboard/status`.
- Frontend reads status only.
- No POST/PUT/DELETE from `/jarvis`.
- No execute route from the dashboard.
- No frontend Hermes call.
- No tool runner.
- No sensor activation.
- No getUserMedia.
- No MediaRecorder.
- No AudioContext capture.
- No camera capture.
- No mobile runtime.
- No money movement.
- No Stripe live.
- No deploy.
- No email send.
- No credentials.
- No fake metrics.

## 7. Criterio de exito

El piloto es correcto cuando David puede ver el dashboard completo, el read
model conectado, todos los paneles esperados, degradacion honesta de valores
sin evidencia, botones criticos disabled y timeline read-only, sin que el
frontend ejecute Hermes ni active sensores.

## 8. Criterio de fallo

Abrir una PR de correccion si aparece cualquiera de estos casos:

- `/jarvis` llama algo distinto del status read model para el cockpit.
- Se introduce una ruta mutante o execute route.
- Se habilita un boton critico.
- Aparece un permiso de navegador.
- Finance / ROI muestra valores medidos sin evidencia.
- El timeline afirma ejecucion real.
- Se conecta Hermes execution desde frontend.
- Se mueve dinero, se crea checkout, se hace deploy, se envia email o se toca
  una credencial.

## 9. Findings que deben abrir PR

- Missing panel.
- Estado real mal degradado.
- Boton critico enabled.
- Browser permission prompt.
- Acceso directo a Hermes desde frontend.
- Metricas financieras sin evidencia.
- Timeline con eventos de ejecucion inventados.
- Vulnerabilidad/dependencia que requiera lockfile o package changes.

## 10. Fuera de alcance

- approvals reales;
- ejecucion Hermes;
- voz real;
- camara real;
- movil real;
- dinero, deploy, email o credenciales;
- dependency hardening separate PR.

Dependency hardening queda para una PR separada. No ejecutar `npm audit fix` en
este piloto.
