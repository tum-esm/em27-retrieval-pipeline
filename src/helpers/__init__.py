import firebase_admin
from firebase_admin import credentials
import os

cred = credentials.Certificate(os.getenv("FIRESTORE_KEY_FILE"))
firebase_admin.initialize_app(cred, {"projectId": "tum-esm"})
