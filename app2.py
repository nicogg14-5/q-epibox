from flask import Flask, render_template_string, request, jsonify, redirect, url_for, session
import time
import random

app = Flask(__name__)
app.secret_key = "clave_secreta_quepibox_segura"

MI_IP_LOCAL = "192.168.0.6"

# 1. Banco de Casilleros de ENVÍO (4 casillas: 1, 2, 3, 4)
casilleros_envio = {
    1: {"libre": True, "order_id": None},
    2: {"libre": True, "order_id": None},
    3: {"libre": True, "order_id": None},
    4: {"libre": True, "order_id": None}
}

# 2. Banco de Casilleros de RECOJO (4 casillas: 5, 6, 7, 8)
casilleros_recojo = {
    5: {"libre": True, "order_id": None},
    6: {"libre": True, "order_id": None},
    7: {"libre": True, "order_id": None},
    8: {"libre": True, "order_id": None}
}

encomiendas_db = {}

# ----------------- PLANTILLAS HTML -----------------

HTML_INICIO = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <!-- AUTO-REFRESCO CADA 4 SEGUNDOS EN LA PANTALLA PRINCIPAL -->
    <meta http-equiv="refresh" content="4">
    <title>Q'epiBox - Estación de Encomiendas</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #eef2f5; text-align: center; margin-top: 30px; }
        .card { background: white; padding: 35px; border-radius: 16px; display: inline-block; box-shadow: 0px 8px 24px rgba(0,0,0,0.12); max-width: 480px; width: 90%; }
        h1 { color: #1a237e; margin-bottom: 5px; font-size: 30px; }
        p.subtitle { color: #666; margin-bottom: 20px; font-size: 14px; }
        .status-banner { background: #e8f5e9; color: #2e7d32; padding: 10px; border-radius: 8px; font-weight: bold; font-size: 14px; margin-bottom: 20px; border: 1px solid #c8e6c9; }
        .status-banner.full { background: #ffebee; color: #c62828; border-color: #ffcdd2; }
        .btn { display: block; width: 100%; padding: 16px; margin: 12px 0; background-color: #1a237e; color: white; text-decoration: none; font-size: 18px; font-weight: bold; border-radius: 10px; border: none; cursor: pointer; box-sizing: border-box; transition: 0.2s; }
        .btn:hover { background-color: #283593; transform: translateY(-2px); }
        .btn-recojer { background-color: #2e7d32; }
        .btn-recojer:hover { background-color: #1b5e20; }
        .footer-info { font-size: 12px; color: #888; margin-top: 25px; }
    </style>
</head>
<body>
    <div class="card">
        <h1>📦 Q’epiBox</h1>
        <p class="subtitle">Estación Automatizada de Encomiendas</p>
        
        <div class="status-banner {% if libres_envio == 0 %}full{% endif %}">
            {% if libres_envio > 0 %}
                🟢 Casillas de Envío Disponibles: {{ libres_envio }} / 4
            {% else %}
                🔴 Casillas de Envío LLENAS (0 / 4 libres)
            {% endif %}
        </div>
        
        <a href="/formulario-envio" class="btn">[ 1 ] ENVIAR ENCOMIENDA</a>
        <a href="/formulario-recojer" class="btn btn-recojer">[ 2 ] RECOGER ENCOMIENDA</a>
        
        <div class="footer-info">U.A.T.F. - Ingeniería Electrónica</div>
    </div>
</body>
</html>
"""

HTML_LOGIN_OPERARIO = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Acceso del Sistema</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #111; color: #eee; text-align: center; margin-top: 80px; }
        .card { background: #222; padding: 35px; border-radius: 16px; display: inline-block; box-shadow: 0px 8px 24px rgba(0,0,0,0.5); max-width: 360px; width: 90%; text-align: left; border: 1px solid #444; }
        h2 { color: #ff9800; text-align: center; margin-top: 0; font-size: 20px; }
        label { font-weight: bold; color: #aaa; display: block; margin-top: 15px; font-size: 13px; }
        input { width: 100%; padding: 12px; margin-top: 6px; background: #333; border: 1px solid #555; color: white; border-radius: 8px; box-sizing: border-box; font-size: 16px; }
        .btn-login { background-color: #ff9800; color: #111; font-size: 16px; font-weight: bold; margin-top: 25px; cursor: pointer; border: none; padding: 14px; border-radius: 8px; width: 100%; }
        .btn-login:hover { background-color: #f57c00; }
        .error-msg { background: #c62828; color: white; padding: 10px; border-radius: 6px; margin-bottom: 15px; font-size: 13px; text-align: center; font-weight: bold; }
        .back-link { display: block; text-align: center; margin-top: 15px; color: #777; text-decoration: none; font-size: 13px; }
    </style>
</head>
<body>
    <div class="card">
        <h2>Terminal Administrativa</h2>
        
        {% if error %}
        <div class="error-msg">{{ error }}</div>
        {% endif %}

        <form action="/operario/login" method="POST">
            <label>Clave de Acceso:</label>
            <input type="password" name="password" placeholder="••••" required autocomplete="current-password">

            <button type="submit" class="btn-login">Acceder al Sistema</button>
        </form>
        <a href="/" class="back-link">Volver a inicio</a>
    </div>
</body>
</html>
"""

HTML_PANEL_OPERARIO = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Q'epiBox - Panel del Operario</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f4f9; padding: 20px; }
        .container { max-width: 1000px; margin: 0 auto; background: white; padding: 30px; border-radius: 12px; box-shadow: 0px 4px 15px rgba(0,0,0,0.1); }
        h2 { color: #d84315; margin-top: 0; }
        table { width: 100%; border-collapse: collapse; margin-top: 15px; font-size: 14px; }
        th, td { border: 1px solid #ddd; padding: 10px; text-align: center; }
        th { background-color: #1a237e; color: white; }
        tr:nth-child(even) { background-color: #f9f9f9; }
        .badge-activo { background: #e8f5e9; color: #2e7d32; padding: 4px 8px; border-radius: 12px; font-weight: bold; }
        .badge-recojo { background: #e3f2fd; color: #1565c0; padding: 4px 8px; border-radius: 12px; font-weight: bold; }
        .badge-retirado { background: #ffebee; color: #c62828; padding: 4px 8px; border-radius: 12px; font-weight: bold; }
        .btn-accion { background: #2e7d32; color: white; padding: 6px 12px; text-decoration: none; border-radius: 4px; font-size: 12px; font-weight: bold; display: inline-block; }
        .btn-accion:hover { background: #1b5e20; }
        .btn-salir { display: inline-block; margin-top: 25px; background: #c62828; color: white; padding: 10px 20px; text-decoration: none; border-radius: 6px; font-weight: bold; }
        .status-container { display: flex; gap: 20px; margin-bottom: 20px; }
        .status-box { flex: 1; background: #eef2f5; padding: 15px; border-radius: 8px; text-align: center; }
        .filter-bar { background: #fffde7; padding: 12px; border-radius: 8px; margin-bottom: 20px; border: 1px solid #fbc02d; display: flex; align-items: center; justify-content: space-between; }
        .filter-bar select { padding: 8px; border-radius: 6px; border: 1px solid #ccc; font-size: 14px; }
        .section-title { color: #1a237e; margin-top: 25px; border-bottom: 2px solid #1a237e; padding-bottom: 5px; }
    </style>
</head>
<body>
    <div class="container">
        <h2>🔑 Panel del Operario (Terminal)</h2>
        <p style="color: #666; font-size: 13px;">Gestión de paquetes salientes y control de casilleros.</p>

        <div class="status-container">
            <div class="status-box">
                <h4 style="margin:0 0 5px 0; color:#1a237e;">Casilleros de ENVÍO (1-4)</h4>
                <span style="font-size:16px; font-weight:bold; color:#2e7d32;">Libres: {{ libres_envio }} / 4</span>
            </div>
            <div class="status-box">
                <h4 style="margin:0 0 5px 0; color:#1a237e;">Casilleros de RECOJO (5-8)</h4>
                <span style="font-size:16px; font-weight:bold; color:#1565c0;">Libres: {{ libres_recojo }} / 4</span>
            </div>
        </div>

        <div class="filter-bar">
            <span>🔍 <b>Filtrar listados por Destino:</b></span>
            <form method="GET" action="/operario/panel">
                <select name="filtro_destino" onchange="this.form.submit()">
                    <option value="TODOS" {% if filtro_actual == 'TODOS' %}selected{% endif %}>-- Todos los Departamentos --</option>
                    <option value="La Paz" {% if filtro_actual == 'La Paz' %}selected{% endif %}>La Paz</option>
                    <option value="Cochabamba" {% if filtro_actual == 'Cochabamba' %}selected{% endif %}>Cochabamba</option>
                    <option value="Santa Cruz" {% if filtro_actual == 'Santa Cruz' %}selected{% endif %}>Santa Cruz</option>
                    <option value="Potosí" {% if filtro_actual == 'Potosí' %}selected{% endif %}>Potosí</option>
                    <option value="Oruro" {% if filtro_actual == 'Oruro' %}selected{% endif %}>Oruro</option>
                    <option value="Chuquisaca" {% if filtro_actual == 'Chuquisaca' %}selected{% endif %}>Chuquisaca (Sucre)</option>
                    <option value="Tarija" {% if filtro_actual == 'Tarija' %}selected{% endif %}>Tarija</option>
                    <option value="Beni" {% if filtro_actual == 'Beni' %}selected{% endif %}>Beni</option>
                    <option value="Pando" {% if filtro_actual == 'Pando' %}selected{% endif %}>Pando</option>
                </select>
            </form>
        </div>

        <h3 class="section-title">📥 Paquetes Pendientes de Mover (En casillas de envío 1-4)</h3>
        <table>
            <tr>
                <th>N° de Guía</th>
                <th>Casilla Envío</th>
                <th>Destino</th>
                <th>C.I. Destinatario</th>
                <th>Acción del Operario</th>
            </tr>
            {% set count_envios = 0 %}
            {% for order_id, d in encomiendas.items() %}
                {% if not d.en_recojo and not d.retirado and d.pagado %}
                    {% if filtro_actual == 'TODOS' or d.destino == filtro_actual %}
                        {% set count_envios = count_envios + 1 %}
                    <tr>
                        <td><b>{{ d.numero_guia }}</b></td>
                        <td><span style="background: #1a237e; color: white; padding: 3px 6px; border-radius: 4px;">Casilla #{{ d.casilla_envio }}</span></td>
                        <td><b style="color: #d84315;">{{ d.destino }}</b></td>
                        <td>{{ d.dni }}</td>
                        <td>
                            <a href="/operario/mover-a-recojo?order_id={{ order_id }}&filtro_destino={{ filtro_actual }}" class="btn-accion">Mover a Casilla de Recojo ➔</a>
                        </td>
                    </tr>
                    {% endif %}
                {% endif %}
            {% endfor %}
            {% if count_envios == 0 %}
            <tr>
                <td colspan="5" style="color: #777; padding: 15px;">No hay paquetes pendientes de mover que coincidan con este filtro.</td>
            </tr>
            {% endif %}
        </table>

        <h3 class="section-title">📤 Paquetes ya ubicados en Casilleros de Recojo (5-8)</h3>
        <table>
            <tr>
                <th>N° de Guía</th>
                <th>Casilla Recojo</th>
                <th>Destino</th>
                <th>C.I. Destinatario</th>
                <th>Estado Actual</th>
            </tr>
            {% set count_recojos = 0 %}
            {% for order_id, d in encomiendas.items() %}
                {% if d.en_recojo %}
                    {% if filtro_actual == 'TODOS' or d.destino == filtro_actual %}
                        {% set count_recojos = count_recojos + 1 %}
                    <tr>
                        <td><b>{{ d.numero_guia }}</b></td>
                        <td><span style="background: #2e7d32; color: white; padding: 3px 6px; border-radius: 4px;">Casilla #{{ d.casilla_recojo }}</span></td>
                        <td><b style="color: #1565c0;">{{ d.destino }}</b></td>
                        <td>{{ d.dni }}</td>
                        <td>
                            {% if d.retirado %}
                                <span class="badge-retirado">Retirado por Cliente</span>
                            {% else %}
                                <span class="badge-recojo">Disponible para Destinatario</span>
                            {% endif %}
                        </td>
                    </tr>
                    {% endif %}
                {% endif %}
            {% endfor %}
            {% if count_recojos == 0 %}
            <tr>
                <td colspan="5" style="color: #777; padding: 15px;">No hay paquetes en casilleros de recojo bajo este filtro.</td>
            </tr>
            {% endif %}
        </table>

        <a href="/operario/logout" class="btn-salir">Cerrar Sesión / Salir</a>
    </div>
</body>
</html>
"""

HTML_ASIGNAR_RECOJO = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Q'epiBox - Asignar Recojo</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #eef2f5; text-align: center; margin-top: 30px; }
        .card { background: white; padding: 35px; border-radius: 16px; display: inline-block; box-shadow: 0px 8px 24px rgba(0,0,0,0.12); max-width: 440px; width: 90%; text-align: left; }
        h2 { color: #1a237e; text-align: center; margin-top: 0; }
        .info-box { background: #e8f5e9; padding: 12px; border-radius: 8px; margin-bottom: 20px; font-size: 14px; color: #2e7d32; font-weight: bold; }
        .error-msg { background: #ffebee; color: #c62828; padding: 12px; border-radius: 8px; margin-bottom: 15px; font-size: 14px; text-align: center; font-weight: bold; }
        label { font-weight: bold; color: #333; display: block; margin-top: 15px; font-size: 14px; }
        select { width: 100%; padding: 12px; margin-top: 6px; border: 1px solid #ccc; border-radius: 8px; box-sizing: border-box; font-size: 16px; }
        .btn-submit { background-color: #2e7d32; color: white; font-size: 18px; font-weight: bold; margin-top: 25px; cursor: pointer; border: none; padding: 14px; border-radius: 8px; width: 100%; }
        .btn-submit:hover { background-color: #1b5e20; }
        .back-link { display: block; text-align: center; margin-top: 15px; color: #666; text-decoration: none; font-size: 14px; }
    </style>
</head>
<body>
    <div class="card">
        <h2>Abastecer Casilla de Recojo</h2>
        
        <div class="info-box">
            Guía: {{ datos.numero_guia }}<br>
            Destino: {{ datos.destino }}
        </div>

        {% if error %}
        <div class="error-msg">{{ error }}</div>
        {% endif %}

        <form action="/operario/guardar-en-recojo" method="POST">
            <input type="hidden" name="order_id" value="{{ order_id }}">
            <input type="hidden" name="filtro_destino" value="{{ filtro_actual }}">
            
            <label>Seleccione una Casilla de Recojo Disponible (5 al 8):</label>
            <select name="casilla_recojo" required>
                {% for num, info in casilleros_recojo.items() %}
                    {% if info.libre %}
                        <option value="{{ num }}">Casilla de Recojo #{{ num }}</option>
                    {% endif %}
                {% endfor %}
            </select>

            <button type="submit" class="btn-submit">Confirmar e Introducir en Casilla ➔</button>
        </form>
        <a href="/operario/panel?filtro_destino={{ filtro_actual }}" class="back-link">← Cancelar y Volver</a>
    </div>
</body>
</html>
"""

HTML_FORMULARIO_ENVIO = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Q'epiBox - Datos del Envío</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #eef2f5; text-align: center; margin-top: 30px; }
        .card { background: white; padding: 30px; border-radius: 16px; display: inline-block; box-shadow: 0px 8px 24px rgba(0,0,0,0.12); max-width: 420px; width: 90%; text-align: left; }
        h2 { color: #1a237e; text-align: center; margin-top: 0; }
        label { font-weight: bold; color: #333; display: block; margin-top: 15px; font-size: 14px; }
        input, select { width: 100%; padding: 12px; margin-top: 6px; border: 1px solid #ccc; border-radius: 8px; box-sizing: border-box; font-size: 16px; }
        .btn-submit { background-color: #2e7d32; color: white; font-size: 18px; font-weight: bold; margin-top: 25px; cursor: pointer; border: none; padding: 14px; border-radius: 8px; width: 100%; }
        .btn-submit:hover { background-color: #1b5e20; }
        .error-box { background: #ffebee; color: #c62828; padding: 15px; border-radius: 8px; margin-bottom: 15px; font-size: 14px; text-align: center; font-weight: bold; }
        .back-link { display: block; text-align: center; margin-top: 15px; color: #666; text-decoration: none; font-size: 14px; }
    </style>
</head>
<body>
    <div class="card">
        <h2>Registro de Envío</h2>
        
        {% if casilleros_libres == 0 %}
        <div class="error-box">
            ❌ ¡CASILLEROS DE ENVÍO LLENOS!<br>
            No hay espacio disponible para depositar nuevos envíos (0 / 4 libres).
        </div>
        <a href="/" class="back-link" style="font-weight: bold; font-size: 16px;">← Volver al Menú Principal</a>
        {% else %}
        <p style="font-size: 13px; color: #2e7d32; font-weight: bold; text-align: center;">Casillas de Envío Libres: {{ casilleros_libres }} de 4</p>
        <form action="/procesar-envio" method="POST">
            <label>DNI / C.I. del Destinatario:</label>
            <input type="text" name="dni_destinatario" placeholder="Ej. 8492019" required autocomplete="off">

            <label>Departamento de Destino:</label>
            <select name="destino" required>
                <option value="La Paz">La Paz</option>
                <option value="Cochabamba">Cochabamba</option>
                <option value="Santa Cruz">Santa Cruz</option>
                <option value="Potosí" selected>Potosí</option>
                <option value="Oruro">Oruro</option>
                <option value="Chuquisaca">Chuquisaca (Sucre)</option>
                <option value="Tarija">Tarija</option>
                <option value="Beni">Beni</option>
                <option value="Pando">Pando</option>
            </select>

            <label>Tamaño del Casillero:</label>
            <select name="tamano" required>
                <option value="5.0 BOB (Pequeño)">Pequeño - 5 BOB</option>
                <option value="10.0 BOB (Mediano)" selected>Mediano - 10 BOB</option>
                <option value="15.0 BOB (Grande)">Grande - 15 BOB</option>
            </select>

            <button type="submit" class="btn-submit">Continuar al Pago QR ➔</button>
        </form>
        <a href="/" class="back-link">← Volver al Menú Principal</a>
        {% endif %}
    </div>
</body>
</html>
"""

HTML_QR_PAGO = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Q'epiBox - Pago QR</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f4f9; text-align: center; margin-top: 20px; }
        .card { background: white; padding: 30px; border-radius: 16px; display: inline-block; box-shadow: 0px 8px 24px rgba(0,0,0,0.12); max-width: 380px; }
        h2 { color: #1a237e; margin-bottom: 5px; }
        .amount { font-size: 26px; color: #2e7d32; font-weight: bold; margin: 10px 0; }
        img { max-width: 230px; height: auto; margin: 10px 0; border: 1px solid #ddd; border-radius: 10px; padding: 8px; }
        .info { color: #555; font-size: 13px; margin: 4px 0; }
        .esperando { color: #e65100; font-weight: bold; margin-top: 15px; animation: blink 1.5s infinite; }
        .timer-box { font-size: 14px; color: #d32f2f; font-weight: bold; margin-top: 10px; background: #ffebee; padding: 8px; border-radius: 6px; }
        @keyframes blink { 0% { opacity: 1; } 50% { opacity: 0.4; } 100% { opacity: 1; } }
    </style>
</head>
<body>
    <div class="card">
        <h2>Escanea para Pagar</h2>
        <div class="amount">{{ precio }}</div>
        
        <img src="https://api.qrserver.com/v1/create-qr-code/?size=250x250&data={{ qr_url }}" alt="QR de Pago">
        
        <p class="info"><b>Casilla de Envío Asignada:</b> #{{ casilla }} | <b>CI:</b> {{ dni }}</p>
        <p class="info"><b>ID de Transacción:</b> {{ order_id }}</p>
        
        <div class="timer-box">⏱️ Tiempo restante para escanear: <span id="timer">05:00</span></div>
        <p class="esperando">⏳ Esperando acción desde el celular...</p>
    </div>

    <script>
        const orderId = "{{ order_id }}";
        let tiempoRestante = 300; 

        const countdown = setInterval(() => {
            tiempoRestante--;
            let mins = Math.floor(tiempoRestante / 60);
            let secs = tiempoRestante % 60;
            document.getElementById("timer").innerText = 
                `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;

            if (tiempoRestante <= 0) {
                clearInterval(countdown);
                alert("⏰ El tiempo para completar el pago ha expirado. Volviendo al inicio.");
                window.location.href = "/";
            }
        }, 1000);

        const verificar = setInterval(async () => {
            try {
                let res = await fetch(`/api/chequear-pago?order_id=${orderId}`);
                let data = await res.json();
                if (data.pagado) {
                    clearInterval(verificar);
                    clearInterval(countdown);
                    window.location.href = `/casillero-asignado?order_id=${orderId}`;
                }
            } catch (e) {
                console.log("Comprobando...");
            }
        }, 1000);
    </script>
</body>
</html>
"""

HTML_MOVIL_PAGO_INTERACTIVO = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Pasarela de Pago Q'epiBox</title>
    <style>
        body { font-family: Arial, sans-serif; background-color: #f4f4f9; text-align: center; margin-top: 40px; padding: 20px; }
        .card { background: white; padding: 30px; border-radius: 16px; display: inline-block; box-shadow: 0px 4px 15px rgba(0,0,0,0.1); max-width: 320px; width: 100%; box-sizing: border-box; }
        h2 { color: #1a237e; margin-top: 0; font-size: 20px; }
        .amount { font-size: 24px; color: #2e7d32; font-weight: bold; margin: 15px 0; }
        p { color: #555; font-size: 14px; text-align: left; }
        .btn-pagar { background: #2e7d32; color: white; border: none; padding: 14px; width: 100%; font-size: 16px; font-weight: bold; border-radius: 8px; cursor: pointer; margin-top: 15px; }
        .btn-pagar:hover { background: #1b5e20; }
        .btn-cancelar { background: #c62828; color: white; border: none; padding: 12px; width: 100%; font-size: 15px; font-weight: bold; border-radius: 8px; cursor: pointer; margin-top: 10px; }
        .btn-cancelar:hover { background: #b71c1c; }
    </style>
</head>
<body>
    <div class="card">
        <h2>Simulación Pasarela QR</h2>
        <div class="amount">{{ precio }}</div>
        
        <p><b>Destino:</b> {{ destino }}<br>
           <b>CI Destinatario:</b> {{ dni }}<br>
           <b>Casilla Envío:</b> #{{ casilla }}</p>

        <form action="/movil/procesar-accion" method="POST">
            <input type="hidden" name="order_id" value="{{ order_id }}">
            <button type="submit" name="accion" value="pagar" class="btn-pagar">✔ Confirmar y Pagar</button>
            <button type="submit" name="accion" value="cancelar" class="btn-cancelar">✖ Cancelar Pago</button>
        </form>
    </div>
</body>
</html>
"""

HTML_MOVIL_MENSAJE = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Estado de Transacción</title>
    <style>
        body { font-family: Arial, sans-serif; background-color: #e8f5e9; text-align: center; margin-top: 60px; padding: 20px; }
        .card { background: white; padding: 30px; border-radius: 16px; display: inline-block; box-shadow: 0px 4px 15px rgba(0,0,0,0.1); max-width: 320px; }
        h1 { color: #2e7d32; font-size: 22px; }
        p { color: #555; font-size: 14px; }
    </style>
</head>
<body>
    <div class="card">
        <h1>{{ titulo }}</h1>
        <p>{{ mensaje }}</p>
    </div>
</body>
</html>
"""

HTML_CASILLERO_PC = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Q'epiBox - Depósito de Envío</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #eef2f5; text-align: center; margin-top: 30px; }
        .card { background: white; padding: 40px; border-radius: 16px; display: inline-block; box-shadow: 0px 8px 24px rgba(0,0,0,0.12); max-width: 480px; width: 90%; }
        .casilla-box { background-color: #1a237e; color: white; padding: 20px; border-radius: 12px; margin: 20px 0; }
        .casilla-num { font-size: 42px; font-weight: bold; margin: 5px 0; color: #ffd54f; }
        .guia-box { background: #f5f5f5; border: 2px dashed #1a237e; padding: 15px; border-radius: 10px; margin: 20px 0; }
        .guia-num { font-size: 24px; font-weight: bold; color: #d32f2f; letter-spacing: 2px; }
        .instrucciones { text-align: left; background: #fffde7; padding: 15px; border-left: 5px solid #fbc02d; border-radius: 4px; font-size: 14px; color: #555; margin-bottom: 25px; }
        .btn { display: inline-block; background-color: #1a237e; color: white; padding: 14px 25px; text-decoration: none; border-radius: 8px; font-weight: bold; font-size: 15px; }
        .timer-box { font-size: 13px; color: #666; margin-top: 15px; font-weight: bold; }
    </style>
</head>
<body>
    <div class="card">
        <h2 style="color: #2e7d32; margin-top:0;">¡Pago Recibido Exitosamente!</h2>
        
        <div class="casilla-box">
            <div>CASILLA DE ENVÍO ASIGNADA</div>
            <div class="casilla-num">PUERTA #{{ casilla }}</div>
            <div style="font-size: 12px; color: #ffd54f;">[ Modbus RTU / RS-485: Solenoide Q0.{{ casilla }} activado ]</div>
        </div>

        <div class="guia-box">
            <div style="font-size: 12px; color: #666;">NÚMERO DE GUÍA (COMPARTIR CON DESTINATARIO):</div>
            <div class="guia-num">{{ numero_guia }}</div>
        </div>

        <div class="instrucciones">
            📌 <b>Instrucciones:</b><br>
            1. La puerta de envío <b>#{{ casilla }}</b> se ha abierto.<br>
            2. Deposite su paquete y cierre la puerta con firmeza.<br>
            3. Sacarle foto al número de guía para enviarlo al destinatario.
        </div>

        <a href="/" class="btn">[ Volver al Menú Principal (Si ya le sacó foto) ]</a>
        <div class="timer-box">⏳ Esta pantalla se cerrará automáticamente en: <span id="timer_guia">02:00</span></div>
    </div>

    <script>
        let tiempoGuia = 120; 
        const countdownGuia = setInterval(() => {
            tiempoGuia--;
            let mins = Math.floor(tiempoGuia / 60);
            let secs = tiempoGuia % 60;
            document.getElementById("timer_guia").innerText = 
                `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;

            if (tiempoGuia <= 0) {
                clearInterval(countdownGuia);
                window.location.href = "/";
            }
        }, 1000);
    </script>
</body>
</html>
"""

HTML_FORMULARIO_RECOGER = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Q'epiBox - Recoger Encomienda</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #eef2f5; text-align: center; margin-top: 30px; }
        .card { background: white; padding: 30px; border-radius: 16px; display: inline-block; box-shadow: 0px 8px 24px rgba(0,0,0,0.12); max-width: 420px; width: 90%; text-align: left; }
        h2 { color: #2e7d32; text-align: center; margin-top: 0; }
        label { font-weight: bold; color: #333; display: block; margin-top: 15px; font-size: 14px; }
        input { width: 100%; padding: 12px; margin-top: 6px; border: 1px solid #ccc; border-radius: 8px; box-sizing: border-box; font-size: 16px; }
        .btn-submit { background-color: #2e7d32; color: white; font-size: 18px; font-weight: bold; margin-top: 25px; cursor: pointer; border: none; padding: 14px; border-radius: 8px; width: 100%; }
        .btn-submit:hover { background-color: #1b5e20; }
        .error-msg { background: #ffebee; color: #c62828; padding: 12px; border-radius: 8px; margin-bottom: 15px; font-size: 14px; text-align: center; font-weight: bold; }
        .back-link { display: block; text-align: center; margin-top: 15px; color: #666; text-decoration: none; font-size: 14px; }
    </style>
</head>
<body>
    <div class="card">
        <h2>Retiro de Encomienda</h2>
        
        {% if error %}
        <div class="error-msg">{{ error }}</div>
        {% endif %}

        <form action="/procesar-recojo" method="POST">
            <label>Número de Guía:</label>
            <input type="text" name="numero_guia" placeholder="Ej. GUIA-481920" required autocomplete="off" style="text-transform: uppercase;">

            <label>Cédula de Identidad (C.I. / DNI):</label>
            <input type="text" name="dni_usuario" placeholder="Ej. 8492019" required autocomplete="off">

            <button type="submit" class="btn-submit">Verificar y Abrir Casilla de Recojo ➔</button>
        </form>
        <a href="/" class="back-link">← Volver al Menú Principal</a>
    </div>
</body>
</html>
"""

HTML_EXITO_RECOJO = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Q'epiBox - Paquete Entregado</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #eef2f5; text-align: center; margin-top: 30px; }
        .card { background: white; padding: 40px; border-radius: 16px; display: inline-block; box-shadow: 0px 8px 24px rgba(0,0,0,0.12); max-width: 480px; width: 90%; }
        .casilla-box { background-color: #2e7d32; color: white; padding: 20px; border-radius: 12px; margin: 20px 0; }
        .casilla-num { font-size: 42px; font-weight: bold; margin: 5px 0; color: #ffd54f; }
        .btn { display: inline-block; background-color: #1a237e; color: white; padding: 12px 30px; text-decoration: none; border-radius: 8px; font-weight: bold; margin-top: 15px; }
        .timer-box { font-size: 13px; color: #666; margin-top: 15px; font-weight: bold; }
    </style>
</head>
<body>
    <div class="card">
        <h2 style="color: #2e7d32; margin-top:0;">¡Identidad Verificada con Éxito!</h2>
        
        <div class="casilla-box">
            <div>CASILLA DE RECOJO DESBLOQUEADA</div>
            <div class="casilla-num">PUERTA #{{ casilla }}</div>
            <div style="font-size: 12px; color: #ffd54f;">[ Casilla de recojo liberada y lista para otro usuario ]</div>
        </div>

        <p style="color: #555; font-size: 15px;">
            Retire su encomienda de la casilla y asegúrese de **cerrar la puerta** firmemente.
        </p>

        <a href="/" class="btn">Finalizar Operación</a>
        <div class="timer-box">⏳ Esta pantalla se cerrará en: <span id="timer_recojo">01:00</span></div>
    </div>

    <script>
        let tiempoRecojo = 60; 
        const countdownRecojo = setInterval(() => {
            tiempoRecojo--;
            document.getElementById("timer_recojo").innerText = 
                `00:${tiempoRecojo.toString().padStart(2, '0')}`;

            if (tiempoRecojo <= 0) {
                clearInterval(countdownRecojo);
                window.location.href = "/";
            }
        }, 1000);
    </script>
</body>
</html>
"""

# ----------------- RUTAS DE LA APLICACIÓN -----------------

@app.route("/")
def inicio():
    libres = sum(1 for c in casilleros_envio.values() if c["libre"])
    return render_template_string(HTML_INICIO, libres_envio=libres)

@app.route("/formulario-envio")
def formulario_envio():
    libres = sum(1 for c in casilleros_envio.values() if c["libre"])
    return render_template_string(HTML_FORMULARIO_ENVIO, casilleros_libres=libres)

@app.route("/procesar-envio", methods=["POST"])
def procesar_envio():
    casilla_asignada = None
    for num_casilla, info in casilleros_envio.items():
        if info["libre"]:
            casilla_asignada = num_casilla
            break

    if not casilla_asignada:
        return redirect(url_for("formulario_envio"))

    dni = request.form.get("dni_destinatario")
    destino = request.form.get("destino")
    tamano = request.form.get("tamano")
    
    order_id = f"QEP-{int(time.time())}"
    numero_guia = f"GUIA-{random.randint(100000, 999999)}"

    casilleros_envio[casilla_asignada]["libre"] = False
    casilleros_envio[casilla_asignada]["order_id"] = order_id

    encomiendas_db[order_id] = {
        "dni": dni,
        "destino": destino,
        "precio": tamano,
        "pagado": False,
        "casilla_envio": casilla_asignada,
        "casilla_recojo": None,
        "numero_guia": numero_guia,
        "en_recojo": False,
        "retirado": False
    }

    return redirect(url_for("pantalla_qr", order_id=order_id))

@app.route("/pantalla-qr")
def pantalla_qr():
    order_id = request.args.get("order_id")
    datos = encomiendas_db.get(order_id)
    if not datos:
        return redirect("/")

    qr_url = f"http://{MI_IP_LOCAL}:8080/movil/pago?order_id={order_id}"
    return render_template_string(HTML_QR_PAGO, 
                                  qr_url=qr_url, 
                                  order_id=order_id, 
                                  precio=datos["precio"],
                                  casilla=datos["casilla_envio"],
                                  dni=datos["dni"])

@app.route("/movil/pago")
def movil_pago():
    order_id = request.args.get("order_id")
    datos = encomiendas_db.get(order_id)
    if not datos:
        return "Transacción no encontrada o expirada.", 404

    return render_template_string(HTML_MOVIL_PAGO_INTERACTIVO,
                                  order_id=order_id,
                                  precio=datos["precio"],
                                  destino=datos["destino"],
                                  dni=datos["dni"],
                                  casilla=datos["casilla_envio"])

@app.route("/movil/procesar-accion", methods=["POST"])
def movil_procesar_accion():
    order_id = request.form.get("order_id")
    accion = request.form.get("accion")
    
    if order_id not in encomiendas_db:
        return render_template_string(HTML_MOVIL_MENSAJE, titulo="Error", mensaje="Orden no encontrada.")

    if accion == "pagar":
        encomiendas_db[order_id]["pagado"] = True
        casilla_E = encomiendas_db[order_id]['casilla_envio']
        print(f"\n >>> [Q'EPIBOX] PAGO MÓVIL CONFIRMADO. Orden: {order_id} <<<")
        print(f" >>> [PLC MODBUS] Abriendo Casilla de ENVÍO #{casilla_E} para depósito del cliente <<-\n")
        return render_template_string(HTML_MOVIL_MENSAJE, titulo="¡Pago Exitoso!", mensaje="Transacción aprobada. Revise la pantalla de la PC.")
    else:
        print(f"\n >>> [Q'EPIBOX] Pago cancelado desde el móvil para la orden: {order_id} <<<")
        return render_template_string(HTML_MOVIL_MENSAJE, titulo="Pago Cancelado", mensaje="La transacción ha sido anulada.")

@app.route("/api/chequear-pago")
def api_chequear_pago():
    order_id = request.args.get("order_id")
    datos = encomiendas_db.get(order_id, {})
    return jsonify({"pagado": datos.get("pagado", False)})

@app.route("/casillero-asignado")
def casillero_asignado():
    order_id = request.args.get("order_id")
    datos = encomiendas_db.get(order_id)
    if not datos:
        return redirect("/")

    return render_template_string(HTML_CASILLERO_PC, 
                                  casilla=datos["casilla_envio"], 
                                  numero_guia=datos["numero_guia"])

# --- MÓDULO DE RECOJO DE ENCOMIENDA (CLIENTE FINAL) ---

@app.route("/formulario-recojer")
def formulario_recojer():
    return render_template_string(HTML_FORMULARIO_RECOGER, error=None)

@app.route("/procesar-recojo", methods=["POST"])
def procesar_recojo():
    guia_ingresada = request.form.get("numero_guia", "").strip().upper()
    dni_ingresado = request.form.get("dni_usuario", "").strip()

    encomienda_encontrada = None
    for order_id, datos in encomiendas_db.items():
        if datos["numero_guia"] == guia_ingresada and datos["dni"] == dni_ingresado:
            encomienda_encontrada = (order_id, datos)
            break

    if not encomienda_encontrada:
        return render_template_string(HTML_FORMULARIO_RECOGER, 
                                      error="❌ Número de Guía o Cédula incorrectos, o encomienda no disponible.")

    order_id, datos = encomienda_encontrada

    if not datos.get("en_recojo"):
        return render_template_string(HTML_FORMULARIO_RECOGER, 
                                      error="⏳ Su paquete ha sido registrado, pero aún no se encuentra disponible en los casilleros de recojo de la terminal.")

    if datos.get("retirado"):
        return render_template_string(HTML_FORMULARIO_RECOGER, 
                                      error="⚠️ Esta encomienda ya fue retirada anteriormente.")

    datos["retirado"] = True
    casilla_R = datos["casilla_recojo"]

    if casilla_R in casilleros_recojo:
        casilleros_recojo[casilla_R]["libre"] = True
        casilleros_recojo[casilla_R]["order_id"] = None

    print(f"\n >>> [Q'EPIBOX RECOJO] Destinatario retiró paquete. Guía: {guia_ingresada} <<<")
    print(f" >>> [PLC MODBUS] Abriendo Casilla de RECOJO #{casilla_R}. Casillero liberado. <<<\n")

    return render_template_string(HTML_EXITO_RECOJO, casilla=casilla_R)

# --- MÓDULO OCULTO Y SEGURO DEL OPERARIO ---

@app.route("/operario/login", methods=["GET", "POST"])
def operario_login():
    error = None
    if request.method == "POST":
        password = request.form.get("password")
        if password == "1234":
            session["operario_autenticado"] = True
            return redirect(url_for("operario_panel"))
        else:
            error = "❌ Clave incorrecta."
    return render_template_string(HTML_LOGIN_OPERARIO, error=error)

@app.route("/operario/panel")
def operario_panel():
    if not session.get("operario_autenticado"):
        return redirect(url_for("operario_login"))

    libres_envio = sum(1 for c in casilleros_envio.values() if c["libre"])
    libres_recojo = sum(1 for c in casilleros_recojo.values() if c["libre"])
    
    filtro_destino = request.args.get("filtro_destino", "TODOS")

    return render_template_string(HTML_PANEL_OPERARIO, 
                                  libres_envio=libres_envio, 
                                  libres_recojo=libres_recojo, 
                                  encomiendas=encomiendas_db,
                                  filtro_actual=filtro_destino)

@app.route("/operario/mover-a-recojo")
def operario_mover_a_recojo():
    if not session.get("operario_autenticado"):
        return redirect(url_for("operario_login"))

    order_id = request.args.get("order_id")
    filtro_destino = request.args.get("filtro_destino", "TODOS")
    datos = encomiendas_db.get(order_id)
    if not datos:
        return redirect(url_for("operario_panel", filtro_destino=filtro_destino))

    libres_recojo = any(c["libre"] for c in casilleros_recojo.values())
    if not libres_recojo:
        return render_template_string(HTML_ASIGNAR_RECOJO, order_id=order_id, datos=datos, casilleros_recojo=casilleros_recojo, filtro_actual=filtro_destino, error="❌ No hay casilleros de recojo libres (5-8).")

    return render_template_string(HTML_ASIGNAR_RECOJO, order_id=order_id, datos=datos, casilleros_recojo=casilleros_recojo, filtro_actual=filtro_destino, error=None)

@app.route("/operario/guardar-en-recojo", methods=["POST"])
def guardar_en_recojo():
    if not session.get("operario_autenticado"):
        return redirect(url_for("operario_login"))

    order_id = request.form.get("order_id")
    casilla_recojo_num = int(request.form.get("casilla_recojo"))
    filtro_destino = request.form.get("filtro_destino", "TODOS")

    if order_id in encomiendas_db:
        casilleros_recojo[casilla_recojo_num]["libre"] = False
        casilleros_recojo[casilla_recojo_num]["order_id"] = order_id

        casilla_envio_antigua = encomiendas_db[order_id]["casilla_envio"]
        if casilla_envio_antigua in casilleros_envio:
            casilleros_envio[casilla_envio_antigua]["libre"] = True
            casilleros_envio[casilla_envio_antigua]["order_id"] = None

        encomiendas_db[order_id]["en_recojo"] = True
        encomiendas_db[order_id]["casilla_recojo"] = casilla_recojo_num

        print(f"\n >>> [OPERARIO Q'EPIBOX] Paquete movido a Casilla de Recojo #{casilla_recojo_num} <<<")
        print(f" >>> [PLC MODBUS] Activando solenoide de recojo #{casilla_recojo_num} para ingreso físico <<-\n")

    return redirect(url_for("operario_panel", filtro_destino=filtro_destino))

@app.route("/operario/logout")
def operario_logout():
    session.pop("operario_autenticado", None)
    return redirect(url_for("operario_login"))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)