-- ============================================================
-- PostgreSQL Dump for Supabase
-- Converted from MySQL/MariaDB (citas_medicas)
-- ============================================================

BEGIN;

-- --------------------------------------------------------
-- Table: medicos
-- --------------------------------------------------------
CREATE TABLE medicos (
    id SERIAL PRIMARY KEY,
    nombres VARCHAR(100) NOT NULL,
    apellidos VARCHAR(100) NOT NULL,
    especialidad VARCHAR(120) NOT NULL,
    correo VARCHAR(255) NOT NULL,
    creado_en TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_medicos_correo UNIQUE (correo)
);

CREATE INDEX idx_medicos_especialidad ON medicos (especialidad);
CREATE INDEX idx_medicos_correo ON medicos (correo);

INSERT INTO medicos (id, nombres, apellidos, especialidad, correo, creado_en) VALUES
(23, 'Jean Pierre Eli', 'Rojas Machuca', 'tbc', 'rojamachuca@gmail.com', '2026-05-30 22:24:14'),
(24, 'José Luis', 'Quispe Mamani', 'neumología', 'joseluisquispemamani@gmail.com', '2026-05-30 23:09:16'),
(25, 'Dr', 'Test', 'Medicina General', 'drflow@test.com', '2026-06-01 21:18:31'),
(26, 'Pedro', 'Luna', 'Medicina General', 'pedro@test.com', '2026-06-01 21:54:31'),
(27, 'Jhandel Jesús', 'Chávez Miranda', 'RBC', 'jhandel@gmail.com', '2026-06-02 04:41:10');

ALTER SEQUENCE medicos_id_seq RESTART WITH 28;

-- --------------------------------------------------------
-- Table: pacientes
-- --------------------------------------------------------
CREATE TABLE pacientes (
    id SERIAL PRIMARY KEY,
    nombres VARCHAR(100) NOT NULL,
    apellidos VARCHAR(100) NOT NULL,
    numero_documento VARCHAR(20) NOT NULL,
    correo VARCHAR(255) NOT NULL,
    telefono VARCHAR(20) NOT NULL,
    fecha_nacimiento DATE NOT NULL,
    creado_en TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    genero VARCHAR(20) DEFAULT NULL,
    CONSTRAINT uq_pacientes_numero_documento UNIQUE (numero_documento),
    CONSTRAINT uq_pacientes_correo UNIQUE (correo)
);

CREATE INDEX idx_pacientes_correo ON pacientes (correo);

INSERT INTO pacientes (id, nombres, apellidos, numero_documento, correo, telefono, fecha_nacimiento, creado_en, genero) VALUES
(22, 'José Antonio', 'Sánchez Carvajal', '60001939', 'joseantoniocarvajal@gmail.com', '918123315', '2005-08-10', '2026-05-31 15:44:15', 'M'),
(28, 'jover Cuba', 'Huamán', '12 15 16 20', 'yoduermeelkiadeesa@gmail.com', '962584321', '1983-08-10', '2026-06-02 02:37:05', 'masculino'),
(29, 'José Luis', 'Chávez Páez', '60 58 19 32', 'joseluispaez@gmail.com', '918501302', '2006-01-01', '2026-06-02 03:19:47', 'Dino'),
(30, 'Kevin', 'Junior', '15121314', 'osco@gmail.com', '987132831', '2006-05-12', '2026-06-02 05:00:41', 'M'),
(31, 'Luis Utos', 'Alberto Ceras', '11231516', 'luisutoceras@gmail.com', '918512301', '2002-05-03', '2026-06-02 13:36:07', 'masculino'),
(32, 'Osnar Balvin', 'Pacheco Hinostroza', '60001859', 'osmarbalvinpacheco@gmail.com', '915312618', '2006-06-11', '2026-06-02 14:18:56', 'masculino'),
(33, 'Jaime Pedrito', 'González Maldini', '68834759', 'jaimegonza@gmail.com', '962512833', '2008-05-15', '2026-06-02 15:31:14', 'masculino'),
(34, 'Leonardo', 'Velis Vivas', '60003952', 'jhandeljesuschavezmiranda4@gmail.com', '901512302', '2006-11-16', '2026-06-02 15:57:16', 'masculino'),
(35, 'arrancar', 'huamaní', '8 7 6 5 4 3 2 1 0', 'arrancarguarani4@gmail.com', '972318512', '2002-08-24', '2026-06-02 16:08:45', 'masculino');

ALTER SEQUENCE pacientes_id_seq RESTART WITH 36;

-- --------------------------------------------------------
-- Table: citas
-- --------------------------------------------------------
CREATE TABLE citas (
    id SERIAL PRIMARY KEY,
    paciente_id INTEGER NOT NULL,
    medico_id INTEGER NOT NULL,
    programada_en TIMESTAMP NOT NULL,
    estado VARCHAR(20) NOT NULL DEFAULT 'pendiente' CHECK (estado IN ('pendiente', 'confirmada', 'cancelada', 'reprogramada')),
    motivo VARCHAR(255) NOT NULL,
    creado_en TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_citas_medico_horario UNIQUE (medico_id, programada_en)
);

CREATE INDEX idx_citas_paciente_id ON citas (paciente_id);
CREATE INDEX idx_citas_programada_en ON citas (programada_en);
CREATE INDEX idx_citas_estado ON citas (estado);

INSERT INTO citas (id, paciente_id, medico_id, programada_en, estado, motivo, creado_en) VALUES
(41, 29, 24, '2026-06-02 15:30:00', 'confirmada', 'dolor pulmonar', '2026-06-01 23:26:46'),
(42, 28, 26, '2026-06-24 17:20:00', 'confirmada', 'Problemas psicologicos.', '2026-06-02 00:04:36'),
(43, 33, 25, '2026-06-10 11:40:00', 'confirmada', 'control general', '2026-06-02 10:35:17'),
(44, 34, 24, '2026-07-24 11:40:00', 'confirmada', 'dolor pulmonar', '2026-06-02 11:01:10'),
(45, 30, 24, '2026-06-03 08:10:00', 'confirmada', 'dolor de pecho', '2026-06-02 12:20:54');

ALTER SEQUENCE citas_id_seq RESTART WITH 46;

-- --------------------------------------------------------
-- Table: tickets
-- --------------------------------------------------------
CREATE TABLE tickets (
    id SERIAL PRIMARY KEY,
    cita_id INTEGER NOT NULL,
    codigo VARCHAR(30) NOT NULL,
    esta_confirmado BOOLEAN NOT NULL DEFAULT FALSE,
    emitido_en TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_tickets_cita_id UNIQUE (cita_id),
    CONSTRAINT uq_tickets_codigo UNIQUE (codigo)
);

CREATE INDEX idx_tickets_codigo ON tickets (codigo);

INSERT INTO tickets (id, cita_id, codigo, esta_confirmado, emitido_en) VALUES
(7, 41, 'PICHANAKI-TCK-000041', TRUE, '2026-06-02 04:27:33'),
(8, 43, 'PICHANAKI-TCK-000043', TRUE, '2026-06-02 15:35:17'),
(9, 44, 'PICHANAKI-TCK-000044', TRUE, '2026-06-02 16:01:10'),
(10, 45, 'PICHANAKI-TCK-000045', TRUE, '2026-06-02 17:20:54'),
(11, 42, 'PICHANAKI-TCK-000042', TRUE, '2026-06-02 17:47:08');

ALTER SEQUENCE tickets_id_seq RESTART WITH 12;

-- --------------------------------------------------------
-- Table: historial_asistencia
-- --------------------------------------------------------
CREATE TABLE historial_asistencia (
    id SERIAL PRIMARY KEY,
    paciente_id INTEGER NOT NULL,
    cita_id INTEGER NOT NULL,
    asistio BOOLEAN NOT NULL,
    creado_en TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_historial_paciente_id ON historial_asistencia (paciente_id);
CREATE INDEX idx_historial_cita_id ON historial_asistencia (cita_id);

INSERT INTO historial_asistencia (id, paciente_id, cita_id, asistio, creado_en) VALUES
(1, 33, 43, FALSE, '2026-06-02 12:47:40'),
(2, 30, 45, TRUE, '2026-06-02 12:48:02');

ALTER SEQUENCE historial_asistencia_id_seq RESTART WITH 3;

-- --------------------------------------------------------
-- Table: registro_modelos_ml
-- --------------------------------------------------------
CREATE TABLE registro_modelos_ml (
    id SERIAL PRIMARY KEY,
    nombre_modelo VARCHAR(100) NOT NULL,
    tipo_modelo VARCHAR(100) NOT NULL,
    ruta_modelo VARCHAR(255) NOT NULL,
    ruta_dataset VARCHAR(255) DEFAULT NULL,
    caracteristicas_json JSONB NOT NULL,
    metricas_json JSONB DEFAULT NULL,
    esta_activo BOOLEAN NOT NULL DEFAULT TRUE,
    entrenado_en TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO registro_modelos_ml (id, nombre_modelo, tipo_modelo, ruta_modelo, ruta_dataset, caracteristicas_json, metricas_json, esta_activo, entrenado_en) VALUES
(1, 'no_show_risk_model', 'clasificacion_binaria', 'C:\\xampp\\htdocs\\proj_light\\app\\ml\\models\\no_show_risk_model.pkl', NULL, '{"edad_paciente": "int", "genero": "str", "especialidad": "str", "prioridad": "str", "turno_cita": "str", "conteo_inasistencias_previas": "int", "distancia_km": "float", "dias_hasta_cita": "int", "minutos_espera_estimados": "int"}'::jsonb, 'null'::jsonb, TRUE, '2026-06-02 17:41:42');

ALTER SEQUENCE registro_modelos_ml_id_seq RESTART WITH 2;

-- --------------------------------------------------------
-- Table: predicciones_riesgo_citas
-- --------------------------------------------------------
CREATE TABLE predicciones_riesgo_citas (
    id SERIAL PRIMARY KEY,
    cita_id INTEGER DEFAULT NULL,
    paciente_id INTEGER NOT NULL,
    medico_id INTEGER DEFAULT NULL,
    edad_paciente INTEGER NOT NULL,
    genero VARCHAR(10) NOT NULL,
    especialidad VARCHAR(120) NOT NULL,
    prioridad VARCHAR(20) NOT NULL,
    turno_cita VARCHAR(20) NOT NULL,
    conteo_inasistencias_previas INTEGER NOT NULL DEFAULT 0,
    distancia_km DECIMAL(6,2) NOT NULL,
    dias_hasta_cita INTEGER NOT NULL,
    minutos_espera_estimados INTEGER NOT NULL,
    nivel_riesgo VARCHAR(20) NOT NULL,
    probabilidad_riesgo DECIMAL(5,2) NOT NULL,
    confianza DECIMAL(5,2) DEFAULT NULL,
    nombre_modelo VARCHAR(100) NOT NULL,
    creado_en TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_riesgo_paciente_id ON predicciones_riesgo_citas (paciente_id);
CREATE INDEX idx_riesgo_cita_id ON predicciones_riesgo_citas (cita_id);
CREATE INDEX fk_riesgo_medico ON predicciones_riesgo_citas (medico_id);

INSERT INTO predicciones_riesgo_citas (id, cita_id, paciente_id, medico_id, edad_paciente, genero, especialidad, prioridad, turno_cita, conteo_inasistencias_previas, distancia_km, dias_hasta_cita, minutos_espera_estimados, nivel_riesgo, probabilidad_riesgo, confianza, nombre_modelo, creado_en) VALUES
(3, NULL, 22, 23, 20, 'M', 'tbc', 'alta', 'manana', 2, 5.00, 9, 20, 'bajo', 0.86, 0.86, 'random_forest_ml', '2026-06-01 17:35:44'),
(5, 41, 29, 24, 20, 'M', 'Neumología', 'media', 'tarde', 0, 0.00, 1, 60, 'bajo', 0.91, 0.91, 'random_forest_ml', '2026-06-01 23:26:46'),
(6, 42, 28, 26, 42, 'M', 'Medicina General', 'media', 'tarde', 2, 19.00, 23, 30, 'bajo', 0.93, 0.93, 'random_forest_ml', '2026-06-02 00:04:36');

ALTER SEQUENCE predicciones_riesgo_citas_id_seq RESTART WITH 7;

-- --------------------------------------------------------
-- Table: registros_notificaciones
-- --------------------------------------------------------
CREATE TABLE registros_notificaciones (
    id SERIAL PRIMARY KEY,
    cita_id INTEGER DEFAULT NULL,
    ticket_id INTEGER DEFAULT NULL,
    correo_destinatario VARCHAR(255) NOT NULL,
    tipo_destinatario VARCHAR(30) NOT NULL,
    asunto VARCHAR(255) NOT NULL,
    estado VARCHAR(30) NOT NULL,
    mensaje_error TEXT DEFAULT NULL,
    enviado_en TIMESTAMP DEFAULT NULL,
    creado_en TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_notificacion_cita ON registros_notificaciones (cita_id);
CREATE INDEX fk_notificacion_ticket ON registros_notificaciones (ticket_id);

INSERT INTO registros_notificaciones (id, cita_id, ticket_id, correo_destinatario, tipo_destinatario, asunto, estado, mensaje_error, enviado_en, creado_en) VALUES
(7, 41, 7, 'joseluispaez@gmail.com', 'paciente', 'Confirmación de cita médica - Hospital de Pichanaki', 'registrado', NULL, NULL, '2026-06-01 23:27:40'),
(8, 41, 7, 'joseluisquispemamani@gmail.com', 'medico', 'Nueva cita médica asignada - Hospital de Pichanaki', 'registrado', NULL, NULL, '2026-06-01 23:27:40'),
(9, 42, 11, 'yoduermeelkiadeesa@gmail.com', 'paciente', 'Confirmación de cita médica - Hospital de Pichanaki', 'enviado', NULL, '2026-06-02 17:47:15', '2026-06-02 12:47:15'),
(10, 42, 11, 'pedro@test.com', 'medico', 'Nueva cita médica asignada - Hospital de Pichanaki', 'enviado', NULL, '2026-06-02 17:47:15', '2026-06-02 12:47:15');

ALTER SEQUENCE registros_notificaciones_id_seq RESTART WITH 11;

-- --------------------------------------------------------
-- Table: sesiones_asistente
-- --------------------------------------------------------
CREATE TABLE sesiones_asistente (
    id SERIAL PRIMARY KEY,
    usuario_id INTEGER DEFAULT NULL,
    clave_sesion VARCHAR(100) NOT NULL,
    intencion_actual VARCHAR(100) DEFAULT NULL,
    entidad_actual VARCHAR(100) DEFAULT NULL,
    paso VARCHAR(100) DEFAULT NULL,
    estado_json JSONB NOT NULL,
    esta_activa BOOLEAN NOT NULL DEFAULT TRUE,
    creado_en TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    actualizado_en TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_sesion_asistente_clave UNIQUE (clave_sesion)
);

INSERT INTO sesiones_asistente (id, usuario_id, clave_sesion, intencion_actual, entidad_actual, paso, estado_json, esta_activa, creado_en, actualizado_en) VALUES
(1, 1, '1', 'agendar_cita', NULL, NULL, '{"pending": {"intent": "agendar_cita", "entities": {"patient": null, "patient_id": null, "doctor": null, "doctor_id": null, "specialty": null, "date": null, "time": null, "reason": null, "distance_km": null, "_original_text": "Agendar cita m\u00e9dica para Jos\u00e9 Freddy", "_pending_patient": {"first_name": "Michael", "last_name": "Jerem\u00edas", "document_number": "60005739", "phone": "999888666"}, "_pending_patient_confirmation": true, "_patient_step": "email"}, "text": "jerem\u00edas@gmail.com"}, "_historial": [{"role": "user", "text": "Agendar cita m\u00e9dica"}, {"role": "assistant", "text": "Jhandel Jes\u00fas Chavez Miranda, \u00bfpara qu\u00e9 paciente desea agendar la cita?", "type": "info", "intent": "agendar_cita"}, {"role": "user", "text": "Michael Jerem\u00edas"}, {"role": "assistant", "text": "Jhandel Jes\u00fas Chavez Miranda, no encontr\u00e9 al paciente **Michael Jerem\u00edas**. \u00bfDeseas crearlo?", "type": "info", "intent": "agendar_cita"}, {"role": "user", "text": "s\u00ed"}, {"role": "assistant", "text": "Jhandel Jes\u00fas Chavez Miranda, el **n\u00famero de DNI**. Ej: ''12345678''", "type": "info", "intent": "agendar_cita"}, {"role": "user", "text": "60 0057 39"}, {"role": "assistant", "text": "Jhandel Jes\u00fas Chavez Miranda, el **n\u00famero de tel\u00e9fono**. Ej: ''987654321''", "type": "info", "intent": "agendar_cita"}, {"role": "user", "text": "999 888 666"}, {"role": "assistant", "text": "Jhandel Jes\u00fas Chavez Miranda, el **correo electr\u00f3nico**. Ej: ''rocio@correo.pe''", "type": "info", "intent": "agendar_cita"}, {"role": "user", "text": "Michael Jerem\u00edas gui\u00f3n@gmail.com"}, {"role": "assistant", "text": "Jhandel Jes\u00fas Chavez Miranda, el **correo electr\u00f3nico**. Ej: ''rocio@correo.pe''", "type": "info", "intent": "agendar_cita"}, {"role": "user", "text": "Michael Jerem\u00edas"}, {"role": "assistant", "text": "Jhandel Jes\u00fas Chavez Miranda, el **correo electr\u00f3nico**. Ej: ''rocio@correo.pe''", "type": "info", "intent": "agendar_cita"}, {"role": "user", "text": "Michael arroba gmail.com"}, {"role": "assistant", "text": "Jhandel Jes\u00fas Chavez Miranda, el **correo electr\u00f3nico**. Ej: ''rocio@correo.pe''", "type": "info", "intent": "agendar_cita"}, {"role": "user", "text": "jerem\u00edas@gmail.com"}, {"role": "assistant", "text": "Jhandel Jes\u00fas Chavez Miranda, el **correo electr\u00f3nico**. Ej: ''rocio@correo.pe''", "type": "info", "intent": "agendar_cita"}]}'::jsonb, TRUE, '2026-06-01 15:48:25', '2026-06-02 00:31:58'),
(2, 8, '8', NULL, NULL, NULL, '{"_historial": [{"role": "user", "text": "hola"}, {"role": "assistant", "text": "\u00a1Hola Recepcionista! Soy **La IA**, tu asistente inteligente del Hospital de Pichanaki. \u00bfEn qu\u00e9 puedo ayudarte?\n\nPuedes pedirme: *agendar cita* \u2022 *consultar m\u00e9dico* \u2022 *informaci\u00f3n* \u2022 *emergencia*", "type": "greeting", "intent": "saludo"}]}'::jsonb, FALSE, '2026-06-01 16:55:57', '2026-06-01 16:55:57');

ALTER SEQUENCE sesiones_asistente_id_seq RESTART WITH 3;

-- --------------------------------------------------------
-- Trigger: emula ON UPDATE CURRENT_TIMESTAMP de MySQL
-- --------------------------------------------------------
CREATE OR REPLACE FUNCTION update_actualizado_en_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.actualizado_en = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_sesiones_asistente_actualizado_en ON sesiones_asistente;
CREATE TRIGGER trg_sesiones_asistente_actualizado_en
    BEFORE UPDATE ON sesiones_asistente
    FOR EACH ROW
    EXECUTE FUNCTION update_actualizado_en_column();

-- --------------------------------------------------------
-- Table: usuarios
-- --------------------------------------------------------
CREATE TABLE usuarios (
    id SERIAL PRIMARY KEY,
    nombre_completo VARCHAR(150) NOT NULL,
    correo VARCHAR(255) NOT NULL,
    contrasena_hash VARCHAR(255) NOT NULL,
    rol VARCHAR(30) NOT NULL,
    creado_en TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT ix_usuarios_correo UNIQUE (correo)
);

CREATE INDEX ix_usuarios_id ON usuarios (id);

INSERT INTO usuarios (id, nombre_completo, correo, contrasena_hash, rol, creado_en) VALUES
(1, 'Jhandel Jesús Chavez Miranda', 'admin@hospitalpichanaki.pe', '$2b$12$55AvUlokiJfLX6r5q0bgoeinoFWQVD.QfnFF.P93HLbScA//b2zYC', 'admin', '2026-05-22 12:18:00'),
(2, 'Admin Prueba', 'test@test.com', '$2b$12$lvp7brLtLrWAqcEKf4LpOeJwmRXD1YiJ72UZwjOSmY.HbF9X.wQz6', 'admin', '2026-05-26 08:45:31'),
(3, 'Admin Prueba 2', 'testadmin@test.com', '$2b$12$zuEMKHlskg6qrDtk0AtUP.TlJgkxRqXcWEBCByxUwGw1a1uNpM7YO', 'admin', '2026-05-26 20:35:49'),
(4, 'Admin Prueba', 'admin@hospital.com', '$2b$12$PjygBXYkoxLrZ3n8DovSKOt5KXFzj3oXYSpHnVWXdSXxAP9IHT9MO', 'admin', '2026-05-26 21:18:57'),
(5, '', 'nuevo@admin.com', '$2b$12$jgSaxjUk6LYb.pTniu1l/eGkVKEDxwyv..S9N1gg.ss16QiChSp0q', 'admin', '2026-05-29 08:34:07'),
(6, 'Admin', 'admin@hospital.pe', '$2b$12$30Uyej2GA3c4loI3/kondeIN.Y6iJLMZ6HkvcQUDJG9QK0JViJT3.', 'admin', '2026-05-29 11:54:35'),
(7, 'Prueba Flujo', 'testflow@test.com', '$2b$12$Z91i5O3gfiigsRCoq1wb1OhVhF4oKyUx0RyX3Bd4yitx5IduYBBLy', 'admin', '2026-05-29 14:12:29'),
(8, 'Recepcionista', 'recep@hospital.com', '$2b$12$DBVkc10ILE72R8OqggR90OzHs/cYxRWnePkZWGlXsMMNWppQnicrO', 'recepcion', '2026-06-01 16:55:57');

ALTER SEQUENCE usuarios_id_seq RESTART WITH 9;

-- --------------------------------------------------------
-- Table: versiones_migracion
-- --------------------------------------------------------
CREATE TABLE versiones_migracion (
    numero_version VARCHAR(32) PRIMARY KEY
);

-- --------------------------------------------------------
-- Foreign Key Constraints
-- --------------------------------------------------------

ALTER TABLE citas
    ADD CONSTRAINT fk_citas_paciente FOREIGN KEY (paciente_id) REFERENCES pacientes (id) ON UPDATE CASCADE,
    ADD CONSTRAINT fk_citas_medico FOREIGN KEY (medico_id) REFERENCES medicos (id) ON UPDATE CASCADE;

ALTER TABLE historial_asistencia
    ADD CONSTRAINT fk_historial_paciente FOREIGN KEY (paciente_id) REFERENCES pacientes (id),
    ADD CONSTRAINT fk_historial_cita FOREIGN KEY (cita_id) REFERENCES citas (id);

ALTER TABLE tickets
    ADD CONSTRAINT fk_tickets_cita FOREIGN KEY (cita_id) REFERENCES citas (id) ON DELETE CASCADE ON UPDATE CASCADE;

ALTER TABLE predicciones_riesgo_citas
    ADD CONSTRAINT fk_riesgo_paciente FOREIGN KEY (paciente_id) REFERENCES pacientes (id),
    ADD CONSTRAINT fk_riesgo_cita FOREIGN KEY (cita_id) REFERENCES citas (id),
    ADD CONSTRAINT fk_riesgo_medico FOREIGN KEY (medico_id) REFERENCES medicos (id);

ALTER TABLE registros_notificaciones
    ADD CONSTRAINT fk_notificacion_cita FOREIGN KEY (cita_id) REFERENCES citas (id),
    ADD CONSTRAINT fk_notificacion_ticket FOREIGN KEY (ticket_id) REFERENCES tickets (id);

COMMIT;
