from __future__ import annotations

import csv
import random
import string
from datetime import datetime, timedelta

random.seed(42)

# ============================================================
# 1. CONFIGURACIÓN GEOGRÁFICA REAL - RED DE SALUD PICHANAKI
# ============================================================
# La Red de Salud Pichanaki pertenece a la DIRESA Junín
# Ubigeo real: 120304 (Pichanaki), provincia Chanchamayo

REGION = "Junín"
PROVINCIA = "Chanchamayo"

DISTRITOS = [
    # (distrito, ubigeo, poblacion_aprox)
    ("Pichanaki", "120304", 65000),
    ("San Ramón", "120301", 25000),
    ("Chanchamayo", "120302", 15000),
    ("Perené", "120303", 60000),
    ("San Luis de Shuaro", "120305", 8000),
    ("Villa Rica", "120306", 20000),
    ("Río Negro", "120701", 18000),   # Satipo
    ("Mazamari", "120702", 25000),    # Satipo
    ("Satipo", "120701", 30000),      # Satipo
]

ESTABLECIMIENTOS = [
    # (nombre, tipo, nivel)
    ("Hospital de Pichanaki", "Hospital II-1", "II-1"),
    ("Centro de Salud San Ramón", "Centro de Salud", "I-4"),
    ("Centro de Salud Perené", "Centro de Salud", "I-4"),
    ("Puesto de Salud Santo Domingo", "Puesto de Salud", "I-2"),
    ("Puesto de Salud Alto Cahuapanas", "Puesto de Salud", "I-2"),
    ("Puesto de Salud Río Negro", "Puesto de Salud", "I-2"),
    ("Centro de Salud Mazamari", "Centro de Salud", "I-3"),
    ("Puesto de Salud Villa Rica", "Puesto de Salud", "I-2"),
    ("Hospital de Satipo", "Hospital II-1", "II-1"),
    ("Microred Pichanaki", "Microred", "I-3"),
]

# Distancia promedio desde cada distrito al Hospital de Pichanaki (km)
DISTANCIAS = {
    "Pichanaki": (0, 5),
    "San Ramón": (20, 35),
    "Chanchamayo": (15, 25),
    "Perené": (10, 30),
    "San Luis de Shuaro": (25, 40),
    "Villa Rica": (60, 90),
    "Río Negro": (50, 75),
    "Mazamari": (70, 100),
    "Satipo": (80, 110),
}

# Ubigeo por distrito
UBIGEO_MAP = {d[0]: d[1] for d in DISTRITOS}

# ============================================================
# 2. NOMBRES Y APELLIDOS REALISTAS - PERÚ (REGIÓN JUNÍN)
# ============================================================

NOMBRES_F = [
    "María", "Carmen", "Rosa", "Elena", "Ana", "Lucía", "Juana", "Sofía",
    "Dora", "Isabel", "Martha", "Gloria", "Silvia", "Ruth", "Bertha",
    "Vilma", "Olga", "Yolanda", "Nelly", "Luz", "Teresa", "Felicita",
    "Victoria", "Margarita", "Elsa", "Clotilde", "Paulina", "Justina",
    "Teodora", "Sabina", "Hilda", "Nora", "Zulema", "Esperanza", "Lidia",
    "Edith", "Norma", "Maribel", "Rocio", "Milagros", "Yesenia",
]

NOMBRES_M = [
    "Juan", "Carlos", "José", "Luis", "Manuel", "Pedro", "Jorge", "Víctor",
    "Miguel", "Alberto", "Raúl", "Fernando", "Hugo", "Oscar", "Ricardo",
    "Pablo", "Edgar", "Ronald", "Javier", "Wilfredo", "Walter", "Rolando",
    "César", "Saúl", "Marco", "Elmer", "Joel", "Fredy", "Moisés", "David",
    "Efraín", "Julio", "Félix", "Tito", "Abel", "Dante", "Elías",
]

APELLIDOS = [
    "Quispe", "Huamán", "Mamani", "Cárdenas", "Torres", "López", "García",
    "Rodríguez", "Martínez", "Rojas", "Pérez", "Sánchez", "Ramírez",
    "Flores", "Ortiz", "Castro", "Chávez", "Ramos", "Díaz", "Vega",
    "Morales", "Gómez", "Vásquez", "Romero", "Reyes", "Rivera", "Medina",
    "Contreras", "Cruz", "Silva", "Huertas", "Llanos", "Paredes",
    "Campos", "Vilchez", "Salazar", "Córdova", "Mendoza", "Tapia",
    "Aguilar", "Zevallos", "Baldeón", "Yupanqui", "Ccoicca", "Sinche",
    "Untiveros", "Paucar", "Meléndez", "Carhuallanqui", "Tueros",
]

# ============================================================
# 3. ESPECIALIDADES MÉDICAS REALES
# ============================================================

ESPECIALIDADES = [
    "Medicina General", "Pediatría", "Ginecología", "Cardiología",
    "Dermatología", "Traumatología", "Oftalmología", "Otorrinolaringología",
    "Neumología", "Neurología", "Psicología", "Nutrición",
    "Odontología", "Medicina Interna", "Cirugía General", "Urología",
    "Reumatología", "Endocrinología", "Gastroenterología", "Oncología",
]

# Médicos por especialidad (nombres realistas)
MEDICOS_POR_ESPECIALIDAD: dict[str, list[tuple[str, str]]] = {
    "Medicina General": [
        ("Dr. Luis", "Huamán Torres"), ("Dra. Carmen", "Ramos López"),
        ("Dr. Jorge", "Cárdenas Flores"), ("Dra. Rosa", "Salazar Huertas"),
        ("Dr. Pedro", "Sánchez Quispe"),
    ],
    "Pediatría": [
        ("Dr. Carlos", "Vega Morales"), ("Dra. Lucía", "Castro Ramírez"),
        ("Dr. Manuel", "Torres Rojas"), ("Dra. Martha", "López Huamán"),
    ],
    "Ginecología": [
        ("Dra. Ana", "Rivera Paredes"), ("Dra. María", "Quispe Cárdenas"),
        ("Dra. Elena", "Mendoza Tapia"), ("Dra. Silvia", "Campos Vilchez"),
    ],
    "Cardiología": [
        ("Dr. Alberto", "Ramírez Chávez"), ("Dr. Fernando", "García Torres"),
        ("Dra. Isabel", "Reyes Contreras"), ("Dr. Ricardo", "Pérez Dávila"),
    ],
    "Traumatología": [
        ("Dr. Oscar", "Cruz Meléndez"), ("Dr. Miguel", "Ríos Pineda"),
        ("Dr. Víctor", "López Sánchez"),
    ],
    "Oftalmología": [
        ("Dr. Raúl", "Flores Medina"), ("Dra. Gloria", "Vega Rojas"),
        ("Dr. Walter", "Ramos Cárdenas"),
    ],
    "Dermatología": [
        ("Dra. Bertha", "Salazar Córdova"), ("Dr. César", "Huamán Llanos"),
        ("Dra. Patricia", "Montesinos Páucar"),
    ],
    "Psicología": [
        ("Dra. Nelly", "Morales Rojas"), ("Dr. Efraín", "Cárdenas Vargas"),
        ("Dra. Dora", "Paucar Sinche"),
    ],
    "Nutrición": [
        ("Dra. Ruth", "Campos Untiveros"), ("Dr. Marco", "Torres Paucar"),
        ("Lic. Juana", "Quispe Mamani"),
    ],
    "Odontología": [
        ("Dr. Ronald", "Paredes Llanos"), ("Dra. Maribel", "Cárdenas Rojas"),
        ("Dr. Joel", "Mamani Quispe"), ("Dra. Lidia", "Huertas López"),
    ],
    "Medicina Interna": [
        ("Dr. José", "Medina Zevallos"), ("Dra. Norma", "Tapia Córdova"),
        ("Dr. Hugo", "García Rodríguez"),
    ],
    "Neurología": [
        ("Dr. Wilfredo", "Ramos Huamán"), ("Dra. Sofía", "Torres Llanos"),
    ],
    "Otorrinolaringología": [
        ("Dr. Saúl", "Rojas Campos"), ("Dra. Hilda", "Sánchez Vega"),
    ],
    "Neumología": [
        ("Dr. Fredy", "Castro Salazar"), ("Dra. Olga", "Morales Torres"),
    ],
    "Cirugía General": [
        ("Dr. Pablo", "Rivera Huertas"), ("Dr. Dante", "Cárdenas Zevallos"),
    ],
    "Urología": [
        ("Dr. Elmer", "Ramírez Tapia"), ("Dr. Javier", "López Quispe"),
    ],
    "Reumatología": [
        ("Dra. Zulema", "Vilchez Huamán"), ("Dr. Julio", "Pérez Castro"),
    ],
    "Endocrinología": [
        ("Dra. Yesenia", "Baldeón Yupanqui"), ("Dr. Rolando", "Chávez Ríos"),
    ],
    "Gastroenterología": [
        ("Dr. Tito", "Huamán Cárdenas"), ("Dra. Maribel", "Vega Rojas"),
    ],
    "Oncología": [
        ("Dr. Félix", "Meléndez Córdova"), ("Dra. Teodora", "Quispe Salazar"),
    ],
}

# ============================================================
# 4. CIE-10 - DIAGNÓSTICOS REALES
# ============================================================

CIE10: list[tuple[str, str, str]] = [
    # (codigo, descripcion, especialidad_asociada)
    ("I10", "Hipertensión esencial", "Cardiología"),
    ("E11", "Diabetes mellitus tipo 2", "Endocrinología"),
    ("J00", "Resfriado común", "Medicina General"),
    ("J15", "Neumonía bacteriana", "Neumología"),
    ("M54", "Lumbago", "Traumatología"),
    ("N39", "Infección urinaria", "Medicina General"),
    ("K29", "Gastritis", "Gastroenterología"),
    ("H52", "Miopía", "Oftalmología"),
    ("L20", "Dermatitis atópica", "Dermatología"),
    ("J45", "Asma", "Neumología"),
    ("E66", "Obesidad", "Nutrición"),
    ("F32", "Depresión mayor", "Psicología"),
    ("K02", "Caries dental", "Odontología"),
    ("N76", "Enfermedad inflamatoria pélvica", "Ginecología"),
    ("I50", "Insuficiencia cardíaca", "Cardiología"),
    ("M17", "Artrosis de rodilla", "Traumatología"),
    ("E03", "Hipotiroidismo", "Endocrinología"),
    ("H10", "Conjuntivitis", "Oftalmología"),
    ("L40", "Psoriasis", "Dermatología"),
    ("G40", "Epilepsia", "Neurología"),
    ("N40", "Hiperplasia prostática", "Urología"),
    ("K08", "Pérdida de dientes", "Odontología"),
    ("J01", "Sinusitis aguda", "Otorrinolaringología"),
    ("E78", "Hipercolesterolemia", "Nutrición"),
    ("D50", "Anemia ferropénica", "Medicina General"),
    ("F41", "Trastorno de ansiedad", "Psicología"),
    ("M06", "Artritis reumatoide", "Reumatología"),
    ("C50", "Tumor maligno de mama", "Oncología"),
    ("C16", "Tumor maligno de estómago", "Oncología"),
    ("K40", "Hernia inguinal", "Cirugía General"),
    ("N20", "Cálculo renal", "Urología"),
    ("J32", "Sinusitis crónica", "Otorrinolaringología"),
    ("L30", "Dermatitis no especificada", "Dermatología"),
    ("H65", "Otitis media", "Otorrinolaringología"),
    ("M10", "Gota", "Reumatología"),
    ("K21", "Enfermedad por reflujo gastroesofágico", "Gastroenterología"),
    ("K25", "Úlcera gástrica", "Gastroenterología"),
    ("N97", "Infertilidad femenina", "Ginecología"),
    ("I48", "Fibrilación auricular", "Cardiología"),
    ("G47", "Trastornos del sueño", "Neurología"),
]

# ============================================================
# 5. MOTIVOS DE CONSULTA Y SÍNTOMAS REALISTAS
# ============================================================

MOTIVOS_POR_SINTOMA: dict[str, list[str]] = {
    "dolor de cabeza intenso": [
        "Control por migraña recurrente", "Evaluación de cefalea crónica",
        "Dolor de cabeza persistente desde hace una semana",
    ],
    "dolor abdominal": [
        "Dolor en la parte baja del abdomen", "Malestar estomacal persistente",
        "Dolor abdominal con náuseas y vómitos",
    ],
    "fiebre": [
        "Fiebre alta desde hace 3 días", "Cuadro febril sin foco aparente",
        "Fiebre intermitente con escalofríos",
    ],
    "tos seca": [
        "Tos persistente desde hace dos semanas", "Tos seca y dificultad para respirar",
        "Cuadro respiratorio con tos y congestión",
    ],
    "dolor de espalda": [
        "Lumbago crónico agudizado", "Dolor lumbar irradiado a pierna derecha",
        "Contractura muscular en zona lumbar",
    ],
    "control prenatal": [
        "Control de embarazo - tercer trimestre", "Gestante para control mensual",
        "Control prenatal con ecografía",
    ],
    "control niño sano": [
        "Control de crecimiento y desarrollo", "Vacunación del menor",
        "Evaluación de peso y talla - niño de 2 años",
    ],
    "dolor en articulaciones": [
        "Dolor en rodillas al caminar", "Artritis reumatoide en control",
        "Inflamación articular en manos y muñecas",
    ],
    "problemas de visión": [
        "Visión borrosa progresiva", "Evaluación para lentes correctores",
        "Ojo rojo con secreción y ardor",
    ],
    "problemas dentales": [
        "Dolor de muela intenso", "Caries dental para tratamiento",
        "Extracción de pieza dental dañada",
    ],
    "malestar general": [
        "Chequeo general por fatiga constante", "Evaluación médica anual",
        "Malestar general sin causa aparente",
    ],
    "problemas emocionales": [
        "Ansiedad y ataques de pánico", "Depresión en seguimiento",
        "Trastorno de sueño y alimentación",
    ],
    "dolor en el pecho": [
        "Dolor torácico con palpitaciones", "Control cardiológico mensual",
        "Evaluación de hipertensión arterial",
    ],
    "alergias": [
        "Reacción alérgica cutánea", "Rinitis alérgica estacional",
        "Urticaria por posible alergia alimentaria",
    ],
    "diabetes": [
        "Control de diabetes mellitus tipo 2", "Evaluación de glucemia",
        "Pie diabético - control de úlcera",
    ],
    "herida": [
        "Herida cortante en mano", "Quemadura de segundo grado en brazo",
        "Traumatismo por caída en vía pública",
    ],
    "control de peso": [
        "Plan nutricional para perder peso", "Evaluación de obesidad infantil",
        "Asesoría nutricional por sobrepeso",
    ],
    "dolor de oído": [
        "Otitis media con supuración", "Dolor de oído intenso desde hace 2 días",
        "Hipoacusia súbita en oído izquierdo",
    ],
    "problemas urinarios": [
        "Ardor al orinar con fiebre", "Infección urinaria recurrente",
        "Dificultad para orinar por próstata",
    ],
    "anemia": [
        "Control de anemia en gestante", "Fatiga por anemia ferropénica",
        "Evaluación de hemoglobina baja",
    ],
}

# ============================================================
# 6. TEXTOS REALISTAS DE PACIENTES (para el modelo LSTM)
# ============================================================

TEXTOS_POR_INTENT: dict[str, list[str]] = {
    "agendar_cita": [
        "Buenos días, quisiera agendar una cita con el médico por favor",
        "Necesito sacar una cita para control general",
        "Quiero reservar una consulta con el cardiólogo",
        "Por favor, necesito separar una cita para mi mamá que tiene dolor de cabeza",
        "Buenas tardes, deseo programar una cita médica para hoy si es posible",
        "Hola, me puede agendar una cita con el doctor para la próxima semana",
        "Quisiera programar una consulta con el ginecólogo, tengo dolor abdominal",
        "Necesito una cita urgente para mi niño que tiene fiebre alta",
        "Buen día, quiero agendar un control para mi diabetes",
        "Por favor agéndeme una cita con el traumatólogo me duele la rodilla",
        "Hola buenas, quisiera separar cita para control prenatal",
        "Necesito sacar cita con el odontólogo por un dolor de muela",
        "Buenas tardes, me puede dar una cita con la nutricionista para bajar de peso",
        "Quisiera agendar una consulta por teléfono con el médico general",
        "Por favor, necesito reservar una cita para un chequeo completo",
        "Buenos días, deseo programar mi cita de control mensual",
        "Hola, me podría agendar una cita para el dermatólogo tengo alergia en la piel",
        "Necesito separar una consulta con el psicólogo por ansiedad",
        "Buenas, quisiera sacar cita para el otorrino porque no escucho bien",
        "Por favor agende una cita para control de presión arterial",
    ],
    "cancelar_cita": [
        "Buenos días, quiero cancelar mi cita por favor",
        "Lamento informar que no podré asistir a mi consulta programada",
        "Necesito anular mi cita del día de mañana",
        "Hola, por favor cancele mi cita porque tengo una emergencia familiar",
        "Buenas tardes, deseo eliminar la cita que tenía agendada para el jueves",
        "No voy a poder ir a mi cita, por favor cancélela",
        "Quisiera cancelar la cita de mi papá porque se siente mal para viajar",
        "Por favor anule mi cita, tuve un imprevisto y no podré asistir",
        "Hola, necesito dar de baja mi cita programada para mañana",
        "Buen día, cancéleme la cita por favor, ya no la necesito",
    ],
    "consultar_cita": [
        "Quisiera saber el estado de mi cita por favor",
        "Buenos días, quiero consultar si mi cita está confirmada",
        "Hola, me puede decir a qué hora tengo mi cita mañana",
        "Necesito verificar si mi cita sigue siendo a las 10 de la mañana",
        "Buenas tardes, quiero confirmar los datos de mi cita médica",
        "Cómo puedo saber si mi cita ya fue aprobada",
        "Quiero revisar el horario de mi consulta por favor",
        "Hola, consultar el estado de mi ticket por favor",
        "Buen día, me puede decir si ya tengo hora confirmada para mi control",
        "Necesito saber con qué médico tengo mi cita mañana",
    ],
    "reprogramar_cita": [
        "Buenos días, quisiera cambiar la fecha de mi cita por favor",
        "Necesito reprogramar mi consulta para otro día",
        "Hola, puedo mover mi cita de mañana para la próxima semana",
        "Quisiera cambiar el horario de mi cita, ya no me queda bien",
        "Buenas tardes, necesito adelantar mi cita si es posible",
        "Por favor, puede reprogramar mi cita para el viernes en la tarde",
        "Hola, tengo una cita el miércoles pero quisiera pasarla al jueves",
        "Necesito cambiar la fecha de mi consulta por motivos de trabajo",
        "Quisiera modificar la hora de mi cita de las 8 a las 11",
        "Buen día, puedo cambiar mi cita para un horario más temprano",
    ],
    "consultar_doctor": [
        "Qué médicos hay disponibles en cardiología",
        "Quisiera saber qué doctores atienden hoy",
        "Buenos días, me puede decir los horarios del doctor Huamán",
        "Cuáles son los especialistas que atienden en la tarde",
        "Hola, necesito saber qué pediatras están atendiendo esta semana",
        "Quiero conocer la disponibilidad del Dr. Ramírez para esta semana",
        "Qué días atiende el ginecólogo en el hospital",
        "Buenas tardes, me informa los médicos disponibles para hoy por favor",
        "Necesito saber qué traumatólogo recomiendan para mi lesión",
        "Podría darme información sobre los doctores de la especialidad de neurología",
    ],
    "emergencia": [
        "Ayuda, es una emergencia, mi papá se cayó y no puede moverse",
        "Tengo un dolor muy fuerte en el pecho, necesito atención urgente",
        "Emergencia por favor, mi hijo se está ahogando",
        "Necesito atención inmediata, estoy sangrando mucho",
        "Por favor ayuda urgente, un familiar tuvo un accidente",
        "Es una urgencia, tengo fiebre muy alta que no baja con nada",
        "Mi mamá se desmayó, necesito que la atiendan urgente",
        "Tengo una herida profunda en el brazo, necesito ayuda ya",
        "Emergencia, creo que estoy teniendo un infarto",
        "Por favor rápido, mi bebé tiene convulsiones",
    ],
    "informacion_servicios": [
        "A qué hora abren el hospital los fines de semana",
        "Cuánto cuesta una consulta particular en el hospital",
        "Aceptan seguro SIS para las consultas externas",
        "Qué documentos necesito para sacar mi cita por primera vez",
        "Dónde queda el laboratorio del hospital",
        "Buenos días, quisiera información sobre los servicios de emergencia",
        "Cómo puedo sacar una cita si soy de otro distrito",
        "Hay farmacia en el hospital o tengo que comprar afuera",
        "Qué especialidades médicas tienen disponibles",
        "Cuál es el costo de un electrocardiograma",
    ],
    "queja_reclamo": [
        "Quiero hacer una queja por la demora en la atención",
        "Buenos días, deseo presentar un reclamo sobre mi última cita",
        "No estoy conforme con la atención recibida ayer en emergencia",
        "Quiero reportar que el doctor no llegó a mi cita programada",
        "Hola, necesito hacer un reclamo porque perdí mi cita por mala información",
        "La atención en admisión fue muy lenta, quiero quejarme formalmente",
        "Me atendieron mal en el laboratorio, quiero presentar mi queja",
        "El médico me canceló la cita sin avisar, quiero reportarlo",
    ],
    "resultados_lab": [
        "Quisiera saber si ya están listos mis resultados de laboratorio",
        "Buenos días, vengo a recoger mis análisis de sangre",
        "Ya están disponibles los resultados de mi ecografía",
        "Hola, necesito los resultados de mi examen de orina",
        "Cómo puedo ver mis resultados de laboratorio por internet",
        "Buenas tardes, vengo por los resultados de mi mamografía",
    ],
}

# ============================================================
# 7. GENERACIÓN PRINCIPAL
# ============================================================

def generar_paciente() -> dict:
    genero = random.choice(["M", "F"])
    nombres = NOMBRES_F if genero == "F" else NOMBRES_M
    nombre = random.choice(nombres)
    apellido1 = random.choice(APELLIDOS)
    apellido2 = random.choice(APELLIDOS)
    apellidos = f"{apellido1} {apellido2}"

    edad = int(random.triangular(1, 90, 40))
    edad = max(1, min(99, edad))

    # Fecha de nacimiento
    today = datetime.now()
    nacimiento = today - timedelta(days=edad * 365 + random.randint(0, 364))
    nacimiento_str = nacimiento.strftime("%Y-%m-%d")

    # Documento (DNI peruano: 8 dígitos)
    doc = str(random.randint(10000000, 99999999))

    # Teléfono móvil peruano (9 dígitos, empieza con 9)
    tel = "9" + "".join(random.choices(string.digits, k=8))

    # Email
    email = f"{nombre.lower()}.{apellido1.lower()}{random.randint(1, 999)}@gmail.com"
    email = email.replace(" ", "").replace("á", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u").replace("ñ", "n")

    # Seguro
    seguro = random.choices(
        ["SIS", "EsSalud", "Privado", "Sin seguro"],
        weights=[0.40, 0.30, 0.15, 0.15],
    )[0]

    # Distrito y ubicación
    distrito = random.choices(
        [d[0] for d in DISTRITOS],
        weights=[d[2] for d in DISTRITOS],
    )[0]
    ubigeo = UBIGEO_MAP[distrito]

    # Distancia al hospital
    dist_min, dist_max = DISTANCIAS[distrito]
    distancia = round(random.uniform(dist_min, dist_max), 1)

    # Establecimiento (ponderado al Hospital de Pichanaki)
    # Los pacientes de distritos lejanos van más a su centro local
    if distancia > 50:
        pesos_est = [0.15, 0.10, 0.10, 0.08, 0.08, 0.12, 0.15, 0.08, 0.10, 0.04]
    else:
        pesos_est = [0.38, 0.12, 0.10, 0.06, 0.06, 0.02, 0.05, 0.04, 0.05, 0.12]
    establecimiento = random.choices(
        [e[0] for e in ESTABLECIMIENTOS],
        weights=pesos_est,
    )[0]

    paciente = {
        "genero": genero,
        "nombre": nombre,
        "apellidos": apellidos,
        "edad": edad,
        "fecha_nac": nacimiento_str,
        "documento": doc,
        "telefono": tel,
        "email": email,
        "seguro": seguro,
        "distrito": distrito,
        "ubigeo": ubigeo,
        "distancia_km": distancia,
        "establecimiento": establecimiento,
    }
    return paciente


def generar_cita(paciente: dict) -> dict:
    # Especialidad según edad y género
    if paciente["edad"] < 14:
        especialidad = random.choices(
            ["Pediatría", "Medicina General", "Odontología", "Nutrición"],
            weights=[0.50, 0.25, 0.15, 0.10],
        )[0]
    elif paciente["edad"] > 60:
        especialidad = random.choices(
            ["Cardiología", "Medicina General", "Medicina Interna", "Traumatología",
             "Neumología", "Oftalmología", "Urología", "Endocrinología"],
            weights=[0.20, 0.20, 0.10, 0.15, 0.10, 0.10, 0.08, 0.07],
        )[0]
    else:
        if paciente["genero"] == "F":
            especialidad = random.choices(
                ["Ginecología", "Medicina General", "Dermatología", "Psicología",
                 "Nutrición", "Oftalmología", "Traumatología"],
                weights=[0.20, 0.25, 0.10, 0.15, 0.10, 0.10, 0.10],
            )[0]
        else:
            especialidad = random.choices(
                ["Medicina General", "Cardiología", "Traumatología", "Odontología",
                 "Dermatología", "Oftalmología", "Urología"],
                weights=[0.30, 0.15, 0.15, 0.12, 0.10, 0.10, 0.08],
            )[0]

    # Especialidad de emergencia (4% de las citas - realista)
    if random.random() < 0.04:
        especialidad = "Emergencia"

    # Seleccionar médico de la especialidad
    if especialidad == "Emergencia":
        # Médico de guardia (cualquier especialidad)
        esp_random = random.choice(list(MEDICOS_POR_ESPECIALIDAD.keys()))
        medico_data = random.choice(MEDICOS_POR_ESPECIALIDAD[esp_random])
        cod_medico = random.randint(1, 50)
    else:
        if especialidad in MEDICOS_POR_ESPECIALIDAD:
            medico_data = random.choice(MEDICOS_POR_ESPECIALIDAD[especialidad])
        else:
            esp_fallback = random.choice(list(MEDICOS_POR_ESPECIALIDAD.keys()))
            medico_data = random.choice(MEDICOS_POR_ESPECIALIDAD[esp_fallback])
        cod_medico = random.randint(1, 50)

    medico_nombre = medico_data[0]
    medico_apellido = medico_data[1]
    medico_email = f"{medico_nombre.lower().replace('dr. ', '').replace('dra. ', '').replace('lic. ', '')}.{medico_apellido.lower().replace(' ', '')}@hospitalpichanaki.gob.pe"
    medico_email = medico_email.replace("á", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u").replace("ñ", "n")

    # Diagnóstico CIE-10
    cie_candidatos = [c for c in CIE10 if c[2] == especialidad or especialidad == "Emergencia"]
    if not cie_candidatos:
        cie = random.choice(CIE10)
    else:
        cie = random.choice(cie_candidatos)

    # Síntoma / motivo
    sintoma_random = random.choice(list(MOTIVOS_POR_SINTOMA.keys()))
    motivo = random.choice(MOTIVOS_POR_SINTOMA[sintoma_random])

    # Tipo de cita
    tipo_cita = random.choices(
        ["control", "primera_vez", "resultados"],
        weights=[0.55, 0.35, 0.10],
    )[0]
    if especialidad == "Emergencia":
        tipo_cita = "emergencia"

    # Prioridad
    if especialidad == "Emergencia" or sintoma_random in ["dolor en el pecho", "herida", "fiebre"]:
        prioridad = random.choices(["alta", "media", "baja"], weights=[0.60, 0.30, 0.10])[0]
    elif paciente["edad"] > 70:
        prioridad = random.choices(["alta", "media", "baja"], weights=[0.30, 0.50, 0.20])[0]
    else:
        prioridad = random.choices(["alta", "media", "baja"], weights=[0.10, 0.40, 0.50])[0]

    # Canal de atención
    canal = random.choices(
        ["web", "telefono", "voz_ia", "presencial", "whatsapp"],
        weights=[0.25, 0.22, 0.20, 0.18, 0.15],
    )[0]

    # Fecha de la cita (entre 30 días atrás y 60 días adelante)
    dias_offset = random.randint(-30, 60)
    fecha_cita = datetime.now() + timedelta(days=dias_offset)

    # Turno
    if random.random() < 0.55:
        hora = random.randint(7, 12)
        turno = "manana"
        minuto = random.choice([0, 15, 30, 45])
    else:
        hora = random.randint(13, 18)
        turno = "tarde"
        minuto = random.choice([0, 15, 30, 45])

    fecha_hora_cita = fecha_cita.replace(hour=hora, minute=minuto, second=0, microsecond=0)

    # Estado de la cita
    if fecha_hora_cita > datetime.now():
        estado = random.choices(
            ["pending", "confirmed", "cancelled", "rescheduled"],
            weights=[0.35, 0.40, 0.15, 0.10],
        )[0]
    else:
        estado = random.choices(
            ["completed", "cancelled", "no_show"],
            weights=[0.60, 0.25, 0.15],
        )[0]

    # No-show previo (basado en edad, distancia, seguro)
    no_show_prev = 0
    if paciente["distancia_km"] > 40:
        no_show_prev += random.randint(0, 2)
    if paciente["seguro"] == "Sin seguro":
        no_show_prev += random.randint(0, 1)
    if paciente["edad"] < 5 or paciente["edad"] > 75:
        no_show_prev += random.randint(0, 1)
    no_show_prev = min(no_show_prev, 5)

    # Días hasta la cita
    dias_hasta = max(0, (fecha_hora_cita - datetime.now()).days)

    # Minutos de espera estimados
    minutos_espera = int(random.triangular(5, 120, 30))

    # Nivel de riesgo (basado en features - distribución realista)
    score_riesgo = 0
    if no_show_prev >= 1:
        score_riesgo += no_show_prev * 12
    if paciente["distancia_km"] > 30:
        score_riesgo += 10 + (paciente["distancia_km"] - 30) * 0.5
    if dias_hasta > 14:
        score_riesgo += 8 + (dias_hasta - 14) * 0.3
    if paciente["seguro"] == "Sin seguro":
        score_riesgo += 18
    if minutos_espera > 45:
        score_riesgo += 8 + (minutos_espera - 45) * 0.2
    if paciente["edad"] < 10 or paciente["edad"] > 70:
        score_riesgo += 12
    if turno == "tarde":
        score_riesgo += 5
    score_riesgo += random.gauss(0, 10)
    score_riesgo = max(0, min(100, round(score_riesgo, 1)))

    # Asignación balanceada para mejor entrenamiento del modelo
    rand = random.random()
    if score_riesgo < 25:
        nivel_riesgo = random.choices(["bajo", "medio", "alto"], weights=[0.70, 0.22, 0.08])[0]
    elif score_riesgo < 45:
        nivel_riesgo = random.choices(["bajo", "medio", "alto"], weights=[0.35, 0.45, 0.20])[0]
    elif score_riesgo < 65:
        nivel_riesgo = random.choices(["bajo", "medio", "alto"], weights=[0.15, 0.40, 0.45])[0]
    else:
        nivel_riesgo = random.choices(["bajo", "medio", "alto"], weights=[0.05, 0.25, 0.70])[0]

    # no_show_target basado en nivel de riesgo
    if nivel_riesgo == "bajo":
        no_show_target = 1 if random.random() < 0.10 else 0
    elif nivel_riesgo == "medio":
        no_show_target = 1 if random.random() < 0.40 else 0
    else:
        no_show_target = 1 if random.random() < 0.75 else 0

    # Ticket
    ticket_code = f"PICHANAKI-TCK-{random.randint(100000, 999999)}"
    ticket_confirmado = estado == "confirmed"

    # Notificaciones
    notif_email = random.random() < 0.85
    notif_sms = random.random() < 0.30

    cita = {
        "paciente_id": None,  # se asigna después
        "medico_id": cod_medico,
        "medico_nombre": medico_nombre,
        "medico_apellido": medico_apellido,
        "medico_email": medico_email,
        "especialidad": especialidad,
        "cie_codigo": cie[0],
        "cie_descripcion": cie[1],
        "sintoma": sintoma_random,
        "motivo": motivo,
        "tipo_cita": tipo_cita,
        "fecha": fecha_hora_cita.strftime("%Y-%m-%d"),
        "hora": fecha_hora_cita.strftime("%H:%M"),
        "turno": turno,
        "fecha_completa": fecha_hora_cita.strftime("%Y-%m-%d %H:%M:%S"),
        "estado": estado,
        "prioridad": prioridad,
        "canal": canal,
        "no_show_previo": no_show_prev,
        "dias_hasta_cita": dias_hasta,
        "minutos_espera": minutos_espera,
        "score_riesgo": score_riesgo,
        "nivel_riesgo": nivel_riesgo,
        "no_show_target": no_show_target,
        "ticket_code": ticket_code,
        "ticket_confirmado": ticket_confirmado,
        "notif_email": notif_email,
        "notif_sms": notif_sms,
    }
    return cita


def generar_texto_voz(intent: str, paciente: dict, cita: dict) -> str:
    """Genera un texto de voz realista basado en el intent y datos del paciente."""
    textos_base = TEXTOS_POR_INTENT.get(intent, ["Consulta médica general"])

    # Personalizar el texto con datos del paciente para que sea más realista
    texto = random.choice(textos_base)

    # A veces agregar datos personales al texto
    if random.random() < 0.25:
        nombre_pac = f"{paciente['nombre']} {paciente['apellidos']}"
        texto = texto.replace("mi mamá", f"mi mamá {nombre_pac}")
        texto = texto.replace("mi papá", f"mi papá {nombre_pac}")

    return texto


def main():
    NUM_REGISTROS = 5000

    # Lista de intents con sus pesos
    intents_disponibles = [
        "agendar_cita", "consultar_cita", "cancelar_cita",
        "reprogramar_cita", "consultar_doctor", "emergencia",
        "informacion_servicios", "queja_reclamo", "resultados_lab",
    ]
    pesos_intents = [0.32, 0.20, 0.12, 0.10, 0.10, 0.05, 0.05, 0.03, 0.03]

    columns = [
        # Metadata
        "record_id", "country", "region", "province", "district", "ubigeo",
        "health_facility", "health_facility_type",
        # Paciente
        "patient_id", "patient_first_name", "patient_last_name",
        "patient_document_number", "patient_gender", "gender",
        "patient_age", "patient_birth_date", "patient_phone",
        "patient_email", "insurance_type",
        # Médico
        "doctor_id", "doctor_full_name", "doctor_specialty", "specialty",
        "doctor_email",
        # Cita
        "appointment_id", "appointment_code", "appointment_type",
        "appointment_date", "appointment_time", "appointment_shift",
        "scheduled_at", "appointment_status", "status", "priority",
        "reason", "symptom", "cie10_code", "cie10_description",
        # Canal y voz
        "channel", "voice_text", "text", "intent",
        # Ticket
        "ticket_code", "ticket_confirmed",
        # Notificaciones
        "notification_email_sent", "notification_sms_sent",
        # ML features
        "previous_no_show_count", "distance_km",
        "days_until_appointment", "waiting_minutes_estimated",
        "risk_score", "risk_level", "no_show_target",
        # Fechas
        "created_at",
    ]

    pacientes_cache: list[dict] = []
    records: list[list] = []
    ahora = datetime.now()

    for i in range(1, NUM_REGISTROS + 1):
        # Generar o reutilizar paciente
        if random.random() < 0.70 or not pacientes_cache:
            paciente = generar_paciente()
            pacientes_cache.append(paciente)
            paciente_id = len(pacientes_cache)
        else:
            paciente = random.choice(pacientes_cache)
            paciente_id = pacientes_cache.index(paciente) + 1

        # Generar cita
        cita = generar_cita(paciente)

        # Intent (para entrenamiento del LSTM)
        intent = random.choices(intents_disponibles, weights=pesos_intents)[0]

        # Asignar intent según el contexto si es necesario
        if cita["estado"] == "cancelled" and random.random() < 0.40:
            intent = "cancelar_cita"
        elif cita["estado"] == "no_show" and random.random() < 0.30:
            intent = "reprogramar_cita"
        elif cita["tipo_cita"] == "emergencia":
            intent = "emergencia"

        # Texto de voz
        texto = generar_texto_voz(intent, paciente, cita)

        # Si el canal es voz_ia, el texto es la transcripción
        if cita["canal"] == "voz_ia":
            texto_mostrar = texto
        else:
            texto_mostrar = texto

        # Códigos
        app_code = f"PICHANAKI-CIT-{i:06d}"

        record = [
            # Metadata
            i, "Peru", REGION, PROVINCIA, paciente["distrito"], paciente["ubigeo"],
            paciente["establecimiento"],
            # Tipo de establecimiento
            [e[1] for e in ESTABLECIMIENTOS if e[0] == paciente["establecimiento"]][0]
            if paciente["establecimiento"] in [e[0] for e in ESTABLECIMIENTOS] else "Centro de Salud",
            # Paciente
            paciente_id, paciente["nombre"], paciente["apellidos"],
            paciente["documento"], paciente["genero"], paciente["genero"],
            paciente["edad"], paciente["fecha_nac"],
            paciente["telefono"], paciente["email"], paciente["seguro"],
            # Médico
            cita["medico_id"],
            f"{cita['medico_nombre']} {cita['medico_apellido']}",
            cita["especialidad"], cita["especialidad"],
            cita["medico_email"],
            # Cita
            i, app_code, cita["tipo_cita"],
            cita["fecha"], cita["hora"], cita["turno"],
            cita["fecha_completa"],
            cita["estado"], cita["estado"], cita["prioridad"],
            cita["motivo"], cita["sintoma"],
            cita["cie_codigo"], cita["cie_descripcion"],
            # Canal y voz
            cita["canal"], texto_mostrar, texto_mostrar, intent,
            # Ticket
            cita["ticket_code"], 1 if cita["ticket_confirmado"] else 0,
            # Notificaciones
            1 if cita["notif_email"] else 0,
            1 if cita["notif_sms"] else 0,
            # ML features
            cita["no_show_previo"], paciente["distancia_km"],
            cita["dias_hasta_cita"], cita["minutos_espera"],
            cita["score_riesgo"], cita["nivel_riesgo"],
            cita["no_show_target"],
            # Fecha de creación (entre 1 y 60 días antes de la cita)
            (ahora - timedelta(days=random.randint(0, 60))).strftime("%Y-%m-%d %H:%M:%S"),
        ]
        records.append(record)

    # Guardar CSV
    output_path = "app/ml/datasets/citas_medicas_pichanaki_junin_5000.csv"
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(columns)
        writer.writerows(records)

    print(f"[OK] Dataset generado: {output_path}")
    print(f"[DATA] Total registros: {len(records)}")
    print(f"[DATA] Pacientes unicos: {len(pacientes_cache)}")
    print(f"[DATA] Columnas: {len(columns)}")

    # Estadísticas rápidas
    from collections import Counter
    intents_count = Counter(r[columns.index("intent")] for r in records)
    risk_count = Counter(r[columns.index("risk_level")] for r in records)
    status_count = Counter(r[columns.index("appointment_status")] for r in records)
    channel_count = Counter(r[columns.index("channel")] for r in records)
    spec_count = Counter(r[columns.index("specialty")] for r in records)

    print("\n=== INTENTS ===")
    for intent, count in intents_count.most_common():
        print(f"  {intent}: {count} ({count*100//len(records)}%)")
    print("\n=== RIESGOS ===")
    for risk, count in risk_count.most_common():
        print(f"  {risk}: {count} ({count*100//len(records)}%)")
    print("\n=== ESTADOS ===")
    for status, count in status_count.most_common():
        print(f"  {status}: {count} ({count*100//len(records)}%)")
    print("\n=== CANALES ===")
    for ch, count in channel_count.most_common():
        print(f"  {ch}: {count} ({count*100//len(records)}%)")
    print("\n=== TOP 10 ESPECIALIDADES ===")
    for sp, count in spec_count.most_common(10):
        print(f"  {sp}: {count}")


if __name__ == "__main__":
    main()
