import json
import os
import uuid
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
DATA_FILE = os.path.join(DATA_DIR, "trailers.json")
SOLICITUDES_FILE = os.path.join(DATA_DIR, "solicitudes.json")
LEADS_FILE = os.path.join(DATA_DIR, "leads.json")


def load_trailers():
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_trailers(trailers):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(trailers, f, ensure_ascii=False, indent=2)


def load_solicitudes():
    with open(SOLICITUDES_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_solicitudes(solicitudes):
    with open(SOLICITUDES_FILE, "w", encoding="utf-8") as f:
        json.dump(solicitudes, f, ensure_ascii=False, indent=2)


def load_leads():
    with open(LEADS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_leads(leads):
    with open(LEADS_FILE, "w", encoding="utf-8") as f:
        json.dump(leads, f, ensure_ascii=False, indent=2)


def trailers_que_califican(down_payment):
    trailers = load_trailers()
    resultado = []
    for t in trailers:
        if t["down_min"] is None:
            continue
        califica = down_payment >= t["down_min"]
        balance = None
        if califica and t["precio"] is not None:
            balance = t["precio"] - down_payment
        resultado.append({**t, "califica": califica, "balance": balance})
    return resultado


def evaluar_requisitos(s):
    """Devuelve (lista_pendientes, completo)."""
    pendientes = []

    for rol, persona in (("Aplicante", s["aplicante"]), ("Coaplicante", s["coaplicante"])):
        if not persona.get("nombre"):
            pendientes.append(f"{rol}: falta nombre")
        if not persona.get("telefono"):
            pendientes.append(f"{rol}: falta teléfono")
        if not persona.get("direccion"):
            pendientes.append(f"{rol}: falta dirección")
        if not persona.get("id_doc"):
            pendientes.append(f"{rol}: falta identificación (ID/pasaporte)")

    if not s.get("down_payment") or s["down_payment"] <= 0:
        pendientes.append("Falta monto de down payment con el que cuenta el cliente")

    dir_a = (s["aplicante"].get("direccion") or "").strip().lower()
    dir_c = (s["coaplicante"].get("direccion") or "").strip().lower()
    misma_direccion = bool(dir_a) and bool(dir_c) and dir_a == dir_c
    s["misma_direccion"] = misma_direccion

    if misma_direccion:
        if not s["aplicante"].get("comprobante_domicilio"):
            pendientes.append("Aplicante: falta comprobante de domicilio (misma dirección que coaplicante)")
        if not s["coaplicante"].get("comprobante_domicilio"):
            pendientes.append("Coaplicante: falta comprobante de domicilio (misma dirección que aplicante)")
    else:
        for rol, persona in (("Aplicante", s["aplicante"]), ("Coaplicante", s["coaplicante"])):
            if not persona.get("comprobante_domicilio"):
                pendientes.append(f"{rol}: falta comprobante de domicilio #1 (direcciones distintas, se requieren 2)")
            if not persona.get("comprobante_domicilio_2"):
                pendientes.append(f"{rol}: falta comprobante de domicilio #2 (direcciones distintas, se requieren 2)")

    return pendientes, len(pendientes) == 0


@app.route("/", methods=["GET", "POST"])
def index():
    trailers = load_trailers()
    resultado = None
    down_payment = None

    if request.method == "POST":
        try:
            down_payment = float(request.form.get("down_payment", "0"))
        except ValueError:
            down_payment = 0

        resultado = []
        for t in trailers:
            if t["down_min"] is None:
                continue
            califica = down_payment >= t["down_min"]
            balance = None
            if califica and t["precio"] is not None:
                balance = t["precio"] - down_payment
            resultado.append({
                **t,
                "califica": califica,
                "balance": balance,
            })

    return render_template("index.html", resultado=resultado, down_payment=down_payment)


def _persona_desde_form(form, prefijo):
    return {
        "nombre": form.get(f"{prefijo}_nombre", "").strip(),
        "telefono": form.get(f"{prefijo}_telefono", "").strip(),
        "email": form.get(f"{prefijo}_email", "").strip(),
        "direccion": form.get(f"{prefijo}_direccion", "").strip(),
        "id_doc": form.get(f"{prefijo}_id_doc") == "on",
        "comprobante_domicilio": form.get(f"{prefijo}_comprobante_domicilio") == "on",
        "comprobante_domicilio_2": form.get(f"{prefijo}_comprobante_domicilio_2") == "on",
    }


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

        solicitud = {
            "id": str(uuid.uuid4())[:8],
            "fecha": datetime.now().isoformat(timespec="seconds"),
            "down_payment": down_payment,
            "aplicante": _persona_desde_form(request.form, "aplicante"),
            "coaplicante": _persona_desde_form(request.form, "coaplicante"),
        }

        solicitudes = load_solicitudes()
        solicitudes.append(solicitud)
        save_solicitudes(solicitudes)
        return redirect(url_for("solicitud_detalle", solicitud_id=solicitud["id"]))

    return render_template("solicitud_form.html", solicitud=None)


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
        s["aplicante"] = _persona_desde_form(request.form, "aplicante")
        s["coaplicante"] = _persona_desde_form(request.form, "coaplicante")
        save_solicitudes(solicitudes)
        return redirect(url_for("solicitud_detalle", solicitud_id=solicitud_id))

    pendientes, completo = evaluar_requisitos(s)
    modelos = trailers_que_califican(s["down_payment"]) if s["down_payment"] else []
    return render_template(
        "solicitud_form.html", solicitud=s, pendientes=pendientes, completo=completo, modelos=modelos
    )


@app.route("/precalifica", methods=["GET", "POST"])
def precalifica():
    """Formulario público para cookingboxusa.com — pre-calificación sin revisar crédito."""
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

        lead = {
            "id": str(uuid.uuid4())[:8],
            "fecha": datetime.now().isoformat(timespec="seconds"),
            "nombre": nombre,
            "telefono": telefono,
            "email": email,
            "down_payment": down_payment,
            "califica": califica_algo,
        }
        leads = load_leads()
        leads.append(lead)
        save_leads(leads)

        resultado = {"modelos": modelos, "califica_algo": califica_algo}

    return render_template(
        "precalifica.html",
        resultado=resultado,
        nombre=nombre, telefono=telefono, email=email, down_payment=down_payment,
    )


@app.route("/leads")
def leads_lista():
    leads = load_leads()
    leads.sort(key=lambda x: x["fecha"], reverse=True)
    return render_template("leads.html", leads=leads)


@app.route("/precios", methods=["GET", "POST"])
def precios():
    trailers = load_trailers()

    if request.method == "POST":
        for t in trailers:
            campo = f"precio_{t['pies']}"
            valor = request.form.get(campo, "").strip()
            t["precio"] = float(valor) if valor else None
        save_trailers(trailers)
        return redirect(url_for("precios"))

    return render_template("precios.html", trailers=trailers)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
