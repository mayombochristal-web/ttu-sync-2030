import streamlit as st
import time
import base64
import hashlib
import uuid
import io
import qrcode
from cryptography.fernet import Fernet

# ===============================
# CONFIG
# ===============================
TTL_SECONDS = 120  # durée de vie du lien

st.set_page_config(
    page_title="TTU-Sync P2P",
    layout="centered"
)

st.title("🔐 TTU-Sync | Partage Temporaire Sécurisé")

# ===============================
# MÉMOIRE SERVEUR ÉPHÉMÈRE
# ===============================
if "relay" not in st.session_state:
    st.session_state.relay = {}

# ===============================
# OUTILS
# ===============================
def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def generate_qr(link: str):
    qr = qrcode.make(link)
    buf = io.BytesIO()
    qr.save(buf, format="PNG")
    buf.seek(0)
    return buf

# ===============================
# RÉCUPÉRATION TOKEN
# ===============================
query = st.query_params
token = query.get("token", None)

# ===============================
# MODE RÉCEPTEUR
# ===============================
if token and token in st.session_state.relay:
    session = st.session_state.relay[token]

    remaining = int(session["expires_at"] - time.time())

    if remaining <= 0:
        st.error("⏳ Lien expiré")
        del st.session_state.relay[token]
        st.stop()

    st.success("📥 Session P2P active")
    st.info(f"⏳ Temps restant : {remaining} s")

    st.progress(remaining / TTL_SECONDS)

    encrypted = session["payload"]
    key = session["key"]

    fernet = Fernet(key)
    decrypted = fernet.decrypt(encrypted)
    raw = base64.b64decode(decrypted)

    st.download_button(
        label="⬇️ Télécharger le fichier",
        data=raw,
        file_name=session["filename"],
        mime="application/octet-stream"
    )

    st.caption(f"🧾 SHA-256 : `{session['hash']}`")

    st.stop()

# ===============================
# MODE ÉMETTEUR
# ===============================
st.subheader("📤 Envoyer un fichier")

uploaded = st.file_uploader(
    "Choisir un fichier",
    accept_multiple_files=False
)

if uploaded:
    data = uploaded.getvalue()

    key = Fernet.generate_key()
    fernet = Fernet(key)

    encrypted = fernet.encrypt(base64.b64encode(data))

    token = str(uuid.uuid4())

    st.session_state.relay[token] = {
        "payload": encrypted,
        "filename": uploaded.name,
        "hash": sha256(data),
        "key": key,
        "expires_at": time.time() + TTL_SECONDS
    }

    link = f"{st.request.url}?token={token}"

    st.success("🔐 Session P2P créée")
    st.code(link)

    qr_img = generate_qr(link)
    st.image(qr_img, caption="📱 Scanner avec le téléphone")

    st.info("⚠️ Ne ferme pas cette page tant que le transfert n’est pas terminé")

# ===============================
# NETTOYAGE AUTO
# ===============================
now = time.time()
expired = [
    t for t, v in st.session_state.relay.items()
    if v["expires_at"] < now
]
for t in expired:
    del st.session_state.relay[t]
