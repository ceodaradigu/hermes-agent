# Errores Conocidos

## Aprendidos en PRs recientes

- Duplicar Hermes dentro de JARVIS: crear browser/file/terminal operators en
  `jarvis/` cuando Hermes ya tiene tools reales.
- Cerrar una PR solo porque pasan tests, aunque no haya validacion manual de la
  capacidad prometida.
- Llamar `done` a readiness, preview, mock, status o contrato.
- Asumir que browser/file operator ya funciona desde JARVIS como flujo completo
  hacia Hermes.
- Usar OpenRouter como excusa para acciones basicas que deberian ser
  deterministas y gobernadas.
- Crear operadores Playwright dentro de JARVIS sin comprobar primero Hermes
  browser tools.
- Confundir `webbrowser.open` con navegador controlado.
- Confundir wake phrase con permiso o approval.
- Confundir memoria con autorizacion.
- Exponer shell/raw command desde UI o mobile.

## Regla practica

Si Hermes ya ejecuta una clase de accion, JARVIS debe gobernarla y llamarla de
forma allowlisted. Si la integracion no existe, marcar `READINESS` o `PARCIAL`;
no construir una copia paralela sin decision explicita.
