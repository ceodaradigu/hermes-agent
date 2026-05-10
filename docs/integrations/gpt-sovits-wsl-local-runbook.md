# GPT-SoVITS local WSL runbook para JARVIS

## Objetivo

Documentar el procedimiento local para instalar, arrancar y probar GPT-SoVITS como sidecar de voz de JARVIS en WSL/Ubuntu.

Esta guía es para uso local privado de David.

No convierte GPT-SoVITS en dependencia obligatoria de JARVIS.
No cambia el provider mock por defecto.
No publica audio.
No sube modelos ni audios al repo.

## Arquitectura local

JARVIS corre como API local en:

http://127.0.0.1:8000

GPT-SoVITS corre como sidecar local en:

http://127.0.0.1:9880

Flujo:

```text
JARVIS /voice/tts
→ VoiceAdapter
→ GPTSoVITSAdapter
→ GPT-SoVITS /tts
→ audio_bytes
→ save_audio opcional
→ .jarvis/voice_outputs
```

## Reglas importantes

- Instalar GPT-SoVITS dentro de WSL/Linux, por ejemplo:
  `~/sidecars/GPT-SoVITS`
- Evitar instalar GPT-SoVITS dentro de `/mnt/c` porque puede dar errores `chmod`/`fchmod`.
- Mantener JARVIS y GPT-SoVITS separados.
- No versionar audios generados.
- No versionar modelos pesados.
- Usar solo voces autorizadas.
- No usar voces de terceros sin consentimiento.

## Requisitos previos

- WSL/Ubuntu funcionando.
- GPU NVIDIA accesible desde WSL.
- `nvidia-smi` funcionando fuera de Codex sandbox.
- Miniconda instalado.
- Repo JARVIS clonado.
- GPT-SoVITS clonado en `~/sidecars/GPT-SoVITS`.
- Archivo de voz de referencia autorizado.

## Comprobar GPU

```bash
nvidia-smi
```

La GPU validada localmente fue:

```text
NVIDIA GeForce RTX 2070 with Max-Q Design
```

## Instalar GPT-SoVITS en WSL

Trabajar dentro del filesystem Linux de WSL:

```bash
mkdir -p ~/sidecars
cd ~/sidecars
git clone https://github.com/RVC-Boss/GPT-SoVITS.git
cd GPT-SoVITS
```

No clonar ni instalar GPT-SoVITS dentro de `/mnt/c`.

Crear o activar el entorno conda usado para el sidecar:

```bash
conda activate GPTSoVits
python --version
```

La versión validada fue Python 3.10.x.

Ejecutar la instalación base:

```bash
bash install.sh --device CU128 --source HF
```

## Fix de PyTorch/Torchaudio para CUDA 12.8

Durante la instalación se detectó que `torch 2.11.0+cu128` / `torchaudio 2.11.0` pedía `libcudart.so.13`.

El fix validado fue instalar PyTorch 2.7.0 con CUDA 12.8:

```bash
pip uninstall -y torch torchaudio torchvision torchcodec
pip install --index-url https://download.pytorch.org/whl/cu128 torch==2.7.0 torchaudio==2.7.0 torchvision==0.22.0
```

Comprobar el resultado:

```bash
python - <<'PY'
import torch
import torchaudio

print("torch", torch.__version__)
print("torchaudio", torchaudio.__version__)
print("torch cuda", torch.version.cuda)
print("cuda available", torch.cuda.is_available())
if torch.cuda.is_available():
    print("gpu", torch.cuda.get_device_name(0))
PY
```

Resultado validado:

```text
torch 2.7.0+cu128
torchaudio 2.7.0+cu128
torch cuda 12.8
cuda available True
gpu NVIDIA GeForce RTX 2070 with Max-Q Design
```

## Arrancar GPT-SoVITS API

Desde WSL:

```bash
cd ~/sidecars/GPT-SoVITS
conda activate GPTSoVits
python api_v2.py -a 127.0.0.1 -p 9880
```

Comprobar que la documentación local responde:

```text
http://127.0.0.1:9880/docs
```

## Configurar JARVIS para usar el sidecar

Desde el repo de JARVIS:

```bash
cd /mnt/c/Users/diazd/Desktop/JARVIS/hermes-agent
source venv/bin/activate
```

Configurar las variables locales necesarias para apuntar al sidecar GPT-SoVITS.

Ejemplo:

```bash
export JARVIS_VOICE_PROVIDER=gpt_sovits
export JARVIS_GPT_SOVITS_BASE_URL=http://127.0.0.1:9880
export JARVIS_GPT_SOVITS_PROMPT_LANG=en
```

GPT-SoVITS v2 no acepta `text_lang="es"` en la ruta validada. Para la prueba real se usó:

```text
language="en"
JARVIS_GPT_SOVITS_PROMPT_LANG=en
```

## Probar TTS desde JARVIS

Con JARVIS arrancado en:

```text
http://127.0.0.1:8000
```

Lanzar una petición local de TTS guardando el audio:

```bash
curl -X POST http://127.0.0.1:8000/voice/tts \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Hello David. JARVIS voice sidecar is online.",
    "language": "en",
    "save_audio": true
  }'
```

Si GPT-SoVITS está activo y la configuración local es correcta, JARVIS genera un WAV real y, con `save_audio=true`, lo guarda bajo:

```text
.jarvis/voice_outputs
```

## Resultado esperado

- GPT-SoVITS responde en `http://127.0.0.1:9880/docs`.
- JARVIS responde en `http://127.0.0.1:8000`.
- `/voice/tts` devuelve audio generado por GPT-SoVITS cuando el provider local está activado.
- Con `save_audio=true`, aparece un archivo `.wav` bajo `.jarvis/voice_outputs`.
- Si GPT-SoVITS está apagado, JARVIS devuelve `503` para el provider GPT-SoVITS.

## Notas de seguridad y privacidad

- Usar solo archivos de voz de referencia autorizados.
- No subir audios generados al repositorio.
- No subir modelos, checkpoints ni pesos pesados al repositorio.
- No exponer GPT-SoVITS fuera de `127.0.0.1` salvo que haya una razón explícita y controlada.
- Mantener el uso como sidecar local privado.

## Troubleshooting

### Error relacionado con `libcudart.so.13`

Reinstalar PyTorch/Torchaudio con las versiones validadas para CUDA 12.8:

```bash
pip uninstall -y torch torchaudio torchvision torchcodec
pip install --index-url https://download.pytorch.org/whl/cu128 torch==2.7.0 torchaudio==2.7.0 torchvision==0.22.0
```

### Errores `chmod` o `fchmod`

Verificar que GPT-SoVITS esté instalado dentro del filesystem Linux de WSL:

```text
~/sidecars/GPT-SoVITS
```

Evitar rutas bajo:

```text
/mnt/c
```

### `/voice/tts` devuelve 503

Comprobar que GPT-SoVITS esté arrancado:

```bash
cd ~/sidecars/GPT-SoVITS
conda activate GPTSoVits
python api_v2.py -a 127.0.0.1 -p 9880
```

Después abrir:

```text
http://127.0.0.1:9880/docs
```

### Idioma español rechazado por GPT-SoVITS v2

En la ruta validada, GPT-SoVITS v2 no aceptó `text_lang="es"`.

Usar inglés para la prueba local:

```text
language="en"
JARVIS_GPT_SOVITS_PROMPT_LANG=en
```
