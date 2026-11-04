from flask import Flask, render_template_string, request, jsonify
import time

app = Flask(__name__)

MI_IP_LOCAL = "192.168.0.6"

# Estado de los pedidos en tiempo real
estado_pedidos = {}

HTML_QR_TEMPLATE = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Simulador de QR Interactivo</title>
    <style>
        body { font-family: Arial, sans-serif; background-color: #f4f4f9; text-align: center; margin-top: 30px; }
        .card { background: white; padding: 30px; border-radius: 12px; display: inline-block; box-shadow: 0px 4px 15px rgba(0,0,0,0.1); max-width: 360px; }
        h2 { color: #333; margin-bottom: 5px; }
        .amount { font-size: 24px; color: #2e7d32; font-weight: bold; margin: 10px 0; }
        img { max-width: 240px; height: auto; margin: 10px 0; border: 1px solid #ddd; border-radius: 8px; padding: 10px; }
        .info { color: #666; font-size: 12px; margin: 4px 0; }
        .esperando { color: #e65100; font-weight: bold; margin-top: 15px; animation: blink 1.5s infinite; }
        @keyframes blink { 0% { opacity: 1; } 50% { opacity: 0.4; } 100% { opacity: 1; } }
    </style>
</head>
<body>
    <div class="card">
        <h2>Escanea con tu Móvil</h2>
        <div class="amount">1.00 BOB</div>
        
        <img src="https://api.qrserver.com/v1/create-qr-code/?size=250x250&data={{ qr_url }}" alt="QR Interactivo">
        
        <p class="info"><b>ID de Orden:</b> {{ order_id }}</p>
        <p class="esperando">⏳ Esperando lectura del celular...</p>
    </div>

    <script>
        const orderId = "{{ order_id }}";
        
        // La PC consulta cada segundo si el celular ya escaneó
        const verificar = setInterval(async () => {
            try {
                let res = await fetch(`/api/chequear?order_id=${orderId}`);
                let data = await res.json();
                if (data.pagado) {
                    clearInterval(verificar);
                    window.location.href = `/exito-pc?order_id=${orderId}`;
                }
            } catch (e) {
                console.log("Comprobando...");
            }
        }, 1000);
    </script>
</body>
</html>
"""

SUCCESS_TEMPLATE = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>¡Pago Exitoso!</title>
    <style>
        body { font-family: Arial, sans-serif; background-color: #e8f5e9; text-align: center; margin-top: 60px; padding: 20px; }
        .card { background: white; padding: 40px; border-radius: 12px; display: inline-block; box-shadow: 0px 4px 15px rgba(0,0,0,0.1); max-width: 320px; }
        h1 { color: #2e7d32; font-size: 24px; }
        <p> { color: #555; }
        .badge { background: #c8e6c9; color: #2e7d32; padding: 8px 15px; border-radius: 20px; font-weight: bold; display: inline-block; margin-bottom: 15px;}
        .btn { display: inline-block; margin-top: 20px; background: #2e7d32; color: white; padding: 10px 20px; text-decoration: none; border-radius: 6px; font-weight: bold; }
    </style>
</head>
<body>
    <div class="card">
        <div class="badge">¡TRANSACCIÓN EXITOSA!</div>
        <h1>Pago Confirmado</h1>
        <p>La orden <b>{{ order_id }}</b> se procesó correctamente.</p>
        <a href="/generar-qr" class="btn">Generar otro QR</a>
    </div>
</body>
</html>
"""

@app.route("/generar-qr", methods=["GET"])
def generar_qr():
    order_id = f"pedido-{int(time.time())}"
    estado_pedidos[order_id] = False  
    
    # Esta URL dentro del QR ahora sí apunta a la ruta de confirmación de sincronización
    qr_url = f"http://{MI_IP_LOCAL}:8080/confirmar-desde-movil?order_id={order_id}"
    
    return render_template_string(HTML_QR_TEMPLATE, qr_url=qr_url, order_id=order_id)

@app.route("/confirmar-desde-movil", methods=["GET"])
def confirmar_desde_movil():
    order_id = request.args.get("order_id")
    if order_id in estado_pedidos:
        estado_pedidos[order_id] = True  # ¡Aquí se marca como pagado para que la PC despierte!
        
    print(f"\n >>> ¡LECTURA EXITOSA DESDE MÓVIL! Orden: {order_id} <<<\n")
    return render_template_string(SUCCESS_TEMPLATE, order_id=order_id)

@app.route("/api/chequear", methods=["GET"])
def api_chequear():
    order_id = request.args.get("order_id")
    pagado = estado_pedidos.get(order_id, False)
    return jsonify({"pagado": pagado})

@app.route("/exito-pc", methods=["GET"])
def exito_pc():
    order_id = request.args.get("order_id", "Desconocido")
    return render_template_string(SUCCESS_TEMPLATE, order_id=order_id)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)