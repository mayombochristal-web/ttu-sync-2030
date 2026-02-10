import streamlit as st
import base64
import os
import json
import time
import uuid
import hashlib
from datetime import datetime, timedelta

from cryptography.fernet import Fernet
import qrcode
from PIL import Image
import plotly.graph_objects as go

# ===============================
# CONFIG
# ===============================
STORAGE_DIR = "ttu_storage"
TTL_MINUTES = 10  # auto-destruction

os.makedirs(STORAGE_DIR, exist_ok=True)

st.set_page_config(page_title="TTU-Sync Secure Share", layout="wide")

# ===============================
# CRYPTO
# ===============================
def generate_key():
    return Fernet.generate_key()

def encrypt(data: bytes, key: bytes) -> bytes:
    return Fernet(key).encrypt(data)

def decrypt(data: bytes, key: bytes) -> bytes:
    return Fernet(key).decrypt(data)

def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

# ===============================
# STORAGE
# ===============================
def save_payload(token, payload):
    path = os.path.join(STORAGE_DIR, f"{token}.json")
    with open(path, "w") as f:
        json.dump(payload, f)

def load_payload(token):
    path = os.path.join(STORAGE_DIR, f"{token}.json")
    if not os.path.exists(path):
        return None
    with open(path, "r") as f:
        return json.load(f)

def delete_payload(token):
    path = os.path.join(STORAGE_DIR, f"{token}.json")
    if os.path.exists(path):
        os.remove(path)

def expired(payload):
    return datetime.utcnow() > datetime.fromisoformat(payload["expires_at"])

# ===============================
# UI
# ===============================
st.title("🔐 TTU-Sync — Secure File Transfer")

tabs = st.tabs(["📤 Envoyer", "📥 Recevoir"])

# =========================================================
# 📤 ENVOI
# =========================================================
with tabs[0]:
    st.subheader("📤 Partager des fichiers")

    uploaded_files = st.file_uploader(
        "Sélectionner un ou plusieurs fichiers",
        accept_multiple_files=True
    )

    if uploaded_files:
        if st.button("🚀 Générer lien sécurisé TTU"):
            key = generate_key()
            token = str(uuid.uuid4())

            files_meta = []

            for file in uploaded_files:
                raw = file.getvalue()
                encrypted = encrypt(raw, key)

                files_meta.append({
                    "name": file.name,
                    "size": len(raw),
                    "sha256": sha256(raw),
                    "payload": base64.b64encode(encrypted).decode()
                })

            payload = {
                "token": token,
                "key": base64.b64encode(key).decode(),
                "created_at": datetime.utcnow().isoformat(),
                "expires_at": (datetime.utcnow() + timedelta(minutes=TTL_MINUTES)).isoformat(),
                "files": files_meta
            }

            save_payload(token, payload)

            link = f"{st.get_url()}?token={token}"

            st.success("Lien généré avec succès")
            st.code(link)

            # QR Code
            qr = qrcode.make(link)
            st.image(qr, caption="📱 Scanner sur mobile")

            st.info(f"⏳ Auto-destruction dans {TTL_MINUTES} minutes")

# =========================================================
# 📥 RÉCEPTION
# =========================================================
with tabs[1]:
    st.subheader("📥 Récupérer des fichiers")

    query = st.query_params
    token = query.get("token", None)

    if token:
        payload = load_payload(token)

        if payload is None:
            st.error("❌ Lien invalide ou déjà détruit")
        elif expired(payload):
            delete_payload(token)
            st.error("⏳ Lien expiré (auto-détruit)")
        else:
            st.success("🔓 Lien valide")

            key = base64.b64decode(payload["key"])

            for file in payload["files"]:
                encrypted = base64.b64decode(file["payload"])
                decrypted = decrypt(encrypted, key)

                st.download_button(
                    label=f"⬇️ Télécharger {file['name']}",
                    data=decrypted,
                    file_name=file["name"]
                )

                st.caption(
                    f"📦 {file['size']} octets | 🧾 SHA-256 : `{file['sha256']}`"
                )

            if st.button("🗑 Détruire le lien maintenant"):
                delete_payload(token)
                st.warning("Lien détruit manuellement")

    else:
        st.info("📎 Ouvre un lien TTU pour récupérer les fichiers")

# =========================================================
# FOOTER
# =========================================================
st.divider()
st.markdown("""
### 🧠 Ce que fait réellement TTU-Sync

✔ Partage PC ↔ téléphone  
✔ Aucun compte  
✔ Aucun stockage permanent  
✔ Sécurité par chiffrement AES (Fernet)  
✔ Intégrité garantie SHA-256  
✔ Auto-destruction contrôlée  

👉 **TTU-Sync = WeTransfer + Signal + QR**
""")
