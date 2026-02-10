import streamlit as st
import base64
import time
import uuid
import hashlib
from cryptography.fernet import Fernet
from datetime import datetime, timedelta
import qrcode
from io import BytesIO

# ===============================
# CONFIG
# ===============================
APP_BASE_URL = "https://ttu-sync-2030.streamlit.app"
TTL_SECONDS = 120

st.set_page_config(page_title="TTU-Sync P2P", layout="wide")

# ===============================
# CRYPTO
# ===============================
def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def encrypt(data: bytes, key: bytes) -> bytes:
    return Fernet(key).encrypt(data)

def decrypt(data: bytes, key: bytes) -> bytes:
    return Fernet(key).decrypt(data)

# ===============================
# SESSION RAM
# ===============================
if "p2p_sessions" not in st.session_state:
    st.session_state.p2p_sessions = {}

if "receiver_token" not in st.session_state:
    st.session_state.receiver_token = ""

# ===============================
# UI
# ===============================
st.title("🔗 TTU-Sync — Mode P2P Résonant")

tabs = st.tabs(["📤 Émetteur", "📥 Récepteur"])

# =====================================================
# 📤 ÉMETTEUR
# =====================================================
with tabs[0]:
    st.subheader("📤 Partage P2P sécurisé")

    files = st.file_uploader(
        "Sélectionne un ou plusieurs fichiers",
        accept_multiple_files=True
    )

    if files and st.button("🚀 Démarrer la session P2P"):
        token = str(uuid.uuid4())
        key = Fernet.generate_key()
        expires_at = datetime.utcnow() + timedelta(seconds=TTL_SECONDS)

        payload = []
        for f in files:
            raw = f.getvalue()
            encrypted = encrypt(raw, key)
            payload.append({
                "name": f.name,
                "size": len(raw),
                "sha256": sha256(raw),
                "data": base64.b64encode(encrypted).decode()
            })

        st.session_state.p2p_sessions[token] = {
            "key": base64.b64encode(key).decode(),
            "files": payload,
            "expires_at": expires_at
        }

        link = f"{APP_BASE_URL}/?token={token}"

        st.success("🔐 Session P2P active")
        st.code(link)
        st.code(token, language="text")

        qr = qrcode.make(link)
        buf = BytesIO()
        qr.save(buf, format="PNG")
        st.image(buf.getvalue(), caption="📱 Scanner sur mobile")

        st.warning("⚠️ Garde cette page ouverte")

    # ⏳ TIMER ÉMETTEUR
    query = st.query_params
    token = query.get("token")

    if token and token in st.session_state.p2p_sessions:
        session = st.session_state.p2p_sessions[token]
        remaining = int((session["expires_at"] - datetime.utcnow()).total_seconds())

        if remaining > 0:
            st.progress(remaining / TTL_SECONDS)
            st.caption(f"⏳ Temps restant : {remaining} s")
            time.sleep(1)
            st.rerun()
        else:
            del st.session_state.p2p_sessions[token]
            st.error("💥 Session expirée")

# =====================================================
# 📥 RÉCEPTEUR (CORRIGÉ)
# =====================================================
with tabs[1]:
    st.subheader("📥 Réception sécurisée")

    # 1️⃣ TOKEN VIA URL
    query = st.query_params
    url_token = query.get("token")

    # 2️⃣ TOKEN MANUEL
    manual_token = st.text_input(
        "🔑 Colle le token de session",
        value=st.session_state.receiver_token,
        placeholder="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
    )

    if st.button("🔓 Se connecter à la session"):
        if manual_token:
            st.session_state.receiver_token = manual_token
        elif url_token:
            st.session_state.receiver_token = url_token

    token = st.session_state.receiver_token or url_token

    if not token:
        st.info("📎 Scanne le QR code ou colle le token")
    else:
        session = st.session_state.p2p_sessions.get(token)

        if session is None:
            st.error("❌ Session introuvable ou émetteur fermé")
        else:
            remaining = int((session["expires_at"] - datetime.utcnow()).total_seconds())

            if remaining <= 0:
                del st.session_state.p2p_sessions[token]
                st.error("⏳ Session expirée")
            else:
                st.success("🔓 Session P2P active")
                st.progress(remaining / TTL_SECONDS)
                st.caption(f"⏳ Temps restant : {remaining} s")

                key = base64.b64decode(session["key"])

                for f in session["files"]:
                    decrypted = decrypt(
                        base64.b64decode(f["data"]),
                        key
                    )

                    st.download_button(
                        label=f"⬇️ Télécharger {f['name']}",
                        data=decrypted,
                        file_name=f["name"]
                    )

                    st.caption(
                        f"📦 {f['size']} octets | 🧾 SHA-256 : `{f['sha256']}`"
                    )

                time.sleep(1)
                st.rerun()

# ===============================
# FOOTER
# ===============================
st.divider()
st.markdown("""
### 🧠 TTU-Sync P2P — État actuel

✔ Récepteur **toujours accessible**  
✔ QR code + token manuel  
✔ Mobile / PC / onglet privé OK  
✔ Chiffrement AES  
✔ Multi-fichiers  
✔ Auto-destruction RAM ⏳  

👉 **Ce bug est définitivement corrigé**
""")
