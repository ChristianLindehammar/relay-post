from fastapi import FastAPI
from aiosmtpd.controller import Controller
from smtp_handler import MailHandler, storage, storage_lock
import time
from threading import Thread
import uvicorn

app = FastAPI()

def run_smtp():
    handler = MailHandler()
    controller = Controller(handler, hostname='0.0.0.0', port=25)
    controller.start()

def cleanup_old_emails():
    while True:
        time.sleep(60)  # Clean every minute
        current_time = time.time()
        with storage_lock:
            for username in list(storage.keys()):
                storage[username] = [email for email in storage[username]
                    if current_time - email['timestamp'] < 600  # 10 minutes
                ]
                if not storage[username]:
                    del storage[username]

@app.on_event("startup")
async def startup_event():
    # Start SMTP server in background thread
    smtp_thread = Thread(target=run_smtp)
    smtp_thread.daemon = True
    smtp_thread.start()
    
    # Start cleanup thread
    cleanup_thread = Thread(target=cleanup_old_emails)
    cleanup_thread.daemon = True
    cleanup_thread.start()

@app.get("/check/{username}")
async def check_emails(username: str):
    with storage_lock:
        emails = storage.get(username, [])
    return {"emails": emails}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)