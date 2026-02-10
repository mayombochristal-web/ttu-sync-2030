import streamlit as st
import base64
import uuid
import time
import hashlib
import shutil
from cryptography.fernet import Fernet
from datetime import datetime, timedelta
from pathlib import Path
import qrcode
from io import BytesIO

# ===============================
# CONFIG
# ===============================
TTL_SECONDS = 120
BASE_DIR = Path("/tmp/ttu_sync")
BASE_DIR.mkdir(exist_ok=True)

st.set_page_config(
    page_title="TTU-Sync P2P",
    layout="wide"
)

# ===============================
# UTILS
# ===============================
def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def encrypt(data: bytes, key: bytes) -> bytes:
    return Fernet(key).encrypt(data)

def decrypt(data: bytes, key: bytes) -> bytes:
    return Fernet(key).decrypt(data)

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

    files = st.file_uploader(
        "Sélectionner fichiers",
        accept_multiple_files=True
    )

    if files and st.button("🚀 Démarrer session"):
        token = str(uuid.uuid4())
        session_dir = BASE_DIR / token
        session_dir.mkdir()

        key = Fernet.generate_key()
        expires_at = now() + timedelta(seconds=TTL_SECONDS)

        meta = {
            "key": base64.b64encode(key).decode(),
            "expires": expires_at.timestamp(),
            "files": []
        }

        for f in files:
            raw = f.getvalue()
            encrypted = encrypt(raw, key)

            file_id = f"{uuid.uuid4()}.bin"
            (session_dir / file_id).write_bytes(encrypted)

            meta["files"].append({
                "name": f.name,
                "size": len(raw),
                "sha256": sha256(raw),
                "file_id": file_id
            })

        (session_dir / "meta.json").write_text(
            base64.b64encode(
                str(meta).encode()
            ).decode()
        )

        link = f"?token={token}"

        st.success("🔐 Session active")
        st.code(link)

        qr = qrcode.make(link)
        buf = BytesIO()
        qr.save(buf)
        st.image(buf.getvalue(), caption="📱 Scanner")

        st.warning("⚠️ Garde cette page ouverte jusqu’à la réception")

# =====================================================
# 📥 RÉCEPTEUR
# =====================================================
with tabs[1]:
    st.subheader("📥 Réception sécurisée")

    token = st.query_params.get("token")

    if not token:
        st.info("📎 Ouvre un lien TTU-Sync ou scanne un QR code")
    else:
        session_dir = BASE_DIR / token

        if not session_dir.exists():
            st.error("❌ Session introuvable ou expirée")
        else:
            meta_path = session_dir / "meta.json"
            meta = eval(
                base64.b64decode(
                    meta_path.read_text()
                ).decode()
            )

            expires = datetime.utcfromtimestamp(meta["expires"])
            remaining = int((expires - now()).total_seconds())

            if remaining <= 0:
                shutil.rmtree(session_dir, ignore_errors=True)
                st.error("⏳ Session expirée")
            else:
                st.success("🔓 Session valide")

                st.progress(remaining / TTL_SECONDS)
                st.caption(f"⏳ Temps restant : {remaining} s")

                key = base64.b64decode(meta["key"])

                for f in meta["files"]:
                    encrypted = (session_dir / f["file_id"]).read_bytes()
                    decrypted = decrypt(encrypted, key)

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

# ===============================
# CLEANUP GLOBAL
# ===============================
for d in BASE_DIR.iterdir():
    try:
        meta = eval(
            base64.b64decode(
                (d / "meta.json").read_text()
            ).decode()
        )
        if datetime.utcfromtimestamp(meta["expires"]) < now():
            shutil.rmtree(d, ignore_errors=True)
    except Exception:
        pass
