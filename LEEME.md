# Dashboard local de saturación simulada

Conserva los rangos originales de capacidad (50–300 req/s), tráfico legítimo (10–100 req/s), tráfico adicional (0–500 req/s) y mitigación del 80%. Incluye gráficos locales sin dependencias externas, actualizados cada segundo activo, historial de 60 segundos, contadores, pausa y reinicio.

## Ejecutar en Windows PowerShell

Si el simulador anterior sigue ejecutándose, detenlo con **Ctrl+C** en su terminal. Luego:

```powershell
Set-Location 'C:\Lab-DDoS'
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install Flask
.\.venv\Scripts\python.exe .\simulador.py
```

Si ya existe `.venv`, puedes reutilizarla y omitir su creación. No es necesario activar el entorno ni cambiar la política de ejecución de PowerShell. Si `py` no está disponible pero tienes Python instalado en PATH, usa `python -m venv .venv`.

Abre **http://127.0.0.1:5000** en tu navegador. Para detener el servidor usa **Ctrl+C**. Si el puerto está ocupado, detén la instancia anterior antes de volver a ejecutar.

## Ejercicio guiado

1. Capacidad 100, legítimo 30 y adicional 0: demanda 30 req/s, relación demanda/capacidad 30%, legítimas atendidas 100%.
2. Sube el adicional a 200: demanda 230 req/s, relación 230%, atendidas totales 100 req/s y legítimas atendidas aproximadamente 43,5%.
3. Activa mitigación: se filtran 160 req/s adicionales, quedan 40 adicionales y 30 legítimas. Demanda 70 req/s, relación 70%, legítimas atendidas 100%.
4. Reinicia los contadores para comparar escenarios. Los controles conservan sus valores. Pausar detiene los contadores y el historial; puedes ajustar el próximo escenario durante la pausa.

## Qué significan los datos

- **Recibidas**: suma acumulada de legítimas y adicionales antes del filtro.
- **Filtradas**: adicionales retiradas por la mitigación idealizada.
- **Atendidas**: demanda posterior al filtro limitada por la capacidad.
- **No atendidas**: exceso de demanda posterior al filtro; se considera descartado, sin colas ni reintentos.
- Se conserva la relación: recibidas = atendidas + filtradas + no atendidas. Los valores pueden ser fraccionarios porque representan tasas y estimaciones.
- **Demanda/capacidad** puede superar 100%; la capacidad ocupada se limita al 100%.
- **Legítimas atendidas** supone un reparto proporcional del servicio entre tráfico legítimo y adicional. No es una medición de disponibilidad real ni un SLA.
- Precaución desde 80%; sobrecarga por encima de 100%.

El reloj avanza un segundo por actualización activa. Una pestaña oculta pausa el avance y no acumula tiempo en segundo plano. Los temporizadores pueden retrasarse si el navegador está ocupado: no es un reloj de medición real. Cada pestaña tiene su propia simulación; recargar borra el historial y los contadores.

## Alcance y seguridad del laboratorio

Todos los gráficos y contadores se calculan en el navegador. No se envían solicitudes de ataque, no hay sondeo periódico, no se usan CDN y no se mide CPU, memoria, red o tráfico HTTP real. Las solicitudes normales para abrir la página no se cuentan como tráfico simulado. Flask escucha exclusivamente en `127.0.0.1`, con depuración y recarga automática desactivadas. Ejecuta el archivo directamente como se indica arriba para conservar esta configuración.

Este modelo sirve para explorar capacidad y filtrado, no para evaluar defensas DDoS reales. La mitigación supone que identifica perfectamente el tráfico adicional sin bloquear usuarios legítimos.
