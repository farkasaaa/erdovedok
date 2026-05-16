# 🌲 Erdővédők (Forest Defenders) - v2.0

Az **Erdővédők** egy valós idejű, szerver nélküli multiplayer ügyességi és kvízjáték, ahol a játékosok célja, hogy végigfussanak egy akadálypályán, és a célban tudásukkal megvédjék az erdőt a fakitermelőktől.

![Erdővédők Banner](https://img.shields.io/badge/Erdővédők-v2.0-green?style=for-the-badge&logo=treehouse)
![Tech Stack](https://img.shields.io/badge/Tech-Python_|_Firebase_|_WebSocket-blue?style=for-the-badge)

## ✨ Főbb Funkciók

- **Valós Idejű Multiplayer**: Versenyezz barátaiddal (LAN vagy Internet) egy 350 méteres 3D-hatású pályán.
- **Globális Ranglista**: Firebase Firestore alapú dicsőségtábla a legjobb védelmezőknek.
- **Prémium UI**: Modern "Chill Dark Forest" dizájn, Glassmorphism effektekkel és sima animációkkal.
- **Kvíz Rendszer**: A célban környezetvédelmi kérdések megválaszolásával szerezhetsz pontokat és mentheted meg a fákat.
- **Cross-Platform**: Webes felület a statisztikákhoz és standalone Windows alkalmazás a játékhoz.
- **Biztonságos Profilok**: Google és E-mail alapú bejelentkezés szinkronizált adatokkal.

## 🚀 Telepítés és Futtatás

### 1. Előfeltételek
- Python 3.10 vagy újabb
- [Firebase Projekt](https://console.firebase.google.com/) (Firestore és Auth beállítva)

### 2. Telepítés
Klónozd a tárolót:
```bash
git clone https://github.com/farkasaaa/erdovedok.git
cd erdovedok
```

Telepítsd a függőségeket:
```bash
pip install -r requirements.txt
```

### 3. Futtatás
Indítsd el a játékot:
```bash
python main.py
```

### 4. EXE Build (Windows)
Ha saját futtatható állományt szeretnél készíteni:
```bash
pyinstaller --noconfirm Erdővédők.spec
```
A kész alkalmazás a `dist/` mappában lesz megtalálható.

## 🛠 Technológiai Stack

- **Frontend**: HTML5, CSS3 (Glassmorphism), Vanilla JavaScript, Three.js (3D renderelés)
- **Backend**: Python, WebSocket (real-time szinkronizáció), HTTP szerver
- **Adatbázis & Auth**: Google Firebase (Firestore, Authentication)
- **Csomagolás**: PyInstaller, PyWebView

## 📜 Licenc
Ez a projekt oktatási célra készült. Minden jog fenntartva.

---
**Készítette**: Farkas András | 2026
