from flask import Flask, render_template_string

app = Flask(__name__)

HTML = r"""
<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Laboratorio DDoS · Vivero Florida</title>
<style>
:root{color-scheme:dark;font-family:system-ui,Arial,sans-serif;background:#0d1625;color:#edf3fc}
*{box-sizing:border-box}body{margin:0;padding:24px}main{max-width:1120px;margin:auto}
h1{margin:12px 0;font-size:clamp(24px,4vw,36px)}h2{font-size:18px;margin-top:0}
p{line-height:1.6;color:#bdcbe0}.badge{color:#7ee0cb;font-weight:700;font-size:13px}
.grid{display:grid;grid-template-columns:320px 1fr;gap:18px}.panel,.metric{background:#18263b;border:1px solid #2c405c;border-radius:14px;padding:20px}
label{display:block;margin:18px 0 8px;line-height:1.5}input[type=range]{width:100%;accent-color:#67c7ff}input[type=checkbox]{accent-color:#67c7ff}
.metrics{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-bottom:16px}.metric{padding:14px}.metric span{display:block;color:#bdcbe0;font-size:13px}.metric strong{display:block;font-size:25px;margin-top:7px;font-variant-numeric:tabular-nums}
.bar{height:14px;background:#34455f;border-radius:8px;overflow:hidden;margin:14px 0}.fill{height:100%;background:#63d6ad;transition:width .2s}
.alert{padding:12px;border-radius:8px;background:#193e35;line-height:1.5}.alert.warn{background:#594315}.alert.over{background:#642a35}
.chart{margin-top:18px}canvas{display:block;width:100%;height:220px}.legend{display:flex;flex-wrap:wrap;gap:14px;font-size:12px;color:#c7d3e7}.legend span:before{content:'●';color:var(--color);margin-right:5px}
button{background:#294460;color:white;border:1px solid #517193;padding:10px 14px;border-radius:8px;cursor:pointer;margin:12px 8px 0 0}button:focus-visible,input:focus-visible{outline:3px solid #67c7ff;outline-offset:3px}
.small{font-size:13px}.count{font-variant-numeric:tabular-nums}.footer{margin-top:20px}.muted{color:#bdcbe0}
@media(max-width:850px){.grid{grid-template-columns:1fr}.metrics{grid-template-columns:repeat(2,1fr)}body{padding:14px}}
</style>
</head>
<body><main>
<div class="badge">LABORATORIO LOCAL · TODOS LOS DATOS SON SIMULADOS</div>
<h1>Monitoreo de saturación DDoS</h1>
<p>Vivero Florida · Ajusta la demanda y observa cómo cambia el servicio. El navegador calcula los datos sin generar tráfico de ataque.</p>
<div class="grid">
<section class="panel" aria-label="Controles de simulación">
<h2>Configura el escenario</h2>
<label for="capacidad">Capacidad del servidor: <b id="c">100</b> req/s</label>
<input id="capacidad" type="range" min="50" max="300" value="100">
<label for="legitimo">Tráfico legítimo: <b id="l">30</b> req/s</label>
<input id="legitimo" type="range" min="10" max="100" value="30">
<label for="adicional">Tráfico adicional simulado: <b id="a">0</b> req/s</label>
<input id="adicional" type="range" min="0" max="500" value="0">
<label for="mitigacion"><input id="mitigacion" type="checkbox"> Activar mitigación simulada (filtrar el 80% del tráfico adicional)</label>
<p class="small">La mitigación conserva todo el tráfico legítimo en este modelo idealizado.</p>
<button id="pausa" type="button">Pausar</button><button id="reiniciar" type="button">Reiniciar contadores</button>
<p class="small" id="reloj">Tiempo simulado: 0 s</p>
<p class="small">Un segundo activo equivale a un segundo simulado. Cambiar de pestaña pausa el avance; los controles se mantienen.</p>
</section>
<section aria-label="Métricas simuladas">
<div class="metrics">
<div class="metric"><span>Demanda tras el filtro</span><strong id="demanda">0</strong><span>req/s simuladas</span></div>
<div class="metric"><span>Demanda / capacidad</span><strong id="uso">0%</strong><span>Puede superar el 100%</span></div>
<div class="metric"><span>Legítimas atendidas</span><strong id="disponibilidad">100%</strong><span>Estimación del modelo</span></div>
<div class="metric"><span>Solicitudes recibidas</span><strong id="recibidas">0</strong><span>Acumuladas antes del filtro</span></div>
<div class="metric"><span>Solicitudes atendidas</span><strong id="atendidas">0</strong><span>Acumuladas tras el filtro</span></div>
<div class="metric"><span>Filtradas / no atendidas</span><strong id="descartadas">0 / 0</strong><span>Acumuladas · causas separadas</span></div>
</div>
<div class="panel">
<h2>Estado de capacidad</h2>
<div class="bar"><div class="fill" id="barra"></div></div>
<div id="estado" class="alert" role="status" aria-live="polite"></div>
<p id="detalle" class="small"></p>
</div>
</section>
</div>
<section class="panel chart">
<h2>Tráfico simulado · últimos 60 segundos activos</h2>
<div class="legend"><span style="--color:#67c7ff">Legítimo</span><span style="--color:#f7b76b">Adicional tras filtro</span><span style="--color:#e898ee">Demanda total</span><span style="--color:#63d6ad">Capacidad</span></div>
<canvas id="trafico" role="img" aria-label="Historial de tráfico simulado en solicitudes por segundo"></canvas>
</section>
<section class="panel chart">
<h2>Saturación y servicio · últimos 60 segundos activos</h2>
<div class="legend"><span style="--color:#f7b76b">Demanda / capacidad (%)</span><span style="--color:#67c7ff">Legítimas atendidas (%)</span><span style="--color:#63d6ad">Umbral del 100%</span></div>
<canvas id="servicio" role="img" aria-label="Historial del porcentaje de demanda y solicitudes legítimas atendidas"></canvas>
</section>
<section class="panel footer"><h2>Cómo interpretar el ejercicio</h2>
<p>Una demanda del 150% significa que se solicitan 1,5 veces los recursos disponibles; la capacidad ocupada se limita al 100%. Cuando hay sobrecarga, el modelo reparte las solicitudes atendidas proporcionalmente entre tráfico legítimo y adicional. Las solicitudes no atendidas se descartan; no se modelan colas ni reintentos.</p>
<p class="small">Todos los valores, alertas y contadores son simulados y pertenecen a esta pestaña. No representan mediciones de CPU, memoria, red, latencia o solicitudes HTTP reales. Flask solo entrega esta página en 127.0.0.1; no hay sondeos periódicos, llamadas a servicios externos ni envío de tráfico. Recargar la página reinicia el ejercicio.</p>
</section>
</main>
<script>
'use strict';
const el = id => document.getElementById(id);
const controls = ['capacidad','legitimo','adicional','mitigacion'];
const fmt = n => n.toLocaleString('es-CL',{maximumFractionDigits:1});
let seconds=0, paused=false, history=[], totals={received:0,served:0,filtered:0,lost:0};
function model(c,l,a,mitigation){
 const filtered=mitigation?a*0.8:0, extra=a-filtered, demand=l+extra;
 const served=Math.min(c,demand), lost=Math.max(0,demand-c);
 return {c,l,extra,demand,served,lost,filtered,received:l+a,
 usage:demand/c*100,availability:served/demand*100};
}
function current(){return model(+el('capacidad').value,+el('legitimo').value,+el('adicional').value,el('mitigacion').checked);}
function render(){
 const m=current();
 el('c').textContent=m.c;el('l').textContent=m.l;el('a').textContent=el('adicional').value;
 el('demanda').textContent=fmt(m.demand);el('uso').textContent=fmt(m.usage)+'%';
 el('disponibilidad').textContent=fmt(m.availability)+'%';
 el('recibidas').textContent=fmt(totals.received);el('atendidas').textContent=fmt(totals.served);
 el('descartadas').textContent=fmt(totals.filtered)+' / '+fmt(totals.lost);
 el('barra').style.width=Math.min(m.usage,100)+'%';
 const over=m.usage>100, warn=m.usage>=80&&!over;
 el('barra').style.background=over?'#ff8090':warn?'#f7b76b':'#63d6ad';
 el('estado').className='alert'+(over?' over':warn?' warn':'');
 el('estado').textContent=over?'ALERTA: demanda superior a la capacidad.':warn?'PRECAUCIÓN: queda poco margen de capacidad.':'ESTADO: capacidad suficiente.';
 el('detalle').textContent='Capacidad ocupada: '+fmt(Math.min(m.usage,100))+'%. Atendidas: '+fmt(m.served)+' req/s. No atendidas por sobrecarga: '+fmt(m.lost)+' req/s. Filtradas: '+fmt(m.filtered)+' req/s. Todo simulado.';
 el('reloj').textContent='Tiempo simulado: '+seconds+' s'+(paused?' · Pausado':document.hidden?' · Pestaña inactiva':' · En ejecución');
}
function chart(id,series,minimum,unit){
 const canvas=el(id), rect=canvas.getBoundingClientRect(), ratio=window.devicePixelRatio||1;
 canvas.width=Math.round(rect.width*ratio);canvas.height=Math.round(rect.height*ratio);
 const ctx=canvas.getContext('2d');ctx.scale(ratio,ratio);
 const w=rect.width,h=rect.height,left=54,right=16,top=18,bottom=32,pw=w-left-right,ph=h-top-bottom;
 let max=minimum;for(const row of history)for(const s of series)max=Math.max(max,s.value(row));
 max=Math.ceil(max/50)*50;
 ctx.font='11px system-ui';ctx.lineWidth=1;
 for(let i=0;i<=4;i++){const y=top+ph-i*ph/4;ctx.strokeStyle='#34455f';ctx.beginPath();ctx.moveTo(left,y);ctx.lineTo(w-right,y);ctx.stroke();ctx.fillStyle='#bdcbe0';ctx.fillText(Math.round(max*i/4)+unit,4,y+4);}
 const end=seconds,start=Math.max(0,end-60),range=Math.max(60,end-start);
 ctx.fillText(start+' s',left,h-8);ctx.fillText(end+' s',w-right-38,h-8);
 for(const s of series){ctx.strokeStyle=s.color;ctx.lineWidth=2;ctx.setLineDash(s.dash||[]);ctx.beginPath();
 history.forEach((row,i)=>{const x=left+(row.t-start)/range*pw,y=top+ph-s.value(row)/max*ph;i?ctx.lineTo(x,y):ctx.moveTo(x,y);});ctx.stroke();
 if(history.length===1){const row=history[0];ctx.fillStyle=s.color;ctx.beginPath();ctx.arc(left,top+ph-s.value(row)/max*ph,3,0,Math.PI*2);ctx.fill();}}
 ctx.setLineDash([]);
}
function draw(){
 chart('trafico',[{color:'#67c7ff',value:m=>m.l},{color:'#f7b76b',value:m=>m.extra},{color:'#e898ee',value:m=>m.demand},{color:'#63d6ad',value:m=>m.c,dash:[5,4]}],100,'');
 chart('servicio',[{color:'#f7b76b',value:m=>m.usage},{color:'#67c7ff',value:m=>m.availability},{color:'#63d6ad',value:()=>100,dash:[5,4]}],150,'%');
}
function tick(){
 if(paused||document.hidden)return;
 const m=current();seconds++;
 totals.received+=m.received;totals.served+=m.served;totals.filtered+=m.filtered;totals.lost+=m.lost;
 history.push({...m,t:seconds});history=history.filter(row=>row.t>=seconds-60);
 render();draw();
}
controls.forEach(id=>el(id).addEventListener('input',render));
el('pausa').addEventListener('click',()=>{paused=!paused;el('pausa').textContent=paused?'Continuar':'Pausar';render();});
el('reiniciar').addEventListener('click',()=>{seconds=0;totals={received:0,served:0,filtered:0,lost:0};history=[{...current(),t:0}];render();draw();});
window.addEventListener('resize',draw);document.addEventListener('visibilitychange',render);
history=[{...current(),t:0}];render();draw();setInterval(tick,1000);
</script>
</body></html>
"""


@app.route("/")
def inicio():
    return render_template_string(HTML)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False, use_reloader=False)
