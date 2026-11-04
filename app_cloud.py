import os
from datetime import datetime, timedelta, timezone
import boto3
from botocore.exceptions import BotoCoreError, ClientError
from flask import Flask, jsonify, render_template_string

app = Flask(__name__)

# Reemplaza 'i-0123456789abcdef0' por el Instance ID real de tu EC2 en AWS Learner Lab
INSTANCE_ID = os.getenv("AWS_INSTANCE_ID", "i-093c86a2faa0935cd")
AWS_REGION = os.getenv("AWS_DEFAULT_REGION", "us-east-1")

HTML_HYBRID = r"""
<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<title>Dashboard Híbrido · Simulación DDoS & AWS Cloud Monitoring</title>
<style>
:root{color-scheme:dark;font-family:system-ui,sans-serif;background:#0d1625;color:#edf3fc}
body{margin:0;padding:24px}main{max-width:1120px;margin:auto}
.card,.panel{background:#18263b;border:1px solid #2c405c;border-radius:14px;padding:20px;margin-bottom:18px}
.grid{display:grid;grid-template-columns:repeat(3,1fr);gap:14px}
.metric span{display:block;color:#bdcbe0;font-size:13px}.metric strong{display:block;font-size:24px;margin-top:6px}
.mode-selector{background:#1d2f47;padding:16px;border-radius:10px;margin-bottom:20px;border:1px solid #385375}
select{background:#0d1625;color:#fff;border:1px solid #517193;padding:8px 12px;border-radius:6px;font-size:15px}
.status-ok{color:#63d6ad}.status-warn{color:#f7b76b}.status-err{color:#ff8090}
</style>
</head>
<body><main>
<h1>Monitoreo de Infraestructura y Saturación</h1>
<div class="mode-selector">
    <label for="modeSelect"><strong>Seleccionar Modo de Operación: </strong></label>
    <select id="modeSelect" onchange="toggleMode()">
        <option value="sim">Modo 1: Simulación DDoS (Algoritmo Browser Local)</option>
        <option value="cloud">Modo 2: Monitoreo Cloud Real (AWS CloudWatch SDK)</option>
    </select>
</div>

<!-- SECCIÓN MODULO CLOUD AWS -->
<div id="cloudSection" style="display:none;">
    <div class="card">
        <h2>Métricas Reales de AWS EC2 (CloudWatch)</h2>
        <p><strong>Proveedor:</strong> AWS CloudWatch | <strong>Región:</strong> <span id="cwRegion">-</span></p>
        <p><strong>Recurso (EC2 Instance ID):</strong> <span id="cwResource">-</span></p>
        <p><strong>Última Muestra Registrada:</strong> <span id="cwTimestamp">-</span></p>

        <div class="grid" style="margin-top:16px;">
            <div class="card metric"><span>Métrica 1: Uso de CPU</span><strong id="cpuVal">- %</strong><span>Agregación: Average (60s)</span></div>
            <div class="card metric"><span>Métrica 2: Tráfico Red Entrante</span><strong id="netVal">- Bytes</strong><span>Agregación: Average (60s)</span></div>
            <div class="card metric"><span>Métrica 3: Lectura en Disco</span><strong id="diskVal">- Bytes</strong><span>Agregación: Average (60s)</span></div>
        </div>

        <div id="cwStatus" style="margin-top:12px;"></div>
    </div>
</div>

<!-- SECCIÓN MODULO SIMULADOR -->
<div id="simSection">
    <div class="card">
        <p style="color:#7ee0cb;"><strong>MODO SIMULADOR ACTIVO:</strong> Los controles cambian el modelo matemático local sin modificar recursos Cloud real.</p>
        <p>Para usar la simulación completa abre la vista <code>/</code> original o alterna a Modo Cloud arriba.</p>
    </div>
</div>
</main>

<script>
function toggleMode(){
    const mode = document.getElementById('modeSelect').value;
    document.getElementById('simSection').style.display = (mode === 'sim') ? 'block' : 'none';
    document.getElementById('cloudSection').style.display = (mode === 'cloud') ? 'block' : 'none';
    if(mode === 'cloud') fetchMetrics();
}

async function fetchMetrics(){
    const statusDiv = document.getElementById('cwStatus');
    statusDiv.innerHTML = "<p class='status-warn'>Consultando SDK boto3 en servidor Python...</p>";
    try {
        const res = await fetch('/api/cloud-metrics');
        const data = await res.json();
        
        if (data.status === 'error') {
            statusDiv.innerHTML = `<p class='status-err'><strong>Error de Consulta:</strong> ${data.message}</p>`;
            return;
        }
        
        if (data.status === 'no_data') {
            statusDiv.innerHTML = `<p class='status-warn'><strong>Sin datos:</strong> No existen muestras registradas en los últimos 10 minutos para la instancia.</p>`;
            return;
        }

        document.getElementById('cwRegion').textContent = data.region;
        document.getElementById('cwResource').textContent = data.resource;
        document.getElementById('cwTimestamp').textContent = data.timestamp;
        
        document.getElementById('cpuVal').textContent = data.metrics.CPUUtilization + ' %';
        document.getElementById('netVal').textContent = data.metrics.NetworkIn + ' Bytes';
        document.getElementById('diskVal').textContent = data.metrics.DiskReadBytes + ' Bytes';

        if(data.outdated){
            statusDiv.innerHTML = "<p class='status-warn'>⚠️ <strong>Advertencia:</strong> Los datos mostrados corresponden a una muestra desactualizada (> 5 minutos).</p>";
        } else {
            statusDiv.innerHTML = "<p class='status-ok'>● Muestras AWS sincronizadas correctamente.</p>";
        }
    } catch(err) {
        statusDiv.innerHTML = `<p class='status-err'><strong>Error de red local:</strong> ${err.message}</p>`;
    }
}

// Intervalo de consulta a la API local cada 60 segundos
setInterval(() => {
    if(document.getElementById('modeSelect').value === 'cloud') fetchMetrics();
}, 60000);
</script>
</body>
</html>
"""


def query_cloudwatch(cw, metric_name):
    end_time = datetime.now(timezone.utc)
    start_time = end_time - timedelta(minutes=10)
    try:
        response = cw.get_metric_data(
            MetricDataQueries=[
                {
                    "Id": "m1",
                    "MetricStat": {
                        "Metric": {
                            "Namespace": "AWS/EC2",
                            "MetricName": metric_name,
                            "Dimensions": [
                                {"Name": "InstanceId", "Value": INSTANCE_ID}
                            ],
                        },
                        "Period": 60,
                        "Stat": "Average",
                    },
                }
            ],
            StartTime=start_time,
            EndTime=end_time,
        )
        results = response["MetricDataResults"][0]["Values"]
        timestamps = response["MetricDataResults"][0]["Timestamps"]
        if not results:
            return None, None
        return round(results[0], 2), timestamps[0]
    except Exception as e:
        print(f"Error consultando {metric_name}: {e}")
        return None, None


@app.route("/")
def index():
    return render_template_string(HTML_HYBRID)


@app.route("/api/cloud-metrics")
def cloud_metrics():
    try:
        # boto3 utiliza automáticamente las variables de entorno de AWS Learner Lab
        cw = boto3.client("cloudwatch", region_name=AWS_REGION)

        cpu, ts_cpu = query_cloudwatch(cw, "CPUUtilization")
        net, ts_net = query_cloudwatch(cw, "NetworkIn")
        disk, ts_disk = query_cloudwatch(cw, "DiskReadBytes")

        if cpu is None:
            return jsonify(
                {
                    "status": "no_data",
                    "message": "Instancia EC2 sin métricas publicadas en el intervalo.",
                }
            )

        now = datetime.now(timezone.utc)
        outdated = (now - ts_cpu).total_seconds() > 300

        return jsonify(
            {
                "status": "success",
                "provider": "AWS CloudWatch",
                "resource": INSTANCE_ID,
                "region": AWS_REGION,
                "timestamp": ts_cpu.strftime("%Y-%m-%d %H:%M:%S UTC"),
                "outdated": outdated,
                "metrics": {
                    "CPUUtilization": cpu,
                    "NetworkIn": net if net is not None else 0,
                    "DiskReadBytes": disk if disk is not None else 0,
                },
            }
        )
    except (BotoCoreError, ClientError) as e:
        return (
            jsonify(
                {
                    "status": "error",
                    "message": f"Fallo de autenticación/permisos AWS: {str(e)}",
                }
            ),
            500,
        )


if __name__ == "__main__":
    # Flask restringido obligatoriamente a localhost 127.0.0.1
    app.run(host="127.0.0.1", port=5000, debug=False)