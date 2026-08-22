from flask import Flask, render_template, request, jsonify, session, redirect, url_for
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

    # =====================================================
    # CREAR TABLA ESTUDIANTES
    # =====================================================

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


    # =====================================================
    # AGREGAR NUEVAS COLUMNAS A ESTUDIANTES
    # =====================================================

    columnas_estudiantes = {

        "edad": "INTEGER",

        "sexo": "TEXT",

        "ciudad": "TEXT",

        "grupo": "TEXT",

        "tipo_minoria": "TEXT",

        "otro_grupo": "TEXT",

        "tipo_estudio": "TEXT",

        "modalidad": "TEXT",

        "universidad_anterior": "TEXT",

        "consentimiento": "INTEGER DEFAULT 0"

    }


    columnas_existentes = [
        columna["name"]
        for columna in conexion.execute(
            "PRAGMA table_info(estudiantes)"
        ).fetchall()
    ]


    for nombre_columna, tipo_columna in columnas_estudiantes.items():

        if nombre_columna not in columnas_existentes:

            conexion.execute(
                f"""
                ALTER TABLE estudiantes
                ADD COLUMN {nombre_columna} {tipo_columna}
                """
            )


    # =====================================================
    # CREAR TABLA EVALUACIONES
    # =====================================================

    conexion.execute("""
        CREATE TABLE IF NOT EXISTS evaluaciones (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            estudiante_id INTEGER NOT NULL,

            tipo TEXT NOT NULL,

            puntuacion INTEGER NOT NULL,

            porcentaje INTEGER NOT NULL,

            nivel TEXT NOT NULL,

            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (estudiante_id)
            REFERENCES estudiantes(id)

        )
    """)


    # =====================================================
    # ACTUALIZAR TABLA EVALUACIONES
    # =====================================================

    columnas_evaluaciones = [
        columna["name"]
        for columna in conexion.execute(
            "PRAGMA table_info(evaluaciones)"
        ).fetchall()
    ]


    nuevas_columnas_evaluaciones = {

        "habilidades_adecuadas": "TEXT",

        "habilidades_observar": "TEXT",

        "resumen": "TEXT",

        "mensaje": "TEXT"

    }


    for nombre_columna, tipo_columna in nuevas_columnas_evaluaciones.items():

        if nombre_columna not in columnas_evaluaciones:

            conexion.execute(
                f"""
                ALTER TABLE evaluaciones
                ADD COLUMN {nombre_columna} {tipo_columna}
                """
            )

                # =====================================================
    # CREAR TABLA TAMIZAJES
    # =====================================================

    conexion.execute("""
        CREATE TABLE IF NOT EXISTS tamizajes (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            estudiante_id INTEGER NOT NULL,

            respuestas TEXT NOT NULL,

            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (estudiante_id)
            REFERENCES estudiantes(id)

        )
    """)


    # =====================================================
    # CREAR TABLA COGNITIVAS
    # =====================================================

    conexion.execute("""
        CREATE TABLE IF NOT EXISTS cognitivas (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            estudiante_id INTEGER NOT NULL,

            respuestas TEXT NOT NULL,

            puntaje REAL DEFAULT 0,

            porcentaje REAL DEFAULT 0,

            resultado TEXT,

            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (estudiante_id)
            REFERENCES estudiantes(id)

        )
    """)

    # =====================================================
    # GUARDAR CAMBIOS
    # =====================================================

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
# CONTINUAR COMO ESTUDIANTE REGISTRADO
# =========================================================

@app.route("/continuar-estudiante")
def continuar_estudiante():

    codigo = request.args.get("codigo", "").strip()

    if not codigo:
        return """
        <h2>Código requerido</h2>
        <p>Debes ingresar tu código de estudiante.</p>
        <a href="/estudiante">Volver al área de estudiantes</a>
        """, 400

    conexion = conectar_db()

    try:

        # =================================================
        # BUSCAR ESTUDIANTE
        # =================================================

        estudiante = conexion.execute("""
            SELECT *
            FROM estudiantes
            WHERE codigo = ?
        """, (codigo,)).fetchone()


        # =================================================
        # SI NO EXISTE
        # =================================================

        if estudiante is None:

            return """
            <!DOCTYPE html>

            <html lang="es">

            <head>

                <meta charset="UTF-8">

                <meta
                    name="viewport"
                    content="width=device-width, initial-scale=1.0"
                >

                <title>Leo | Código no encontrado</title>

                <style>

                    body {
                        font-family:
                            -apple-system,
                            BlinkMacSystemFont,
                            "Segoe UI",
                            Arial,
                            sans-serif;

                        min-height: 100vh;

                        display: flex;

                        align-items: center;

                        justify-content: center;

                        background: #fff7f8;

                        padding: 20px;
                    }

                    .tarjeta {

                        max-width: 500px;

                        width: 100%;

                        background: white;

                        padding: 40px 30px;

                        border-radius: 22px;

                        text-align: center;

                        border: 1px solid #eadcdf;

                        box-shadow:
                            0 12px 30px
                            rgba(70, 35, 40, 0.08);
                    }

                    .icono {

                        font-size: 45px;

                        margin-bottom: 15px;
                    }

                    h1 {

                        color: #8f1628;

                        margin-bottom: 12px;
                    }

                    p {

                        color: #75696c;

                        line-height: 1.6;

                        margin-bottom: 25px;
                    }

                    a {

                        display: inline-block;

                        padding: 13px 22px;

                        background: #a6192e;

                        color: white;

                        text-decoration: none;

                        border-radius: 11px;

                        font-weight: 700;
                    }

                </style>

            </head>

            <body>

                <div class="tarjeta">

                    <div class="icono">
                        🔎
                    </div>

                    <h1>
                        Código no encontrado
                    </h1>

                    <p>
                        No encontramos un estudiante registrado
                        con ese código.
                    </p>

                    <a href="/estudiante">
                        Volver
                    </a>

                </div>

            </body>

            </html>
            """, 404


        # =================================================
        # ESTUDIANTE ENCONTRADO
        # =================================================

        print(
            "ESTUDIANTE ENCONTRADO:",
            estudiante["codigo"],
            estudiante["nombre"]
        )


        # =================================================
        # CONTINUAR AL PROCESO
        # =================================================

        return redirect(
            url_for(
                "tamizaje",
                codigo=estudiante["codigo"]
            )
        )


    except Exception as error:

        print(
            "ERROR AL BUSCAR ESTUDIANTE:",
            error
        )

        return """
        <h2>Error</h2>

        <p>
            Ocurrió un error al buscar el estudiante.
        </p>

        <a href="/estudiante">
            Volver
        </a>
        """, 500


    finally:

        conexion.close()

    # =========================================================
# BIENVENIDA DEL ESTUDIANTE
# =========================================================

@app.route("/bienvenida")
def bienvenida():

    codigo = request.args.get("codigo")

    return render_template(
        "bienvenida.html",
        codigo=codigo
    )

# =========================================================
# CONOZCÁMONOS
# =========================================================

@app.route("/conozcamonos", methods=["GET", "POST"])
def conozcamonos():

    if request.method == "POST":

        datos = request.get_json()

        if not datos:
            return jsonify({
                "ok": False,
                "mensaje": "No se recibieron datos."
            }), 400

        nombre = datos.get("nombre", "").strip()
        identificacion = datos.get("identificacion", "").strip()
        edad = datos.get("edad")
        sexo = datos.get("sexo", "")
        ciudad = datos.get("ciudad", "").strip()
        grupo = datos.get("grupo", "").strip()

        tipo_estudio = datos.get("tipo_estudio", "")
        modalidad = datos.get("modalidad", "")
        programa = datos.get("programa", "").strip()
        semestre = datos.get("semestre", "").strip()

        universidad_anterior = datos.get(
            "universidad_anterior",
            ""
        )

        consentimiento = datos.get(
            "consentimiento",
            0
        )


        # =====================================================
        # VALIDAR CONSENTIMIENTO
        # =====================================================

        if not consentimiento:

            return jsonify({
                "ok": False,
                "mensaje":
                    "Debes aceptar el consentimiento para continuar."
            }), 400


        # =====================================================
        # CONECTAR CON LA BASE DE DATOS
        # =====================================================

        conexion = conectar_db()


        try:

            # =================================================
            # BUSCAR SI YA EXISTE EL ESTUDIANTE
            # =================================================

            estudiante = conexion.execute(
                """
                SELECT id, codigo
                FROM estudiantes
                WHERE identificacion = ?
                """,
                (identificacion,)
            ).fetchone()


            # =================================================
            # SI YA EXISTE
            # =================================================

            if estudiante:

                conexion.execute(
                    """
                    UPDATE estudiantes
                    SET
                        nombre = ?,
                        edad = ?,
                        sexo = ?,
                        ciudad = ?,
                        grupo = ?,
                        tipo_estudio = ?,
                        modalidad = ?,
                        programa = ?,
                        semestre = ?,
                        universidad_anterior = ?,
                        consentimiento = ?
                    WHERE identificacion = ?
                    """,
                    (
                        nombre,
                        edad,
                        sexo,
                        ciudad,
                        grupo,
                        tipo_estudio,
                        modalidad,
                        programa,
                        semestre,
                        universidad_anterior,
                        consentimiento,
                        identificacion
                    )
                )

                estudiante_id = estudiante["id"]

                estudiante_codigo = estudiante["codigo"]


            # =================================================
            # SI NO EXISTE
            # =================================================

            else:

                codigo = "LEO-" + identificacion

                cursor = conexion.execute(
                    """
                    INSERT INTO estudiantes (
                        codigo,
                        nombre,
                        identificacion,
                        edad,
                        sexo,
                        ciudad,
                        grupo,
                        tipo_estudio,
                        modalidad,
                        programa,
                        semestre,
                        universidad_anterior,
                        consentimiento
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        codigo,
                        nombre,
                        identificacion,
                        edad,
                        sexo,
                        ciudad,
                        grupo,
                        tipo_estudio,
                        modalidad,
                        programa,
                        semestre,
                        universidad_anterior,
                        consentimiento
                    )
                )

                estudiante_id = cursor.lastrowid

                estudiante_codigo = codigo


            # =================================================
            # GUARDAR CAMBIOS
            # =================================================

            conexion.commit()


            print(
                "CONOZCÁMONOS GUARDADO:",
                estudiante_codigo,
                nombre
            )


            # =================================================
            # RESPUESTA
            # =================================================

            return jsonify({
                "ok": True,
                "estudiante_id": estudiante_id,
                "codigo": estudiante_codigo,
                "mensaje":
                    "Información guardada correctamente."
            })


        except sqlite3.IntegrityError as error:

            conexion.rollback()

            print(
                "ERROR DE INTEGRIDAD EN CONOZCÁMONOS:",
                error
            )

            return jsonify({
                "ok": False,
                "mensaje":
                    "Ya existe un estudiante con esos datos."
            }), 400


        except Exception as error:

            conexion.rollback()

            print(
                "ERROR EN CONOZCÁMONOS:",
                error
            )

            return jsonify({
                "ok": False,
                "mensaje":
                    "Ocurrió un error al guardar la información."
            }), 500


        finally:

            conexion.close()


    return render_template(
    "conozcamonos.html"
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
# RESULTADOS PROFESIONALES
# =========================================================

@app.route("/resultados")
def resultados():

    codigo = request.args.get("codigo", "").strip()

    conexion = conectar_db()

    try:

        # =====================================================
        # LISTA DE ESTUDIANTES
        # =====================================================

        estudiantes_db = conexion.execute("""
            SELECT *
            FROM estudiantes
            ORDER BY id DESC
        """).fetchall()

        estudiantes = [
            dict(estudiante)
            for estudiante in estudiantes_db
        ]


        # =====================================================
        # SI NO SE HA SELECCIONADO ESTUDIANTE
        # =====================================================

        if not codigo:

            return render_template(
                "resultados.html",
                estudiantes=estudiantes,
                estudiante=None,
                cognitiva=None
            )


        # =====================================================
        # BUSCAR ESTUDIANTE SELECCIONADO
        # =====================================================

        estudiante_db = conexion.execute("""
            SELECT *
            FROM estudiantes
            WHERE codigo = ?
        """, (codigo,)).fetchone()


        if estudiante_db is None:

            return render_template(
                "resultados.html",
                estudiantes=estudiantes,
                estudiante=None,
                cognitiva=None
            )


        estudiante = dict(estudiante_db)


        # =====================================================
        # BUSCAR ÚLTIMA EVALUACIÓN COGNITIVA
        # =====================================================

        cognitiva_db = conexion.execute("""
            SELECT *
            FROM cognitivas
            WHERE estudiante_id = ?
            ORDER BY id DESC
            LIMIT 1
        """, (estudiante["id"],)).fetchone()


        cognitiva = None


        if cognitiva_db is not None:

            cognitiva = dict(cognitiva_db)


        # =====================================================
        # MOSTRAR RESULTADOS
        # =====================================================

        return render_template(
            "resultados.html",

            estudiantes=estudiantes,

            estudiante=estudiante,

            cognitiva=cognitiva
        )


    except Exception as error:

        print(
            "ERROR EN RESULTADOS:",
            error
        )

        return """
        <h2>Error</h2>
        <p>No fue posible cargar los resultados.</p>
        <a href="/area-profesional">
            Volver al área profesional
        </a>
        """, 500


    finally:

        conexion.close()

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
# GUARDAR TAMIZAJE
# =========================================================

@app.route("/guardar-tamizaje", methods=["POST"])
def guardar_tamizaje():

    datos = request.get_json(silent=True)

    if not datos:
        return jsonify({
            "ok": False,
            "mensaje": "No se recibieron los datos del tamizaje."
        }), 400

    codigo = str(
        datos.get("codigo", "")
    ).strip()

    if not codigo:
        return jsonify({
            "ok": False,
            "mensaje": "No se recibió el código del estudiante."
        }), 400

    conexion = conectar_db()

    try:

        # =====================================================
        # BUSCAR ESTUDIANTE
        # =====================================================

        estudiante = conexion.execute("""
            SELECT *
            FROM estudiantes
            WHERE codigo = ?
        """, (codigo,)).fetchone()

        if estudiante is None:

            return jsonify({
                "ok": False,
                "mensaje": "No se encontró el estudiante."
            }), 404

        # =====================================================
        # GUARDAR RESPUESTAS
        # =====================================================

        respuestas = {}

        for clave, valor in datos.items():

            if clave != "codigo":

                respuestas[clave] = valor

        # =====================================================
        # INSERTAR TAMIZAJE
        # =====================================================

        conexion.execute("""
            INSERT INTO tamizajes
            (
                estudiante_id,
                respuestas
            )
            VALUES (?, ?)
        """, (
            estudiante["id"],
            json.dumps(
                respuestas,
                ensure_ascii=False
            )
        ))

        conexion.commit()

        print(
            "TAMIZAJE GUARDADO:",
            codigo
        )

        # =====================================================
        # RESPUESTA AL JAVASCRIPT
        # =====================================================

        return jsonify({
            "ok": True,
            "mensaje": "Tamizaje guardado correctamente."
        })

    except Exception as error:

        conexion.rollback()

        print(
            "ERROR AL GUARDAR TAMIZAJE:",
            error
        )

        return jsonify({
            "ok": False,
            "mensaje":
                "No fue posible guardar el tamizaje."
        }), 500

    finally:

        conexion.close()

# =========================================================
# DIMENSIÓN COGNITIVA
# =========================================================

@app.route("/cognitiva")
def cognitiva():

    codigo = request.args.get("codigo", "").strip()

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
        <p>No se encontró el estudiante.</p>
        <a href="/">Volver al inicio</a>
        """, 404

    return render_template(
        "cognitiva.html",
        codigo=codigo,
        estudiante=dict(estudiante)
    )


# =========================================================
# GUARDAR RESULTADO DE LA DIMENSIÓN COGNITIVA
# =========================================================

# =========================================================
# RESULTADO DE LA DIMENSIÓN COGNITIVA
# =========================================================

# =========================================================
# GUARDAR RESULTADO DE LA DIMENSIÓN COGNITIVA
# =========================================================

@app.route("/resultado-cognitiva", methods=["POST"])
def resultado_cognitiva():

    codigo = request.form.get("codigo", "").strip()

    if not codigo:
        return """
        <h2>Error</h2>
        <p>No se recibió el código del estudiante.</p>
        <a href="/">Volver al inicio</a>
        """, 400

    conexion = conectar_db()

    try:

        # =====================================================
        # BUSCAR ESTUDIANTE
        # =====================================================

        estudiante = conexion.execute("""
            SELECT *
            FROM estudiantes
            WHERE codigo = ?
        """, (codigo,)).fetchone()

        if estudiante is None:
            return """
            <h2>Error</h2>
            <p>No se encontró el estudiante.</p>
            <a href="/">Volver al inicio</a>
            """, 404

        # =====================================================
        # ESTRUCTURA OFICIAL DE LA DIMENSIÓN COGNITIVA
        # =====================================================

        subhabilidades = {

            "memoria_trabajo": {
                "nombre": "Memoria de trabajo",
                "preguntas": [
                    "c1", "c2", "c3", "c4", "c5"
                ]
            },

            "atencion_concentracion": {
                "nombre": "Atención/concentración",
                "preguntas": [
                    "c6", "c7", "c8", "c9", "c10"
                ]
            },

            "planificacion": {
                "nombre": "Planificación",
                "preguntas": [
                    "c11", "c12", "c13", "c14", "c15"
                ]
            },

            "gestion_tiempo": {
                "nombre": "Gestión del tiempo",
                "preguntas": [
                    "c16", "c17", "c18", "c19", "c20"
                ]
            },

            "flexibilidad_cognitiva": {
                "nombre": "Flexibilidad cognitiva",
                "preguntas": [
                    "c21", "c22", "c23", "c24", "c25"
                ]
            },

            "velocidad_procesamiento": {
                "nombre": "Velocidad de procesamiento",
                "preguntas": [
                    "c26", "c27", "c28", "c29", "c30"
                ]
            },

            "organizacion": {
                "nombre": "Organización",
                "preguntas": [
                    "c31", "c32", "c33", "c34", "c35"
                ]
            }
        }

        # =====================================================
        # RECIBIR LAS 35 RESPUESTAS
        # =====================================================

        respuestas = {}

        preguntas_faltantes = []

        for numero in range(1, 36):

            pregunta = f"c{numero}"

            respuesta = request.form.get(
                pregunta,
                ""
            ).strip()

            if respuesta == "":

                preguntas_faltantes.append(
                    pregunta
                )

                continue

            try:

                valor = int(respuesta)

            except ValueError:

                return """
                <h2>Error en la evaluación</h2>
                <p>Se recibió una respuesta no válida.</p>
                <a href="/">Volver al inicio</a>
                """, 400

            if valor not in [0, 1, 2, 3]:

                return """
                <h2>Error en la evaluación</h2>
                <p>Una de las respuestas está fuera del rango permitido.</p>
                <a href="/">Volver al inicio</a>
                """, 400

            respuestas[pregunta] = valor

        # =====================================================
        # VERIFICAR QUE ESTÉN LAS 35 RESPUESTAS
        # =====================================================

        if preguntas_faltantes:

            return """
            <h2>Evaluación incompleta</h2>

            <p>
                Debes responder todas las preguntas
                de la dimensión cognitiva.
            </p>

            <br>

            <a href="/cognitiva?codigo=""" + codigo + """">
                Volver a la evaluación
            </a>
            """, 400

        # =====================================================
        # CALCULAR RESULTADOS POR SUBHABILIDAD
        # =====================================================

        resultados_subhabilidades = {}

        puntaje_total = 0

        for clave, datos in subhabilidades.items():

            puntaje = sum(
                respuestas[pregunta]
                for pregunta in datos["preguntas"]
            )

            porcentaje = round(
                (puntaje / 15) * 100
            )

            resultados_subhabilidades[clave] = {

                "nombre": datos["nombre"],

                "puntaje": puntaje,

                "maximo": 15,

                "porcentaje": porcentaje
            }

            puntaje_total += puntaje

        # =====================================================
        # PORCENTAJE GENERAL
        #
        # 35 preguntas × 3 puntos = 105 puntos
        # =====================================================

        porcentaje_total = round(
            (puntaje_total / 105) * 100
        )

        # =====================================================
        # CLASIFICACIÓN GENERAL
        #
        # IMPORTANTE:
        # 0 = menor frecuencia de dificultad
        # 3 = mayor frecuencia de dificultad
        # =====================================================

        if porcentaje_total <= 33:

            nivel = "Indicadores favorables"

        elif porcentaje_total <= 66:

            nivel = "Aspectos por observar"

        else:

            nivel = "Requiere mayor observación"

        # =====================================================
        # CLASIFICAR SUBHABILIDADES
        # =====================================================

        fortalezas = []

        areas_observar = []

        for datos in resultados_subhabilidades.values():

            porcentaje = datos["porcentaje"]

            if porcentaje <= 33:

                fortalezas.append(
                    datos["nombre"]
                )

            else:

                areas_observar.append(
                    datos["nombre"]
                )

        # =====================================================
        # GUARDAR RESULTADO EN LA BASE DE DATOS
        # =====================================================

        conexion.execute("""
            INSERT INTO cognitivas
            (
                estudiante_id,
                respuestas,
                puntaje,
                porcentaje,
                resultado
            )
            VALUES (?, ?, ?, ?, ?)
        """, (

            estudiante["id"],

            json.dumps(
                respuestas,
                ensure_ascii=False
            ),

            puntaje_total,

            porcentaje_total,

            nivel
        ))

        conexion.commit()

        # =====================================================
        # REGISTRO EN TERMINAL
        # =====================================================

        print(
            "=========================================="
        )

        print(
            "COGNITIVA GUARDADA"
        )

        print(
            "Estudiante:",
            codigo
        )

        print(
            "Puntaje:",
            puntaje_total,
            "/ 105"
        )

        print(
            "Porcentaje:",
            porcentaje_total,
            "%"
        )

        print(
            "Resultado:",
            nivel
        )

        print(
            "Subhabilidades:",
            resultados_subhabilidades
        )

        print(
            "=========================================="
        )

        # =====================================================
        # NO MOSTRAR RESULTADOS AL ESTUDIANTE
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
                Leo | Evaluación completada
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

                    min-height: 100vh;

                    background:
                        linear-gradient(
                            135deg,
                            #fff5f5,
                            #ffffff,
                            #fff8f8
                        );

                    display: flex;

                    align-items: center;

                    justify-content: center;

                    padding: 20px;

                    color: #263238;
                }}

                .contenedor {{

                    width: 100%;

                    max-width: 600px;

                }}

                .tarjeta {{

                    background: white;

                    border-radius: 24px;

                    padding: 45px 35px;

                    text-align: center;

                    box-shadow:
                        0 12px 35px
                        rgba(120, 30, 30, 0.10);

                    border:
                        1px solid #f1dddd;
                }}

                .icono {{

                    width: 75px;

                    height: 75px;

                    margin: 0 auto 22px;

                    border-radius: 22px;

                    background: #a6192e;

                    color: white;

                    display: flex;

                    align-items: center;

                    justify-content: center;

                    font-size: 36px;

                    box-shadow:
                        0 8px 20px
                        rgba(166, 25, 46, 0.20);
                }}

                h1 {{

                    color: #8f1628;

                    font-size: 28px;

                    margin-bottom: 15px;
                }}

                .mensaje {{

                    color: #64748b;

                    font-size: 15px;

                    line-height: 1.6;

                    margin-bottom: 25px;
                }}

                .confirmacion {{

                    background: #fff5f5;

                    border:
                        1px solid #f3d4d9;

                    border-radius: 15px;

                    padding: 17px;

                    color: #7f1d2d;

                    font-size: 14px;

                    margin-bottom: 25px;
                }}

                .boton {{

                    display: inline-block;

                    text-decoration: none;

                    background: #a6192e;

                    color: white;

                    padding: 14px 25px;

                    border-radius: 12px;

                    font-size: 14px;

                    font-weight: 700;

                    transition: .2s;
                }}

                .boton:hover {{

                    background: #8f1628;

                    transform:
                        translateY(-1px);
                }}

                @media (max-width: 600px) {{

                    .tarjeta {{

                        padding:
                            35px 22px;
                    }}

                    h1 {{

                        font-size: 24px;
                    }}

                }}

            </style>

        </head>

        <body>

            <div class="contenedor">

                <div class="tarjeta">

                    <div class="icono">
                        ✓
                    </div>

                    <h1>
                        Evaluación completada
                    </h1>

                    <p class="mensaje">

                        Has completado correctamente
                        la dimensión cognitiva.

                    </p>

                    <div class="confirmacion">

                        ✓ Tus respuestas fueron registradas
                        correctamente.

                    </div>

                    <a
                        href="/"
                        class="boton"
                    >
                        Continuar
                    </a>

                </div>

            </div>

        </body>

        </html>

        """

    except Exception as error:

        conexion.rollback()

        print(
            "ERROR AL GUARDAR COGNITIVA:",
            error
        )

        return """
        <h2>Error</h2>
        <p>
            Ocurrió un error al guardar
            la evaluación cognitiva.
        </p>
        <a href="/">Volver al inicio</a>
        """, 500

    finally:

        conexion.close()

# =========================================================
# RESULTADO COGNITIVO PARA EL PROFESIONAL
# =========================================================

@app.route("/profesional/cognitiva")
def profesional_cognitiva():

    codigo = request.args.get("codigo", "").strip()

    if not codigo:
        return """
        <h2>Error</h2>
        <p>No se recibió el código del estudiante.</p>
        <a href="/">Volver al inicio</a>
        """, 400

    conexion = conectar_db()

    try:

        # =====================================================
        # BUSCAR ESTUDIANTE
        # =====================================================

        estudiante = conexion.execute("""
            SELECT *
            FROM estudiantes
            WHERE codigo = ?
        """, (codigo,)).fetchone()

        if estudiante is None:

            return """
            <h2>Error</h2>
            <p>No se encontró el estudiante.</p>
            <a href="/">Volver al inicio</a>
            """, 404

        # =====================================================
        # BUSCAR ÚLTIMA EVALUACIÓN COGNITIVA
        # =====================================================

        resultado = conexion.execute("""
            SELECT *
            FROM cognitivas
            WHERE estudiante_id = ?
            ORDER BY id DESC
            LIMIT 1
        """, (estudiante["id"],)).fetchone()

        if resultado is None:

            return render_template(
                "profesional_cognitiva.html",

                estudiante=dict(estudiante),

                codigo=codigo,

                evaluacion=None
            )

        # =====================================================
        # RECUPERAR RESPUESTAS
        # =====================================================

        respuestas = json.loads(
            resultado["respuestas"]
        )

        # =====================================================
        # ESTRUCTURA OFICIAL
        # =====================================================

        subhabilidades = {

            "memoria_trabajo": {
                "nombre": "Memoria de trabajo",
                "preguntas": [
                    "c1", "c2", "c3", "c4", "c5"
                ]
            },

            "atencion_concentracion": {
                "nombre": "Atención/concentración",
                "preguntas": [
                    "c6", "c7", "c8", "c9", "c10"
                ]
            },

            "planificacion": {
                "nombre": "Planificación",
                "preguntas": [
                    "c11", "c12", "c13", "c14", "c15"
                ]
            },

            "gestion_tiempo": {
                "nombre": "Gestión del tiempo",
                "preguntas": [
                    "c16", "c17", "c18", "c19", "c20"
                ]
            },

            "flexibilidad_cognitiva": {
                "nombre": "Flexibilidad cognitiva",
                "preguntas": [
                    "c21", "c22", "c23", "c24", "c25"
                ]
            },

            "velocidad_procesamiento": {
                "nombre": "Velocidad de procesamiento",
                "preguntas": [
                    "c26", "c27", "c28", "c29", "c30"
                ]
            },

            "organizacion": {
                "nombre": "Organización",
                "preguntas": [
                    "c31", "c32", "c33", "c34", "c35"
                ]
            }
        }

        # =====================================================
        # CALCULAR RESULTADOS POR SUBHABILIDAD
        # =====================================================

        resultados_subhabilidades = {}

        fortalezas = []

        areas_observar = []

        for clave, datos in subhabilidades.items():

            puntaje = sum(
                respuestas.get(pregunta, 0)
                for pregunta in datos["preguntas"]
            )

            porcentaje = round(
                (puntaje / 15) * 100
            )

            if porcentaje <= 33:

                clasificacion = "Indicador favorable"

                clase = "favorable"

                fortalezas.append(
                    datos["nombre"]
                )

            elif porcentaje <= 66:

                clasificacion = "Aspectos por observar"

                clase = "observacion"

                areas_observar.append(
                    datos["nombre"]
                )

            else:

                clasificacion = "Mayor frecuencia de indicadores"

                clase = "alerta"

                areas_observar.append(
                    datos["nombre"]
                )

            resultados_subhabilidades[clave] = {

                "nombre": datos["nombre"],

                "puntaje": puntaje,

                "maximo": 15,

                "porcentaje": porcentaje,

                "clasificacion": clasificacion,

                "clase": clase
            }

        # =====================================================
        # DATOS GENERALES
        # =====================================================

        evaluacion = {

            "puntaje": resultado["puntaje"],

            "porcentaje": resultado["porcentaje"],

            "resultado": resultado["resultado"],

            "fecha": resultado["fecha"]
            if "fecha" in resultado.keys()
            else None
        }

        return render_template(
            "profesional_cognitiva.html",

            estudiante=dict(estudiante),

            codigo=codigo,

            evaluacion=evaluacion,

            respuestas=respuestas,

            subhabilidades=resultados_subhabilidades,

            fortalezas=fortalezas,

            areas_observar=areas_observar
        )

    except Exception as error:

        print(
            "ERROR AL CONSULTAR COGNITIVA:",
            error
        )

        return """
        <h2>Error</h2>
        <p>No fue posible consultar el resultado cognitivo.</p>
        <a href="/">Volver al inicio</a>
        """, 500

    finally:

        conexion.close()

# =========================================================
# RESULTADO DE COMPRENSIÓN LECTORA
# =========================================================

@app.route("/resultado-comprension", methods=["POST"])
def resultado_comprension():

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
    # VARIABLES TEMPORALES
    # =====================================================

    progreso_html = ""

    porcentaje = 0
    puntuacion = 0
    nivel = "Pendiente"
    clase_nivel = "nivel-naranja"
    mensaje = "Evaluación pendiente."

    fortalezas_html = ""
    areas_html = ""
    resumen_areas = ""
    plan_html = ""

    # =====================================================
    # HTML
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

        <title>Leo | Resultados</title>
    </head>

    <body>

        <div class="contenedor">

            {progreso_html}

            <h1>Resultado de comprensión lectora</h1>

            <h2>{porcentaje}%</h2>

            <p>{puntuacion} respuestas correctas</p>

            <p>{nivel}</p>

            <p>{mensaje}</p>

            <h2>Análisis por habilidades</h2>

            {fortalezas_html}

            {areas_html}

            <div>
                {resumen_areas}
            </div>

            <h2>Plan de apoyo</h2>

            {plan_html}

        </div>

    </body>

    </html>
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

        .resultado-circulo {{
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
}}

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

    inicializar_db()

    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        debug=True
    )