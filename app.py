import streamlit as st
import base64, uuid, time, json, hashlib
from cryptography.fernet import Fernet
from datetime import datetime, timedelta
import qrcode
from io import BytesIO

# ===============================
# CONFIG
# ===============================
TTL_SECONDS = 120
APP_URL = "https://ttu-sync-2030.streamlit.app"

st.set_page_config("TTU-Sync", layout="wide")

# ===============================
# SHARED MEMORY (CLOUD SAFE)
# ===============================
@st.cache_resource
def shared_sessions():
    return {}

SESSIONS = shared_sessions()

# ===============================
# UTILS
# ===============================
def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def now():
    return datetime.utcnow()

# ===============================
# UI
# ===============================
st.title("🔗 TTU-Sync — Partage Sécurisé Temporaire")

tabs = st.tabs(["📤 Émetteur", "📥 Récepteur"])

# =====================================================
# 📤 ÉMETTEUR
# =====================================================
with tabs[0]:
    st.subheader("📤 Envoi sécurisé")

    files = st.file_uploader("Sélectionner fichiers", accept_multiple_files=True)

    if files and st.button("🚀 Démarrer session"):
        token = str(uuid.uuid4())
        key = Fernet.generate_key()
        expires = now() + timedelta(seconds=TTL_SECONDS)

        payload = []
        for f in files:
            raw = f.getvalue()
            encrypted = Fernet(key).encrypt(raw)
            payload.append({
                "name": f.name,
                "data": base64.b64encode(encrypted).decode(),
                "size": len(raw),
                "sha256": sha256(raw)
            })

        SESSIONS[token] = {
            "key": base64.b64encode(key).decode(),
            "files": payload,
            "expires": expires.timestamp()
        }

        link = f"{APP_URL}/?token={token}"

        st.success("🔐 Session active")
        st.code(link)

        qr = qrcode.make(link)
        buf = BytesIO()
        qr.save(buf)
        st.image(buf.getvalue(), caption="📱 Scanner sur mobile")

# =====================================================
# 📥 RÉCEPTEUR
# =====================================================
with tabs[1]:
    st.subheader("📥 Réception sécurisée")

    token = st.query_params.get("token")

    if not token:
        st.info("📎 Ouvre un lien ou scanne un QR code")
    elif token not in SESSIONS:
        st.error("❌ Session introuvable ou expirée")
    else:
        session = SESSIONS[token]
        remaining = int(session["expires"] - now().timestamp())

        if remaining <= 0:
            del SESSIONS[token]
            st.error("⏳ Session expirée")
        else:
            st.success("🔓 Session valide")
            st.progress(remaining / TTL_SECONDS)
            st.caption(f"⏳ Temps restant : {remaining} s")

            key = base64.b64decode(session["key"])

            for f in session["files"]:
                decrypted = Fernet(key).decrypt(
                    base64.b64decode(f["data"])
                )

                st.download_button(
                    f"⬇️ {f['name']}",
                    data=decrypted,
                    file_name=f["name"]
                )

                st.caption(
                    f"📦 {f['size']} octets | SHA-256 : `{f['sha256']}`"
                )

            time.sleep(1)
            st.rerun()
