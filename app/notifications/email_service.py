import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class EmailService:
    def send_confirmation_email(
        self,
        to_email: str | None,
        ticket_code: str,
        recipient_type: str,
    ) -> tuple[bool, str]:
        if not to_email or "@" not in to_email:
            logger.warning("Correo no enviado: destinatario inválido para %s", recipient_type)
            return False, "destinatario inválido"

        subject = self._build_subject(recipient_type)
        plain_body = self._build_body(ticket_code, recipient_type)
        html_body = self._build_html_body(ticket_code, recipient_type)

        if not settings.email_notifications_enabled:
            logger.info("EMAIL DESACTIVADO - Para: %s - Asunto: %s", to_email, subject)
            return False, "notificaciones desactivadas"

        missing = []
        if not settings.smtp_host:
            missing.append("SMTP_HOST")
        if not settings.smtp_username:
            missing.append("SMTP_USERNAME")
        if not settings.smtp_password:
            missing.append("SMTP_PASSWORD")
        if not settings.smtp_from:
            missing.append("SMTP_FROM")
        if missing:
            logger.error("No se puede enviar correo. Faltan variables SMTP: %s", ", ".join(missing))
            return False, f"faltan variables SMTP: {', '.join(missing)}"

        message = MIMEMultipart("alternative")
        message["From"] = formataddr(("Hospital de Pichanaki", settings.smtp_from))
        message["To"] = to_email
        message["Subject"] = subject
        message.attach(MIMEText(plain_body, "plain", "utf-8"))
        message.attach(MIMEText(html_body, "html", "utf-8"))

        try:
            with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=20) as server:
                if settings.smtp_use_tls:
                    server.starttls()
                server.login(settings.smtp_username, settings.smtp_password)
                server.sendmail(settings.smtp_from, [to_email], message.as_string())
            logger.info("Correo enviado correctamente a %s", to_email)
            return True, ""
        except Exception as error:
            logger.error("ERROR AL ENVIAR CORREO A %s: %s", to_email, error)
            return False, str(error)

    def _build_subject(self, recipient_type: str) -> str:
        if recipient_type == "medico":
            return "Nueva cita médica asignada - Hospital de Pichanaki"
        return "Confirmación de cita médica - Hospital de Pichanaki"

    def _build_body(self, ticket_code: str, recipient_type: str) -> str:
        if recipient_type == "medico":
            return f"""
Hospital de Pichanaki

Estimado(a) médico(a),

Se le ha asignado una nueva cita médica en el sistema.

Código de ticket:
{ticket_code}

Por favor, revise el panel del sistema para ver los detalles del paciente y horario.

Sistema Inteligente para la Gestión de Citas Médicas
Autor: Jhandel Jesús Chavez Miranda
"""
        return f"""
Hospital de Pichanaki

Estimado(a) paciente,

Su cita médica ha sido confirmada correctamente.

Código de ticket:
{ticket_code}

Conserve este código para su atención en el hospital.

Sistema Inteligente para la Gestión de Citas Médicas
Autor: Jhandel Jesús Chavez Miranda
"""

    def _build_html_body(self, ticket_code: str, recipient_type: str) -> str:
        titulo = "Nueva cita médica asignada" if recipient_type == "medico" else "Cita médica confirmada"
        mensaje = (
            "Se le ha asignado una nueva cita médica en el sistema."
            if recipient_type == "medico"
            else "Su cita médica ha sido confirmada correctamente."
        )
        return f"""
<html>
  <body style="font-family: Arial, sans-serif; color:#1f2937;">
    <h2>Hospital de Pichanaki</h2>
    <h3>{titulo}</h3>
    <p>{mensaje}</p>
    <p><strong>Código de ticket:</strong></p>
    <p style="font-size:20px; background:#f3f4f6; padding:10px; display:inline-block;">{ticket_code}</p>
    <p>Sistema Inteligente para la Gestión de Citas Médicas</p>
    <p><small>Autor: Jhandel Jesús Chavez Miranda</small></p>
  </body>
</html>
"""
