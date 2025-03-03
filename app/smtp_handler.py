import email
from email.policy import default
import time
from threading import Lock

storage = {}
storage_lock = Lock()

class MailHandler:
    async def handle_DATA(self, server, session, envelope):
        try:
            msg_data = envelope.content
            msg = email.message_from_bytes(msg_data, policy=default)
            
            # Extract message details
            mail_from = envelope.mail_from
            rcpt_tos = envelope.rcpt_tos
            subject = msg.get('Subject', '')
            body = self._get_body(msg)
            
            email_data = {
                "from": mail_from,
                "to": rcpt_tos,
                "subject": subject,
                "body": body,
                "timestamp": time.time(),
                "raw": msg_data.decode('utf-8', errors='replace')
            }
            
            with storage_lock:
                for rcpt in rcpt_tos:
                    username = rcpt.split('@')[0]
                    if username not in storage:
                        storage[username] = []
                    storage[username].append(email_data)
            
            return '250 Message accepted for delivery'
        except Exception as e:
            return f'500 Error: {str(e)}'

    def _get_body(self, msg):
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == 'text/plain':
                    return part.get_payload(decode=True).decode()
        return msg.get_payload(decode=True).decode()