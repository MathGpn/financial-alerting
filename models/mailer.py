import smtplib

from datetime import datetime
from typing import List, Optional
from dataclasses import dataclass
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart

from .alert import Alert


@dataclass
class Mailer:

    _smtp_server: str
    _port: int
    _sender_email: str
    _sender_password: str
    _recipient_email: str
    _subject: str
    _alerts: List[Alert]
    _msg: Optional[MIMEMultipart] = None
    _body: Optional[str] = None

    @classmethod
    def create(
        cls,
        smtp_server: str,
        port: int,
        sender_email: str,
        sender_password: str,
        recipient_email: str,
        subject: str,
        alerts: List[Alert]
    ) -> 'Mailer':
        return cls(
            _smtp_server=smtp_server,
            _port=port,
            _sender_email=sender_email,
            _sender_password=sender_password,
            _recipient_email=recipient_email,
            _subject=subject,
            _alerts=alerts
        )

    @property
    def alerts(self) -> List[Alert]:
        return self._alerts

    @property
    def msg(self) -> MIMEMultipart:
        if not self._msg:
            self._msg = MIMEMultipart("related")
            self._msg['Subject'] = f"Alerte Financiere - {datetime.now().strftime('%Y-%m-%d')}"
            self._msg.attach(MIMEText(self.body, "html", "utf-8"))
        
        return self._msg

    @property
    def body(self) -> str:
        html_body = f"""
            <html>
                <body style="margin:0;padding:0;font-family:Arial,Helvetica,sans-serif;background:#f0f2f5;">
                    <div style="max-width:800px;margin:20px auto;padding:0 15px;">
                        <div style="background:linear-gradient(135deg,#34495e,#2ecc71);padding:20px;border-radius:12px 12px 0 0;text-align:center;color:#fff;">
                            <h1 style="margin:0;font-size:26px;">📊 Alerte Financière</h1>
                            <p style="margin:5px 0 0;font-size:14px;">{datetime.now().strftime('%Y-%m-%d')}</p>
                        </div>
        """

        for idx, alert in enumerate(self.alerts):
            # Color coding: red if negative change, green if positive (assuming msg contains percentage)
            color = "#27ae60" if alert.msg and "-" not in alert.msg else "#e74c3c"

            html_body += f"""
                <div style="background:#ffffff;border-radius:10px;padding:18px;margin-top:20px;box-shadow:0 4px 16px rgba(0,0,0,0.08);">
                    <p style="margin:0 0 8px;font-size:16px;">
                        <strong style="font-size:18px;color:#34495e;">{alert.symbol} - {alert.product}</strong>
                    </p>
                    <p style="margin:0 0 12px;font-size:14px;color:{color};line-height:1.5;">
                        {alert.msg}
                    </p>
            """

            if alert.graph:
                html_body += f"""
                    <div style="text-align:center;margin-top:10px;">
                        <img src="cid:chart_{idx}" alt="Chart {idx}" style="max-width:100%;border-radius:8px;border:1px solid #ddd;box-shadow:0 2px 8px rgba(0,0,0,0.05);"/>
                    </div>
                """
                
            html_body += "</div>"

        html_body += """
                    <div style="text-align:center;margin-top:30px;font-size:12px;color:#999;">
                        <p>Envoyé automatiquement par <strong>Le Zêlé</strong></p>
                    </div>
                </div>
            </body>
            </html>
        """
        return html_body

    def add_charts(self):
        if self.alerts:
            for idx, alert in enumerate(self.alerts):
                if alert.graph:
                    img = MIMEImage(alert.graph, _subtype="png")
                    img.add_header("Content-ID", f"<chart_{idx}>")
                    img.add_header("Content-Disposition", "inline", filename=f"chart_{idx}.png")
                    self.msg.attach(img)

    def send(self):
        with smtplib.SMTP_SSL(self._smtp_server, self._port) as server:
            server.ehlo()
            server.login(self._sender_email, self._sender_password)
            if self._msg:
                server.sendmail(
                    self._sender_email,
                    self._recipient_email,
                    self._msg.as_string()
                )