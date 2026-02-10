import streamlit as st
import base64
import time
import uuid
import hashlib
import io
from cryptography.fernet import Fernet
from datetime import datetime, timedelta
import qrcode

# ===============================
# CONFIG
# ===============================
TTL_SECONDS = 120
APP_BASE_URL = st.request.url.split("?")[0]

st.set_page_config(page_title="TTU-Sync P2P", layout="wide")
st.title("🔗 TTU-Sync — Partage Temporaire Sécurisé")

# ===============================
# RELAIS MÉMOIRE GLOBAL (STREAMLIT)
# ===============================
@st.cache_resource
def relay():
    return {}

RELAY = relay()

# ===============================
# CRYPTO
# ===============================
def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def encrypt(data: bytes, key: bytes) -> bytes:
    return Fernet(key).encrypt(data)

def decrypt(data: bytes, key: bytes) -> bytes:
    return Fernet(key).decrypt(data)

def make_qr(link: str):
    img = qrcode.make(link)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf

# ===============================
# TOKEN URL
# ===============================
query = st.query_params
token = query.get("token")

tabs = st.tabs(["📤 Émetteur", "📥 Récepteur"])

# =====================================================
# 📤 ÉMETTEUR
# =====================================================
with tabs[0]:
    st.subheader("📤 Envoyer des fichiers")

    files = st.file_uploader(
        "Sélectionner des fichiers",
        accept_multiple_files=True
    )

    if files and st.button("🚀 Créer session P2P"):
        token = str(uuid.uuid4())
        key = Fernet.generate_key()
        expires_at = datetime.utcnow() + timedelta(seconds=TTL_SECONDS)

        payload = []

        for f in files:
            raw = f.getvalue()
            payload.append({
                "name": f.name,
                "size": len(raw),
                "sha256": sha256(raw),
                "data": base64.b64encode(
                    encrypt(raw, key)
                ).decode()
            })

        RELAY[token] = {
            "key": base64.b64encode(key).decode(),
            "files": payload,
            "expires_at": expires_at
        }

        link = f"{APP_BASE_URL}?token={token}"

        st.success("🔐 Session active")
        st.code(link)
        st.image(make_qr(link), caption="📱 Scanner avec le téléphone")
        st.warning("⚠️ Ne ferme pas cette page")

    if token in RELAY:
        remaining = int(
            (RELAY[token]["expires_at"] - datetime.utcnow()).total_seconds()
        )
        if remaining > 0:
            st.progress(remaining / TTL_SECONDS)
            st.caption(f"⏳ Temps restant : {remaining}s")
        else:
            RELAY.pop(token, None)
            st.error("⏳ Session expirée")

# =====================================================
# 📥 RÉCEPTEUR
# =====================================================
with tabs[1]:
    st.subheader("📥 Réception")

    if token and token in RELAY:
        session = RELAY[token]
        remaining = int(
            (session["expires_at"] - datetime.utcnow()).total_seconds()
        )

        if remaining <= 0:
            RELAY.pop(token, None)
            st.error("⏳ Session expirée")
        else:
            st.success("🔓 Session active")
            st.progress(remaining / TTL_SECONDS)
            st.caption(f"⏳ Temps restant : {remaining}s")

            key = base64.b64decode(session["key"])

            for f in session["files"]:
                decrypted = decrypt(
                    base64.b64decode(f["data"]),
                    key
                )

                st.download_button(
                    f"⬇️ Télécharger {f['name']}",
                    data=decrypted,
                    file_name=f["name"]
                )

                st.caption(
                    f"📦 {f['size']} octets | 🧾 SHA-256 : `{f['sha256']}`"
                )
    else:
        st.info("📎 Scanne ou ouvre un lien TTU-Sync")

# ===============================
# NETTOYAGE AUTO
# ===============================
now = datetime.utcnow()
expired = [t for t, v in RELAY.items() if v["expires_at"] < now]
for t in expired:
    RELAY.pop(t, None)

# ===============================
# FOOTER
# ===============================
st.divider()
st.markdown("""
### 🧠 Ce mode TTU-Sync fait réellement

✔ RAM uniquement (aucun disque)  
✔ Partage multi-fichiers  
✔ Chiffrement AES (Fernet)  
✔ QR code mobile stable  
✔ Hash SHA-256  
✔ Auto-destruction TTL  
✔ Récepteur **fonctionnel PC ↔ mobile**

👉 Ce n’est pas du WebRTC pur  
👉 Mais **le comportement utilisateur est identique**
""")
