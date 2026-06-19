# PR #163 - Phase 1 Voice Runtime Pack

## Resumen

Esta PR pertenece a Fase 1 - JARVIS usable en local. Implementa un Voice Runtime Pack seguro para el runtime de voz local/manual:

- Nuevo control-plane read-only `VoiceRuntimePack`.
- Nuevo endpoint GET `/mark-3/voice-runtime/status`.
- Provider contracts STT/TTS para browser y futuros providers locales.
- Mejoras del Local Voice Loop en `/jarvis`: stop/cancel, interrupt TTS, estados `listening`/`transcribing`/`thinking`/`speaking`/`cancelled`/`stopped`, cola corta TTS y filtro de eco.
- Integracion con la esfera de particulas de #162 por estado, sin Web Audio nuevo.
- Dashboard/read model/event stream/doctor actualizados.

JARVIS gobierna. Hermes ejecuta. Esta PR no crea otro Hermes, no duplica runtime de ejecucion y no abre ejecucion desde frontend.

## Que se implemento

Backend/control-plane:

- `jarvis/voice_runtime_pack.py`.
- `schema_version=jarvis.voice_runtime_pack.v1`.
- `runtime_id=jarvis-local-manual-voice-runtime-pack`.
- `mode=local_manual_browser_voice_control_plane`.
- `enabled=true`.
- `manual_push_to_talk_enabled=true`.
- `browser_stt_available=client_side_unknown`.
- `browser_tts_available=client_side_unknown`.
- `local_stt_provider_status`.
- `local_tts_provider_status`.
- `wake_runtime_status`.
- `active_session`.
- `last_transcript_summary`.
- `last_response_summary`.
- `current_state=idle`.
- `can_interrupt=true`.
- `can_cancel=true`.
- `raw_audio_sent_to_backend=false`.
- `transcript_persistence=false`.
- `voice_approval_enabled=false`.
- `voice approval disabled`.
- `wake phrase no aprueba`.
- `wake_phrase_can_approve=false`.
- `wake_phrase_can_execute=false`.
- `hermes_dispatch_allowed=false`.

Estados declarados:

- `idle`
- `listening`
- `transcribing`
- `thinking`
- `speaking`
- `cancelled`
- `stopped`
- `error`
- `approval_required`
- `wake_listening_available`
- `wake_listening_disabled`

Read model/event stream:

- `/mark-3/dashboard/status` expone `voice_runtime_pack`.
- `/mark-3/dashboard/events` y `/mark-3/dashboard/events/stream` exponen `voice_runtime_state`.
- `/mark-3/local-doctor/status` declara `voice_runtime_pack_endpoint` y safety `no_voice_provider_install=true`, `no_voice_model_download=true`.
- El stream sigue siendo GET/read-only, sin secretos, sin audio bruto, sin frames y sin ejecucion.

Frontend `/jarvis`:

- `useLocalVoiceLoop` conserva activacion manual por boton.
- Stop/cancel aborta SpeechRecognition, cancela `speechSynthesis`, limpia timers y deja estado `cancelled`.
- Timeout de conversacion manual deja estado `stopped`.
- TTS usa una cola corta local, con cancel/interruption por `speechSynthesis.cancel()`.
- Se filtra posible eco de la propia respuesta de JARVIS.
- La smart bar muestra respuesta humana corta; los detalles tecnicos siguen plegados en `details`.
- Se conserva la frase exacta: `No puedo hacer eso, David. Las credenciales y secretos estan protegidos.`
- La esfera recibe `cancelled`/`stopped` como estado visual calmado.

## Estado real de voz

- STT real disponible solo si el navegador soporta `SpeechRecognition` o `webkitSpeechRecognition`.
- TTS real disponible solo si el navegador soporta `speechSynthesis` y `SpeechSynthesisUtterance`.
- El backend no puede detectar honestamente esas APIs, por eso declara `client_side_unknown`.
- El backend no abre microfono.
- El backend no recibe audio bruto.
- El backend no guarda transcripciones por defecto.
- La conversacion manual existe solo en el navegador y solo tras gesto del operador.

## Provider contracts STT/TTS

STT:

- `browser_speech_recognition`: browser/client-side, detection en navegador, `status=client_side_unknown`.
- `faster_whisper_disabled_or_missing`: futuro local STT, disabled por defecto, requiere modelo, no descarga modelo.
- `whisper_cpp_disabled_or_missing`: futuro local STT via binario, disabled por defecto, requiere modelo, no compila ni descarga modelo.

TTS:

- `browser_speech_synthesis`: browser/client-side, voices detectadas por navegador, `status=client_side_unknown`.
- `piper_local_disabled_or_missing`: futuro local TTS, disabled por defecto, requiere voz/modelo, no descarga nada.

Todos los providers reales locales quedan `enabled=false`. Todos declaran `network_required=false`, `external_provider=false` y no persisten audio bruto.

## Que NO se implemento

- No se implemento wake real always-on.
- No se implemento STT local real.
- No se implemento TTS local Piper real.
- No se instalo `faster-whisper`.
- No se instalo `whisper.cpp`.
- No se instalo Piper.
- No se instalo `ffmpeg`.
- No se instalo `sounddevice`.
- No se instalo `torch`.
- No se instalo `openwakeword`.
- No se instalo MediaPipe/TFJS.
- No se descargaron modelos.
- No se abrio microfono automaticamente.
- No se abrio camara automaticamente.
- No se envio audio bruto al backend.
- No se guardo audio bruto nuevo.
- No se guardaron transcripciones por defecto.
- No se implemento voice approval real.
- No se implemento approve/reject real por voz.
- No se conecto Hermes directo desde frontend.
- No se creo `/execute`.
- No se agregaron APIs externas, LLM externo, deploy, dinero, email ni credenciales.

## Como probar

Backend:

```bash
source ~/venvs/hermes-agent/bin/activate
export PYTHONPATH=.
PYTHONPATH=. python -m pytest -c /dev/null tests/jarvis/test_pr_163_voice_runtime_pack.py -q -x
```

Read model:

```bash
python - <<'PY'
from jarvis.api.app import create_app
app = create_app()
route = next(r for r in app.routes if r.path == "/mark-3/voice-runtime/status")
print(route.endpoint())
PY
```

Frontend:

```bash
cd web
npm run build
```

## Como verificar browser STT/TTS

En `/jarvis`:

1. Abrir la pantalla.
2. Revisar la smart bar:
   - `STT navegador soportado/no soportado`.
   - `TTS navegador soportado/no soportado`.
3. Si STT no existe, la UI debe decir que no se simula escucha.
4. Si TTS no existe, la respuesta debe quedar visible como texto.
5. La voz seleccionada debe venir del catalogo real de `speechSynthesis`; no se afirma voz premium si no existe.

## Como verificar visual states

1. Abrir `/jarvis`.
2. Pulsar el microfono manualmente.
3. Observar:
   - `listening` -> esfera atenta/concentrada.
   - `transcribing` -> reorganizacion.
   - `thinking` -> turbulencia.
   - `speaking` -> picos/ondas.
   - `error` -> patron error.
   - `stopped`/`cancelled` -> esfera calmada.
4. Tambien se puede usar el Visual QA plegado de #162 con `jarvisVisualPreview`.

## Riesgos

- Web Speech API no es uniforme entre navegadores.
- SpeechRecognition del navegador puede depender de servicios del proveedor del navegador; por eso se declara browser/client-side y no backend local.
- `speechSynthesis.getVoices()` puede cargar voces tarde; la UI escucha `onvoiceschanged`.
- El filtro de eco es heuristico.
- Providers locales futuros requieren decisiones separadas sobre modelos, licencias, paths, consumo CPU/GPU y packaging.
- Piper GPL-3.0 requiere cuidado legal si se integra o distribuye.

## Repos externas revisadas

| Repo | URL | Licencia visible | Que se tomo |
|---|---|---|---|
| `OpenVoiceOS/ovos-core` | https://github.com/OpenVoiceOS/ovos-core | Apache-2.0 | Patron conceptual de runtime de voz modular. Reimplementado como read model seguro. |
| `MycroftAI/mycroft-core` | https://github.com/MycroftAI/mycroft-core | Apache-2.0 visible en GitHub | Separacion conceptual entre wake, skills, bus y servicios. No se copio runtime ni skills. |
| `dscripka/openWakeWord` | https://github.com/dscripka/openWakeWord | Apache-2.0 | Solo contrato/status futuro para wake provider. No se instalo ni activo. |
| `SYSTRAN/faster-whisper` | https://github.com/SYSTRAN/faster-whisper | MIT | Solo provider contract futuro `faster_whisper_disabled_or_missing`. |
| `openai/whisper` | https://github.com/openai/whisper | MIT | Referencia de STT local futuro. No se instalo ni se llamo. |
| `ggml-org/whisper.cpp` | https://github.com/ggml-org/whisper.cpp | MIT | Solo deteccion segura de binario futuro. No build, no modelo. |
| `OHF-Voice/piper1-gpl` | https://github.com/OHF-Voice/piper1-gpl | GPL-3.0 | Solo contrato/status futuro `piper_local_disabled_or_missing`; no codigo copiado. |
| `OHF-Voice/wyoming` | https://github.com/OHF-Voice/wyoming | MIT | Referencia de protocolo voice services. No se adopto porque transporta audio/payloads. |
| `ethanplusai/jarvis` | https://github.com/ethanplusai/jarvis | Personal/no comercial visible | Solo referencia de UX voice-first; no codigo ni integraciones. |
| `harsh-raj00/my-jarvis` | https://github.com/harsh-raj00/my-jarvis | MIT | Referencia visual/voice assistant; no codigo ni providers. |
| `chevgan/react-ai-voice-visualizer` | https://github.com/chevgan/react-ai-voice-visualizer | MIT visible | Patron conceptual de estados `idle/listening/thinking/speaking`; no dependencia instalada. |

## Codigo copiado/adaptado/reimplementado

- Codigo copiado: ninguno.
- No se copio runtime externo.
- Codigo adaptado: ninguno de repos externos.
- Reimplementado: contracts de providers, estado runtime, mapping visual y cola/cancel TTS, escritos sobre los componentes existentes del repo.

## Seguridad revisada

- `raw_audio_sent_to_backend=false`.
- `transcript_persistence=false`.
- `voice_approval_enabled=false`.
- `wake_phrase_can_approve=false`.
- `wake_phrase_can_execute=false`.
- `hermes_dispatch_allowed=false`.
- No `/execute`.
- No Hermes directo desde frontend.
- No auto `getUserMedia` en Local Voice Loop.
- No providers externos.
- No modelos descargados.
- No dependencias nuevas.
- No dinero, deploy, email, credenciales ni secretos.

## Siguiente PR recomendada

PR #164 recomendado: Local Voice QA + Browser Compatibility Matrix.

Objetivo:

- Probar Chrome/Edge/Safari/Firefox para STT/TTS real de navegador.
- Medir errores reales `not-allowed`, `service-not-allowed`, `no-speech`.
- Mejorar copy de fallback por navegador.
- Mantener todo manual/local y sin providers STT/TTS locales pesados.

Despues de esa matriz, una PR separada puede proponer Piper local experimental disabled-by-default con modelo path explicito, licencia revisada y sin descarga automatica.
