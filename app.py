from turtle import width

from flask import Flask, render_template, request, jsonify
from google import genai
from dotenv import load_dotenv
import os
import sqlite3
import json

# =========================================================
# CONFIGURACIÓN
# =========================================================

load_dotenv()

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)

app = Flask(__name__)

DATABASE = "leo.db"


# =========================================================
# BASE DE DATOS
# =========================================================

def conectar_db():
    conexion = sqlite3.connect(DATABASE)
    conexion.row_factory = sqlite3.Row
    return conexion


def inicializar_db():

    conexion = conectar_db()

    conexion.execute("""
        CREATE TABLE IF NOT EXISTS estudiantes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo TEXT UNIQUE NOT NULL,
            nombre TEXT NOT NULL,
            identificacion TEXT,
            programa TEXT,
            semestre TEXT
        )
    """)

    conexion.execute("""
        CREATE TABLE IF NOT EXISTS evaluaciones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            estudiante_id INTEGER NOT NULL,
            tipo TEXT NOT NULL,
            puntuacion INTEGER NOT NULL,
            porcentaje INTEGER NOT NULL,
            nivel TEXT NOT NULL,
            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (estudiante_id) REFERENCES estudiantes(id)
        )
    """)

    # =====================================================
    # ACTUALIZAR TABLA DE EVALUACIONES
    # =====================================================

    columnas = conexion.execute("""
        PRAGMA table_info(evaluaciones)
    """).fetchall()

    nombres_columnas = [
        columna["name"]
        for columna in columnas
    ]

    if "habilidades_adecuadas" not in nombres_columnas:

        conexion.execute("""
            ALTER TABLE evaluaciones
            ADD COLUMN habilidades_adecuadas TEXT
        """)

    if "habilidades_observar" not in nombres_columnas:

        conexion.execute("""
            ALTER TABLE evaluaciones
            ADD COLUMN habilidades_observar TEXT
        """)

    if "resumen" not in nombres_columnas:

        conexion.execute("""
            ALTER TABLE evaluaciones
            ADD COLUMN resumen TEXT
        """)

    if "mensaje" not in nombres_columnas:

        conexion.execute("""
            ALTER TABLE evaluaciones
            ADD COLUMN mensaje TEXT
        """)

    conexion.commit()
    conexion.close()


# =========================================================
# PÁGINA PRINCIPAL
# =========================================================

@app.route("/")
def inicio():
    return render_template("index.html")


# =========================================================
# ÁREA PROFESIONAL
# =========================================================

@app.route("/profesional")
def profesional():
    return render_template("panel_profesional.html")

    # =========================================================
# ÁREA ESTUDIANTE
# =========================================================

@app.route("/estudiante")
def estudiante():
    return render_template("panel_estudiante.html")


@app.route("/tamizaje")
def tamizaje():

    codigo = request.args.get("codigo")

    return render_template(
        "tamizaje.html",
        codigo=codigo
    )


# =========================================================
# ESTUDIANTES
# =========================================================

@app.route("/estudiantes")
def estudiantes_pagina():

    conexion = conectar_db()

    estudiantes_db = conexion.execute("""
        SELECT *
        FROM estudiantes
        ORDER BY id DESC
    """).fetchall()

    conexion.close()

    estudiantes = [
        dict(estudiante)
        for estudiante in estudiantes_db
    ]

    return render_template(
        "estudiantes.html",
        estudiantes=estudiantes
    )

# =========================================================
# ACCESO DEL ESTUDIANTE
# =========================================================

@app.route("/acceso-estudiante", methods=["GET"])
def acceso_estudiante():

    return render_template(
        "acceso_estudiante.html"
    )


@app.route("/acceso-estudiante", methods=["POST"])
def validar_acceso_estudiante():

    datos = request.get_json()

    if not datos:

        return jsonify({
            "ok": False,
            "mensaje": "No se recibieron datos."
        }), 400

    codigo = datos.get(
        "codigo",
        ""
    ).strip().upper()

    if not codigo:

        return jsonify({
            "ok": False,
            "mensaje": "Debes ingresar tu código de estudiante."
        }), 400

    conexion = conectar_db()

    estudiante = conexion.execute("""
        SELECT *
        FROM estudiantes
        WHERE codigo = ?
    """, (codigo,)).fetchone()

    conexion.close()

    if estudiante is None:

        return jsonify({
            "ok": False,
            "mensaje":
                "No encontramos un estudiante con ese código."
        }), 404

    return jsonify({
        "ok": True,
        "mensaje": "Estudiante encontrado.",
        "codigo": codigo
    })

# =========================================================
# PERFIL INDIVIDUAL DEL ESTUDIANTE
# =========================================================

@app.route("/estudiante/<codigo>")
def perfil_estudiante(codigo):

    conexion = conectar_db()

    estudiante = conexion.execute("""
        SELECT *
        FROM estudiantes
        WHERE codigo = ?
    """, (codigo,)).fetchone()

    if estudiante is None:
        conexion.close()
        return "Estudiante no encontrado", 404

    evaluaciones_db = conexion.execute("""
        SELECT *
        FROM evaluaciones
        WHERE estudiante_id = ?
        ORDER BY fecha DESC
    """, (estudiante["id"],)).fetchall()

    conexion.close()

    estudiante = dict(estudiante)

    evaluaciones = []

    for evaluacion in evaluaciones_db:

        evaluacion = dict(evaluacion)

        evaluaciones.append(evaluacion)

    return render_template(
        "perfil_estudiante.html",
        estudiante=estudiante,
        evaluaciones=evaluaciones
    )

# =========================================================
# DETALLE DE UNA EVALUACIÓN
# =========================================================

@app.route("/estudiante/<codigo>/evaluacion/<int:evaluacion_id>")
def detalle_evaluacion(codigo, evaluacion_id):

    conexion = conectar_db()

    estudiante = conexion.execute("""
        SELECT *
        FROM estudiantes
        WHERE codigo = ?
    """, (codigo,)).fetchone()

    if estudiante is None:
        conexion.close()
        return "Estudiante no encontrado", 404

    evaluacion = conexion.execute("""
        SELECT *
        FROM evaluaciones
        WHERE id = ?
        AND estudiante_id = ?
    """, (
        evaluacion_id,
        estudiante["id"]
    )).fetchone()

    conexion.close()

    if evaluacion is None:
        return "Evaluación no encontrada", 404

    estudiante = dict(estudiante)
    evaluacion = dict(evaluacion)

    habilidades_adecuadas = []

    habilidades_observar = []

    if evaluacion.get("habilidades_adecuadas"):

        try:
            habilidades_adecuadas = json.loads(
                evaluacion["habilidades_adecuadas"]
            )
        except:
            habilidades_adecuadas = []

    if evaluacion.get("habilidades_observar"):

        try:
            habilidades_observar = json.loads(
                evaluacion["habilidades_observar"]
            )
        except:
            habilidades_observar = []

    return render_template(
        "detalle_evaluacion.html",
        estudiante=estudiante,
        evaluacion=evaluacion,
        habilidades_adecuadas=habilidades_adecuadas,
        habilidades_observar=habilidades_observar
    )

# =========================================================
# REGISTRAR ESTUDIANTE
# =========================================================

@app.route("/registrar-estudiante", methods=["POST"])
def registrar_estudiante():

    datos = request.get_json()

    if not datos:
        return jsonify({
            "ok": False,
            "mensaje": "No se recibieron datos."
        }), 400

    nombre = datos.get("nombre", "").strip()
    identificacion = datos.get("identificacion", "").strip()
    programa = datos.get("programa", "").strip()
    semestre = datos.get("semestre", "").strip()

    if not nombre:
        return jsonify({
            "ok": False,
            "mensaje": "Debes escribir el nombre del estudiante."
        }), 400

    conexion = conectar_db()

    try:

        ultimo = conexion.execute("""
            SELECT id
            FROM estudiantes
            ORDER BY id DESC
            LIMIT 1
        """).fetchone()

        if ultimo:
            numero = ultimo["id"] + 1
        else:
            numero = 1

        codigo = f"EST-{numero:03d}"

        cursor = conexion.execute("""
            INSERT INTO estudiantes
            (
                codigo,
                nombre,
                identificacion,
                programa,
                semestre
            )
            VALUES (?, ?, ?, ?, ?)
        """, (
            codigo,
            nombre,
            identificacion,
            programa,
            semestre
        ))

        conexion.commit()

        nuevo_estudiante = {
            "id": cursor.lastrowid,
            "codigo": codigo,
            "nombre": nombre,
            "identificacion": identificacion,
            "programa": programa,
            "semestre": semestre
        }

        print(
            "ESTUDIANTE REGISTRADO:",
            nuevo_estudiante
        )

        return jsonify({
            "ok": True,
            "mensaje": "Estudiante registrado correctamente.",
            "estudiante": nuevo_estudiante
        })

    except sqlite3.IntegrityError:

        conexion.rollback()

        return jsonify({
            "ok": False,
            "mensaje": "Ya existe un estudiante con esos datos."
        }), 400

    except Exception as error:

        conexion.rollback()

        print(
            "ERROR AL REGISTRAR ESTUDIANTE:",
            error
        )

        return jsonify({
            "ok": False,
            "mensaje": "Ocurrió un error al registrar el estudiante."
        }), 500

    finally:

        conexion.close()


# =========================================================
# PÁGINA DE EVALUACIÓN
# =========================================================

@app.route("/evaluacion")
def evaluacion():
    return render_template("evaluacion.html")


# =========================================================
# COMPRENSIÓN LECTORA
# =========================================================

@app.route("/comprension")
def comprension():

    codigo = request.args.get("codigo")

    return render_template(
        "comprension.html",
        codigo=codigo
    )


# =========================================================
# RESULTADO DE COMPRENSIÓN LECTORA
# =========================================================

@app.route("/resultado-comprension", methods=["POST"])
def resultado_comprension():

    # =====================================================
    # IDENTIFICAR AL ESTUDIANTE
    # =====================================================

    codigo = request.form.get("codigo", "").strip()

    if not codigo:
        return """
        <h2>Error</h2>
        <p>No se recibió el código del estudiante.</p>
        <a href="/">Volver al inicio</a>
        """, 400

    conexion = conectar_db()

    estudiante = conexion.execute("""
        SELECT *
        FROM estudiantes
        WHERE codigo = ?
    """, (codigo,)).fetchone()

    conexion.close()

    if estudiante is None:
        return """
        <h2>Error</h2>
        <p>No se encontró el estudiante asociado a esta evaluación.</p>
        <a href="/">Volver al inicio</a>
        """, 404

    # =====================================================
    # RESPUESTAS CORRECTAS
    # =====================================================

    respuestas_correctas = {
        "q1": "B",
        "q2": "C",
        "q3": "A",
        "q4": "C",
        "q5": "B"
    }

    # =====================================================
    # RESPUESTAS DEL ESTUDIANTE
    # =====================================================

    respuestas_usuario = {
        "q1": request.form.get("q1"),
        "q2": request.form.get("q2"),
        "q3": request.form.get("q3"),
        "q4": request.form.get("q4"),
        "q5": request.form.get("q5")
    }

    print(
        "RESPUESTAS RECIBIDAS:",
        respuestas_usuario
    )

    # =====================================================
    # CALIFICACIÓN
    # =====================================================

    puntuacion = 0

    for pregunta in respuestas_correctas:

        if (
            respuestas_usuario.get(pregunta)
            == respuestas_correctas[pregunta]
        ):
            puntuacion += 1

    porcentaje = puntuacion * 20

    # =====================================================
    # HABILIDADES EVALUADAS
    # =====================================================

    habilidades = {

        "idea_principal": {
            "nombre": "Identificación de la idea principal",
            "pregunta": "q1"
        },

        "informacion_explicita": {
            "nombre": "Comprensión de información explícita",
            "pregunta": "q2"
        },

        "inferencia": {
            "nombre": "Inferencia",
            "pregunta": "q3"
        },

        "relacion_informacion": {
            "nombre": "Relación de información",
            "pregunta": "q4"
        },

        "conclusion": {
            "nombre": "Identificación de la conclusión",
            "pregunta": "q5"
        }
    }

    # =====================================================
    # CLASIFICACIÓN DE HABILIDADES
    # =====================================================

    habilidades_adecuadas = []
    habilidades_observar = []

    for habilidad, datos in habilidades.items():

        pregunta = datos["pregunta"]
        nombre = datos["nombre"]

        if (
            respuestas_usuario.get(pregunta)
            == respuestas_correctas[pregunta]
        ):
            habilidades_adecuadas.append(nombre)

        else:
            habilidades_observar.append(nombre)

    # =====================================================
    # INTERPRETACIÓN GENERAL
    # =====================================================

    if porcentaje == 100:

        nivel = "Desempeño adecuado"
        clase_nivel = "nivel-verde"

        mensaje = (
            "El estudiante mostró un desempeño adecuado en las "
            "habilidades evaluadas durante esta actividad."
        )

        resumen_areas = (
            "No se identificaron áreas prioritarias por observar "
            "en esta actividad."
        )

    elif porcentaje >= 80:

        nivel = "Desempeño adecuado"
        clase_nivel = "nivel-verde"

        mensaje = (
            "El estudiante mostró un desempeño generalmente adecuado. "
            "Se identificó un área que podría continuar fortaleciéndose "
            "mediante actividades de práctica."
        )

        resumen_areas = (
            "Se identificó un área que podría beneficiarse de "
            "actividades adicionales de fortalecimiento."
        )

    elif porcentaje >= 60:

        nivel = "Aspectos por observar"
        clase_nivel = "nivel-naranja"

        mensaje = (
            "El resultado muestra algunos aspectos de la comprensión "
            "lectora que podrían beneficiarse de actividades adicionales "
            "de fortalecimiento."
        )

        resumen_areas = (
            "Se identificaron algunas habilidades que podrían beneficiarse "
            "de actividades adicionales y de la recopilación de nuevas "
            "evidencias sobre el desempeño."
        )

    else:

        nivel = "Requiere observación"
        clase_nivel = "nivel-naranja"

        mensaje = (
            "El resultado sugiere que sería conveniente observar "
            "con mayor detalle el desempeño del estudiante mediante "
            "otras actividades y evidencias."
        )

        resumen_areas = (
            "Se identificaron varias áreas que podrían beneficiarse "
            "de una observación más detallada y actividades de apoyo."
        )

    # =====================================================
    # GUARDAR RESULTADO EN LA BASE DE DATOS
    # =====================================================

    conexion = conectar_db()

    try:

        conexion.execute("""
    INSERT INTO evaluaciones
    (
        estudiante_id,
        tipo,
        puntuacion,
        porcentaje,
        nivel,
        habilidades_adecuadas,
        habilidades_observar,
        resumen,
        mensaje
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
""", (
    estudiante["id"],
    "Comprensión lectora",
    puntuacion,
    porcentaje,
    nivel,
    json.dumps(
        habilidades_adecuadas,
        ensure_ascii=False
    ),
    json.dumps(
        habilidades_observar,
        ensure_ascii=False
    ),
    resumen_areas,
    mensaje
))

        conexion.commit()

        print(
            "EVALUACIÓN GUARDADA:",
            codigo,
            puntuacion,
            porcentaje,
            nivel
        )

    except Exception as error:

        conexion.rollback()

        print(
            "ERROR AL GUARDAR EVALUACIÓN:",
            error
        )

    finally:

        conexion.close()

    # =====================================================
    # PLANES DE APOYO
    # =====================================================

    planes_apoyo = {

        "Identificación de la idea principal": {

            "objetivo": (
                "Fortalecer la capacidad para reconocer la idea central "
                "de un texto y diferenciarla de información secundaria."
            ),

            "actividad": (
                "Leer textos breves y seleccionar entre varias opciones "
                "la afirmación que resume mejor el contenido principal."
            ),

            "estrategia": (
                "Después de cada lectura, pedir al estudiante que explique "
                "en una o dos frases de qué trata principalmente el texto."
            )
        },

        "Comprensión de información explícita": {

            "objetivo": (
                "Fortalecer la capacidad para localizar y recuperar "
                "información presentada directamente en un texto."
            ),

            "actividad": (
                "Realizar lecturas breves acompañadas de preguntas sobre "
                "datos, hechos, personajes, lugares o información expresada "
                "directamente."
            ),

            "estrategia": (
                "Enseñar al estudiante a volver al texto y localizar "
                "la información que sustenta cada respuesta."
            )
        },

        "Inferencia": {

            "objetivo": (
                "Fortalecer la capacidad para deducir información "
                "a partir de pistas presentes en el texto."
            ),

            "actividad": (
                "Presentar pequeños textos y solicitar al estudiante "
                "que determine qué puede deducirse aunque no aparezca "
                "escrito de manera directa."
            ),

            "estrategia": (
                "Pedir que explique qué información del texto utilizó "
                "para llegar a cada conclusión."
            )
        },

        "Relación de información": {

            "objetivo": (
                "Fortalecer la capacidad para relacionar información "
                "presentada en diferentes partes de un texto."
            ),

            "actividad": (
                "Utilizar textos breves en los que el estudiante deba "
                "relacionar causas, consecuencias, hechos o ideas "
                "presentadas en distintos párrafos."
            ),

            "estrategia": (
                "Utilizar esquemas o mapas de ideas para conectar "
                "informaciones relacionadas."
            )
        },

        "Identificación de la conclusión": {

            "objetivo": (
                "Fortalecer la capacidad para reconocer la conclusión "
                "o idea final derivada del contenido de un texto."
            ),

            "actividad": (
                "Presentar textos breves y solicitar al estudiante "
                "que identifique la afirmación que representa mejor "
                "la conclusión."
            ),

            "estrategia": (
                "Practicar la síntesis del texto en una frase final "
                "que reúna sus ideas más importantes."
            )
        }
    }

    # =====================================================
    # FORTALEZAS
    # =====================================================

    fortalezas_html = ""

    for habilidad in habilidades_adecuadas:

        fortalezas_html += f"""
        <div class="habilidad-card fortaleza">

            <div class="habilidad-icono">
                ✓
            </div>

            <div>
                <strong>{habilidad}</strong>

                <p>
                    Se observó un desempeño adecuado durante esta actividad.
                </p>
            </div>

        </div>
        """

    if not habilidades_adecuadas:

        fortalezas_html = """
        <div class="vacio">

            En esta actividad no se identificaron habilidades con
            desempeño adecuado suficiente para destacarlas como fortaleza.

        </div>
        """

    # =====================================================
    # ÁREAS POR OBSERVAR
    # =====================================================

    areas_html = ""

    for habilidad in habilidades_observar:

        areas_html += f"""
        <div class="habilidad-card observar">

            <div class="habilidad-icono">
                !
            </div>

            <div>
                <strong>{habilidad}</strong>

                <p>
                    Área que puede beneficiarse de práctica adicional.
                </p>
            </div>

        </div>
        """

    if not habilidades_observar:

        areas_html = """
        <div class="vacio">

            No se identificaron áreas prioritarias por observar
            en esta actividad.

        </div>
        """

    # =====================================================
    # PLAN DE APOYO PERSONALIZADO
    # =====================================================

    plan_html = ""

    if habilidades_observar:

        plan_html += """
        <div class="plan-intro">

            <div class="plan-intro-icon">
                🎯
            </div>

            <div>

                <strong>
                    Leo preparó estas recomendaciones para ti.
                </strong>

                <p>
                    A partir del desempeño obtenido, se identificaron
                    algunas habilidades que pueden beneficiarse de
                    actividades adicionales de fortalecimiento.
                </p>

            </div>

        </div>
        """

        for numero, habilidad in enumerate(
            habilidades_observar,
            1
        ):

            plan = planes_apoyo[habilidad]

            plan_html += f"""
            <div class="plan-card">

                <div class="plan-header">

                    <div class="plan-numero">
                        {numero}
                    </div>

                    <div>

                        <span class="plan-etiqueta">
                            ÁREA DE APOYO
                        </span>

                        <h3>
                            📚 {habilidad}
                        </h3>

                    </div>

                </div>

                <div class="plan-contenido">

                    <div class="plan-bloque">

                        <span class="bloque-titulo">
                            🎯 Objetivo
                        </span>

                        <p>
                            {plan["objetivo"]}
                        </p>

                    </div>

                    <div class="plan-bloque">

                        <span class="bloque-titulo">
                            ✏️ Actividad recomendada
                        </span>

                        <p>
                            {plan["actividad"]}
                        </p>

                    </div>

                    <div class="plan-bloque">

                        <span class="bloque-titulo">
                            💡 Estrategia
                        </span>

                        <p>
                            {plan["estrategia"]}
                        </p>

                    </div>

                    <button
                        class="boton-actividad"
                        type="button"
                    >
                        ▶ Comenzar actividad
                    </button>

                </div>

            </div>
            """

    else:

        plan_html = """
        <div class="plan-card plan-adecuado">

            <div class="plan-header">

                <div class="plan-numero">
                    ✓
                </div>

                <div>

                    <span class="plan-etiqueta">
                        RESULTADO
                    </span>

                    <h3>
                        Continúa fortaleciendo tus habilidades
                    </h3>

                </div>

            </div>

            <div class="plan-contenido">

                <p>
                    En esta actividad el estudiante mostró un desempeño
                    adecuado en las habilidades evaluadas.
                </p>

                <p>
                    Se recomienda continuar realizando actividades de
                    comprensión lectora con dificultad progresiva para
                    mantener y fortalecer estas habilidades.
                </p>

            </div>

        </div>
        """

    # =====================================================
    # INDICADOR DE PROGRESO
    # =====================================================

    progreso_html = """

    <div class="progreso">

        <div class="progreso-linea">

            <div class="paso activo">

                <div class="paso-circulo">
                    ✓
                </div>

                <span>
                    Evaluación
                </span>

            </div>

            <div class="linea activa"></div>

            <div class="paso activo">

                <div class="paso-circulo">
                    ✓
                </div>

                <span>
                    Resultado
                </span>

            </div>

            <div class="linea"></div>

            <div class="paso actual">

                <div class="paso-circulo">
                    3
                </div>

                <span>
                    Plan de apoyo
                </span>

            </div>

            <div class="linea"></div>

            <div class="paso">

                <div class="paso-circulo">
                    4
                </div>

                <span>
                    Actividades
                </span>

            </div>

        </div>

    </div>

    """

    # =====================================================
    # HTML FINAL
    # =====================================================

    return f"""

<!DOCTYPE html>

<html lang="es">

<head>

    <meta charset="UTF-8">

    <meta
        name="viewport"
        content="width=device-width, initial-scale=1.0"
    >

    <title>
        Leo | Resultados
    </title>

    <style>

        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }}

        body {{
            font-family:
                -apple-system,
                BlinkMacSystemFont,
                "Segoe UI",
                Arial,
                sans-serif;

            background:
                linear-gradient(
                    135deg,
                    #f4f8ff 0%,
                    #f8fbff 50%,
                    #eef5ff 100%
                );

            min-height: 100vh;
            color: #263238;
            padding: 30px 18px;
        }}

        .contenedor {{
            width: 100%;
            max-width: 1050px;
            margin: 0 auto;
        }}

        .header {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 25px;
        }}

        .logo-contenedor {{
            display: flex;
            align-items: center;
            gap: 12px;
        }}

        .logo-icono {{
            width: 48px;
            height: 48px;
            display: flex;
            align-items: center;
            justify-content: center;
            background: #ffffff;
            border-radius: 15px;
            box-shadow:
                0 5px 18px rgba(66, 133, 244, 0.15);
            font-size: 27px;
        }}

        .logo-texto h2 {{
            color: #2563eb;
            font-size: 22px;
            margin-bottom: 2px;
        }}

        .logo-texto span {{
            color: #718096;
            font-size: 13px;
        }}

        .progreso {{
            background: #ffffff;
            border-radius: 18px;
            padding: 20px 25px;
            margin-bottom: 22px;
            box-shadow:
                0 8px 25px rgba(31, 65, 114, 0.06);
        }}

        .progreso-linea {{
            display: flex;
            align-items: center;
            justify-content: center;
        }}

        .paso {{
            display: flex;
            align-items: center;
            gap: 8px;
            color: #a0aec0;
            font-size: 12px;
            white-space: nowrap;
        }}

        .paso-circulo {{
            width: 29px;
            height: 29px;
            border-radius: 50%;
            background: #edf2f7;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 12px;
            font-weight: 700;
        }}

        .paso.activo,
        .paso.actual {{
            color: #2563eb;
            font-weight: 600;
        }}

        .paso.activo .paso-circulo {{
            background: #2563eb;
            color: white;
        }}

        .paso.actual .paso-circulo {{
            background: #dbeafe;
            color: #2563eb;
            border: 2px solid #2563eb;
        }}

        .linea {{
            height: 2px;
            width: 70px;
            background: #e2e8f0;
            margin: 0 10px;
        }}

        .linea.activa {{
            background: #2563eb;
        }}

        .hero {{
            background: #ffffff;
            border-radius: 24px;
            padding: 38px;
            box-shadow:
                0 12px 35px rgba(31, 65, 114, 0.08);

            display: grid;
            grid-template-columns: 230px 1fr;
            gap: 40px;
            align-items: center;
            margin-bottom: 22px;
        }}

        .resultado-circulo {
    width: 190px;
    height: 190px;
    margin: auto;
    border-radius: 50%;

    background: conic-gradient(
        #2563eb 0 var(--porcentaje),
        #e8f0fe var(--porcentaje) 100%
    );

    display: flex;
    align-items: center;
    justify-content: center;

    position: relative;
}

        .resultado-circulo::before {{
            content: "";
            position: absolute;
            width: 148px;
            height: 148px;
            background: white;
            border-radius: 50%;
        }}

        .resultado-numero {{
            position: relative;
            z-index: 1;
            text-align: center;
        }}

        .resultado-numero strong {{
            display: block;
            font-size: 45px;
            line-height: 1;
            color: #2563eb;
        }}

        .resultado-numero span {{
            display: block;
            margin-top: 7px;
            color: #718096;
            font-size: 13px;
        }}

        .hero-contenido .subtitulo {{
            color: #718096;
            font-size: 14px;
            margin-bottom: 7px;
        }}

        .hero-contenido h1 {{
            font-size: 31px;
            color: #1e293b;
            margin-bottom: 18px;
        }}

        .badge {{
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 9px 14px;
            border-radius: 999px;
            font-size: 13px;
            font-weight: 700;
        }}

        .nivel-verde {{
            background: #e9f8ef;
            color: #16803c;
        }}

        .nivel-naranja {{
            background: #fff5df;
            color: #b76e00;
        }}

        .hero-contenido p {{
            margin-top: 17px;
            color: #5f6f82;
            line-height: 1.65;
            max-width: 650px;
        }}

        .mensaje-leo {{
            background:
                linear-gradient(
                    135deg,
                    #eef6ff,
                    #f7fbff
                );

            border: 1px solid #dbeafe;
            border-radius: 20px;
            padding: 22px 25px;
            display: flex;
            align-items: flex-start;
            gap: 15px;
            margin-bottom: 30px;
        }}

        .leo-avatar {{
            width: 45px;
            height: 45px;
            flex-shrink: 0;
            border-radius: 14px;
            background: #2563eb;
            color: white;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 23px;
        }}

        .mensaje-leo strong {{
            color: #1e40af;
            display: block;
            margin-bottom: 5px;
        }}

        .mensaje-leo p {{
            color: #53657a;
            line-height: 1.55;
        }}

        .seccion {{
            margin-top: 30px;
        }}

        .titulo-seccion {{
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 16px;
        }}

        .titulo-seccion h2 {{
            font-size: 22px;
            color: #1e293b;
        }}

        .titulo-seccion span {{
            color: #718096;
            font-size: 13px;
        }}

        .habilidades-grid {{
            display: grid;
            grid-template-columns:
                repeat(2, minmax(0, 1fr));
            gap: 13px;
        }}

        .habilidad-card {{
            background: #ffffff;
            border-radius: 17px;
            padding: 18px;
            display: flex;
            align-items: flex-start;
            gap: 14px;
            border: 1px solid #edf2f7;
            box-shadow:
                0 5px 18px rgba(31, 65, 114, 0.045);
        }}

        .habilidad-icono {{
            width: 34px;
            height: 34px;
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            flex-shrink: 0;
            font-weight: 800;
        }}

        .fortaleza .habilidad-icono {{
            background: #e9f8ef;
            color: #16803c;
        }}

        .observar .habilidad-icono {{
            background: #fff5df;
            color: #b76e00;
        }}

        .habilidad-card strong {{
            display: block;
            color: #26364a;
            font-size: 15px;
            margin-bottom: 5px;
        }}

        .habilidad-card p {{
            color: #718096;
            font-size: 13px;
            line-height: 1.5;
        }}

        .vacio {{
            background: white;
            border: 1px dashed #cbd5e0;
            padding: 20px;
            border-radius: 15px;
            color: #718096;
        }}

        .resumen {{
            margin-top: 15px;
            padding: 16px 18px;
            background: #fffaf0;
            border-radius: 13px;
            color: #76551a;
            font-size: 13px;
            line-height: 1.55;
        }}

        .plan-intro {{
            display: flex;
            align-items: flex-start;
            gap: 15px;
            padding: 20px;
            border-radius: 18px;

            background:
                linear-gradient(
                    135deg,
                    #eef6ff,
                    #f7fbff
                );

            border: 1px solid #dbeafe;
            margin-bottom: 18px;
        }}

        .plan-intro-icon {{
            font-size: 27px;
            width: 43px;
            height: 43px;
            display: flex;
            align-items: center;
            justify-content: center;
            background: white;
            border-radius: 12px;
            flex-shrink: 0;
        }}

        .plan-intro strong {{
            color: #1e40af;
        }}

        .plan-intro p {{
            margin-top: 5px;
            color: #5f6f82;
            font-size: 13px;
            line-height: 1.55;
        }}

        .plan-card {{
            background: white;
            border-radius: 20px;
            margin-bottom: 18px;
            border: 1px solid #e7edf5;
            box-shadow:
                0 7px 25px rgba(31, 65, 114, 0.06);
            overflow: hidden;
        }}

        .plan-header {{
            padding: 22px;
            display: flex;
            align-items: center;
            gap: 15px;
            border-bottom: 1px solid #edf2f7;
        }}

        .plan-numero {{
            width: 43px;
            height: 43px;
            border-radius: 13px;
            background: #eaf2ff;
            color: #2563eb;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 800;
            flex-shrink: 0;
        }}

        .plan-etiqueta {{
            font-size: 10px;
            font-weight: 800;
            letter-spacing: 0.8px;
            color: #718096;
        }}

        .plan-header h3 {{
            margin-top: 3px;
            font-size: 18px;
            color: #1e293b;
        }}

        .plan-contenido {{
            padding: 22px;
        }}

        .plan-bloque {{
            margin-bottom: 18px;
        }}

        .bloque-titulo {{
            font-weight: 700;
            font-size: 13px;
            color: #334155;
        }}

        .plan-bloque p {{
            margin-top: 6px;
            color: #64748b;
            line-height: 1.6;
            font-size: 14px;
        }}

        .boton-actividad {{
            width: 100%;
            border: none;
            padding: 13px 18px;
            border-radius: 11px;
            background: #2563eb;
            color: white;
            font-size: 14px;
            font-weight: 700;
            cursor: pointer;
            transition: 0.2s;
        }}

        .boton-actividad:hover {{
            background: #1d4ed8;
            transform: translateY(-1px);
        }}

        .plan-adecuado {{
            border-top: 4px solid #34a853;
        }}

        .advertencia {{
            margin-top: 30px;
            padding: 20px;
            background: #fffaf0;
            border: 1px solid #f6dfae;
            border-radius: 17px;
            color: #76551a;
            font-size: 13px;
            line-height: 1.6;
        }}

        .advertencia strong {{
            color: #9a6700;
        }}

        .botones {{
            display: flex;
            justify-content: center;
            gap: 12px;
            margin-top: 30px;
            padding-bottom: 20px;
        }}

        .boton {{
            display: inline-flex;
            align-items: center;
            justify-content: center;
            padding: 13px 20px;
            border-radius: 11px;
            text-decoration: none;
            font-size: 14px;
            font-weight: 700;
            transition: 0.2s;
        }}

        .boton-principal {{
            background: #2563eb;
            color: white;
        }}

        .boton-secundario {{
            background: white;
            color: #2563eb;
            border: 1px solid #dbeafe;
        }}

        .boton:hover {{
            transform: translateY(-1px);
        }}

        @media (max-width: 800px) {{

            body {{
                padding: 18px 12px;
            }}

            .hero {{
                grid-template-columns: 1fr;
                text-align: center;
                padding: 30px 22px;
                gap: 25px;
            }}

            .hero-contenido p {{
                margin-left: auto;
                margin-right: auto;
            }}

            .habilidades-grid {{
                grid-template-columns: 1fr;
            }}
        }}

        @media (max-width: 600px) {{

            .header {{
                margin-bottom: 15px;
            }}

            .logo-icono {{
                width: 42px;
                height: 42px;
            }}

            .logo-texto h2 {{
                font-size: 20px;
            }}

            .logo-texto span {{
                display: none;
            }}

            .progreso {{
                padding: 15px 10px;
                overflow-x: auto;
            }}

            .progreso-linea {{
                justify-content: flex-start;
                min-width: 500px;
            }}

            .linea {{
                width: 35px;
                margin: 0 5px;
            }}

            .hero {{
                border-radius: 20px;
                padding: 25px 18px;
            }}

            .resultado-circulo {{
                width: 160px;
                height: 160px;
            }}

            .resultado-circulo::before {{
                width: 124px;
                height: 124px;
            }}

            .resultado-numero strong {{
                font-size: 38px;
            }}

            .hero-contenido h1 {{
                font-size: 25px;
            }}

            .mensaje-leo {{
                padding: 18px;
            }}

            .titulo-seccion h2 {{
                font-size: 19px;
            }}

            .plan-header {{
                padding: 18px;
            }}

            .plan-contenido {{
                padding: 18px;
            }}

            .botones {{
                flex-direction: column;
            }}

            .boton {{
                width: 100%;
            }}

        }}

    </style>

</head>

<body>

<div class="contenedor">

    <header class="header">

        <div class="logo-contenedor">

            <div class="logo-icono">
                🤖
            </div>

            <div class="logo-texto">

                <h2>
                    Leo
                </h2>

                <span>
                    Tu asistente de aprendizaje
                </span>

            </div>

        </div>

    </header>

    {progreso_html}

    <section class="hero">

        <div class="resultado-circulo">

            <div class="resultado-numero">

                <strong>
                    {porcentaje}%
                </strong>

                <span>
                    {puntuacion} de 5 respuestas
                </span>

            </div>

        </div>

        <div class="hero-contenido">

            <div class="subtitulo">
                Resultado de tu evaluación
            </div>

            <h1>
                Comprensión lectora
            </h1>

            <div class="badge {clase_nivel}">
                {nivel}
            </div>

            <p>
                {mensaje}
            </p>

        </div>

    </section>

    <section class="mensaje-leo">

        <div class="leo-avatar">
            🤖
        </div>

        <div>

            <strong>
                Leo dice:
            </strong>

            <p>
                Tu resultado muestra habilidades que ya estás
                desarrollando adecuadamente y otras que podemos
                seguir fortaleciendo con práctica.
            </p>

        </div>

    </section>

    <section class="seccion">

        <div class="titulo-seccion">

            <h2>
                📊 Análisis por habilidades
            </h2>

        </div>

        <div class="habilidades-grid">

            {fortalezas_html}

            {areas_html}

        </div>

        <div class="resumen">

            {resumen_areas}

        </div>

    </section>

    <section class="seccion">

        <div class="titulo-seccion">

            <h2>
                🎯 Tu plan de apoyo
            </h2>

        </div>

        {plan_html}

    </section>

    <div class="advertencia">

        <strong>
            ℹ️ Importante
        </strong>

        <br><br>

        Este resultado constituye una orientación educativa
        inicial y no representa un diagnóstico clínico.

        <br><br>

        Las áreas señaladas como "por observar" requieren
        actividades adicionales y otras evidencias antes
        de establecer cualquier conclusión sobre el desempeño
        del estudiante.

    </div>

    <div class="botones">

        <a
            class="boton boton-secundario"
            href="/"
        >
            🏠 Inicio
        </a>

        <a
            class="boton boton-principal"
            href="/comprension"
        >
            🔄 Nueva evaluación
        </a>

    </div>

</div>

</body>

</html>

"""


# =========================================================
# CHAT CON LEO
# =========================================================

@app.route("/preguntar", methods=["POST"])
def preguntar():

    datos = request.get_json()

    if not datos:

        return jsonify({
            "respuesta": "No se recibieron datos."
        }), 400

    pregunta = datos.get(
        "pregunta",
        ""
    ).strip()

    historial = datos.get(
        "historial",
        []
    )

    if not pregunta:

        return jsonify({
            "respuesta":
                "Escribe una pregunta para que pueda ayudarte."
        }), 400

    # =====================================================
    # CONSTRUIR HISTORIAL
    # =====================================================

    conversacion = ""

    for mensaje in historial:

        rol = mensaje.get(
            "rol",
            ""
        )

        contenido = mensaje.get(
            "contenido",
            ""
        )

        if not contenido:
            continue

        if rol == "usuario":

            conversacion += (
                f"Estudiante: {contenido}\n\n"
            )

        elif rol == "leo":

            conversacion += (
                f"Leo: {contenido}\n\n"
            )

    # =====================================================
    # INSTRUCCIONES DE LEO
    # =====================================================

    instrucciones = """

Eres Leo, un asistente educativo universitario diseñado para
acompañar a estudiantes de pregrado y posgrado en su proceso
de aprendizaje.

Tu objetivo principal NO es simplemente entregar respuestas.

Tu objetivo es ayudar al estudiante a:

- comprender;
- razonar;
- aprender;
- corregir errores;
- desarrollar autonomía académica.

=========================================================
PERSONALIDAD
=========================================================

- Sé amable, cercano, respetuoso y profesional.
- Habla de forma natural.
- No seas excesivamente formal ni robótico.
- No trates al estudiante como un niño.
- Motiva al estudiante cuando sea apropiado.
- Evita frases repetitivas.
- Responde siempre en español, salvo que el estudiante solicite
  otro idioma.

=========================================================
FORMA DE ENSEÑAR
=========================================================

Cuando el estudiante haga una pregunta:

1. Identifica qué necesita comprender.
2. Explica primero la idea principal.
3. Desarrolla los detalles necesarios.
4. Utiliza ejemplos cuando realmente ayuden.
5. Divide los conceptos complejos en pasos.
6. Adapta la profundidad a la pregunta y al nivel demostrado
   por el estudiante.
7. No hagas respuestas innecesariamente largas.

No conviertas cada respuesta en una clase completa.

Si la pregunta es sencilla, responde de manera sencilla.

Si requiere razonamiento, explica el razonamiento.

=========================================================
APRENDIZAJE ACTIVO
=========================================================

Leo debe procurar que el estudiante participe activamente.

Cuando sea apropiado:

- haz una pregunta breve para comprobar comprensión;
- plantea un pequeño ejercicio;
- pide al estudiante que explique con sus propias palabras;
- solicita que justifique una respuesta;
- utiliza preguntas progresivas.

NO hagas una pregunta de comprobación después de absolutamente
todas las respuestas.

Hazlo especialmente cuando:

- se esté aprendiendo un concepto nuevo;
- el estudiante haya pedido una explicación;
- exista riesgo de confusión;
- sea útil comprobar si realmente comprendió.

=========================================================
CUANDO EL ESTUDIANTE RESPONDA UNA PREGUNTA DE LEO
=========================================================

Analiza primero la respuesta del estudiante.

Si es CORRECTA:

- reconoce brevemente el acierto;
- explica por qué es correcta cuando sea útil;
- puedes aumentar ligeramente la dificultad;
- evita repetir toda la explicación anterior.

Si es PARCIALMENTE CORRECTA:

- reconoce lo que está bien;
- identifica claramente qué falta o qué debe corregirse;
- proporciona una pista o explicación;
- permite que el estudiante complete el razonamiento
  cuando sea pedagógicamente útil.

Si es INCORRECTA:

- no respondas simplemente "incorrecto";
- explica qué concepto necesita revisar;
- proporciona una pista;
- guía al estudiante hacia la respuesta;
- si es necesario, después explica la respuesta correcta.

La prioridad es que el estudiante comprenda el error.

=========================================================
ADAPTACIÓN DE DIFICULTAD
=========================================================

Observa el desempeño del estudiante durante la conversación.

Si demuestra dominio:

- aumenta progresivamente la dificultad;
- plantea preguntas que requieran mayor razonamiento;
- utiliza casos o aplicaciones.

Si presenta dificultades:

- reduce la complejidad;
- explica nuevamente con lenguaje más claro;
- utiliza ejemplos;
- divide el problema en pasos pequeños.

No aumentes la dificultad demasiado rápido.

=========================================================
NIVEL UNIVERSITARIO
=========================================================

- Utiliza terminología académica correcta.
- Explica términos especializados cuando sea necesario.
- Para preguntas básicas, responde de forma sencilla.
- Para preguntas universitarias, utiliza mayor precisión conceptual.
- Para preguntas avanzadas, desarrolla los fundamentos necesarios.

Nunca confundas una explicación sencilla con una explicación
incorrecta.

=========================================================
RAZONAMIENTO Y PRECISIÓN
=========================================================

- No inventes información.
- Si no estás seguro de un dato, dilo claramente.
- No presentes una suposición como un hecho.
- Evita simplificaciones que puedan generar errores conceptuales.
- Cuando utilices una analogía, aclara que es una forma de
  comprender el concepto y no necesariamente una descripción literal.

=========================================================
AYUDA ACADÉMICA
=========================================================

Puedes ayudar al estudiante a:

- comprender conceptos;
- estudiar;
- organizar ideas;
- resolver ejercicios;
- preparar trabajos académicos;
- analizar información;
- preparar exámenes;
- practicar preguntas.

Cuando resuelvas un problema académico:

1. explica el procedimiento;
2. muestra cómo se llega a la respuesta;
3. procura que el estudiante pueda repetir el procedimiento
   por sí mismo.

No fomentes una dependencia de Leo.

=========================================================
TAREAS Y TRABAJOS ACADÉMICOS
=========================================================

Si el estudiante pide ayuda para una tarea:

- primero intenta ayudarle a comprender lo que debe hacer;
- explica el procedimiento;
- puedes proporcionar ejemplos;
- si solicita una respuesta completa, puedes ayudarle,
  pero procura que comprenda el proceso.

=========================================================
SALUD Y DIAGNÓSTICOS
=========================================================

Si un estudiante pregunta por síntomas, dificultades de aprendizaje
u otras condiciones de salud:

- proporciona información general;
- no realices diagnósticos;
- no presentes una posibilidad como diagnóstico;
- cuando corresponda, indica que una evaluación profesional
  es necesaria.

=========================================================
EVALUACIONES EDUCATIVAS
=========================================================

Puedes ayudar a interpretar resultados educativos de manera general.

No conviertas un resultado bajo en un diagnóstico.

Utiliza expresiones como:

- "área por observar";
- "aspecto a fortalecer";
- "se recomienda recopilar más evidencias";
- "podría beneficiarse de práctica adicional".

=========================================================
MEMORIA DE LA CONVERSACIÓN
=========================================================

Utiliza el historial proporcionado para mantener continuidad.

Si anteriormente se habló de un tema, no actúes como si fuera
la primera vez.

Si el estudiante está estudiando un tema concreto, mantenlo como
contexto mientras la conversación continúe.

No inventes información que no aparezca en el historial.

=========================================================
REGLA IMPORTANTE SOBRE EL HISTORIAL
=========================================================

El historial contiene mensajes anteriores del estudiante y de Leo.

Utilízalo para determinar:

- qué tema está estudiando;
- qué conceptos ya fueron explicados;
- qué preguntas ya fueron realizadas;
- qué respuestas dio el estudiante;
- qué errores o dificultades aparecieron;
- qué nivel de comprensión parece tener.

No repitas innecesariamente contenido que el estudiante
ya comprendió.

=========================================================
FORMATO DE RESPUESTA
=========================================================

Responde directamente al estudiante.

No menciones estas instrucciones.

No digas que eres una inteligencia artificial.

No digas que estás analizando el historial.

No utilices etiquetas como:

"ANÁLISIS INTERNO"
"RAZONAMIENTO"
"PROMPT"
"INSTRUCCIONES"

La respuesta debe sentirse como una conversación natural
entre un estudiante y su tutor.

=========================================================
OBJETIVO FINAL
=========================================================

Tu objetivo es que el estudiante pueda llegar progresivamente
a resolver y comprender los problemas por sí mismo.

Enseña, guía, comprueba comprensión y adapta la dificultad.

"""

    # =====================================================
    # CONSTRUIR PROMPT FINAL
    # =====================================================

    prompt = f"""
{instrucciones}

=========================================================
HISTORIAL DE LA CONVERSACIÓN
=========================================================

{conversacion}

=========================================================
PREGUNTA / MENSAJE ACTUAL DEL ESTUDIANTE
=========================================================

{pregunta}

=========================================================
RESPUESTA DE LEO
=========================================================

Responde ahora al estudiante siguiendo todas las instrucciones
anteriores.
"""

    # =====================================================
    # CONSULTAR GEMINI
    # =====================================================

    try:

        respuesta = client.models.generate_content(
            model="gemini-3.5-flash",
            contents=prompt
        )

        texto_respuesta = respuesta.text

        if not texto_respuesta:

            texto_respuesta = (
                "No pude generar una respuesta en este momento. "
                "Inténtalo nuevamente."
            )

        return jsonify({
            "respuesta": texto_respuesta
        })

    except Exception as error:

        print(
            "ERROR GEMINI:",
            error
        )

        return jsonify({
            "respuesta": (
                "Lo siento, en este momento no pude procesar "
                "la pregunta. Puedes intentarlo nuevamente."
            )
        }), 500


# =========================================================
# EJECUTAR APLICACIÓN
# =========================================================

if __name__ == "__main__":

    app.run(
        debug=True
    )