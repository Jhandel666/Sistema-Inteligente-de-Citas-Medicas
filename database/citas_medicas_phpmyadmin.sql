-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Servidor: 127.0.0.1
-- Tiempo de generación: 01-06-2026 a las 15:33:31
-- Versión del servidor: 10.4.32-MariaDB
-- Versión de PHP: 8.2.12

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Base de datos: `citas_medicas`
--

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `citas`
--

CREATE TABLE `citas` (
  `id` int(10) UNSIGNED NOT NULL,
  `paciente_id` int(10) UNSIGNED NOT NULL,
  `medico_id` int(10) UNSIGNED NOT NULL,
  `programada_en` datetime NOT NULL,
  `estado` enum('pendiente','confirmada','cancelada','reprogramada') NOT NULL DEFAULT 'pendiente',
  `motivo` varchar(255) NOT NULL,
  `creado_en` datetime NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `medicos`
--

CREATE TABLE `medicos` (
  `id` int(10) UNSIGNED NOT NULL,
  `nombres` varchar(100) NOT NULL,
  `apellidos` varchar(100) NOT NULL,
  `especialidad` varchar(120) NOT NULL,
  `correo` varchar(255) NOT NULL,
  `creado_en` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Volcado de datos para la tabla `medicos`
--

INSERT INTO `medicos` (`id`, `nombres`, `apellidos`, `especialidad`, `correo`, `creado_en`) VALUES
(23, 'Jean Pierre Eli', 'Rojas Machuca', 'tbc', 'rojamachuca@gmail.com', '2026-05-30 22:24:14'),
(24, 'José Luis', 'Quispe Mamani', 'neumología', 'joseluisquispemamani@gmail.com', '2026-05-30 23:09:16');

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `pacientes`
--

CREATE TABLE `pacientes` (
  `id` int(10) UNSIGNED NOT NULL,
  `nombres` varchar(100) NOT NULL,
  `apellidos` varchar(100) NOT NULL,
  `numero_documento` varchar(20) NOT NULL,
  `correo` varchar(255) NOT NULL,
  `telefono` varchar(20) NOT NULL,
  `fecha_nacimiento` date NOT NULL,
  `creado_en` timestamp NOT NULL DEFAULT current_timestamp(),
  `genero` varchar(20) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Volcado de datos para la tabla `pacientes`
--

INSERT INTO `pacientes` (`id`, `nombres`, `apellidos`, `numero_documento`, `correo`, `telefono`, `fecha_nacimiento`, `creado_en`, `genero`) VALUES
(21, 'Rocío', 'Miranda', '64125816', 'miranda@gmail.com', '988886450', '1986-04-03', '2026-05-30 22:22:49', 'F'),
(22, 'José Antonio', 'Sánchez Carvajal', '60001939', 'joseantoniocarvajal@gmail.com', '918123315', '2005-08-10', '2026-05-31 15:44:15', 'M'),
(23, 'Rosario', 'García', '12233456', 'geraldinerosariogarcia@gmail.com', '917584621', '1990-07-29', '2026-05-31 23:08:02', 'F'),
(24, 'Jhandel Jesús', 'Chávez Miranda', '60005739', 'jhandeljesuschavezmiranda4@gmail.com', '987132831', '2006-11-16', '2026-05-31 23:22:13', 'M');

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `predicciones_riesgo_citas`
--

CREATE TABLE `predicciones_riesgo_citas` (
  `id` int(10) UNSIGNED NOT NULL,
  `cita_id` int(10) UNSIGNED DEFAULT NULL,
  `paciente_id` int(10) UNSIGNED NOT NULL,
  `medico_id` int(10) UNSIGNED DEFAULT NULL,
  `edad_paciente` int(11) NOT NULL,
  `genero` varchar(10) NOT NULL,
  `especialidad` varchar(120) NOT NULL,
  `prioridad` varchar(20) NOT NULL,
  `turno_cita` varchar(20) NOT NULL,
  `conteo_inasistencias_previas` int(11) NOT NULL DEFAULT 0,
  `distancia_km` decimal(6,2) NOT NULL,
  `dias_hasta_cita` int(11) NOT NULL,
  `minutos_espera_estimados` int(11) NOT NULL,
  `nivel_riesgo` varchar(20) NOT NULL,
  `probabilidad_riesgo` decimal(5,2) NOT NULL,
  `confianza` decimal(5,2) DEFAULT NULL,
  `nombre_modelo` varchar(100) NOT NULL,
  `creado_en` datetime NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `registros_notificaciones`
--

CREATE TABLE `registros_notificaciones` (
  `id` int(10) UNSIGNED NOT NULL,
  `cita_id` int(10) UNSIGNED DEFAULT NULL,
  `ticket_id` int(10) UNSIGNED DEFAULT NULL,
  `correo_destinatario` varchar(255) NOT NULL,
  `tipo_destinatario` varchar(30) NOT NULL,
  `asunto` varchar(255) NOT NULL,
  `estado` varchar(30) NOT NULL,
  `mensaje_error` text DEFAULT NULL,
  `enviado_en` datetime DEFAULT NULL,
  `creado_en` datetime NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `registro_modelos_ml`
--

CREATE TABLE `registro_modelos_ml` (
  `id` int(10) UNSIGNED NOT NULL,
  `nombre_modelo` varchar(100) NOT NULL,
  `tipo_modelo` varchar(100) NOT NULL,
  `ruta_modelo` varchar(255) NOT NULL,
  `ruta_dataset` varchar(255) DEFAULT NULL,
  `caracteristicas_json` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL CHECK (json_valid(`caracteristicas_json`)),
  `metricas_json` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL CHECK (json_valid(`metricas_json`)),
  `esta_activo` tinyint(1) NOT NULL DEFAULT 1,
  `entrenado_en` datetime NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `sesiones_asistente`
--

CREATE TABLE `sesiones_asistente` (
  `id` int(10) UNSIGNED NOT NULL,
  `usuario_id` int(11) DEFAULT NULL,
  `clave_sesion` varchar(100) NOT NULL,
  `intencion_actual` varchar(100) DEFAULT NULL,
  `entidad_actual` varchar(100) DEFAULT NULL,
  `paso` varchar(100) DEFAULT NULL,
  `estado_json` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL CHECK (json_valid(`estado_json`)),
  `esta_activa` tinyint(1) NOT NULL DEFAULT 1,
  `creado_en` datetime NOT NULL DEFAULT current_timestamp(),
  `actualizado_en` datetime NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `tickets`
--

CREATE TABLE `tickets` (
  `id` int(10) UNSIGNED NOT NULL,
  `cita_id` int(10) UNSIGNED NOT NULL,
  `codigo` varchar(30) NOT NULL,
  `esta_confirmado` tinyint(1) NOT NULL DEFAULT 0,
  `emitido_en` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `usuarios`
--

CREATE TABLE `usuarios` (
  `id` int(11) NOT NULL,
  `nombre_completo` varchar(150) NOT NULL,
  `correo` varchar(255) NOT NULL,
  `contrasena_hash` varchar(255) NOT NULL,
  `rol` varchar(30) NOT NULL,
  `creado_en` datetime NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Volcado de datos para la tabla `usuarios`
--

INSERT INTO `usuarios` (`id`, `nombre_completo`, `correo`, `contrasena_hash`, `rol`, `creado_en`) VALUES
(1, 'Jhandel Jesús Chavez Miranda', 'admin@hospitalpichanaki.pe', '$2b$12$55AvUlokiJfLX6r5q0bgoeinoFWQVD.QfnFF.P93HLbScA//b2zYC', 'admin', '2026-05-22 12:18:00'),
(2, 'Admin Prueba', 'test@test.com', '$2b$12$lvp7brLtLrWAqcEKf4LpOeJwmRXD1YiJ72UZwjOSmY.HbF9X.wQz6', 'admin', '2026-05-26 08:45:31'),
(3, 'Admin Prueba 2', 'testadmin@test.com', '$2b$12$zuEMKHlskg6qrDtk0AtUP.TlJgkxRqXcWEBCByxUwGw1a1uNpM7YO', 'admin', '2026-05-26 20:35:49'),
(4, 'Admin Prueba', 'admin@hospital.com', '$2b$12$PjygBXYkoxLrZ3n8DovSKOt5KXFzj3oXYSpHnVWXdSXxAP9IHT9MO', 'admin', '2026-05-26 21:18:57'),
(5, '', 'nuevo@admin.com', '$2b$12$jgSaxjUk6LYb.pTniu1l/eGkVKEDxwyv..S9N1gg.ss16QiChSp0q', 'admin', '2026-05-29 08:34:07'),
(6, 'Admin', 'admin@hospital.pe', '$2b$12$30Uyej2GA3c4loI3/kondeIN.Y6iJLMZ6HkvcQUDJG9QK0JViJT3.', 'admin', '2026-05-29 11:54:35'),
(7, 'Prueba Flujo', 'testflow@test.com', '$2b$12$Z91i5O3gfiigsRCoq1wb1OhVhF4oKyUx0RyX3Bd4yitx5IduYBBLy', 'admin', '2026-05-29 14:12:29');

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `versiones_migracion`
--

CREATE TABLE `versiones_migracion` (
  `numero_version` varchar(32) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Índices para tablas volcadas
--

--
-- Indices de la tabla `citas`
--
ALTER TABLE `citas`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `uq_citas_medico_horario` (`medico_id`,`programada_en`),
  ADD KEY `idx_citas_paciente_id` (`paciente_id`),
  ADD KEY `idx_citas_programada_en` (`programada_en`),
  ADD KEY `idx_citas_estado` (`estado`);

--
-- Indices de la tabla `medicos`
--
ALTER TABLE `medicos`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `uq_medicos_correo` (`correo`),
  ADD KEY `idx_medicos_especialidad` (`especialidad`),
  ADD KEY `idx_medicos_correo` (`correo`);

--
-- Indices de la tabla `pacientes`
--
ALTER TABLE `pacientes`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `uq_pacientes_numero_documento` (`numero_documento`),
  ADD UNIQUE KEY `uq_pacientes_correo` (`correo`),
  ADD KEY `idx_pacientes_correo` (`correo`);

--
-- Indices de la tabla `predicciones_riesgo_citas`
--
ALTER TABLE `predicciones_riesgo_citas`
  ADD PRIMARY KEY (`id`),
  ADD KEY `idx_riesgo_paciente_id` (`paciente_id`),
  ADD KEY `idx_riesgo_cita_id` (`cita_id`),
  ADD KEY `fk_riesgo_medico` (`medico_id`);

--
-- Indices de la tabla `registros_notificaciones`
--
ALTER TABLE `registros_notificaciones`
  ADD PRIMARY KEY (`id`),
  ADD KEY `idx_notificacion_cita` (`cita_id`),
  ADD KEY `fk_notificacion_ticket` (`ticket_id`);

--
-- Indices de la tabla `registro_modelos_ml`
--
ALTER TABLE `registro_modelos_ml`
  ADD PRIMARY KEY (`id`);

--
-- Indices de la tabla `sesiones_asistente`
--
ALTER TABLE `sesiones_asistente`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `uq_sesion_asistente_clave` (`clave_sesion`);

--
-- Indices de la tabla `tickets`
--
ALTER TABLE `tickets`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `uq_tickets_cita_id` (`cita_id`),
  ADD UNIQUE KEY `uq_tickets_codigo` (`codigo`),
  ADD KEY `idx_tickets_codigo` (`codigo`);

--
-- Indices de la tabla `usuarios`
--
ALTER TABLE `usuarios`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `ix_usuarios_correo` (`correo`),
  ADD KEY `ix_usuarios_id` (`id`);

--
-- Indices de la tabla `versiones_migracion`
--
ALTER TABLE `versiones_migracion`
  ADD PRIMARY KEY (`numero_version`);

--
-- AUTO_INCREMENT de las tablas volcadas
--

--
-- AUTO_INCREMENT de la tabla `citas`
--
ALTER TABLE `citas`
  MODIFY `id` int(10) UNSIGNED NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=36;

--
-- AUTO_INCREMENT de la tabla `medicos`
--
ALTER TABLE `medicos`
  MODIFY `id` int(10) UNSIGNED NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=25;

--
-- AUTO_INCREMENT de la tabla `pacientes`
--
ALTER TABLE `pacientes`
  MODIFY `id` int(10) UNSIGNED NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=25;

--
-- AUTO_INCREMENT de la tabla `predicciones_riesgo_citas`
--
ALTER TABLE `predicciones_riesgo_citas`
  MODIFY `id` int(10) UNSIGNED NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `registros_notificaciones`
--
ALTER TABLE `registros_notificaciones`
  MODIFY `id` int(10) UNSIGNED NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `registro_modelos_ml`
--
ALTER TABLE `registro_modelos_ml`
  MODIFY `id` int(10) UNSIGNED NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `sesiones_asistente`
--
ALTER TABLE `sesiones_asistente`
  MODIFY `id` int(10) UNSIGNED NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `tickets`
--
ALTER TABLE `tickets`
  MODIFY `id` int(10) UNSIGNED NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=7;

--
-- AUTO_INCREMENT de la tabla `usuarios`
--
ALTER TABLE `usuarios`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=8;

--
-- Restricciones para tablas volcadas
--

--
-- Filtros para la tabla `citas`
--
ALTER TABLE `citas`
  ADD CONSTRAINT `fk_citas_medico` FOREIGN KEY (`medico_id`) REFERENCES `medicos` (`id`) ON UPDATE CASCADE,
  ADD CONSTRAINT `fk_citas_paciente` FOREIGN KEY (`paciente_id`) REFERENCES `pacientes` (`id`) ON UPDATE CASCADE;

--
-- Filtros para la tabla `predicciones_riesgo_citas`
--
ALTER TABLE `predicciones_riesgo_citas`
  ADD CONSTRAINT `fk_riesgo_cita` FOREIGN KEY (`cita_id`) REFERENCES `citas` (`id`),
  ADD CONSTRAINT `fk_riesgo_medico` FOREIGN KEY (`medico_id`) REFERENCES `medicos` (`id`),
  ADD CONSTRAINT `fk_riesgo_paciente` FOREIGN KEY (`paciente_id`) REFERENCES `pacientes` (`id`);

--
-- Filtros para la tabla `registros_notificaciones`
--
ALTER TABLE `registros_notificaciones`
  ADD CONSTRAINT `fk_notificacion_cita` FOREIGN KEY (`cita_id`) REFERENCES `citas` (`id`),
  ADD CONSTRAINT `fk_notificacion_ticket` FOREIGN KEY (`ticket_id`) REFERENCES `tickets` (`id`);

--
-- Filtros para la tabla `tickets`
--
ALTER TABLE `tickets`
  ADD CONSTRAINT `fk_tickets_cita` FOREIGN KEY (`cita_id`) REFERENCES `citas` (`id`) ON DELETE CASCADE ON UPDATE CASCADE;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;

-- --------------------------------------------------------
-- Tabla adicional requerida por el ORM actual para historial de asistencia
-- --------------------------------------------------------
CREATE TABLE IF NOT EXISTS `historial_asistencia` (
  `id` int(10) UNSIGNED NOT NULL AUTO_INCREMENT,
  `paciente_id` int(10) UNSIGNED NOT NULL,
  `cita_id` int(10) UNSIGNED NOT NULL,
  `asistio` tinyint(1) NOT NULL,
  `creado_en` datetime NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  KEY `idx_historial_paciente_id` (`paciente_id`),
  KEY `idx_historial_cita_id` (`cita_id`),
  CONSTRAINT `fk_historial_paciente` FOREIGN KEY (`paciente_id`) REFERENCES `pacientes` (`id`),
  CONSTRAINT `fk_historial_cita` FOREIGN KEY (`cita_id`) REFERENCES `citas` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
