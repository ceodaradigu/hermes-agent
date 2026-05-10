# Voice Runtime control CLI

`scripts/local/voice-runtime-control.sh` permite consultar y controlar la Voice Runtime API local sin usar micrófono, wake word, STT ni reproducción de audio.

El script usa `http://127.0.0.1:8000` como URL base por defecto. Puedes cambiarla con `JARVIS_BASE_URL`.

```bash
scripts/local/voice-runtime-control.sh status
JARVIS_BASE_URL=http://127.0.0.1:9000 scripts/local/voice-runtime-control.sh status
```

## Comandos

Consultar estado:

```bash
scripts/local/voice-runtime-control.sh status
```

Arrancar o detener el runtime:

```bash
scripts/local/voice-runtime-control.sh start
scripts/local/voice-runtime-control.sh stop
```

Cambiar modo:

```bash
scripts/local/voice-runtime-control.sh mode awake
scripts/local/voice-runtime-control.sh mode asleep
```

Enviar comandos de control simulados:

```bash
scripts/local/voice-runtime-control.sh control "jarvis silencio"
scripts/local/voice-runtime-control.sh control "jarvis no escuches"
```

Enviar una transcripcion simulada:

```bash
scripts/local/voice-runtime-control.sh transcript "abre el panel de estado"
```

Consultar o limpiar feedback acumulado:

```bash
scripts/local/voice-runtime-control.sh feedback-list
scripts/local/voice-runtime-control.sh feedback-clear
```

## Endpoints

| Comando | Metodo | Endpoint |
| --- | --- | --- |
| `status` | `GET` | `/voice/runtime/status` |
| `start` | `POST` | `/voice/runtime/start` |
| `stop` | `POST` | `/voice/runtime/stop` |
| `mode <mode>` | `POST` | `/voice/runtime/mode` |
| `control <text>` | `POST` | `/voice/runtime/control` |
| `transcript <text>` | `POST` | `/voice/runtime/transcript` |
| `feedback-list` | `GET` | `/voice/runtime/feedback` |
| `feedback-clear` | `DELETE` | `/voice/runtime/feedback` |

El script imprime la respuesta JSON que devuelve la API. Si no recibe comando, muestra el uso y sale con codigo `2`.
