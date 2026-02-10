import streamlit as st
import uuid
import time
import hashlib
from cryptography.fernet import Fernet

# ===============================
# CONFIG
# ===============================
st.set_page_config(page_title="TTU-Sync 2030", layout="centered")

# ===============================
# STOCKAGE RAM GLOBAL
# ===============================
if "SESSIONS" not in st.session_state:
    st.session_state.SESSIONS = {}

# ===============================
# CRYPTO
# ===============================
def generate_key():
    return Fernet.generate_key()

def encrypt(data, key):
    return Fernet(key).encrypt(data)

def decrypt(data, key):
    return Fernet(key).decrypt(data)

def sha256(data):
    return hashlib.sha256(data).hexdigest()

# ===============================
# UI
# ===============================
st.title("🔐 TTU-Sync 2030")
st.caption("Transfert sécurisé temporaire — sans stockage disque")

mode = st.radio(
    "Mode",
    ["📤 Émission sécurisée", "📥 Réception sécurisée"],
    horizontal=True
)

# ===============================
# EMETTEUR
# ===============================
if mode == "📤 Émission sécurisée":

    files = st.file_uploader(
        "📦 Sélectionne un ou plusieurs fichiers",
        accept_multiple_files=True
    )

    ttl = st.slider("⏳ Durée de validité (minutes)", 1, 30, 5)

    if st.button("🚀 Générer le lien sécurisé") and files:
        token = str(uuid.uuid4())
        key = generate_key()
        expires_at = time.time() + ttl * 60

        payload = []
        for f in files:
            raw = f.read()
            encrypted = encrypt(raw, key)
            payload.append({
                "name": f.name,
                "data": encrypted,
                "hash": sha256(raw)
            })

        st.session_state.SESSIONS[token] = {
            "files": payload,
            "key": key,
            "expires": expires_at
        }

        link = f"{st.query_params.get('base', '')}?token={token}"

        st.success("✅ Lien généré")
        st.code(link)
        st.code(key.decode(), language="text")

        st.warning("⚠️ Garde cette page ouverte jusqu’au téléchargement")

# ===============================
# RECEPTEUR
# ===============================
else:
    params = st.query_params
    token = params.get("token", "")

    token = st.text_input("🔑 Token de session", token)
    key_input = st.text_input("🔐 Clé AES", type="password")

    if st.button("📥 Récupérer les fichiers"):
        session = st.session_state.SESSIONS.get(token)

        if not session:
            st.error("❌ Session introuvable ou expirée")
        elif time.time() > session["expires"]:
            st.error("⏳ Session expirée")
            del st.session_state.SESSIONS[token]
        else:
            try:
                key = key_input.encode()
                st.success("📂 Fichiers disponibles")

                for f in session["files"]:
                    decrypted = decrypt(f["data"], key)
                    if sha256(decrypted) != f["hash"]:
                        st.error(f"❌ Intégrité compromise : {f['name']}")
                    else:
                        st.download_button(
                            label=f"⬇️ Télécharger {f['name']}",
                            data=decrypted,
                            file_name=f["name"]
                        )
            except Exception:
                st.error("❌ Clé invalide")

