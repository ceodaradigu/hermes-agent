# JARVIS Visual Command Center Pilot

PR #153 valida el cockpit local `/jarvis` como Visual Command Center read-only.
PR #154 endurece la composicion UX para que la primera pantalla sea un cockpit
horizontal compacto, no una pagina vertical interminable.
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
- El primer viewport prioriza header, radar de modulos, nucleo central JARVIS,
  Approval Console resumida, Mission Control resumido, Hermes Execution
  resumido, Finance / ROI compacto, Product Builder compacto, Kill Switch y
  salud del sistema.
- Los detalles largos quedan en tabs locales: Cockpit, Approvals, Hermes,
  Voice / Wake, Vision / Mobile, Finance / Product y Pilot / Audit.
- Las listas largas usan scroll interno; abrir `/jarvis` no debe sentirse como
  un informe desplegado completo.

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
4. Comprobar que el cockpit principal cabe razonablemente above-the-fold en
   desktop.
5. Comprobar tabs: Cockpit, Approvals, Hermes, Voice / Wake, Vision / Mobile,
   Finance / Product y Pilot / Audit.
6. Comprobar panels.
7. Comprobar `unknown`/`disabled`/`not_connected`/`preview`/`future_gated`.
8. Comprobar que botones criticos estan disabled.
9. Comprobar que no hay permisos de navegador.
10. Comprobar que no hay ejecucion Hermes.
11. Comprobar que Finance / ROI no inventa datos.
12. Comprobar timeline read-only.

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

El piloto es correcto cuando David puede ver en menos de 10 segundos si JARVIS
esta online, si esta en modo preview/read-only, si hay approvals, si Hermes
ejecuta algo, si sensores estan apagados, si dinero/deploy/email estan
bloqueados y donde esta el Kill Switch. El read model sigue conectado, todos
los paneles esperados siguen disponibles en tabs, los valores sin evidencia
degradan honestamente, los botones criticos estan disabled y el timeline es
read-only, sin que el frontend ejecute Hermes ni active sensores.

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
- `/jarvis` vuelve a ser una sabana vertical con todos los detalles desplegados
  a la vez.
- Los tabs desaparecen o los paneles largos pierden scroll interno.

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
