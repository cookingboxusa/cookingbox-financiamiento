import json
import os
import uuid
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, send_from_directory
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024  # 10 MB max por archivo
app.jinja_env.globals.update(enumerate=enumerate)

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
DATA_FILE = os.path.join(DATA_DIR, "trailers.json")
SOLICITUDES_FILE = os.path.join(DATA_DIR, "solicitudes.json")
LEADS_FILE = os.path.join(DATA_DIR, "leads.json")
COTIZADOR_CONFIG = os.path.join(DATA_DIR, "cotizador_config.json")
UPLOADS_DIR = os.path.join(DATA_DIR, "uploads")

ALLOWED_EXTENSIONS = {"pdf", "jpg", "jpeg", "png", "heic"}

PLAZOS = ["12 meses", "24 meses", "36 meses", "48 meses", "60 meses"]
PARENTESCOS = ["Padre/Madre", "Hijo/Hija", "Hermano/Hermana", "Esposo/Esposa",
               "Amigo/Amiga", "Compañero de trabajo", "Vecino/Vecina", "Otro"]


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_trailers():
    return load_json(DATA_FILE)


def save_trailers(t):
    save_json(DATA_FILE, t)


def load_solicitudes():
    return load_json(SOLICITUDES_FILE)


def save_solicitudes(s):
    save_json(SOLICITUDES_FILE, s)


def load_leads():
    return load_json(LEADS_FILE)


def save_leads(l):
    save_json(LEADS_FILE, l)


def trailers_que_califican(down_payment):
    resultado = []
    for t in load_trailers():
        if t["down_min"] is None:
            continue
        califica = down_payment >= t["down_min"]
        balance = (t["precio"] - down_payment) if califica and t["precio"] else None
        resultado.append({**t, "califica": califica, "balance": balance})
    return resultado


def save_upload(file, solicitud_id, campo):
    """Guarda archivo subido y retorna el nombre guardado o None."""
    if not file or file.filename == "":
        return None
    if not allowed_file(file.filename):
        return None
    ext = file.filename.rsplit(".", 1)[1].lower()
    folder = os.path.join(UPLOADS_DIR, solicitud_id)
    os.makedirs(folder, exist_ok=True)
    filename = secure_filename(f"{campo}.{ext}")
    file.save(os.path.join(folder, filename))
    return filename


def referencias_desde_form(form, prefijo):
    refs = []
    for i in range(1, 6):
        refs.append({
            "nombre": form.get(f"{prefijo}_ref{i}_nombre", "").strip(),
            "telefono": form.get(f"{prefijo}_ref{i}_telefono", "").strip(),
            "parentesco": form.get(f"{prefijo}_ref{i}_parentesco", "").strip(),
        })
    return refs


def persona_desde_form(form, files, prefijo, solicitud_id, existente=None):
    existente = existente or {}

    id_doc = save_upload(files.get(f"{prefijo}_id_doc"), solicitud_id, f"{prefijo}_id_doc")
    comprobante = save_upload(files.get(f"{prefijo}_comprobante"), solicitud_id, f"{prefijo}_comprobante")

    persona = {
        "nombre": form.get(f"{prefijo}_nombre", "").strip(),
        "direccion": form.get(f"{prefijo}_direccion", "").strip(),
        "telefono": form.get(f"{prefijo}_telefono", "").strip(),
        "email": form.get(f"{prefijo}_email", "").strip(),
        "plazo": form.get(f"{prefijo}_plazo", "").strip(),
        "red_social": form.get(f"{prefijo}_red_social", "").strip(),
        "referencias": referencias_desde_form(form, prefijo),
        "id_doc": id_doc or existente.get("id_doc"),
        "comprobante": comprobante or existente.get("comprobante"),
    }

    if prefijo == "aplicante":
        persona["direccion_trailer"] = form.get("aplicante_direccion_trailer", "").strip()
        estado = save_upload(files.get("aplicante_estado_cuenta"), solicitud_id, "aplicante_estado_cuenta")
        persona["estado_cuenta"] = estado or existente.get("estado_cuenta")

    return persona


def evaluar_requisitos(s):
    pendientes = []
    ap = s.get("aplicante", {})
    co = s.get("coaplicante", {})

    for rol, p in [("Aplicante", ap), ("Coaplicante", co)]:
        if not p.get("nombre"):       pendientes.append(f"{rol}: falta nombre")
        if not p.get("direccion"):    pendientes.append(f"{rol}: falta dirección")
        if not p.get("telefono"):     pendientes.append(f"{rol}: falta teléfono")
        if not p.get("plazo"):        pendientes.append(f"{rol}: falta plazo del contrato")
        if not p.get("red_social"):   pendientes.append(f"{rol}: falta red social")
        if not p.get("id_doc"):       pendientes.append(f"{rol}: falta foto de ID")
        if not p.get("comprobante"):  pendientes.append(f"{rol}: falta comprobante de domicilio")
        refs = p.get("referencias", [])
        vacias = sum(1 for r in refs if not r.get("nombre"))
        if vacias > 0:
            pendientes.append(f"{rol}: faltan {vacias} de 5 referencias personales")

    if not ap.get("direccion_trailer"):
        pendientes.append("Aplicante: falta dirección donde trabajará el trailer")
    if not ap.get("estado_cuenta"):
        pendientes.append("Aplicante: falta estado de cuenta (comprobante de down payment)")
    if not s.get("down_payment") or s["down_payment"] <= 0:
        pendientes.append("Falta monto de down payment")

    return pendientes, len(pendientes) == 0


# ── Rutas ─────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/solicitudes")
def solicitudes_lista():
    solicitudes = load_solicitudes()
    for s in solicitudes:
        s["pendientes"], s["completo"] = evaluar_requisitos(s)
    solicitudes.sort(key=lambda x: x["fecha"], reverse=True)
    return render_template("solicitudes.html", solicitudes=solicitudes)


@app.route("/solicitud/nueva", methods=["GET", "POST"])
def solicitud_nueva():
    if request.method == "POST":
        try:
            down_payment = float(request.form.get("down_payment", "0"))
        except ValueError:
            down_payment = 0

        sid = str(uuid.uuid4())[:8]
        solicitud = {
            "id": sid,
            "fecha": datetime.now().isoformat(timespec="seconds"),
            "down_payment": down_payment,
            "aplicante": persona_desde_form(request.form, request.files, "aplicante", sid),
            "coaplicante": persona_desde_form(request.form, request.files, "coaplicante", sid),
        }
        solicitudes = load_solicitudes()
        solicitudes.append(solicitud)
        save_solicitudes(solicitudes)
        return redirect(url_for("solicitud_detalle", solicitud_id=sid))

    return render_template("solicitud_form.html",
                           solicitud=None, plazos=PLAZOS, parentescos=PARENTESCOS)


@app.route("/solicitud/<solicitud_id>", methods=["GET", "POST"])
def solicitud_detalle(solicitud_id):
    solicitudes = load_solicitudes()
    s = next((x for x in solicitudes if x["id"] == solicitud_id), None)
    if s is None:
        return redirect(url_for("solicitudes_lista"))

    if request.method == "POST":
        try:
            s["down_payment"] = float(request.form.get("down_payment", "0"))
        except ValueError:
            s["down_payment"] = 0
        s["aplicante"] = persona_desde_form(
            request.form, request.files, "aplicante", solicitud_id, s.get("aplicante"))
        s["coaplicante"] = persona_desde_form(
            request.form, request.files, "coaplicante", solicitud_id, s.get("coaplicante"))
        save_solicitudes(solicitudes)
        return redirect(url_for("solicitud_detalle", solicitud_id=solicitud_id))

    pendientes, completo = evaluar_requisitos(s)
    modelos = trailers_que_califican(s["down_payment"]) if s.get("down_payment") else []
    return render_template("solicitud_form.html",
                           solicitud=s, pendientes=pendientes, completo=completo,
                           modelos=modelos, plazos=PLAZOS, parentescos=PARENTESCOS)


@app.route("/uploads/<solicitud_id>/<filename>")
def uploaded_file(solicitud_id, filename):
    folder = os.path.join(UPLOADS_DIR, solicitud_id)
    return send_from_directory(folder, filename)


@app.route("/leads")
def leads_lista():
    leads = load_leads()
    leads.sort(key=lambda x: x["fecha"], reverse=True)
    return render_template("leads.html", leads=leads)


@app.route("/precalifica", methods=["GET", "POST"])
def precalifica():
    resultado = None
    nombre = telefono = email = ""
    down_payment = None

    if request.method == "POST":
        nombre = request.form.get("nombre", "").strip()
        telefono = request.form.get("telefono", "").strip()
        email = request.form.get("email", "").strip()
        try:
            down_payment = float(request.form.get("down_payment", "0"))
        except ValueError:
            down_payment = 0

        modelos = trailers_que_califican(down_payment)
        califica_algo = any(m["califica"] for m in modelos)

        leads = load_leads()
        leads.append({
            "id": str(uuid.uuid4())[:8],
            "fecha": datetime.now().isoformat(timespec="seconds"),
            "nombre": nombre, "telefono": telefono, "email": email,
            "down_payment": down_payment, "califica": califica_algo,
        })
        save_leads(leads)
        resultado = {"modelos": modelos, "califica_algo": califica_algo}

    return render_template("precalifica.html",
                           resultado=resultado, nombre=nombre,
                           telefono=telefono, email=email, down_payment=down_payment)


@app.route("/precios", methods=["GET", "POST"])
def precios():
    trailers = load_trailers()
    if request.method == "POST":
        for t in trailers:
            valor = request.form.get(f"precio_{t['pies']}", "").strip()
            t["precio"] = float(valor) if valor else None
        save_trailers(trailers)
        return redirect(url_for("precios"))
    return render_template("precios.html", trailers=trailers)


def calcular_pago_semanal(monto_financiado):
    """Pago semanal a 3 años (156 semanas) basado en tabla RTO."""
    if monto_financiado < 11000:
        return None
    if monto_financiado > 25000:
        monto_financiado = 25000
    pago = 190 + ((monto_financiado - 11000) / 250) * 3.67
    return round(pago, 2)


@app.route("/cotizador", methods=["GET", "POST"])
def cotizador():
    cfg = load_json(COTIZADOR_CONFIG)
    resultado = None
    form = {}

    if request.method == "POST":
        form = request.form
        trailer_idx = int(form.get("trailer_idx", 0))
        trailer = cfg["trailers"][trailer_idx]
        color = form.get("color", "").strip()
        down_payment = float(form.get("down_payment", 0) or 0)
        cliente_nombre = form.get("cliente_nombre", "").strip()
        cliente_telefono = form.get("cliente_telefono", "").strip()

        equipos_sel = []
        total_equipos = 0
        for i, eq in enumerate(cfg["equipos"]):
            if form.get(f"equipo_{i}"):
                qty = int(form.get(f"qty_{i}", 1) or 1)
                subtotal = eq["precio"] * qty
                equipos_sel.append({**eq, "qty": qty, "subtotal": subtotal})
                total_equipos += subtotal

        precio_trailer = trailer["precio"]
        valor_venta = precio_trailer + total_equipos
        monto_financiado = valor_venta - down_payment
        pago_semanal = calcular_pago_semanal(monto_financiado)

        resultado = {
            "trailer": trailer,
            "color": color,
            "cliente_nombre": cliente_nombre,
            "cliente_telefono": cliente_telefono,
            "equipos_sel": equipos_sel,
            "precio_trailer": precio_trailer,
            "total_equipos": total_equipos,
            "valor_venta": valor_venta,
            "down_payment": down_payment,
            "monto_financiado": monto_financiado,
            "pago_semanal": pago_semanal,
        }

    return render_template("cotizador.html", cfg=cfg, resultado=resultado, form=form)


@app.route("/bos-caja", methods=["GET", "POST"])
def bos_caja():
    solicitudes = load_solicitudes()
    resultado = None
    form = {}

    if request.method == "POST":
        form = request.form
        resultado = {
            "fecha": form.get("fecha", datetime.now().strftime("%Y-%m-%d")),
            "cliente_nombre": form.get("cliente_nombre", ""),
            "cliente_direccion": form.get("cliente_direccion", ""),
            "cliente_telefono": form.get("cliente_telefono", ""),
            "descripcion": form.get("descripcion", ""),
            "sales_price": float(form.get("sales_price", 0) or 0),
            "terminos": form.get("terminos", "FINANCING"),
            "bos_num": form.get("bos_num", ""),
            "vin": form.get("vin", ""),
            "anio": form.get("anio", "2026"),
            "make": form.get("make", ""),
            "modelo": form.get("modelo", ""),
            "body_style": form.get("body_style", "FOOD VENDING"),
            "color": form.get("color", ""),
        }

    return render_template("bos_caja.html", resultado=resultado, form=form,
                           solicitudes=solicitudes,
                           hoy=datetime.now().strftime("%Y-%m-%d"))


@app.route("/bos-kappa", methods=["GET", "POST"])
def bos_kappa():
    cfg = load_json(COTIZADOR_CONFIG)
    solicitudes = load_solicitudes()
    resultado = None
    form = {}

    if request.method == "POST":
        form = request.form
        equipos_sel = []
        for i, eq in enumerate(cfg["equipos"]):
            if form.get(f"equipo_{i}"):
                qty = int(form.get(f"qty_{i}", 1) or 1)
                equipos_sel.append({"nombre": eq["nombre"], "qty": qty})

        resultado = {
            "cliente_nombre": form.get("cliente_nombre", ""),
            "cliente_location": form.get("cliente_location", ""),
            "cliente_telefono": form.get("cliente_telefono", ""),
            "descripcion_trailer": form.get("descripcion_trailer", ""),
            "total_cash": float(form.get("total_cash", 0) or 0),
            "color": form.get("color", ""),
            "equipos_sel": equipos_sel,
            "descripcion_general": cfg["descripcion_general"],
        }

    return render_template("bos_kappa.html", resultado=resultado, form=form,
                           cfg=cfg, solicitudes=solicitudes)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
