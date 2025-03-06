import os
from fastapi import FastAPI
from aiosmtpd.controller import Controller
import time
from threading import Thread
import uvicorn

from app.storage import store_email, get_emails
from app.smtp_handler import MailHandler

app = FastAPI()

def run_smtp():
    handler = MailHandler()
    smtp_port = int(os.environ.get('SMTP_PORT', 25))
    controller = Controller(handler, hostname='0.0.0.0', port=smtp_port)
    controller.start()

@app.on_event("startup")
async def startup_event():
    # Only start SMTP if we're in SMTP mode or full mode
    mode = os.environ.get('SERVICE_MODE', 'full')
    
    if mode in ('smtp', 'full'):
        smtp_thread = Thread(target=run_smtp)
        smtp_thread.daemon = True
        smtp_thread.start()
        
        # No cleanup thread needed as Firebase handles expiration during get_emails

@app.get("/check/{username}")
async def check_emails(username: str):
    emails = get_emails(username)
    return {"emails": emails}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)