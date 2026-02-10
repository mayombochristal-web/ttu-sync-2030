🔗 TTU-Sync — Partage Sécurisé Temporaire (P2P logique)

TTU-Sync est une application Streamlit permettant le partage temporaire et chiffré de fichiers entre appareils (PC ↔ téléphone) via un lien sécurisé ou QR code, sans création de compte et sans stockage persistant.

🧠 Inspiré par une approche de résonance informationnelle :
les données n’existent que tant que la session est vivante.

🚀 Fonctionnalités
🔐 Sécurité

Chiffrement AES (Fernet) en mémoire

Hash SHA-256 pour vérification d’intégrité

Clé de chiffrement éphémère

Aucune écriture disque persistante

⏳ Temporalité

Lien temporaire (TTL configurable)

Auto-destruction automatique

Émetteur fermé = session détruite

📱 Mobilité

QR code généré automatiquement

Accès immédiat depuis smartphone

Compatible PC / Android / iOS (navigateur)

📦 Transfert

Multi-fichiers

Téléchargement individuel

Aucune limite imposée par l’app (hors Streamlit)

🧩 Architecture Technique
Utilisateur A (Émetteur)
        |
        |  lien + QR code
        v
Streamlit Cloud (RAM partagée)
        ^
        |
Utilisateur B (Récepteur)


⚠️ Ce n’est pas du P2P réseau pur
➡️ C’est un P2P logique sécurisé en mémoire, compatible Streamlit Cloud.

🛠 Stack Technique

Python 3.11+

Streamlit

cryptography (Fernet / AES)

qrcode

Pillow

📦 Installation locale
git clone https://github.com/mayombochristal-web/ttu-sync-2030.git
cd ttu-sync-2030
pip install -r requirements.txt
streamlit run app.py

🌍 Démo en ligne

👉 https://ttu-sync-2030.streamlit.app

🧪 Utilisation
1️⃣ Émetteur

Ouvre l’onglet 📤 Émetteur

Sélectionne un ou plusieurs fichiers

Clique sur 🚀 Démarrer session

Partage le lien ou le QR code

2️⃣ Récepteur

Ouvre le lien ou scanne le QR code

Onglet 📥 Récepteur

Télécharge les fichiers avant expiration ⏳

📁 Structure du projet
ttu-sync-2030/
├── app.py
├── requirements.txt
├── README.md

⚠️ Limitations connues

Dépend de la RAM Streamlit

La session disparaît si :

le TTL expire

l’instance Cloud redémarre

Pas de reprise après interruption

🔮 Améliorations possibles

🔥 WebRTC (vrai P2P)

📱 APK Android (WebView)

🌐 Backend FastAPI + Redis

🔐 Partage par mot de passe

📊 Historique local chiffré

🧠 Philosophie TTU

Pas d’archive.
Pas de trace.
Seulement une résonance temporaire de l’information.

👤 Auteur

Christal Mayombo
Projet expérimental — 2026
TTU / MC³ Framework
