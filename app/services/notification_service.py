from app.notifications.email_service import EmailService


class ServicioNotificaciones:
    def __init__(self, servicio_email: EmailService) -> None:
        self.servicio_email = servicio_email

    def enviar_confirmacion_ticket(
        self,
        correo_paciente: str,
        correo_medico: str,
        codigo_ticket: str,
    ) -> dict[str, tuple[bool, str]]:
        resultado_paciente = self.servicio_email.send_confirmation_email(
            to_email=correo_paciente,
            ticket_code=codigo_ticket,
            recipient_type="paciente",
        )
        resultado_medico = self.servicio_email.send_confirmation_email(
            to_email=correo_medico,
            ticket_code=codigo_ticket,
            recipient_type="medico",
        )
        return {"paciente": resultado_paciente, "medico": resultado_medico}
