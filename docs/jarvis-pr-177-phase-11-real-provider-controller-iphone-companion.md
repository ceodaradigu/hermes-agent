# PR #177 - Phase 11 Real Provider Wiring + Local Controller + iPhone Companion

Phase 11 convierte la readiness de Phase 10 en el primer operator layer usable:
proveedores reales configurables, router de modelo/coste v2, controlador local
acotado, navegacion gobernada e iPhone Safari/PWA como superficie del mismo
JARVIS.

La direccion de producto queda fija: el iPhone no es otro JARVIS. El iPhone es
un cliente seguro del mismo JARVIS que vive en el ordenador de David. El
cerebro, persona, modo JARVIS/UTRON, presupuesto, approvals, acciones
pendientes, auditoria y reglas de memoria/gobernanza son compartidos.

## Lo que ahora es real

- `Phase11RealProviderControllerIPhoneCompanion` centraliza el control plane de
  Phase 11 sin duplicar Hermes.
- El registro de proveedores detecta OpenRouter por `OPENROUTER_API_KEY` o
  `JARVIS_OPENROUTER_API_KEY`, proveedor local por endpoint/modelo local y slots
  futuros OpenAI/Anthropic como readiness.
- El router v2 clasifica `simple_chat`, `planning`, `code`,
  `browser_research`, `summarization`, `risky_operation_reasoning` y
  `voice_response`.
- El presupuesto mensual por defecto es 30 EUR. Las decisiones muestran coste
  estimado, presupuesto restante, proveedor/modelo, tier de calidad, motivo,
  fallback y si requieren approval.
- Hay ledger metadata-only para gasto estimado/registrado. No guarda prompts,
  respuestas, secretos ni payloads sensibles.
- Hay adapter OpenRouter seguro e inyectable para tests. Solo puede hacer una
  llamada si hay key, live calls estan habilitadas, el caller permite paid call,
  el presupuesto alcanza y la approval requerida ya esta confirmada.
- El controlador local puede abrir `/jarvis` en navegador/Chrome mediante
  `webbrowser.open` y prepara candidatos para apps conocidas sin aceptar shell
  libre.
- La navegacion gobernada puede abrir URLs `http/https` seguras y busquedas web
  en el navegador local. Formularios, pagos, compras, publicaciones y
  credenciales quedan bloqueados o requieren approval fuerte.
- El companion iPhone tiene endpoints propios para estado, pairing,
  comandos de texto y approvals enlazadas a action id/scope/device.
- `/mobile` es alias de `/jarvis` y se anade manifest PWA para iPhone Safari.
- Dashboard y event stream exponen Phase 11, provider status, router v2 e
  iPhone companion sin secretos.

## Lo que sigue siendo readiness o fallback

- No hay exposicion publica del PC por defecto.
- Acceso remoto fuera de LAN sigue siendo readiness.
- No hay app nativa iOS/App Store en esta fase.
- No hay ejecucion Hermes directa desde frontend o movil.
- No hay `/execute`, shell generico ni comandos arbitrarios desde UI/iPhone.
- Abrir apps distintas a `/jarvis` queda como candidato preparado salvo que el
  camino seguro este implementado y aprobado.
- Automatizacion avanzada de navegador, rellenado de formularios, submit,
  compra, login y entrada de credenciales siguen bloqueados o manuales.
- OpenAI/Anthropic quedan como slots futuros/readiness, no como adapters vivos.
- Conversacion cross-device persistente completa queda como contrato/read model;
  la sincronizacion real de Phase 11 es de sesion actual y metadata compartida.

## Configuracion OpenRouter segura

Variables soportadas:

```bash
OPENROUTER_API_KEY=
JARVIS_OPENROUTER_API_KEY=
JARVIS_OPENROUTER_ENABLED=true
JARVIS_OPENROUTER_LIVE_CALLS_ENABLED=false
JARVIS_OPENROUTER_DEFAULT_MODEL=
JARVIS_OPENROUTER_QUALITY_MODEL=
JARVIS_OPENROUTER_ECONOMY_MODEL=
```

Si falta la key, OpenRouter queda `configured=false`, `enabled=false`,
`ready=false` y el status indica `OPENROUTER_API_KEY` como missing. Si existe
key, el status solo muestra `configured_redacted`; nunca devuelve el valor.

`JARVIS_OPENROUTER_LIVE_CALLS_ENABLED=false` es el default seguro. Con key
presente, JARVIS puede decidir que OpenRouter seria el proveedor correcto, pero
no gasta dinero hasta que un adapter gobernado reciba llamada explicita,
approval valida si aplica y permiso `allow_paid_call=true`.

## Presupuesto de 30 EUR

Variables:

```bash
JARVIS_API_MONTHLY_BUDGET_EUR=30
JARVIS_API_SPEND_EUR=0
JARVIS_API_APPROVAL_THRESHOLD_EUR=1
```

El router calcula coste estimado con metadata de tokens y coste por perfil. Si
el coste supera el presupuesto restante, la decision queda bloqueada con
`budget_exceeded`. Si el coste es significativo o el task es riesgoso, la
decision requiere approval antes de usar proveedor pago.

El router prefiere local cuando la calidad esperada es suficiente. Si la tarea
requiere calidad alta o critica, no baja a un modelo barato/local solo por
coste; marca `quality_downgrade_rejected=true` y explica el motivo.

## iPhone Companion

El iPhone usa Safari/PWA/LAN como primera superficie:

- abrir `/mobile` o `/jarvis` desde Safari;
- instalar como PWA si Safari ofrece "Add to Home Screen";
- consultar estado JARVIS, proveedores, budget, approvals, auditoria y modo
  persona;
- enviar comandos de texto;
- usar microfono si Safari lo permite y la UI del navegador concede permiso;
- aprobar/denegar acciones pendientes solo tras pairing;
- activar/desactivar UTRON a traves del mismo estado de persona de Phase 10.

El companion no contiene un runtime Hermes, no ejecuta shell, no llama tools y
no tiene memoria separada. Todo pasa por la capa gobernada de JARVIS.

## Pairing

Endpoints principales:

```text
GET  /iphone/companion/status
GET  /iphone/companion/state
POST /iphone/pairing/start
POST /iphone/pairing/verify
POST /iphone/pairing/revoke
POST /iphone/command
POST /iphone/approval/decision
```

`/iphone/pairing/start` genera challenge efimero con codigo, nonce, QR payload
y expiracion corta. `/iphone/pairing/verify` enlaza el dispositivo si codigo,
nonce y challenge coinciden antes de expirar. `/iphone/pairing/revoke` revoca
el dispositivo.

Las approvals desde iPhone se enlazan a:

- `approval_id`;
- `action_id`;
- scope exacto;
- canal `iphone_pwa`;
- device id confiable;
- expiracion;
- frase exacta `confirmo y autorizo` cuando el riesgo lo exige.

Se rechaza replay, scope distinto, action id distinto, wake phrase, dispositivo
no emparejado y cualquier intento no autenticado.

## LAN y acceso remoto

Phase 11 esta pensada para LAN/iPhone Safari primero. Un arranque local tipico:

```bash
python -m uvicorn jarvis.api.app:app --host 0.0.0.0 --port 9119
```

David debe abrir desde el iPhone la IP LAN del PC y ruta `/mobile` o `/jarvis`.
Esto no debe exponerse a internet sin una decision explicita de tunnel/auth.

Opciones futuras seguras:

- tunnel autenticado y revocable;
- bridge Telegram/Hermes notification/control con approvals;
- app nativa iOS/App Store cuando la PWA demuestre valor;
- VPS solo si hay necesidad tecnica probada o JARVIS ya justifica el coste.

Mac mini/VPS no es requisito de esta fase. JARVIS permanece en el PC de David.

## Piloto de apps

Apps conocidas:

- Chrome/browser;
- Cursor;
- VS Code;
- Windows Terminal/Terminal/WSL;
- File Explorer;
- WhatsApp;
- Spotify;
- carpeta del proyecto JARVIS.

La accion real acotada en Phase 11 es abrir `/jarvis` en el navegador. Para
apps conocidas se crea candidato gobernado con riesgo, approval y auditoria.
Para app desconocida JARVIS responde:

```text
No sé dónde está esa aplicación. Dime la ruta una vez y la guardaré como app conocida.
```

No se acepta comando raw, shell libre ni ruta sensible desde frontend/iPhone.

## Piloto de navegador

Intents soportados:

- abrir URL segura;
- buscar en web;
- resumir pagina actual si el adapter futuro lo soporta;
- preparar form fill;
- preparar mensaje;
- navegar a servicio conocido.

Reglas:

- submit de formularios requiere approval;
- pagos/compras/publicacion requieren strong approval;
- login y credenciales quedan manuales hasta un flujo de vault futuro;
- no se guardan passwords en texto plano;
- no se finge navegacion si el adapter no la hizo.

## Seguridad

Invariantes:

- JARVIS gobierna; Hermes ejecuta.
- Frontend/iPhone no ejecutan Hermes directamente.
- Wake phrase nunca aprueba.
- UTRON no salta approvals.
- Memoria no concede permisos ni baja riesgo.
- Secretos se redacted antes de status, audit, dashboard, event stream y tests.
- Illegal, unsafe, unauthorized, impossible o unsupported se deniega o se marca
  honestamente como unsupported.
- Mobile approval requiere pairing/trust, action id, scope, readback,
  expiracion y audit.
- No public exposure por defecto.

## Endpoints nuevos

```text
GET  /mark-3/phase-11/status
GET  /mark-3/providers/status
GET  /mark-3/model-router-v2/status
POST /mark-3/model-router-v2/classify
POST /mark-3/model-router-v2/decision
GET  /mark-3/phase-11/approval/status
POST /mark-3/phase-11/approval/start
POST /mark-3/phase-11/approval/confirm
GET  /mark-3/phase-11/local-controller/status
POST /mark-3/phase-11/local-controller/launch-candidate
POST /mark-3/phase-11/local-controller/launch
GET  /mark-3/phase-11/browser/status
POST /mark-3/phase-11/browser/prepare
POST /mark-3/phase-11/browser/open
GET  /mark-3/phase-11/shared-state
GET  /iphone/companion/status
GET  /iphone/companion/state
POST /iphone/pairing/start
POST /iphone/pairing/verify
POST /iphone/pairing/revoke
POST /iphone/command
POST /iphone/approval/decision
```

## Validacion manual

1. Arrancar API local en LAN solo cuando se quiera probar iPhone:

```bash
python -m uvicorn jarvis.api.app:app --host 0.0.0.0 --port 8000
```

2. En desktop, abrir `http://127.0.0.1:8000/jarvis`.
3. En iPhone conectado a la misma red, abrir `http://<IP-LAN-PC>:8000/mobile`.
4. Confirmar que `/mobile` muestra el mismo cockpit JARVIS y no una consola
   separada.
5. Consultar `GET /iphone/companion/status`.
6. Crear pairing con `POST /iphone/pairing/start`, verificarlo con
   `/iphone/pairing/verify` y revocarlo con `/iphone/pairing/revoke`.
7. Probar comando iPhone emparejado para activar/desactivar UTRON.
8. Crear approval y aprobar desde iPhone con `confirmo y autorizo`, verificando
   que scope/action id equivocados fallan.
9. Probar `POST /mark-3/phase-11/local-controller/launch-candidate` con
   `Chrome` y luego launch para abrir `/jarvis`.
10. Probar `POST /mark-3/phase-11/browser/prepare` con URL segura, formulario,
    compra y login, verificando gates distintas.

## Validacion automatizada recomendada

```bash
source venv/bin/activate
PYTHONPATH=. python -m pytest tests/jarvis/test_pr_177_phase_11_real_provider_controller_iphone_companion.py -q
PYTHONPATH=. python -m pytest tests/jarvis -q
npm --prefix web run build
git diff --check
```
