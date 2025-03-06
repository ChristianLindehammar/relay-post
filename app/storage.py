import os
import json
import time
import redis
from threading import Thread, Lock

# Storage backend selection - priority order
# 1. Firebase (if configured)
# 2. Redis (if configured)
# 3. Local memory (fallback)

# Get configuration from environment
FIREBASE_CERT_PATH = os.environ.get('FIREBASE_CERT_PATH')
FIREBASE_DB_URL = os.environ.get('FIREBASE_DB_URL')
REDIS_HOST = os.environ.get('REDIS_HOST')
REDIS_PORT = int(os.environ.get('REDIS_PORT', 6379))
REDIS_PASSWORD = os.environ.get('REDIS_PASSWORD', '')

# Local fallback storage
local_storage = {}
local_storage_lock = Lock()

# Initialize storage backends
firebase_available = False
redis_client = None

# Try Firebase first
if FIREBASE_CERT_PATH and FIREBASE_DB_URL:
    try:
        import firebase_admin
        from firebase_admin import credentials, db
        
        cred = credentials.Certificate(FIREBASE_CERT_PATH)
        firebase_admin.initialize_app(cred, {
            'databaseURL': FIREBASE_DB_URL
        })
        firebase_available = True
        print("Firebase initialized successfully")
    except Exception as e:
        print(f"Firebase initialization failed: {e}")

# Try Redis if Firebase is not available
if not firebase_available and REDIS_HOST:
    try:
        redis_client = redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            password=REDIS_PASSWORD,
            decode_responses=True
        )
        redis_client.ping()  # Test connection
        print("Redis initialized successfully")
    except Exception as e:
        print(f"Redis initialization failed: {e}")
        redis_client = None

# Fall back to local storage if neither is available
if not firebase_available and not redis_client:
    print("Using local memory storage (emails will be lost on restart)")
    
    # Start cleanup thread for local storage
    def cleanup_old_emails():
        while True:
            time.sleep(60)  # Check every minute
            try:
                current_time = time.time()
                with local_storage_lock:
                    for username in list(local_storage.keys()):
                        if username in local_storage:
                            local_storage[username] = [
                                email for email in local_storage[username]
                                if email.get('expires_at', 0) > current_time
                            ]
            except Exception as e:
                print(f"Local storage cleanup error: {e}")
    
    cleanup_thread = Thread(target=cleanup_old_emails)
    cleanup_thread.daemon = True
    cleanup_thread.start()

def store_email(username, email_data):
    # Add expiry time (10 minutes)
    email_data['expires_at'] = time.time() + 600  # 10 minutes
    
    # Try Firebase
    if firebase_available:
        try:
            ref = db.reference(f'emails/{username}')
            emails_ref = ref.push()
            emails_ref.set(email_data)
            return
        except Exception as e:
            print(f"Firebase storage error: {e}")
    
    # Try Redis
    if redis_client:
        try:
            key = f"emails:{username}"
            emails_json = redis_client.get(key)
            emails = json.loads(emails_json) if emails_json else []
            emails.append(email_data)
            redis_client.setex(key, 600, json.dumps(emails))
            return
        except Exception as e:
            print(f"Redis storage error: {e}")
    
    # Fall back to local storage
    with local_storage_lock:
        if username not in local_storage:
            local_storage[username] = []
        local_storage[username].append(email_data)

def get_emails(username):
    current_time = time.time()
    
    # Try Firebase
    if firebase_available:
        try:
            ref = db.reference(f'emails/{username}')
            emails_data = ref.get()
            if not emails_data:
                return []
            
            active_emails = []
            for key, email in emails_data.items():
                if email.get('expires_at', 0) > current_time:
                    email['id'] = key  # Include reference key
                    active_emails.append(email)
                else:
                    # Clean up expired emails
                    db.reference(f'emails/{username}/{key}').delete()
            
            return active_emails
        except Exception as e:
            print(f"Firebase retrieval error: {e}")
    
    # Try Redis
    if redis_client:
        try:
            key = f"emails:{username}"
            emails_json = redis_client.get(key)
            emails = json.loads(emails_json) if emails_json else []
            
            active_emails = []
            for email in emails:
                if email.get('expires_at', 0) > current_time:
                    active_emails.append(email)
            
            # Clean up expired emails
            redis_client.setex(key, 600, json.dumps(active_emails))
            
            return active_emails
        except Exception as e:
            print(f"Redis retrieval error: {e}")
    
    # Fall back to local storage
    with local_storage_lock:
        if username not in local_storage:
            return []
        
        active_emails = [
            email for email in local_storage[username]
            if email.get('expires_at', 0) > current_time
        ]
        
        return active_emails