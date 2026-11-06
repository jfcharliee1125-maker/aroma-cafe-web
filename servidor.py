from datetime import datetime
from flask import Flask, jsonify, render_template, request, session
from flask_cors import CORS
from pymongo import MongoClient
from bson import ObjectId
import os

app = Flask(__name__)
# Clave secreta necesaria para manejar las sesiones de usuario
app.secret_key = "tu_clave_secreta_super_segura"

CORS(app)

# Conexión dinámica: lee la variable de entorno de Render/Atlas o usa localhost por defecto
mongo_uri = os.environ.get("MONGO_URI", "mongodb://localhost:27017/")
client = MongoClient(mongo_uri)
db = client["aroma_cafe"]
coleccion_pedidos = db["pedidos"]
coleccion_comentarios = db["comentarios"]

# --- RUTA PRINCIPAL ---

@app.route("/", methods=["GET"])
def inicio():
    return render_template("index.html")


# --- RUTAS DE PEDIDOS ---

@app.route("/api/guardar-pedido", methods=["POST"])
def guardar_pedido():
    datos = request.json
    if not datos:
        return jsonify({"error": "No se recibieron datos"}), 400

    datos["estado"] = "Pendiente"
    
    if "metodoPago" not in datos or not datos["metodoPago"]:
        datos["metodoPago"] = "Efectivo"

    coleccion_pedidos.insert_one(datos)
    return jsonify({"mensaje": "¡Pedido guardado con éxito!"}), 200

@app.route("/api/pedidos", methods=["GET"])
def obtener_pedidos():
    pedidos = list(coleccion_pedidos.find({}, {"_id": False}))
    return jsonify(pedidos)

@app.route("/api/pedidos/<folio>", methods=["PUT"])
def actualizar_estado(folio):
    datos = request.json
    nuevo_estado = datos.get("estado")
    
    if not nuevo_estado:
        return jsonify({"error": "No se proporcionó el nuevo estado"}), 400

    resultado = coleccion_pedidos.update_one(
        {"folio": folio},
        {"$set": {"estado": nuevo_estado}}
    )

    if resultado.matched_count == 0:
        return jsonify({"error": "Pedido no encontrado"}), 404

    return jsonify({"mensaje": "Estado actualizado con éxito"}), 200

@app.route("/api/pedidos/<folio>/pago", methods=["PUT"])
def actualizar_pago(folio):
    datos = request.json
    nuevo_pago = datos.get("metodoPago")
    
    if not nuevo_pago:
        return jsonify({"error": "No se proporcionó el método de pago"}), 400

    resultado = coleccion_pedidos.update_one(
        {"folio": folio},
        {"$set": {"metodoPago": nuevo_pago}}
    )

    if resultado.matched_count == 0:
        return jsonify({"error": "Pedido no encontrado"}), 404

    return jsonify({"mensaje": "Método de pago actualizado con éxito"}), 200

@app.route("/api/pedidos/completados", methods=["DELETE"])
def eliminar_completados():
    resultado = coleccion_pedidos.delete_many({"estado": {"$regex": "^completado$", "$options": "i"}})
    return jsonify({"mensaje": f"Se eliminaron {resultado.deleted_count} pedidos completados."}), 200


# --- RUTAS DE COMENTARIOS Y CALIFICACIONES ---

@app.route("/api/comentarios", methods=["POST"])
def guardar_comentario():
    datos = request.json
    if not datos or "comentario" not in datos:
        return jsonify({"error": "No se recibió el comentario"}), 400

    # Valida si hay sesión activa; si no, asigna "usuario desconocido"
    correo_usuario = session.get("user_email", "usuario desconocido")

    nuevo_comentario = {
        "correo": correo_usuario,
        "comentario": datos.get("comentario"),
        "calificacion": int(datos.get("calificacion", 5)),
        "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    coleccion_comentarios.insert_one(nuevo_comentario)
    return jsonify({"mensaje": "¡Comentario guardado con éxito!"}), 200

@app.route("/api/comentarios", methods=["GET"])
def obtener_comentarios():
    comentarios = list(coleccion_comentarios.find().sort("_id", -1))
    for c in comentarios:
        c["_id"] = str(c["_id"])  # Convierte ObjectId a string para que el admin pueda gestionarlos
    return jsonify(comentarios)

@app.route("/api/comentarios/<id>", methods=["DELETE"])
def eliminar_comentario(id):
    try:
        resultado = coleccion_comentarios.delete_one({"_id": ObjectId(id)})
        if resultado.deleted_count == 0:
            return jsonify({"error": "Comentario no encontrado"}), 404
        return jsonify({"mensaje": "Comentario eliminado con éxito"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route("/api/comentarios/multiples", methods=["DELETE"])
def eliminar_multiples_comentarios():
    datos = request.json
    ids = datos.get("ids", [])
    
    if not ids:
        return jsonify({"error": "No se seleccionaron comentarios"}), 400

    try:
        object_ids = [ObjectId(id_str) for id_str in ids]
        resultado = coleccion_comentarios.delete_many({"_id": {"$in": object_ids}})
        return jsonify({"mensaje": f"Se eliminaron {resultado.deleted_count} comentarios correctamente."}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route("/api/comentarios/<id>/responder", methods=["PUT"])
def responder_comentario(id):
    datos = request.json
    respuesta_texto = datos.get("respuesta")
    
    if not respuesta_texto:
        return jsonify({"error": "La respuesta no puede estar vacía"}), 400

    try:
        resultado = coleccion_comentarios.update_one(
            {"_id": ObjectId(id)},
            {"$set": {"respuesta": respuesta_texto}}
        )
        if resultado.matched_count == 0:
            return jsonify({"error": "Comentario no encontrado"}), 404
        return jsonify({"mensaje": "Respuesta guardada con éxito"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400


if __name__ == "__main__":
    app.run(debug=True, port=5000)