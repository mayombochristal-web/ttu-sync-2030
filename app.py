import streamlit as st
import time
import base64
import plotly.graph_objects as go
from datetime import datetime

# ===============================
# MOTEUR TTU-SYNC (CORE)
# ===============================
class TTUSync:
    def __init__(self, device_name, phi_m=0.988, threshold=0.5088, k_curvature=24.92):
        self.device_name = device_name
        self.phi_m = phi_m
        self.threshold = threshold
        self.k_curvature = k_curvature
        self.history = []
        self.transfers = []

    def connect(self, noise_level):
        phi_a = 0.85
        phi_d = noise_level * 0.45

        phi_c = (self.phi_m * phi_a) / (1 + phi_d)
        status = "LINK_STABLE"
        k = self.k_curvature

        if phi_c < self.threshold:
            status = "LINK_RESONANT"
            k = self.k_curvature * (1 + (self.threshold - phi_c))
            phi_a *= 1.35
            phi_c = (self.phi_m * phi_a) / (1 + phi_d)

            if phi_c < self.threshold:
                status = "LINK_DISSOLVED"
                k = 0.0

        self.history.append(phi_c)
        return phi_c, status, k


# ===============================
# ISOTOPISATION TTU
# ===============================
def isotopize_file(uploaded_file, phi_c):
    raw = uploaded_file.getvalue()
    encoded = base64.b64encode(raw).decode("utf-8")

    return {
        "name": uploaded_file.name,
        "size": len(raw),
        "phi_c": round(phi_c, 4),
        "timestamp": datetime.utcnow().isoformat(),
        "payload": encoded
    }


def reconstruct_file(isotope):
    return base64.b64decode(isotope["payload"])


# ===============================
# STREAMLIT UI
# ===============================
st.set_page_config(
    page_title="TTU-Sync 2026",
    layout="wide"
)

st.title("📶 TTU-Sync — Partage de fichiers par résonance")

# ===============================
# SESSION
# ===============================
if "engine" not in st.session_state:
    st.session_state.engine = TTUSync("Device-TTU")

engine = st.session_state.engine

# ===============================
# SIDEBAR
# ===============================
st.sidebar.header("⚙️ Paramètres de liaison")

noise = st.sidebar.slider("Bruit d’environnement", 0.0, 2.0, 0.5)
expert = st.sidebar.toggle("🧠 Mode Expert")

if expert:
    engine.phi_m = st.sidebar.slider("Φm (mémoire)", 0.85, 1.0, engine.phi_m)
    engine.threshold = st.sidebar.slider("Seuil Φc", 0.3, 0.8, engine.threshold)
    engine.k_curvature = st.sidebar.slider("Courbure K", 5.0, 50.0, engine.k_curvature)

# ===============================
# LAYOUT
# ===============================
col1, col2 = st.columns([1, 2])

# ---------- COLONNE GAUCHE ----------
with col1:
    st.subheader("🔗 État de connexion")

    if st.button("Lancer l’appairage"):
        with st.spinner("Synchronisation TTU…"):
            time.sleep(1.1)

        phi, status, k = engine.connect(noise)

        if status == "LINK_STABLE":
            st.success(f"Connexion stable | Φc = {phi:.4f}")
        elif status == "LINK_RESONANT":
            st.warning(f"Connexion compensée | Φc = {phi:.4f}")
        else:
            st.error("Connexion dissoute")

    st.divider()

    uploaded = st.file_uploader("📤 Envoyer un fichier")

    if uploaded and engine.history:
        isotope = isotopize_file(uploaded, engine.history[-1])
        engine.transfers.append(isotope)

        st.success("Fichier encapsulé (TTU-Payload)")

        # Reconstruction automatique
        reconstructed = reconstruct_file(isotope)

        st.download_button(
            label="⬇️ Télécharger le fichier décodé",
            data=reconstructed,
            file_name=isotope["name"],
            mime="application/octet-stream"
        )

        st.json(
            {k: isotope[k] for k in isotope if k != "payload"},
            expanded=False
        )

# ---------- COLONNE DROITE ----------
with col2:
    st.subheader("📈 Cohérence de liaison")

    current_phi = (engine.phi_m * 0.85) / (1 + noise * 0.45)

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=current_phi,
        title={"text": "Φc — Qualité du lien"},
        gauge={
            "axis": {"range": [0, 1]},
            "steps": [
                {"range": [0, engine.threshold], "color": "crimson"},
                {"range": [engine.threshold, 1], "color": "limegreen"}
            ],
            "threshold": {
                "line": {"color": "white", "width": 4},
                "value": engine.threshold
            }
        }
    ))

    st.plotly_chart(fig, use_container_width=True)

    if engine.history:
        st.subheader("🧠 Historique Φc")
        st.line_chart(engine.history)

    if engine.transfers:
        st.subheader("📚 Historique des transferts")
        st.table([
            {
                "Nom": t["name"],
                "Taille (octets)": t["size"],
                "Φc": t["phi_c"],
                "Date": t["timestamp"]
            }
            for t in engine.transfers
        ])

# ===============================
# FOOTER
# ===============================
st.divider()
st.markdown("""
### 🚀 TTU-Sync comme outil de partage

• Partage fichiers **PC ↔ téléphone** via navigateur  
• Sans limite stricte (dépend du serveur Streamlit)  
• Téléchargement immédiat, sans compte  
• Φc = contrôle de qualité du transfert  

👉 Alternative conceptuelle à WeTransfer / Smash  
👉 Base idéale pour chiffrement, lien temporaire, QR code
""")
