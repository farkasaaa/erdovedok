#!/usr/bin/env python3

import asyncio
import json
import random
import time
import threading
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
import websockets
import webview

KVIZ_KERDESEK = [
    {
        "kerdes": "Mennyi CO₂-t nyel el egy átlagos fa évente?",
        "valaszok": ["~22 kg", "~5 kg", "~100 kg", "~1 kg"],
        "helyes": 0,
        "magyarazat": "Egy átlagos fa évente kb. 22 kg CO₂-t nyel el fotoszintézis során!"
    },
    {
        "kerdes": "Melyik erdőtípus a legtöbb fajt tartja fenn?",
        "valaszok": ["Esőerdő", "Tűlevelű erdő", "Lombhullató erdő", "Mangroverdő"],
        "helyes": 0,
        "magyarazat": "A trópusi esőerdők a Föld biológiai sokféleségének ~50%-át tartalmazzák!"
    },
    {
        "kerdes": "Mit jelent az 'erdőirtás' kifejezés?",
        "valaszok": ["Erdők kiirtása", "Erdők telepítése", "Fakitermelés", "Erdőgondozás"],
        "helyes": 0,
        "magyarazat": "Az erdőirtás az erdők tartós eltávolítása más földhasználat céljára."
    },
    {
        "kerdes": "Melyik ország rendelkezik a legnagyobb esőerdővel?",
        "valaszok": ["Brazília", "Indonézia", "Kongó", "Ausztrália"],
        "helyes": 0,
        "magyarazat": "Brazíliában található az Amazonas-medence, a világ legnagyobb esőerdeje!"
    },
    {
        "kerdes": "Hány évet él egy tölgyfa átlagosan?",
        "valaszok": ["200-500 év", "50-100 év", "10-30 év", "1000+ év"],
        "helyes": 0,
        "magyarazat": "A tölgyfák 200-500 évet is élhetnek, különleges esetekben még tovább!"
    },
    {
        "kerdes": "Mi a fenntartható erdőgazdálkodás célja?",
        "valaszok": ["Erdők megőrzése jövő generációknak", "Minél több fa kivágása", "Vadállatok elűzése", "Utak építése"],
        "helyes": 0,
        "magyarazat": "A fenntartható erdőgazdálkodás biztosítja, hogy az erdők a jövő generációknak is megmaradjanak."
    },
    {
        "kerdes": "Mennyi az erdők aránya a Föld szárazföldjéhez képest?",
        "valaszok": ["~31%", "~10%", "~50%", "~70%"],
        "helyes": 0,
        "magyarazat": "Az erdők a Föld szárazföldi területének kb. 31%-át fedik le."
    },
    {
        "kerdes": "Mi az újraerdősítés?",
        "valaszok": ["Fák visszatelepítése kivágott területre", "Erdők védelme", "Fák megjelölése", "Erdei utak karbantartása"],
        "helyes": 0,
        "magyarazat": "Az újraerdősítés során kivágott vagy pusztított területeken új fákat ültetnek!"
    },
    {
        "kerdes": "Melyik gáz a legfontosabb, amit a fák a légkörből kivonnak?",
        "valaszok": ["CO₂ (szén-dioxid)", "O₂ (oxigén)", "N₂ (nitrogén)", "H₂ (hidrogén)"],
        "helyes": 0,
        "magyarazat": "A fák CO₂-t vonnak ki a légkörből és oxigént bocsátanak ki fotoszintézis során!"
    },
    {
        "kerdes": "Mit nevezünk 'zöld tüdőnek'?",
        "valaszok": ["Nagyvárosok parkjai és erdei", "Tengeri algák", "Mezőgazdasági területek", "Hegycsúcsok"],
        "helyes": 0,
        "magyarazat": "A városok parkjait és erdeit 'zöld tüdőnek' nevezik, mert tisztítják a levegőt!"
    },
    {
        "kerdes": "Egy fa hány liter vizet párologtat el naponta?",
        "valaszok": ["100-400 liter", "1-5 liter", "10-20 liter", "1000+ liter"],
        "helyes": 0,
        "magyarazat": "Egy nagy fa naponta 100-400 liter vizet is elpárologtathat!"
    },
    {
        "kerdes": "Mi az erdők szerepe az árvizek megelőzésében?",
        "valaszok": ["Felszívják az esővizet", "Növelik az árvizet", "Nincs szerepük", "Elvezetik a vizet"],
        "helyes": 0,
        "magyarazat": "Az erdők gyökerei és talajuk hatalmas mennyiségű csapadékot szívnak fel, megelőzve az árvizeket!"
    }
]

jatekosok = {}
szobak = {}
ws_szoba = {}

def uj_szoba_id():
    return f"szoba_{random.randint(1000, 9999)}"

def uj_jatek_allapot():
    # Linear path settings
    path_length = 300
    path_width = 16
    
    fak = []
    # Place trees along the path (decor/fail targets)
    for i in range(40):
        side = random.choice([-1, 1])
        x = side * (path_width/2 + random.uniform(3, 12))
        z = random.uniform(10, path_length - 20)
        tip = random.choice(["tolgy", "fenyo", "nyir"])
        fak.append({"id": i, "x": x, "z": z, "tipus": tip, "el": True, "animacio": "none"})
    
    path_length = 350
    path_width = 20
    
    akadaly_elemek = [
        # Start zone fence
        {"tipus": "fal", "x": -10, "z": 10, "w": 4, "h": 5, "l": 2},
        {"tipus": "fal", "x": 10, "z": 10, "w": 4, "h": 5, "l": 2},
        
        # Zone 1: Spinners
        {"tipus": "spinner", "x": -6, "z": 40, "r": 4.5, "seb": 0.05, "offset": 0},
        {"tipus": "spinner", "x": 6, "z": 40, "r": 4.5, "seb": -0.05, "offset": 0},
        
        # Zone 2: Moving Hammers
        {"tipus": "hammer", "x": 0, "z": 100, "range": 12, "seb": 0.04, "offset": 0},
        {"tipus": "hammer", "x": -6, "z": 120, "range": 12, "seb": 0.04, "offset": 1.5},
        {"tipus": "hammer", "x": 6, "z": 120, "range": 12, "seb": 0.04, "offset": 3.14},
        
        # Zone 3: Spinners again
        {"tipus": "spinner", "x": 0, "z": 180, "r": 8, "seb": 0.06, "offset": 0},
        
        # Zone 4: Fast Hammers
        {"tipus": "hammer", "x": -4, "z": 240, "range": 10, "seb": 0.08, "offset": 0},
        {"tipus": "hammer", "x": 4, "z": 250, "range": 10, "seb": 0.08, "offset": 3.14},
        
        # Goal
        {"tipus": "goal", "x": 0, "z": 340, "r": 8}
    ]
    
    # Checkpoints / Runes placed between zones
    runak_z = [25, 70, 150, 210, 280, 310]
    runak = []
    for i, z_pos in enumerate(runak_z):
        runak.append({
            "id": i, 
            "x": 0, 
            "z": z_pos, 
            "aktiv": False, 
            "cel": (i == 0)
        })

    return {
        "fak": fak,
        "akadaly": {"runak": runak, "elemek": akadaly_elemek},
        "mentett_fak": 0,
        "kkor": 0,
        "max_kor": 6,
        "jatek_fazis": "lobby",
        "aktualis_kerdes": None,
        "jatekos_pontok": {},
        "ido_maradt": 30,
        "timer_active": False,
        "path_length": path_length,
        "path_width": path_width
    }

async def kuldes(ws, uzenet):
    try:
        await ws.send(json.dumps(uzenet))
    except:
        pass

async def mindenkinek(szoba_id, uzenet, kivetel=None):
    if szoba_id not in szobak:
        return
    for ws in szobak[szoba_id]["jatekosok"]:
        if ws != kivetel:
            await kuldes(ws, uzenet)

async def allapot_kuldes(szoba_id):
    if szoba_id not in szobak:
        return
    szoba = szobak[szoba_id]
    jatekos_lista = []
    for ws in szoba["jatekosok"]:
        if ws in jatekosok:
            jatekos_lista.append({
                "nev": jatekosok[ws]["nev"],
                "szin": jatekosok[ws]["szin"],
                "pont": jatekosok[ws].get("pont", 0),
                "x": jatekosok[ws].get("x", 0),
                "y": jatekosok[ws].get("y", 0),
                "z": jatekosok[ws].get("z", 0),
                "ero": jatekosok[ws].get("ero", 100),
                "animacio": jatekosok[ws].get("animacio", "idle")
            })
    
    uzenet = {
        "tipus": "allapot",
        "jatekosok": jatekos_lista,
        "jatek": szoba["jatek"],
        "szoba_id": szoba_id
    }
    await mindenkinek(szoba_id, uzenet)

async def kor_indit(szoba_id):
    if szoba_id not in szobak:
        return
    szoba = szobak[szoba_id]
    jatek = szoba["jatek"]
    
    if jatek["kkor"] >= jatek["max_kor"]:
        await jatek_vege(szoba_id)
        return
    
    jatek["kkor"] += 1
    jatek["jatek_fazis"] = "akadaly_kereses"
    
    aktivalatlan_runak = [r for r in jatek["akadaly"]["runak"] if not r["aktiv"]]
    if not aktivalatlan_runak:
        for r in jatek["akadaly"]["runak"]:
            r["aktiv"] = False
        aktivalatlan_runak = jatek["akadaly"]["runak"]

    for r in jatek["akadaly"]["runak"]:
        r["cel"] = False

    cel_runa = random.choice(aktivalatlan_runak)
    cel_runa["cel"] = True
    
    await mindenkinek(szoba_id, {
        "tipus": "uj_kor_cel",
        "kor": jatek["kkor"],
        "max_kor": jatek["max_kor"],
        "akadaly": jatek["akadaly"],
        "uzenet": "🎯 Kersd meg az akadályt és aktiváld a fénylő rúnát!"
    })
    await allapot_kuldes(szoba_id)

async def kerdes_indit(szoba_id, aktivalo_ws):
    if szoba_id not in szobak: return
    szoba = szobak[szoba_id]
    jatek = szoba["jatek"]

    if aktivalo_ws in jatekosok:
        jatekosok[aktivalo_ws]["pont"] = jatekosok[aktivalo_ws].get("pont", 0) + 5
        await kuldes(aktivalo_ws, {
            "tipus": "rendszer_uzenet",
            "szoveg": "🏆 Elsőként aktiváltad az akadályt! +5 BONUS PONT!"
        })
        await mindenkinek(szoba_id, {
            "tipus": "rendszer_uzenet",
            "szoveg": f"⭐ {jatekosok[aktivalo_ws]['nev']} aktiválta az akadályt!"
        }, kivetel=aktivalo_ws)

    el_fak = [f for f in jatek["fak"] if f["el"]]
    if not el_fak:
        await jatek_vege(szoba_id)
        return
    
    celba_vett = random.choice(el_fak)
    celba_vett["animacio"] = "remeg"
    
    jatek["jatek_fazis"] = "kerdes"
    jatek["ido_maradt"] = 30
    
    kerdes_idx = random.randint(0, len(KVIZ_KERDESEK) - 1)
    kerdes = KVIZ_KERDESEK[kerdes_idx].copy()
    kerdes["fa_id"] = celba_vett["id"]
    kerdes["kerdes_idx"] = kerdes_idx
    jatek["aktualis_kerdes"] = kerdes
    jatek["valaszok_beerkezett"] = {}
    
    await mindenkinek(szoba_id, {
        "tipus": "uj_kerdes",
        "kor": jatek["kkor"],
        "max_kor": jatek["max_kor"],
        "fa_id": celba_vett["id"],
        "kerdes": {
            "szoveg": kerdes["kerdes"],
            "valaszok": kerdes["valaszok"]
        },
        "ido": 30
    })
    
    asyncio.create_task(visszaszamlalas(szoba_id, kerdes_idx, celba_vett["id"]))

async def visszaszamlalas(szoba_id, kerdes_idx, fa_id):
    for i in range(30, 0, -1):
        await asyncio.sleep(1)
        if szoba_id not in szobak:
            return
        szoba = szobak[szoba_id]
        jatek = szoba["jatek"]
        if jatek["jatek_fazis"] != "kerdes":
            return
        jatek["ido_maradt"] = i - 1
        await mindenkinek(szoba_id, {"tipus": "ido", "ido": i - 1})
    
    if szoba_id not in szobak:
        return
    await kor_ertekel(szoba_id, kerdes_idx, fa_id, -1)

async def kor_ertekel(szoba_id, kerdes_idx, fa_id, gyoztes_ws_idx):
    if szoba_id not in szobak:
        return
    szoba = szobak[szoba_id]
    jatek = szoba["jatek"]
    
    if jatek["jatek_fazis"] != "kerdes":
        return
    
    jatek["jatek_fazis"] = "kor_eredmeny"
    kerdes = KVIZ_KERDESEK[kerdes_idx]
    
    fa = next((f for f in jatek["fak"] if f["id"] == fa_id), None)
    
    if gyoztes_ws_idx == -1:
        if fa:
            fa["el"] = False
            fa["animacio"] = "esik"
        eredmeny = "fa_kivagva"
        uzenet = "⚠️ Senki nem válaszolt! A fa kivágásra kerül..."
    else:
        if fa:
            fa["animacio"] = "vidul"
        jatek["mentett_fak"] += 1
        eredmeny = "fa_megmentve"
        uzenet = "🌳 Helyes válasz! A fa megmenekült!"
    
    await mindenkinek(szoba_id, {
        "tipus": "kor_eredmeny",
        "eredmeny": eredmeny,
        "fa_id": fa_id,
        "uzenet": uzenet,
        "helyes_valasz": kerdes["helyes"],
        "magyarazat": kerdes["magyarazat"],
        "mentett_fak": jatek["mentett_fak"],
        "jatekos_pontok": {jatekosok[ws]["nev"]: jatekosok[ws].get("pont", 0) 
                          for ws in szoba["jatekosok"] if ws in jatekosok}
    })
    
    await asyncio.sleep(4)
    await kor_indit(szoba_id)

async def jatek_vege(szoba_id):
    if szoba_id not in szobak:
        return
    szoba = szobak[szoba_id]
    jatek = szoba["jatek"]
    jatek["jatek_fazis"] = "vege"
    
    arany = jatek["mentett_fak"] / jatek["max_kor"] * 100
    
    if arany >= 80:
        cim = "🏆 Az erdő megmenekült!"
        uzenet = "Fantasztikus! A csapat megvédte az erdőt!"
    elif arany >= 50:
        cim = "🌿 Részleges győzelem"
        uzenet = "Sok fát sikerült megmenteni!"
    else:
        cim = "💔 Az erdő elveszett..."
        uzenet = "A fakitermelők győztek. Próbáljátok újra!"
    
    rangsor = []
    for ws in szoba["jatekosok"]:
        if ws in jatekosok:
            rangsor.append({
                "nev": jatekosok[ws]["nev"],
                "pont": jatekosok[ws].get("pont", 0),
                "szin": jatekosok[ws]["szin"]
            })
    rangsor.sort(key=lambda x: x["pont"], reverse=True)
    
    await mindenkinek(szoba_id, {
        "tipus": "jatek_vege",
        "cim": cim,
        "uzenet": uzenet,
        "mentett_fak": jatek["mentett_fak"],
        "ossz_kor": jatek["max_kor"],
        "arany": arany,
        "rangsor": rangsor
    })

async def kezel(ws):
    try:
        async for uzenet_str in ws:
            try:
                uzenet = json.loads(uzenet_str)
                tipus = uzenet.get("tipus")
                
                if tipus == "csatlakozas":
                    nev = uzenet.get("nev", "Játékos")[:20]
                    szin_lista = ["#7ec8a0", "#f4a261", "#84b6e0", "#c9a0dc", "#f7c59f"]
                    szin = random.choice(szin_lista)
                    jatekosok[ws] = {
                        "nev": nev,
                        "szin": szin,
                        "pont": 0,
                        "ero": 100,
                        "x": 0,
                        "y": 0,
                        "z": 0,
                        "animacio": "idle"
                    }
                    
                    szoba_id = uzenet.get("szoba_id")
                    if szoba_id and szoba_id in szobak and len(szobak[szoba_id]["jatekosok"]) < 4:
                        szobak[szoba_id]["jatekosok"].append(ws)
                    else:
                        szoba_id = uj_szoba_id()
                        szobak[szoba_id] = {
                            "jatekosok": [ws],
                            "jatek": uj_jatek_allapot()
                        }
                    
                    ws_szoba[ws] = szoba_id
                    
                    await kuldes(ws, {
                        "tipus": "csatlakozva",
                        "szoba_id": szoba_id,
                        "te_neved": nev,
                        "te_szined": szin
                    })
                    await allapot_kuldes(szoba_id)
                    await mindenkinek(szoba_id, {
                        "tipus": "rendszer_uzenet",
                        "szoveg": f"🌿 {nev} csatlakozott az erdőhöz!"
                    }, kivetel=ws)
                
                elif tipus == "mozgas":
                    if ws in ws_szoba and ws in jatekosok:
                        jatekosok[ws]["x"] = uzenet.get("x", 0)
                        jatekosok[ws]["y"] = uzenet.get("y", 0)
                        jatekosok[ws]["z"] = uzenet.get("z", 0)
                        jatekosok[ws]["ero"] = uzenet.get("ero", 100)
                        jatekosok[ws]["animacio"] = uzenet.get("animacio", "idle")
                        szoba_id = ws_szoba[ws]
                        jatekos_lista = []
                        for w in szobak[szoba_id]["jatekosok"]:
                            if w in jatekosok:
                                jatekos_lista.append({
                                    "nev": jatekosok[w]["nev"],
                                    "szin": jatekosok[w]["szin"],
                                    "pont": jatekosok[w].get("pont", 0),
                                    "x": jatekosok[w].get("x", 0),
                                    "y": jatekosok[w].get("y", 0),
                                    "z": jatekosok[w].get("z", 0),
                                    "ero": jatekosok[w].get("ero", 100),
                                    "animacio": jatekosok[w].get("animacio", "idle")
                                })
                        await mindenkinek(szoba_id, {
                            "tipus": "jatekosok_mozgas",
                            "jatekosok": jatekos_lista
                        })
                
                elif tipus == "jatek_indit":
                    if ws in ws_szoba:
                        szoba_id = ws_szoba[ws]
                        szoba = szobak[szoba_id]
                        if len(szoba["jatekosok"]) >= 1:
                            szoba["jatek"]["jatek_fazis"] = "jatek"
                            await mindenkinek(szoba_id, {
                                "tipus": "jatek_indul",
                                "jatekosok_szama": len(szoba["jatekosok"])
                            })
                            await allapot_kuldes(szoba_id)
                            await asyncio.sleep(2)
                            await kor_indit(szoba_id)
                
                elif tipus == "akadaly_aktivalas":
                    if ws in ws_szoba and ws in jatekosok:
                        szoba_id = ws_szoba[ws]
                        szoba = szobak[szoba_id]
                        jatek = szoba["jatek"]
                        runa_id = uzenet.get("runa_id")

                        if jatek["jatek_fazis"] == "akadaly_kereses":
                            cel_runa = next((r for r in jatek["akadaly"]["runak"] if r["id"] == runa_id and r["cel"]), None)
                            if cel_runa and not cel_runa["aktiv"]:
                                cel_runa["aktiv"] = True
                                cel_runa["cel"] = False
                                await kerdes_indit(szoba_id, ws)
                
                elif tipus == "valasz":
                    if ws in ws_szoba and ws in jatekosok:
                        szoba_id = ws_szoba[ws]
                        szoba = szobak[szoba_id]
                        jatek = szoba["jatek"]
                        
                        if jatek["jatek_fazis"] == "kerdes" and jatek["aktualis_kerdes"]:
                            valasz_idx = uzenet.get("valasz_idx")
                            kerdes = jatek["aktualis_kerdes"]
                            
                            if ws not in jatek.get("valaszok_beerkezett", {}):
                                jatek["valaszok_beerkezett"][ws] = valasz_idx
                                
                                helyes = (valasz_idx == kerdes["helyes"])
                                if helyes:
                                    jatekosok[ws]["pont"] = jatekosok[ws].get("pont", 0) + 10
                                    await kuldes(ws, {
                                        "tipus": "valasz_visszajelzes",
                                        "helyes": True,
                                        "pont_kapott": 10
                                    })
                                    await kor_ertekel(szoba_id, kerdes["kerdes_idx"], kerdes["fa_id"], ws)
                                else:
                                    await kuldes(ws, {
                                        "tipus": "valasz_visszajelzes",
                                        "helyes": False,
                                        "pont_kapott": 0
                                    })

                                    mindenki_valaszolt = len(jatek.get("valaszok_beerkezett", {})) == len(szoba["jatekosok"])
                                    if mindenki_valaszolt:
                                        await kor_ertekel(szoba_id, kerdes["kerdes_idx"], kerdes["fa_id"], -1)
                
                elif tipus == "ujra_jatek":
                    if ws in ws_szoba:
                        szoba_id = ws_szoba[ws]
                        szoba = szobak[szoba_id]
                        nev = jatekosok[ws]["nev"]
                        
                        if 'ujra_szavazatok' not in szoba:
                            szoba["ujra_szavazatok"] = set()
                        
                        szoba["ujra_szavazatok"].add(ws)
                        szukseges = len(szoba["jatekosok"]) # All players must vote to restart
                        jelenlegi = len(szoba["ujra_szavazatok"])
                        
                        if jelenlegi >= szukseges:
                            szoba["jatek"] = uj_jatek_allapot()
                            szoba["ujra_szavazatok"] = set()
                            szoba["jatek"]["jatek_fazis"] = "jatek"
                            for w in szoba["jatekosok"]:
                                if w in jatekosok:
                                    jatekosok[w]["pont"] = 0
                                    jatekosok[w]["ero"] = 100
                                    jatekosok[w]["x"], jatekosok[w]["y"], jatekosok[w]["z"] = 0, 0, 0
                            await mindenkinek(szoba_id, {
                                "tipus": "jatek_indul",
                                "jatekosok_szama": len(szoba["jatekosok"])
                            })
                            await allapot_kuldes(szoba_id)
                            await asyncio.sleep(2)
                            await kor_indit(szoba_id)
                
                elif tipus == "chat":
                    if ws in ws_szoba and ws in jatekosok:
                        szoba_id = ws_szoba[ws]
                        szoveg = uzenet.get("szoveg", "")[:100]
                        await mindenkinek(szoba_id, {
                            "tipus": "chat_uzenet",
                            "nev": jatekosok[ws]["nev"],
                            "szoveg": szoveg,
                            "szin": jatekosok[ws]["szin"]
                        })
                        
            except json.JSONDecodeError:
                pass
    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        if ws in jatekosok:
            nev = jatekosok[ws]["nev"]
            if ws in ws_szoba:
                szoba_id = ws_szoba[ws]
                if szoba_id in szobak:
                    szobak[szoba_id]["jatekosok"] = [w for w in szobak[szoba_id]["jatekosok"] if w != ws]
                    await mindenkinek(szoba_id, {
                        "tipus": "rendszer_uzenet",
                        "szoveg": f"🍂 {nev} elhagyta az erdőt."
                    })
                    if not szobak[szoba_id]["jatekosok"]:
                        del szobak[szoba_id]
                del ws_szoba[ws]
            del jatekosok[ws]

HTML_TARTALOM = r"""<!DOCTYPE html>
<html lang="hu">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Erdővédők 🌳</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700;900&family=Fredoka+One&display=swap');
  :root {
    --p-green: #588157;
    --p-green-light: #84a98c;
    --p-text: #354f52;
    --p-bg: #fefae0;
    --p-bg-dark: #e9e5c9;
    --p-accent: #e9c46a;
    --p-danger: #e76f51;
    --p-shadow: rgba(53, 79, 82, 0.08);
    --p-shadow-strong: rgba(53, 79, 82, 0.15);
  }
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body {
    font-family: 'Nunito', sans-serif;
    background: var(--p-bg);
    color: var(--p-text);
    overflow: hidden;
    height: 100vh;
  }
  .kepernyo { display: none; position: absolute; inset: 0; }
  .kepernyo.aktiv { display: flex; animation: fadeIn .3s ease; }
  @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
  #betolto {
    flex-direction: column;
    align-items: center;
    justify-content: center;
    background: var(--p-green-light);
  }
  .logo-fa { font-size: 5rem; animation: lebeg 2s ease-in-out infinite; }
  @keyframes lebeg { 0%,100%{transform:translateY(0)} 50%{transform:translateY(-12px)} }
  .logo-cim {
    font-family: 'Fredoka One', cursive;
    font-size: 3.5rem;
    color: var(--p-green);
    text-shadow: 3px 3px 0 rgba(0,0,0,.1);
    margin: 1rem 0 0.5rem;
  }
  .logo-al { color: var(--p-text); font-size: 1.1rem; opacity: .8; }
  .betolto-sor { width: 200px; height: 8px; background: rgba(255,255,255,.5); border-radius: 99px; margin-top: 2rem; overflow: hidden; }
  .betolto-tolt { height: 100%; background: var(--p-green); border-radius: 99px; animation: tolt 2s ease forwards; }
  @keyframes tolt { from{width:0} to{width:100%} }
  .keszitok { position: absolute; bottom: 1.5rem; font-size: .85rem; color: var(--p-text); opacity: .7; }
  #fomenu { flex-direction: column; align-items: center; justify-content: center; background: var(--p-bg); }
  .menu-kart {
    background: white;
    border-radius: 16px;
    padding: 2.5rem;
    width: min(440px, 95vw);
    box-shadow: 0 8px 24px var(--p-shadow-strong);
    border: 1px solid var(--p-bg-dark);
  }
  .menu-fejlec { text-align: center; margin-bottom: 2rem; }
  .menu-fejlec h1 { font-family: 'Fredoka One', cursive; font-size: 2.4rem; color: var(--p-green); }
  .menu-fejlec p { color: var(--p-text); opacity: .7; font-size: .95rem; margin-top: .3rem; }
  input[type=text] {
    width: 100%;
    padding: .8rem 1rem;
    border: 2px solid var(--p-bg-dark);
    border-radius: 8px;
    font-family: 'Nunito', sans-serif;
    font-size: 1rem;
    background: #fff;
    color: var(--p-text);
    transition: border-color .2s;
    margin-bottom: 1rem;
  }
  input[type=text]:focus { outline: none; border-color: var(--p-green); }
  .gomb {
    width: 100%;
    padding: .9rem;
    border: none;
    border-radius: 8px;
    font-family: 'Nunito', sans-serif;
    font-size: 1rem;
    font-weight: 700;
    cursor: pointer;
    transition: all .2s ease;
    margin-bottom: .7rem;
    border-bottom: 3px solid transparent;
  }
  .gomb:active { transform: translateY(2px); border-bottom-width: 1px; }
  .gomb-fo { background: var(--p-green); color: white; border-bottom-color: #3f613c; }
  .gomb-fo:hover { background: #6a9467; }
  .gomb-masodlagos { background: var(--p-bg-dark); color: var(--p-text); border-bottom-color: #c4bfab; }
  .gomb-masodlagos:hover { background: #d8d2b7; }
  .szoba-sor { display: flex; gap: .5rem; margin-bottom: 1rem; }
  .szoba-sor input { margin-bottom: 0; }
  .szoba-sor .gomb { width: auto; flex-shrink: 0; margin-bottom: 0; padding: .8rem 1.2rem; }
  .gomb.betolt { pointer-events: none; opacity: 0.7; position: relative; color: transparent !important; }
  .gomb.betolt::after { content: ""; position: absolute; width: 18px; height: 18px; top: 50%; left: 50%; margin: -9px; border: 3px solid rgba(255,255,255,0.3); border-top-color: white; border-radius: 50%; animation: pörgés 0.6s linear infinite; }
  @keyframes pörgés { to { transform: rotate(360deg); } }
  #tutorial { flex-direction: column; align-items: center; justify-content: center; background: var(--p-bg); overflow-y: auto; }
  .tutorial-kart { background: white; border-radius: 16px; padding: 2rem; width: min(520px, 95vw); box-shadow: 0 8px 24px var(--p-shadow-strong); margin: 1rem 0; }
  .tutorial-kart h2 { font-family: 'Fredoka One', cursive; color: var(--p-green); font-size: 1.8rem; margin-bottom: 1rem; text-align: center; }
  .tutorial-lepesek { list-style: none; }
  .tutorial-lepesek li { display: flex; gap: 1rem; align-items: flex-start; padding: .7rem 0; border-bottom: 1px solid #eee; font-size: .95rem; line-height: 1.5; }
  .tutorial-lepesek li:last-child { border-bottom: none; }
  .tuto-ikon { font-size: 1.5rem; flex-shrink: 0; }
  #lobby { flex-direction: column; align-items: center; justify-content: center; background: var(--p-bg); }
  .lobby-kart { background: white; border-radius: 16px; padding: 2rem; width: min(480px, 95vw); box-shadow: 0 8px 24px var(--p-shadow-strong); }
  .lobby-cim { font-family: 'Fredoka One', cursive; font-size: 2rem; color: var(--p-green); text-align: center; margin-bottom: .3rem; }
  .szoba-kod { text-align: center; font-size: .9rem; color: var(--p-text); margin-bottom: 1.5rem; }
  .szoba-kod strong { background: var(--p-bg-dark); padding: .2rem .6rem; border-radius: 8px; font-size: 1rem; cursor: pointer; transition: background .2s; }
  .jatekos-lista { list-style: none; margin: 1rem 0 1.5rem; }
  .jatekos-elem { display: flex; align-items: center; gap: .8rem; padding: .6rem; border-radius: 8px; margin-bottom: .4rem; background: var(--p-bg); }
  .jatekos-avatar { width: 36px; height: 36px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 1.2rem; flex-shrink: 0; }
  .jatekos-nev { font-weight: 700; }
  .varas-szoveg { text-align: center; color: var(--p-text); font-size: .9rem; margin-bottom: 1rem; font-style: italic; }
  #jatekter { display: none; flex-direction: column; background: #87CEEB; }
  #jatekter.aktiv { display: flex; }
  #canvas3d { position: absolute; top: 0; left: 0; width: 100%; height: 100%; }
  .hud { position: absolute; top: 0; left: 0; right: 0; padding: .7rem 1rem; display: flex; align-items: center; gap: .8rem; pointer-events: none; z-index: 10; }
  .hud-kart { background: rgba(255, 255, 255, 0.8); backdrop-filter: blur(8px); border-radius: 8px; padding: .4rem .8rem; font-weight: 700; font-size: .9rem; color: var(--p-text); pointer-events: auto; box-shadow: 0 2px 8px var(--p-shadow); }
  .hud-ero { color: #2a9d8f; }
  .hud-ero-bar { width: 100px; height: 8px; background: rgba(0,0,0,0.2); border-radius: 4px; display: inline-block; vertical-align: middle; margin-left: 5px; overflow: hidden; }
  .hud-ero-fill { height: 100%; background: #2a9d8f; width: 100%; transition: width 0.3s, background 0.3s; }
  .hud-jobb { position: absolute; top: .7rem; right: 1rem; display: flex; flex-direction: column; gap: .5rem; z-index: 10; align-items: flex-end; }
  .jatekos-hud-lista { list-style: none; }
  .jatekos-hud-elem { display: flex; align-items: center; gap: .5rem; background: rgba(255, 255, 255, 0.75); backdrop-filter: blur(6px); border-radius: 8px; padding: .3rem .7rem; margin-bottom: .3rem; font-size: .85rem; font-weight: 600; }
  .jp-szin-gomb { width: 12px; height: 12px; border-radius: 50%; flex-shrink: 0; }
  .iranyitas { position: absolute; bottom: 1.5rem; left: 50%; transform: translateX(-50%); z-index: 10; display: grid; grid-template-areas: ". fel ." "bal le jobb"; gap: .3rem; }
  .irany-gomb { width: 52px; height: 52px; background: rgba(255, 255, 255, 0.8); backdrop-filter: blur(6px); border: none; border-radius: 16px; font-size: 1.5rem; cursor: pointer; display: flex; align-items: center; justify-content: center; transition: all .15s; user-select: none; -webkit-tap-highlight-color: transparent; color: var(--p-text); }
  .irany-gomb:active { background: var(--p-green); color: white; transform: scale(.9); }
  .irany-fel { grid-area: fel; }
  .irany-le { grid-area: le; }
  .irany-bal { grid-area: bal; }
  .irany-jobb { grid-area: jobb; }
  .chat-doboz { position: absolute; bottom: 1.5rem; right: 1rem; width: 220px; z-index: 10; }
  .chat-uzenetek { background: rgba(255, 255, 255, 0.7); backdrop-filter: blur(6px); border-radius: 8px 8px 0 0; padding: .5rem; max-height: 120px; overflow-y: auto; font-size: .8rem; }
  .chat-uzenet { margin-bottom: .25rem; line-height: 1.4; }
  .chat-bevitel-sor { display: flex; gap: .3rem; }
  .chat-bevitel-sor input { flex: 1; padding: .4rem .7rem; border-radius: 0 0 0 8px; border: none; background: rgba(255, 255, 255, 0.85); font-family: 'Nunito', sans-serif; font-size: .85rem; margin-bottom: 0; }
  .chat-bevitel-sor input:focus { outline: none; }
  .chat-kuldes { padding: .4rem .7rem; background: var(--p-green); color: white; border: none; border-radius: 0 0 8px 0; cursor: pointer; font-size: .85rem; }
  #kviz-panel { position: absolute; inset: 0; display: none; align-items: center; justify-content: center; background: rgba(53, 79, 82, 0.3); backdrop-filter: blur(4px); z-index: 20; }
  #kviz-panel.aktiv { display: flex; }
  .kviz-kart { background: white; border-radius: 16px; padding: 2rem; width: min(480px, 95vw); box-shadow: 0 12px 48px var(--p-shadow-strong); animation: felbukkan .3s ease; }
  @keyframes felbukkan { from{transform:scale(.8) translateY(20px);opacity:0} to{transform:scale(1) translateY(0);opacity:1} }
  .kviz-fejlec { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem; }
  .kviz-kor-jel { background: var(--p-accent); border-radius: 8px; padding: .2rem .7rem; font-size: .85rem; font-weight: 700; color: var(--p-text); }
  .kviz-ido-jel { background: var(--p-danger); color: white; border-radius: 8px; padding: .2rem .7rem; font-size: .85rem; font-weight: 700; min-width: 60px; text-align: center; transition: background .5s; }
  .kviz-ido-jel.sietos { background: #c0392b; animation: villog .5s infinite; }
  @keyframes villog { 0%,100%{opacity:1} 50%{opacity:.5} }
  .kviz-fa-figyelmeztes { background: #fff3cd; border-left: 4px solid var(--p-accent); border-radius: 0 8px 8px 0; padding: .6rem .9rem; margin-bottom: 1rem; font-size: .9rem; color: #664d03; }
  .kviz-kerdes { font-size: 1.1rem; font-weight: 700; color: var(--p-text); margin-bottom: 1.2rem; line-height: 1.5; }
  .kviz-valaszok { display: grid; grid-template-columns: 1fr 1fr; gap: .6rem; }
  .kviz-valasz { padding: .8rem; border: 2px solid var(--p-bg-dark); border-radius: 8px; background: #fff; cursor: pointer; font-family: 'Nunito', sans-serif; font-size: .9rem; font-weight: 600; text-align: left; transition: all .15s; color: var(--p-text); }
  .kviz-valasz:hover { border-color: var(--p-green); background: #f8fbf7; }
  .kviz-valasz.helyes { background: #d1e7dd; border-color: var(--p-green); color: var(--p-green); }
  .kviz-valasz.helytelen { background: #f8d7da; border-color: var(--p-danger); }
  .kviz-valasz:disabled { cursor: default; }
  .kviz-visszajelzes { margin-top: 1rem; padding: .8rem; border-radius: 12px; font-size: .9rem; display: none; }
  .kviz-visszajelzes.helyes { background: #d1e7dd; color: var(--p-green); display: block; }
  .kviz-visszajelzes.helytelen { background: #f8d7da; color: #842029; display: block; }
  #eredmeny-overlay { position: absolute; inset: 0; display: none; align-items: center; justify-content: center; background: rgba(53, 79, 82, 0.4); backdrop-filter: blur(4px); z-index: 25; }
  #eredmeny-overlay.aktiv { display: flex; }
  .eredmeny-kart { background: white; border-radius: 16px; padding: 2rem; width: min(480px, 95vw); text-align: center; animation: felbukkan .3s ease; }
  .eredmeny-ikon { font-size: 3.5rem; margin-bottom: .5rem; }
  .eredmeny-cim { font-family: 'Fredoka One', cursive; font-size: 2rem; color: var(--p-green); margin-bottom: .5rem; }
  .eredmeny-stat { display: flex; justify-content: center; gap: 2rem; margin: 1.2rem 0; }
  .estat { text-align: center; }
  .estat-szam { font-family: 'Fredoka One', cursive; font-size: 2rem; color: var(--p-accent); }
  .estat-felirat { font-size: .85rem; color: var(--p-text); opacity: .7; }
  .rangsor { list-style: none; margin: 1rem 0; text-align: left; }
  .rangsor-elem { display: flex; align-items: center; gap: .8rem; padding: .5rem .7rem; border-radius: 8px; margin-bottom: .3rem; background: var(--p-bg); font-weight: 600; }
  .rangsor-szam { font-family: 'Fredoka One', cursive; font-size: 1.2rem; color: var(--p-text); opacity: .6; width: 24px; }
  .rangsor-pont { margin-left: auto; color: var(--p-accent); font-size: .9rem; }
  #ertesitesek { position: absolute; top: 4rem; left: 50%; transform: translateX(-50%); z-index: 30; display: flex; flex-direction: column; align-items: center; gap: .4rem; pointer-events: none; width: min(400px, 90vw); }
  .ertesites { background: rgba(53, 79, 82, 0.9); color: white; border-radius: 8px; padding: .6rem 1.2rem; font-size: .9rem; font-weight: 600; box-shadow: 0 4px 16px var(--p-shadow-strong); animation: ertesites-be .3s ease, ertesites-ki .3s ease 3.7s forwards; text-align: center; }
  @keyframes ertesites-be { from{transform:translateY(-20px);opacity:0} to{transform:translateY(0);opacity:1} }
  @keyframes ertesites-ki { to{transform:translateY(-20px);opacity:0} }
  .haladassav-tartaly { position: absolute; bottom: 8rem; left: 50%; transform: translateX(-50%); width: min(280px, 60vw); z-index: 10; }
  .haladassav-cimke { text-align: center; font-size: .8rem; font-weight: 700; color: white; text-shadow: 0 1px 3px rgba(0,0,0,.4); margin-bottom: .3rem; }
  .haladassav-hatter { height: 10px; background: rgba(255,255,255,.4); border-radius: 99px; overflow: hidden; }
  .haladassav-tolt { height: 100%; background: var(--p-accent); border-radius: 99px; transition: width .5s ease; box-shadow: 0 0 8px rgba(233, 196, 106, 0.8); }
  @media (max-width: 480px) {
    .kviz-valaszok { grid-template-columns: 1fr; }
    .kviz-kart { padding: 1.5rem; }
    .iranyitas { bottom: 1rem; }
    .chat-doboz { display: none; }
  }
</style>
</head>
<body>

<div id="betolto" class="kepernyo aktiv">
  <div class="logo-fa">🌲</div>
  <div class="logo-cim">Erdővédők</div>
  <div class="logo-al">Mentsd meg az erdőt!</div>
  <div class="betolto-sor"><div class="betolto-tolt"></div></div>
  <div class="keszitok">Készítő: Farkas András | v2.0</div>
</div>

<div id="fomenu" class="kepernyo">
  <div class="menu-kart">
    <div class="menu-fejlec">
      <h1>Erdővédők</h1>
      <p>Hívd meg barátaidat is (LAN IP: <strong>{{LOCAL_IP}}:8764</strong>)</p>
    </div>
    <input type="text" id="nev-input" placeholder="Add meg a neved..." maxlength="20">
    <button id="uj-jatek-gomb" class="gomb gomb-fo" onclick="jatek_inditasa(this)">Új Játék</button>
    <div class="szoba-sor">
      <input type="text" id="szoba-input" placeholder="Szoba kód..." maxlength="12">
      <button id="csat-gomb" class="gomb gomb-masodlagos" onclick="szobaba_csatlakozas(this)" style="white-space:nowrap">Csatlakozás</button>
    </div>
    <button class="gomb gomb-masodlagos" onclick="tutorial_mutat()">Hogyan játsszak?</button>
  </div>
</div>

<div id="tutorial" class="kepernyo">
  <div class="tutorial-kart">
    <h2>📖 Hogyan játsszak?</h2>
    <ul class="tutorial-lepesek">
      <li><span class="tuto-ikon">🌲</span><div><strong>Az erdő veszélyben!</strong> Fakitermelők próbálják kivágni a fákat.</div></li>
      <li><span class="tuto-ikon">🎯</span><div><strong>Akadály!</strong> Minden körben aktiválnod kell az akadályt az erdő közepén!</div></li>
      <li><span class="tuto-ikon">⭐</span><div><strong>Elsőként érj oda</strong> az akadályhoz és kapj +5 bonus pontot!</div></li>
      <li><span class="tuto-ikon">❓</span><div><strong>Kvízkérdés</strong> jelenik meg. A helyes válasz megmenti a fát!</div></li>
      <li><span class="tuto-ikon">⏱️</span><div><strong>30 másodperc</strong> van válaszolni. Ha senki nem válaszol helyesen, fa veszett.</div></li>
      <li><span class="tuto-ikon">🎮</span><div><strong>Mozogj</strong> az erdőben a nyilakkal! Valós idejű multiplayer!</div></li>
      <li><span class="tuto-ikon">🏆</span><div><strong>10 kör</strong> összesen. Mentsd meg minél több fát!</div></li>
    </ul>
    <button class="gomb gomb-fo" onclick="kepernyo_valt('fomenu')" style="margin-top:1rem">← Vissza a menübe</button>
  </div>
</div>

<div id="lobby" class="kepernyo">
  <div class="lobby-kart">
    <div class="lobby-cim">Lobby</div>
    <div class="szoba-kod">
      Szoba kód: <strong id="szoba-kod-jel" onclick="kod_masol(this)">—</strong>
    </div>
    <ul class="jatekos-lista" id="lobby-jatekos-lista"></ul>
    <div class="varas-szoveg" id="varas-szoveg">Várakozás játékosokra... (1-4 fő)</div>
    <button class="gomb gomb-fo" id="jatek-indit-gomb" onclick="jatek_indit_keres()">Játék indítása!</button>
    <button class="gomb gomb-masodlagos" onclick="kepernyo_valt('fomenu')">← Vissza</button>
  </div>
</div>

<div id="jatekter" class="kepernyo">
  <canvas id="canvas3d"></canvas>
  <div class="hud">
    <div class="hud-kart hud-fa">Mentett fák: <span id="hud-mentett">0</span>/6</div>
    <div class="hud-kart hud-kor">Kör: <span id="hud-kor">0</span>/6</div>
    <div class="hud-kart hud-pont">Pont: <span id="hud-pont">0</span></div>
    <div class="hud-kart hud-ero">💪 <div class="hud-ero-bar"><div id="hud-ero-fill" class="hud-ero-fill"></div></div></div>
  </div>
  <div class="hud-jobb">
    <ul class="jatekos-hud-lista" id="jatekos-hud-lista"></ul>
  </div>
  <div class="haladassav-tartaly">
    <div class="haladassav-cimke">🌿 Erdő védelme</div>
    <div class="haladassav-hatter"><div class="haladassav-tolt" id="haladassav" style="width:100%"></div></div>
  </div>
  <div class="iranyitas">
    <button class="irany-gomb irany-fel" ontouchstart="mozgas_kezd('fel')" ontouchend="mozgas_vege('fel')" onmousedown="mozgas_kezd('fel')" onmouseup="mozgas_vege('fel')">▲</button>
    <button class="irany-gomb irany-bal" ontouchstart="mozgas_kezd('bal')" ontouchend="mozgas_vege('bal')" onmousedown="mozgas_kezd('bal')" onmouseup="mozgas_vege('bal')">◀</button>
    <button class="irany-gomb irany-le" ontouchstart="mozgas_kezd('le')" ontouchend="mozgas_vege('le')" onmousedown="mozgas_kezd('le')" onmouseup="mozgas_vege('le')">▼</button>
    <button class="irany-gomb irany-jobb" ontouchstart="mozgas_kezd('jobb')" ontouchend="mozgas_vege('jobb')" onmousedown="mozgas_kezd('jobb')" onmouseup="mozgas_vege('jobb')">▶</button>
  </div>
  <div class="chat-doboz">
    <div class="chat-uzenetek" id="chat-uzenetek"></div>
    <div class="chat-bevitel-sor">
      <input type="text" id="chat-input" placeholder="Üzenet..." maxlength="80" onkeydown="if(event.key==='Enter')chat_kuldes()">
      <button class="chat-kuldes" onclick="chat_kuldes()">↑</button>
    </div>
  </div>
  <div id="ertesitesek"></div>
  <div id="kviz-panel">
    <div class="kviz-kart">
      <div class="kviz-fejlec">
        <span class="kviz-kor-jel" id="kviz-kor-jel">Kör 1/10</span>
        <span class="kviz-ido-jel" id="kviz-ido">⏱ 30</span>
      </div>
      <div class="kviz-fa-figyelmeztes">🪓 Egy fa veszélyben! Válaszolj helyesen!</div>
      <div class="kviz-kerdes" id="kviz-kerdes">Betöltés...</div>
      <div class="kviz-valaszok" id="kviz-valaszok"></div>
      <div class="kviz-visszajelzes" id="kviz-visszajelzes"></div>
    </div>
  </div>
  <div id="eredmeny-overlay">
    <div class="eredmeny-kart">
      <div class="eredmeny-ikon" id="eredmeny-ikon">🏆</div>
      <div class="eredmeny-cim" id="eredmeny-cim">Játék vége</div>
      <p id="eredmeny-uzenet" style="color:#888;font-size:.9rem;margin-bottom:.5rem"></p>
      <div class="eredmeny-stat">
        <div class="estat">
          <div class="estat-szam" id="eredmeny-mentett">0</div>
          <div class="estat-felirat">🌲 Mentett fa</div>
        </div>
        <div class="estat">
          <div class="estat-szam" id="eredmeny-arany">0%</div>
          <div class="estat-felirat">✅ Sikerráta</div>
        </div>
      </div>
      <ul class="rangsor" id="eredmeny-rangsor"></ul>
      <button class="gomb gomb-fo" onclick="ujra_jatek()">Újra!</button>
      <button class="gomb gomb-masodlagos" onclick="kepernyo_valt('fomenu')">Főmenü</button>
    </div>
  </div>
</div>

<script>
let audioCtx = null;
function audioInit() { if (!audioCtx) audioCtx = new (window.AudioContext || window.webkitAudioContext)(); }
function hang(freq, tipus, hossz, terfogat=0.3) {
  try { audioInit(); const osc = audioCtx.createOscillator(); const gain = audioCtx.createGain(); osc.connect(gain); gain.connect(audioCtx.destination); osc.type = tipus; osc.frequency.setValueAtTime(freq, audioCtx.currentTime); gain.gain.setValueAtTime(terfogat, audioCtx.currentTime); gain.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + hossz); osc.start(); osc.stop(audioCtx.currentTime + hossz); } catch(e) {}
}
function hang_helyes() { hang(523, 'sine', 0.15, 0.4); setTimeout(()=>hang(659, 'sine', 0.15, 0.4), 120); setTimeout(()=>hang(784, 'sine', 0.3, 0.4), 240); }
function hang_helytelen() { hang(220, 'sawtooth', 0.3, 0.3); setTimeout(()=>hang(180, 'sawtooth', 0.3, 0.3), 200); }
function hang_fa_esik() { hang(150, 'sawtooth', 0.4, 0.5); setTimeout(()=>hang(100, 'sawtooth', 0.6, 0.5), 300); }
function hang_fa_megment() { [523,587,659,784].forEach((f,i)=>setTimeout(()=>hang(f,'sine',0.2,0.35),i*80)); }
function hang_leptek() { if(Math.random()<0.3) hang(200+Math.random()*50, 'triangle', 0.08, 0.15); }
function hang_szellő() { try { audioInit(); const noise = audioCtx.createOscillator(); const gainN = audioCtx.createGain(); const filter = audioCtx.createBiquadFilter(); noise.type = 'sawtooth'; noise.frequency.value = 50; filter.type = 'bandpass'; filter.frequency.value = 1200; filter.Q.value = 0.5; noise.connect(filter); filter.connect(gainN); gainN.connect(audioCtx.destination); gainN.gain.setValueAtTime(0, audioCtx.currentTime); gainN.gain.linearRampToValueAtTime(0.03, audioCtx.currentTime + 1); gainN.gain.linearRampToValueAtTime(0, audioCtx.currentTime + 3); noise.start(); noise.stop(audioCtx.currentTime + 3); } catch(e) {} }

const canvas = document.getElementById('canvas3d');
const ctx = canvas.getContext('2d');
let w, h;
function canvas_meret() { w = canvas.width = window.innerWidth; h = canvas.height = window.innerHeight; }
canvas_meret();
window.addEventListener('resize', canvas_meret);

const kamera = { x: 0, z: 0, szog: 0, magassag: 6, tavol: 18 };
let vilag_fak = [];
let vilag_jatekosok = [];
let sajat_jatekos = { x: 0, y: 0, z: 0, vy: 0, szog: 0, animacio: 'idle', animFazis: 0, ero: 100, foldon: true };
let kiemelt_fa_id = null;
let fa_animaciok = {};

const felhok = Array.from({length:8}, (_, i) => ({ x: i * 80 - 200, y: 50 + i * 20, seb: 0.2 + Math.random() * 0.3, meret: 60 + Math.random() * 80 }));
const madarak = Array.from({length:6}, () => ({ x: Math.random()*800, y: 60+Math.random()*100, seb: 0.5+Math.random(), irany: 1, szarny: 0, szarny_seb: 0.15+Math.random()*0.1 }));

function vet(wx, wz, wy = 0) {
  const dx = wx - kamera.x; 
  const dy = wy - kamera.magassag;
  const dz = wz - kamera.z; 
  const cos = Math.cos(kamera.szog); 
  const sin = Math.sin(kamera.szog); 
  const rx = dx * cos - dz * sin; 
  const rz = dx * sin + dz * cos; 
  if (rz <= 0.1) return null; 
  const skala = kamera.tavol / rz; 
  const sx = w / 2 + rx * skala * 35; 
  const sy = h / 2 - dy * skala * 35; 
  return { x: sx, y: sy, skala, melyseg: rz };
}

function fa_rajzol(ctx, px, py, skala, tipus, animFazis, kiemelt, el) {
  const s = skala * 28; if (s < 3) return; ctx.save(); ctx.translate(px, py); let ringatas = 0; if (kiemelt) ringatas = Math.sin(animFazis * 0.15) * 0.08; ctx.rotate(ringatas); const alpha = el ? 1.0 : 0.3; ctx.globalAlpha = alpha; ctx.save(); ctx.scale(1, 0.2); ctx.globalAlpha = 0.15 * alpha; ctx.fillStyle = '#000'; ctx.beginPath(); ctx.ellipse(0, s * 0.9, s * 0.7, s * 0.2, 0, 0, Math.PI * 2); ctx.fill(); ctx.restore(); if (tipus === 'fenyo') { ctx.fillStyle = '#8B6914'; ctx.fillRect(-s*0.08, -s*0.1, s*0.16, s*0.9); const szinek = ['#5a8a4a', '#6aaa58', '#7cc068']; [[0.7, -s*0.85], [0.6, -s*0.65], [0.75, -s*0.38]].forEach(([sz, dy], i) => { ctx.fillStyle = szinek[i]; ctx.beginPath(); ctx.moveTo(0, dy); ctx.lineTo(-s*sz, dy + s*0.35); ctx.lineTo(s*sz, dy + s*0.35); ctx.closePath(); ctx.fill(); }); ctx.fillStyle = '#4a7a3a'; ctx.beginPath(); ctx.moveTo(0, -s*0.95); ctx.lineTo(-s*0.18, -s*0.75); ctx.lineTo(s*0.18, -s*0.75); ctx.closePath(); ctx.fill(); } else if (tipus === 'nyir') { ctx.fillStyle = '#e8e0d0'; ctx.fillRect(-s*0.06, -s*0.15, s*0.12, s*0.85); ctx.fillStyle = '#2a2a2a'; [-0.3, 0.1, 0.4, 0.65].forEach(p => { ctx.fillRect(-s*0.06, p*s*0.8, s*0.12, s*0.04); }); const zold = kiemelt ? '#aad890' : '#90c878'; ctx.fillStyle = zold; ctx.beginPath(); ctx.ellipse(0, -s*0.55, s*0.38, s*0.42, 0, 0, Math.PI*2); ctx.fill(); ctx.fillStyle = '#7ab868'; ctx.beginPath(); ctx.ellipse(s*0.15, -s*0.68, s*0.28, s*0.32, 0.3, 0, Math.PI*2); ctx.fill(); } else { ctx.fillStyle = '#7a5c32'; ctx.fillRect(-s*0.1, -s*0.05, s*0.2, s*0.85); ctx.strokeStyle = '#7a5c32'; ctx.lineWidth = s*0.05; ctx.beginPath(); ctx.moveTo(0, -s*0.05); ctx.lineTo(-s*0.3, -s*0.4); ctx.stroke(); ctx.beginPath(); ctx.moveTo(0, -s*0.05); ctx.lineTo(s*0.25, -s*0.35); ctx.stroke(); const zold2 = kiemelt ? '#88c870' : '#72b860'; ctx.fillStyle = zold2; ctx.beginPath(); ctx.ellipse(0, -s*0.5, s*0.5, s*0.45, 0, 0, Math.PI*2); ctx.fill(); ctx.fillStyle = '#5aa045'; ctx.beginPath(); ctx.ellipse(-s*0.2, -s*0.58, s*0.3, s*0.28, -0.3, 0, Math.PI*2); ctx.fill(); ctx.beginPath(); ctx.ellipse(s*0.22, -s*0.62, s*0.28, s*0.26, 0.3, 0, Math.PI*2); ctx.fill(); } if (kiemelt) { const izzas = 0.5 + 0.5*Math.sin(animFazis*0.1); ctx.globalAlpha = 0.25 * izzas * alpha; ctx.fillStyle = '#ff6600'; ctx.beginPath(); ctx.ellipse(0, -s*0.5, s*0.65, s*0.6, 0, 0, Math.PI*2); ctx.fill(); } ctx.globalAlpha = 1; ctx.restore();
}

function akadaly_rajzol(ctx, px, py, skala) { const s = skala * 28; if (s < 3) return; ctx.save(); ctx.translate(px, py); ctx.save(); ctx.scale(1, 0.2); ctx.globalAlpha = 0.2; ctx.fillStyle = '#000'; ctx.beginPath(); ctx.ellipse(0, s * 0.9, s * 1.5, s * 0.5, 0, 0, Math.PI * 2); ctx.fill(); ctx.restore(); ctx.fillStyle = '#8a9a8c'; ctx.fillRect(-s*0.5, -s*2.5, s*1.0, s*3.5); ctx.fillStyle = '#a8b8aa'; ctx.beginPath(); ctx.ellipse(0, -s*2.5, s*0.5, s*0.15, 0, 0, Math.PI*2); ctx.fill(); ctx.restore(); }

function runa_rajzol(ctx, px, py, skala, runa) { const s = skala * 28; if (s < 2) return; ctx.save(); ctx.translate(px, py - s * 1.5); const fazis = animFazis + runa.id * 20; const lebeges = Math.sin(fazis * 0.03) * s * 0.2; ctx.translate(0, lebeges); if (runa.cel && !runa.aktiv) { const izzas = 0.6 + 0.4 * Math.sin(fazis * 0.08); ctx.globalAlpha = 0.5 * izzas; ctx.fillStyle = '#f7d794'; ctx.beginPath(); ctx.arc(0, 0, s * 0.6, 0, Math.PI * 2); ctx.fill(); ctx.globalAlpha = 1; } ctx.fillStyle = runa.aktiv ? '#e9c46a' : '#9ab0a0'; ctx.beginPath(); ctx.arc(0, 0, s * 0.3, 0, Math.PI * 2); ctx.fill(); ctx.strokeStyle = runa.aktiv ? '#fff' : '#c8d8cc'; ctx.lineWidth = s * 0.05; ctx.beginPath(); ctx.moveTo(0, -s*0.15); ctx.lineTo(0, s*0.15); ctx.moveTo(-s*0.1, 0); ctx.lineTo(s*0.1, 0); ctx.stroke(); ctx.restore(); }

function jatekos_rajzol(ctx, px, py, skala, szin, nev, animacio, animFazis, te, y = 0) { 
  const s = skala * 35; 
  if (s < 4) return; 
  ctx.save(); 
  ctx.translate(px, py); 
  // Shadow
  ctx.save(); 
  ctx.scale(1, 0.3); 
  ctx.globalAlpha = 0.2 / (1 + y*0.1); 
  ctx.fillStyle = '#000'; 
  ctx.beginPath(); ctx.arc(0, 0, s*0.6, 0, Math.PI*2); ctx.fill(); 
  ctx.restore(); 
  
  const h_off = -y * s * 0.8;
  // Body
  ctx.fillStyle = szin;
  ctx.beginPath(); ctx.roundRect(-s*0.3, -s*1.2 + h_off, s*0.6, s*1.0, s*0.15); ctx.fill();
  // Head
  ctx.fillStyle = '#f5d0a0';
  ctx.beginPath(); ctx.arc(0, -s*1.5 + h_off, s*0.35, 0, Math.PI*2); ctx.fill();
  // Eyes
  ctx.fillStyle = '#000';
  ctx.beginPath(); ctx.arc(-s*0.12, -s*1.55 + h_off, s*0.05, 0, Math.PI*2); ctx.fill();
  ctx.beginPath(); ctx.arc(s*0.12, -s*1.55 + h_off, s*0.05, 0, Math.PI*2); ctx.fill();
  
  if (te) {
    ctx.fillStyle = 'rgba(255,255,255,0.9)'; ctx.font = `bold ${Math.max(10, s*0.5)}px Nunito`; ctx.textAlign = 'center';
    ctx.fillText('▼ TE', 0, -s*2.2 + h_off);
  }
  ctx.fillStyle = 'white'; ctx.font = `${Math.max(9, s*0.4)}px Nunito`; ctx.textAlign = 'center';
  ctx.fillText(nev, 0, -s*1.9 + h_off);
  ctx.restore(); 
}
function fal_rajzol(ctx, px, py, skala, w, h) { 
  const s = skala * 35; 
  ctx.save(); 
  ctx.translate(px, py); 
  // Main wall
  ctx.fillStyle = '#94a3b8'; 
  ctx.fillRect(-s*w*0.5, -s*h, s*w, s*h); 
  // Border
  ctx.strokeStyle = '#475569'; ctx.lineWidth = 2; ctx.strokeRect(-s*w*0.5, -s*h, s*w, s*h); 
  // Legs/Pillars
  ctx.fillStyle = '#475569';
  ctx.fillRect(-s*w*0.5 - s*0.2, -s*h, s*0.4, s*h + s*0.1);
  ctx.fillRect(s*w*0.5 - s*0.2, -s*h, s*0.4, s*h + s*0.1);
  ctx.restore(); 
}
function spinner_rajzol(ctx, px, py, skala, r, szog) { 
  const s = skala * 35; 
  ctx.save(); 
  ctx.translate(px, py); 
  // Base Pillar
  ctx.fillStyle = '#1e293b';
  ctx.fillRect(-s*0.3, -s*0.5, s*0.6, s*0.6);
  // Spinner Arm
  ctx.save();
  ctx.translate(0, -s*1.2);
  ctx.rotate(szog); 
  // Arm design
  const armW = s*r;
  const armH = s*0.4;
  ctx.fillStyle = '#ef4444'; 
  ctx.fillRect(-armW, -armH/2, armW*2, armH); 
  // Stripes
  ctx.fillStyle = '#fef08a';
  for(let i=-armW; i<armW; i+=s*1.5) {
      ctx.beginPath();
      ctx.moveTo(i, -armH/2); ctx.lineTo(i+s*0.5, -armH/2);
      ctx.lineTo(i+s*1.0, armH/2); ctx.lineTo(i+s*0.5, armH/2);
      ctx.fill();
  }
  ctx.fillStyle = '#991b1b'; 
  ctx.beginPath(); ctx.arc(0, 0, s*0.6, 0, Math.PI*2); ctx.fill(); 
  ctx.restore();
  ctx.restore(); 
}
function hammer_rajzol(ctx, px, py, skala, h) { 
  const s = skala * 35; 
  ctx.save(); 
  ctx.translate(px, py); 
  // Frame
  ctx.strokeStyle = '#334155'; ctx.lineWidth = s*0.1;
  ctx.strokeRect(-s*1.8, -s*10, s*3.6, s*10);
  // Hammer Head
  ctx.save();
  ctx.translate(0, -s*h);
  ctx.fillStyle = '#f59e0b'; 
  ctx.fillRect(-s*1.5, -s*1.5, s*3, s*1.5); 
  ctx.fillStyle = '#78350f';
  ctx.strokeRect(-s*1.5, -s*1.5, s*3, s*1.5);
  ctx.restore();
  ctx.restore(); 
}
function goal_rajzol(ctx, px, py, skala, r) { 
  const s = skala * 35; 
  ctx.save(); 
  ctx.translate(px, py); 
  // Ground circle
  ctx.fillStyle = 'rgba(16, 185, 129, 0.4)'; 
  ctx.beginPath(); ctx.arc(0, 0, s*r, 0, Math.PI*2); ctx.fill(); 
  // Pillars
  ctx.fillStyle = '#065f46';
  ctx.fillRect(-s*r, -s*8, s*0.5, s*8);
  ctx.fillRect(s*r - s*0.5, -s*8, s*0.5, s*8);
  // Banner
  ctx.fillStyle = '#10b981';
  ctx.fillRect(-s*r, -s*8, s*r*2, s*1.5);
  ctx.fillStyle = 'white'; ctx.font = `bold ${s}px Nunito`; ctx.textAlign = 'center';
  ctx.fillText('CÉL', 0, -s*7);
  ctx.restore(); 
}

const fuvek = Array.from({length:200}, () => ({ x: (Math.random()-0.5)*90, z: (Math.random()-0.5)*90, mag: 0.2 + Math.random() * 0.3, szin: ['#7ec870','#6ab858','#88d068','#5aa048'][Math.floor(Math.random()*4)] }));
const viragok = Array.from({length:40}, () => ({ x: (Math.random()-0.5)*80, z: (Math.random()-0.5)*80, szin: ['#f4a261','#84b6e0','#f7d794','#c9a0dc','#f87171'][Math.floor(Math.random()*5)] }));
let animFazis = 0;

function keret_rajzol() {
  animFazis++;
  const egGrad = ctx.createLinearGradient(0, 0, 0, h);
  egGrad.addColorStop(0, '#a8d8f0');
  egGrad.addColorStop(0.6, '#c8eaf8');
  egGrad.addColorStop(1, '#d4f0c8');
  ctx.fillStyle = egGrad;
  ctx.fillRect(0, 0, w, h);
  
  ctx.save();
  ctx.fillStyle = '#ffd070';
  const napFeny = ctx.createRadialGradient(w*0.82, h*0.12, 0, w*0.82, h*0.12, 70);
  napFeny.addColorStop(0, 'rgba(255,220,80,0.9)');
  napFeny.addColorStop(0.5, 'rgba(255,200,60,0.3)');
  napFeny.addColorStop(1, 'rgba(255,180,40,0)');
  ctx.fillStyle = napFeny;
  ctx.beginPath();
  ctx.arc(w*0.82, h*0.12, 70, 0, Math.PI*2);
  ctx.fill();
  ctx.fillStyle = '#ffdd60';
  ctx.beginPath();
  ctx.arc(w*0.82, h*0.12, 28, 0, Math.PI*2);
  ctx.fill();
  ctx.restore();
  
  felhok.forEach(f => { f.x += f.seb; if (f.x > w + 200) f.x = -200; ctx.save(); ctx.globalAlpha = 0.75; ctx.fillStyle = 'white'; [[0,0,1],[0.4,0.12,0.7],[-0.35,0.1,0.65],[0.2,-0.18,0.6]].forEach(([ox,oy,sz]) => { ctx.beginPath(); ctx.ellipse(f.x+ox*f.meret, f.y+oy*f.meret, f.meret*sz, f.meret*0.38, 0, 0, Math.PI*2); ctx.fill(); }); ctx.restore(); });
  
  madarak.forEach(m => { m.x += m.seb * m.irany; m.szarny += m.szarny_seb; if (m.x > w+100) { m.x = -100; m.y = 60+Math.random()*100; } const szarnyKiteres = Math.sin(m.szarny) * 8; ctx.save(); ctx.strokeStyle = '#4a6a8a'; ctx.lineWidth = 1.5; ctx.beginPath(); ctx.moveTo(m.x - 10, m.y); ctx.quadraticCurveTo(m.x - 5, m.y + szarnyKiteres, m.x, m.y); ctx.quadraticCurveTo(m.x + 5, m.y + szarnyKiteres, m.x + 10, m.y); ctx.stroke(); ctx.restore(); });
  
  const kodGrad = ctx.createLinearGradient(0, h*0.3, 0, h*0.55);
  kodGrad.addColorStop(0, 'rgba(200,230,200,0)');
  kodGrad.addColorStop(1, 'rgba(200,230,200,0.35)');
  ctx.fillStyle = kodGrad;
  ctx.fillRect(0, h*0.3, w, h*0.25);
  
  const talajGrad = ctx.createLinearGradient(0, h*0.52, 0, h);
  talajGrad.addColorStop(0, '#9acc78');
  talajGrad.addColorStop(0.3, '#7eb560');
  talajGrad.addColorStop(1, '#5a8a42');
  ctx.fillStyle = talajGrad;
  
  // Render linear path floor
  if (jatek_allapot) {
    const pw = jatek_allapot.path_width || 16;
    const pl = jatek_allapot.path_length || 300;
    
    // Environment (Wide grass)
    const envP1 = vet(-100, -20);
    const envP2 = vet(100, -20);
    const envP3 = vet(100, pl + 50);
    const envP4 = vet(-100, pl + 50);
    if (envP1 && envP2 && envP3 && envP4) {
      ctx.fillStyle = '#2d4a22';
      ctx.beginPath();
      ctx.moveTo(envP1.x, envP1.y); ctx.lineTo(envP2.x, envP2.y);
      ctx.lineTo(envP3.x, envP3.y); ctx.lineTo(envP4.x, envP4.y);
      ctx.fill();
    }

    // Start Platform
    const startP1 = vet(-15, -15);
    const startP2 = vet(15, -15);
    const startP3 = vet(15, 5);
    const startP4 = vet(-15, 5);
    if (startP1 && startP2 && startP3 && startP4) {
      ctx.fillStyle = '#4a6d49';
      ctx.beginPath();
      ctx.moveTo(startP1.x, startP1.y); ctx.lineTo(startP2.x, startP2.y);
      ctx.lineTo(startP3.x, startP3.y); ctx.lineTo(startP4.x, startP4.y);
      ctx.fill();
      ctx.strokeStyle = 'white'; ctx.lineWidth = 2; ctx.stroke();
    }

    // Colorful tiles
    for (let z = 0; z < pl; z += 10) {
      if (z + 10 <= kamera.z + 0.1) continue;
      const z1 = Math.max(z, kamera.z + 0.1);
      const z2 = Math.max(z+10, kamera.z + 0.1);
      
      const p1 = vet(-pw/2, z1);
      const p2 = vet(pw/2, z1);
      const p3 = vet(pw/2, z2);
      const p4 = vet(-pw/2, z2);
      
      if (p1 && p2 && p3 && p4) {
        // Alternating colors
        const colors = ['#588157', '#3a5a40', '#a3b18a', '#dad7cd'];
        ctx.fillStyle = colors[Math.floor(z/10) % colors.length];
        ctx.beginPath();
        ctx.moveTo(p1.x, p1.y); ctx.lineTo(p2.x, p2.y);
        ctx.lineTo(p3.x, p3.y); ctx.lineTo(p4.x, p4.y);
        ctx.closePath();
        ctx.fill();
        // Side rails
        ctx.strokeStyle = '#344e41'; ctx.lineWidth = 2;
        ctx.beginPath(); ctx.moveTo(p1.x, p1.y); ctx.lineTo(p4.x, p4.y); ctx.stroke();
        ctx.beginPath(); ctx.moveTo(p2.x, p2.y); ctx.lineTo(p3.x, p3.y); ctx.stroke();
      }
    }
  } else {
    // Lobby / Fallback background
    const talajGrad = ctx.createLinearGradient(0, h*0.52, 0, h);
    talajGrad.addColorStop(0, '#9acc78');
    talajGrad.addColorStop(1, '#5a8a42');
    ctx.fillStyle = talajGrad;
    ctx.beginPath();
    ctx.moveTo(0, h*0.52);
    for (let x = 0; x <= w; x += 40) {
      ctx.lineTo(x, h*0.52 + Math.sin(x*0.02 + animFazis*0.005)*3);
    }
    ctx.lineTo(w, h);
    ctx.lineTo(0, h);
    ctx.closePath();
    ctx.fill();
  }
  
  const rajzolando = [];
  fuvek.forEach(f => { const p = vet(f.x, f.z, 0); if (!p || p.melyseg > 60) return; rajzolando.push({ melyseg: p.melyseg, tipus: 'fu', p, f }); });
  viragok.forEach(v => { const p = vet(v.x, v.z, 0); if (!p || p.melyseg > 55) return; rajzolando.push({ melyseg: p.melyseg, tipus: 'virag', p, v }); });
  vilag_fak.forEach(fa => { const p = vet(fa.x, fa.z, 0); if (!p || p.melyseg > 80) return; const animAdatok = fa_animaciok[fa.id] || {}; rajzolando.push({ melyseg: p.melyseg, tipus: 'fa', p, fa, animAdatok }); });
  if (jatek_allapot && jatek_allapot.akadaly) { 
    if (jatek_allapot.akadaly.elemek) {
      jatek_allapot.akadaly.elemek.forEach(el => {
        const p = vet(el.x || 0, el.z, el.y || 0);
        if (p) rajzolando.push({ melyseg: p.melyseg, tipus: 'objektum', p, el });
      });
    }
    jatek_allapot.akadaly.runak.forEach(runa => { const p_runa = vet(runa.x, runa.z, 0); if (p_runa) { rajzolando.push({ melyseg: p_runa.melyseg, tipus: 'runa', p: p_runa, runa }); } }); 
  }
  vilag_jatekosok.forEach(jp => { if (jp.nev === sajat_nev) return; const p = vet(jp.x || 0, jp.z || 0, jp.y || 0); if (!p || p.melyseg > 60) return; rajzolando.push({ melyseg: p.melyseg, tipus: 'jatekos_mas', p, jp }); });
  const sajatP = vet(sajat_jatekos.x, sajat_jatekos.z, sajat_jatekos.y); if (sajatP && sajatP.melyseg <= 1.5) { rajzolando.push({ melyseg: 0.1, tipus: 'sajat_jatekos', p: {x: w/2, y: h*0.65, skala: 1.8}, sajat_jatekos }); } else if (sajatP) { rajzolando.push({ melyseg: sajatP.melyseg, tipus: 'sajat_jatekos', p: sajatP, sajat_jatekos }); }
  rajzolando.sort((a, b) => b.melyseg - a.melyseg);
  rajzolando.forEach(elem => {
    if (elem.tipus === 'fu') { const { p, f } = elem; const sz = Math.max(2, p.skala * 10); ctx.fillStyle = f.szin; ctx.beginPath(); ctx.moveTo(p.x, p.y); ctx.lineTo(p.x - sz*0.3, p.y - sz*(1+Math.sin(animFazis*0.02+f.x)*0.1)); ctx.lineTo(p.x + sz*0.3, p.y - sz*(0.8+Math.sin(animFazis*0.02+f.z)*0.1)); ctx.closePath(); ctx.fill(); }
    else if (elem.tipus === 'virag') { const { p, v } = elem; const sz = Math.max(2, p.skala * 5); ctx.fillStyle = v.szin; ctx.beginPath(); ctx.arc(p.x, p.y, sz, 0, Math.PI*2); ctx.fill(); ctx.fillStyle = '#ffd070'; ctx.beginPath(); ctx.arc(p.x, p.y, sz*0.4, 0, Math.PI*2); ctx.fill(); }
    else if (elem.tipus === 'fa') { const { p, fa, animAdatok } = elem; const kiemelve = fa.id === kiemelt_fa_id; fa_animaciok[fa.id] = fa_animaciok[fa.id] || { fazis: 0 }; fa_animaciok[fa.id].fazis++; fa_rajzol(ctx, p.x, p.y, p.skala, fa.tipus, fa_animaciok[fa.id].fazis, kiemelve, fa.el); }
    else if (elem.tipus === 'jatekos_mas') { const { p, jp } = elem; jatekos_rajzol(ctx, p.x, p.y, p.skala, jp.szin||'#7ec8a0', jp.nev, jp.animacio||'idle', animFazis, false, jp.y||0); }
    else if (elem.tipus === 'sajat_jatekos') { const { p } = elem; jatekos_rajzol(ctx, p.x, p.y, p.skala, sajat_szin||'#7ec8a0', sajat_nev||'Te', sajat_jatekos.animacio, animFazis, true, sajat_jatekos.y); }
    else if (elem.tipus === 'runa') { runa_rajzol(ctx, elem.p.x, elem.p.y, elem.p.skala, elem.runa); }
    else if (elem.tipus === 'objektum') { 
        const { p, el } = elem;
        if (el.tipus === 'fal') fal_rajzol(ctx, p.x, p.y, p.skala, el.w, el.h);
        else if (el.tipus === 'spinner') spinner_rajzol(ctx, p.x, p.y, p.skala, el.r, animFazis * el.seb + el.offset);
        else if (el.tipus === 'hammer') hammer_rajzol(ctx, p.x, p.y, p.skala, Math.abs(Math.sin(animFazis * el.seb + el.offset)) * el.range);
        else if (el.tipus === 'goal') goal_rajzol(ctx, p.x, p.y, p.skala, el.r);
    }
  });
  if (animFazis % 40 === 0) {
    levelek.push({
      x: w*0.2 + Math.random()*w*0.6,
      y: h*0.2,
      vx: (Math.random()-0.5)*1.5,
      vy: 0.5+Math.random(),
      szin: ['#c8a050','#e8b840','#a8d060','#d09030'][Math.floor(Math.random()*4)],
      meret: 4+Math.random()*5,
      szog: Math.random()*Math.PI*2,
      szog_seb: (Math.random()-0.5)*0.1,
      alfa: 1
    });
  }
  levelek.forEach((l, i) => {
    l.x += l.vx + Math.sin(animFazis*0.02)*0.3;
    l.y += l.vy;
    l.szog += l.szog_seb;
    l.alfa -= 0.003;
    if (l.alfa <= 0 || l.y > h) { levelek.splice(i, 1); return; }
    ctx.save();
    ctx.globalAlpha = l.alfa;
    ctx.translate(l.x, l.y);
    ctx.rotate(l.szog);
    ctx.fillStyle = l.szin;
    ctx.beginPath();
    ctx.ellipse(0, 0, l.meret, l.meret*0.5, 0, 0, Math.PI*2);
    ctx.fill();
    ctx.restore();
  });
  requestAnimationFrame(keret_rajzol);
}

const levelek = [];
let ws = null;
let sajat_nev = '';
let sajat_szin = '#7ec8a0';
let szoba_id = '';
let sajat_pont = 0;
let jatek_allapot = null;
let aktivacios_keres_elkulve = false;

function ws_csatlakozes(nev, szoba_kod) {
  const protokoll = location.protocol === 'https:' ? 'wss' : 'ws';
  ws = new WebSocket(`${protokoll}://${location.hostname}:8765`);
  ws.onopen = () => { ws.send(JSON.stringify({ tipus: 'csatlakozas', nev: nev, szoba_id: szoba_kod || null })); };
  ws.onmessage = (e) => { const uzenet = JSON.parse(e.data); uzenet_kezel(uzenet); };
  ws.onclose = () => { ertesites_mutat('🔌 Kapcsolat megszakadt. Frissítsd az oldalt!', '#f8d7da'); };
  ws.onerror = () => { ertesites_mutat('❌ Kapcsolódási hiba!', '#f8d7da'); };
}

function uzenet_kezel(uzenet) {
  switch(uzenet.tipus) {
    case 'csatlakozva': szoba_id = uzenet.szoba_id; sajat_nev = uzenet.te_neved; sajat_szin = uzenet.te_szined; document.getElementById('szoba-kod-jel').textContent = szoba_id; kepernyo_valt('lobby'); break;
    case 'allapot': jatek_allapot = uzenet.jatek; vilag_jatekosok = uzenet.jatekosok; vilag_fak = uzenet.jatek.fak; lobby_frissit(uzenet.jatekosok); hud_frissit(); break;
    case 'jatekosok_mozgas': vilag_jatekosok = uzenet.jatekosok; jatekos_hud_frissit(uzenet.jatekosok); break;
    case 'jatek_indul': kepernyo_valt('jatekter'); keret_rajzol(); hang_szellő(); ertesites_mutat(`🌲 Játék kezdődik! ${uzenet.jatekosok_szama} játékossal`, '#d4edda'); break;
    case 'rendszer_uzenet': chat_uzenet_hozzaad('Rendszer', uzenet.szoveg, 'var(--p-green)'); ertesites_mutat(uzenet.szoveg); break;
    case 'chat_uzenet': chat_uzenet_hozzaad(uzenet.nev, uzenet.szoveg, uzenet.szin); break;
    case 'uj_kor_cel': aktivacios_keres_elkulve = false; jatek_allapot.akadaly = uzenet.akadaly; document.getElementById('hud-kor').textContent = uzenet.kor; ertesites_mutat(uzenet.uzenet); document.getElementById('kviz-panel').classList.remove('aktiv'); break;
    case 'uj_kerdes': kviz_mutat(uzenet); kiemelt_fa_id = uzenet.fa_id; document.getElementById('hud-kor').textContent = uzenet.kor; ido_frissit(uzenet.ido); break;
    case 'ido': ido_frissit(uzenet.ido); break;
    case 'valasz_visszajelzes': valasz_visszajelzes_mutat(uzenet.helyes, uzenet.pont_kapott); break;
    case 'kor_eredmeny': kiemelt_fa_id = null; if (uzenet.eredmeny === 'fa_kivagva') { hang_fa_esik(); const fa = vilag_fak.find(f => f.id === uzenet.fa_id); if (fa) fa.el = false; } else { hang_fa_megment(); ertesites_mutat('Fa megmentve! +10 pont'); } kor_eredmeny_mutat(uzenet); document.getElementById('hud-mentett').textContent = uzenet.mentett_fak; const haladassav = document.getElementById('haladassav'); haladassav.style.width = (uzenet.mentett_fak / 10 * 100) + '%'; sajat_pont = uzenet.jatekos_pontok[sajat_nev] || 0; document.getElementById('hud-pont').textContent = sajat_pont; break;
    case 'jatek_vege': jatek_vege_mutat(uzenet); break;
  }
}

function valasz_visszajelzes_mutat(helyes, pont) { const visszajelzes = document.getElementById('kviz-visszajelzes'); if (helyes) { hang_helyes(); visszajelzes.className = 'kviz-visszajelzes helyes'; visszajelzes.innerHTML = `✅ Helyes! <strong>+${pont} pont</strong>`; } else { hang_helytelen(); visszajelzes.className = 'kviz-visszajelzes helytelen'; visszajelzes.innerHTML = '❌ Sajnos nem ez a helyes válasz.'; } }

function kviz_mutat(adatok) { const panel = document.getElementById('kviz-panel'); panel.classList.add('aktiv'); document.getElementById('kviz-kor-jel').textContent = `Kör ${adatok.kor}/${adatok.max_kor || 10}`; document.getElementById('kviz-kerdes').textContent = adatok.kerdes.szoveg; document.getElementById('kviz-visszajelzes').className = 'kviz-visszajelzes'; document.getElementById('kviz-visszajelzes').textContent = ''; const valaszokDiv = document.getElementById('kviz-valaszok'); valaszokDiv.innerHTML = ''; adatok.kerdes.valaszok.forEach((v, i) => { const gomb = document.createElement('button'); gomb.className = 'kviz-valasz'; gomb.textContent = v; gomb.onclick = () => valasz_kuldes(i, adatok); valaszokDiv.appendChild(gomb); }); }

function valasz_kuldes(idx, adatok) { const gombok = document.querySelectorAll('.kviz-valasz'); gombok.forEach(g => g.disabled = true); ws.send(JSON.stringify({ tipus: 'valasz', valasz_idx: idx })); }

function kor_eredmeny_mutat(adatok) { setTimeout(() => { document.getElementById('kviz-panel').classList.remove('aktiv'); const visszajelzes = document.getElementById('kviz-visszajelzes'); visszajelzes.className = 'kviz-visszajelzes ' + (adatok.eredmeny === 'fa_megmentve' ? 'helyes' : 'helytelen'); visszajelzes.textContent = adatok.uzenet; ertesites_mutat(adatok.magyarazat); }, 1000); }

function jatek_vege_mutat(adatok) { document.getElementById('kviz-panel').classList.remove('aktiv'); const overlay = document.getElementById('eredmeny-overlay'); overlay.classList.add('aktiv'); const arany = Math.round(adatok.arany); document.getElementById('eredmeny-ikon').textContent = arany >= 80 ? '🏆' : arany >= 50 ? '🌿' : '💔'; document.getElementById('eredmeny-cim').textContent = adatok.cim; document.getElementById('eredmeny-uzenet').textContent = adatok.uzenet; document.getElementById('eredmeny-mentett').textContent = adatok.mentett_fak; document.getElementById('eredmeny-arany').textContent = arany + '%'; const rangsor = document.getElementById('eredmeny-rangsor'); rangsor.innerHTML = ''; (adatok.rangsor || []).forEach((jp, i) => { const li = document.createElement('li'); li.className = 'rangsor-elem'; li.innerHTML = `<span class="rangsor-szam">${i+1}</span><span class="jp-szin-gomb" style="background:${jp.szin}"></span><span>${jp.nev}</span><span class="rangsor-pont">⭐ ${jp.pont}</span>`; rangsor.appendChild(li); }); if (arany >= 80) hang_helyes(); }

function jatek_vege_indit() {
  const overlay = document.getElementById('eredmeny-overlay');
  if (overlay.classList.contains('aktiv')) return;
  overlay.classList.add('aktiv');
  hang_helyes();
  document.getElementById('eredmeny-cim').textContent = "🏁 CÉLBA ÉRTÉL!";
  document.getElementById('eredmeny-uzenet').textContent = "Gratulálunk! Te is teljesítetted a pályát!";
  document.getElementById('eredmeny-ikon').textContent = "👑";
}

function ido_frissit(ido) { const idoJel = document.getElementById('kviz-ido'); idoJel.textContent = `⏱ ${ido}`; idoJel.className = 'kviz-ido-jel' + (ido <= 10 ? ' sietos' : ''); }

const mozgas_allapot = { fel: false, le: false, bal: false, jobb: false };
let mozgas_ido = 0;
function mozgas_kezd(irany) { mozgas_allapot[irany] = true; }
function mozgas_vege(irany) { mozgas_allapot[irany] = false; }
document.addEventListener('keydown', e => { 
  if (['ArrowUp','w','W'].includes(e.key)) mozgas_allapot.fel = true; 
  if (['ArrowDown','s','S'].includes(e.key)) mozgas_allapot.le = true; 
  if (['ArrowLeft','a','A'].includes(e.key)) mozgas_allapot.bal = true; 
  if (['ArrowRight','d','D'].includes(e.key)) mozgas_allapot.jobb = true; 
  if (e.key === ' ' && sajat_jatekos.foldon) { sajat_jatekos.vy = 0.5; sajat_jatekos.foldon = false; hang(300, 'sine', 0.1, 0.2); }
});
document.addEventListener('keyup', e => { 
  if (['ArrowUp','w','W'].includes(e.key)) mozgas_allapot.fel = false; 
  if (['ArrowDown','s','S'].includes(e.key)) mozgas_allapot.le = false; 
  if (['ArrowLeft','a','A'].includes(e.key)) mozgas_allapot.bal = false; 
  if (['ArrowRight','d','D'].includes(e.key)) mozgas_allapot.jobb = false; 
});

setInterval(() => {
  if (!ws || ws.readyState !== WebSocket.OPEN) return;
  let mozgott = false;
  const seb = 0.35;
  
  // Movement
  if (mozgas_allapot.fel) { sajat_jatekos.z += seb; mozgott = true; }
  if (mozgas_allapot.le) { sajat_jatekos.z -= seb; mozgott = true; }
  if (mozgas_allapot.bal) { sajat_jatekos.x -= seb; mozgott = true; }
  if (mozgas_allapot.jobb) { sajat_jatekos.x += seb; mozgott = true; }
  
  // Physics (Jump/Gravity)
  if (!sajat_jatekos.foldon) {
    sajat_jatekos.y += sajat_jatekos.vy;
    sajat_jatekos.vy -= 0.04; // Gravity
    if (sajat_jatekos.y <= 0) {
      sajat_jatekos.y = 0;
      sajat_jatekos.vy = 0;
      sajat_jatekos.foldon = true;
    }
  }

  // Path collision & Falling
  if (jatek_allapot) {
    const pw = jatek_allapot.path_width / 2;
    // Falling logic
    if (Math.abs(sajat_jatekos.x) > pw + 0.2) {
        if (sajat_jatekos.y <= 0.1) {
            sajat_jatekos.foldon = false;
            sajat_jatekos.y -= 0.6; // Fall fast
            if (sajat_jatekos.y < -30) {
                // Death/Respawn at start
                sajat_jatekos.x = 0; sajat_jatekos.z = 0; sajat_jatekos.y = 10;
                sajat_jatekos.ero = Math.max(0, sajat_jatekos.ero - 20);
                sajat_jatekos.vy = 0;
                ertesites_mutat('💀 MEGHALTÁL! Visszakerültél az elejére.', '#e76f51');
                hang_fa_esik();
            }
        }
    }
    
    // Obstacle collision (simplified)
    if (jatek_allapot.akadaly.elemek) {
        jatek_allapot.akadaly.elemek.forEach(el => {
            const dx = sajat_jatekos.x - el.x;
            const dz = sajat_jatekos.z - el.z;
            const dist = Math.sqrt(dx*dx + dz*dz);
            if (el.tipus === 'spinner') {
                if (dist < el.r && sajat_jatekos.y < 2) {
                    // Knockback away from center
                    const push = 1.2;
                    sajat_jatekos.x += (dx/dist) * push;
                    sajat_jatekos.z += (dz/dist) * push;
                    sajat_jatekos.ero = Math.max(0, sajat_jatekos.ero - 0.5);
                }
            } else if (el.tipus === 'hammer') {
                const h_val = Math.abs(Math.sin(animFazis * el.seb + el.offset)) * el.range;
                if (dist < 2.5 && sajat_jatekos.y < h_val) {
                    sajat_jatekos.z -= 3; // Hard push back
                    sajat_jatekos.ero = Math.max(0, sajat_jatekos.ero - 5);
                    hang_fa_esik();
                }
            } else if (el.tipus === 'goal') {
                if (dist < el.r && sajat_jatekos.y < 2) {
                    ws.send(JSON.stringify({ tipus: 'chat', szoveg: '🏆 BEÉRTEM A CÉLBA!' }));
                    jatek_vege_indit(); // New local function for goal
                }
            }
        });
    }
  }

  // Camera follow (Improved Standard 3D)
  kamera.x += (sajat_jatekos.x - kamera.x) * 0.15;
  kamera.z += (sajat_jatekos.z - 20 - kamera.z) * 0.15;
  kamera.magassag = 10 + sajat_jatekos.y;
  kamera.tavol = 22;

  sajat_jatekos.animacio = mozgott ? 'fut' : 'idle';
  if (mozgott && sajat_jatekos.foldon) hang_leptek();
  
  // Strength check
  document.getElementById('hud-ero-fill').style.width = sajat_jatekos.ero + '%';
  if (sajat_jatekos.ero < 30) document.getElementById('hud-ero-fill').style.background = '#e76f51';
  
  // Rune activation
  if (jatek_allapot && jatek_allapot.jatek_fazis === 'akadaly_kereses' && !aktivacios_keres_elkulve) { 
    const cel_runa = jatek_allapot.akadaly.runak.find(r => r.cel && !r.aktiv); 
    if (cel_runa) { 
        const dx = sajat_jatekos.x - cel_runa.x; 
        const dz = sajat_jatekos.z - cel_runa.z; 
        const tavolsag = Math.sqrt(dx*dx + dz*dz); 
        if (tavolsag < 3.5 && sajat_jatekos.y < 2) { 
            aktivacios_keres_elkulve = true; 
            ws.send(JSON.stringify({ tipus: 'akadaly_aktivalas', runa_id: cel_runa.id })); 
            hang(440, 'sine', 0.2, 0.5); 
        } 
    } 
  }
  
  mozgas_ido++;
  if (mozgas_ido % 2 === 0) { 
    ws.send(JSON.stringify({ 
        tipus: 'mozgas', 
        x: sajat_jatekos.x, 
        y: sajat_jatekos.y, 
        z: sajat_jatekos.z, 
        ero: sajat_jatekos.ero,
        animacio: sajat_jatekos.animacio 
    })); 
  }
}, 50);

function lobby_frissit(jatekosok) { 
  const lista = document.getElementById('lobby-jatekos-lista'); 
  if (!lista) return;
  lista.innerHTML = ''; 
  if (!jatekosok || jatekosok.length === 0) return;
  jatekosok.forEach(jp => { 
    const li = document.createElement('li'); 
    li.className = 'jatekos-elem'; 
    const te = jp.nev === sajat_nev ? ' (Te)' : ''; 
    li.innerHTML = `<div class="jatekos-avatar" style="background:${jp.szin}20;color:${jp.szin}">●</div><div><div class="jatekos-nev">${jp.nev}${te}</div><div style="font-size:.8rem;color:var(--p-text);opacity:0.7">${jp.pont || 0} pont</div></div>`; 
    lista.appendChild(li); 
  }); 
  const varas = document.getElementById('varas-szoveg');
  if (varas) varas.textContent = `${jatekosok.length}/4 játékos csatlakozott`; 
}

function hud_frissit() { if (!jatek_allapot) return; document.getElementById('hud-mentett').textContent = jatek_allapot.mentett_fak; document.getElementById('hud-kor').textContent = jatek_allapot.kkor; document.getElementById('hud-pont').textContent = sajat_pont; }

function jatekos_hud_frissit(jatekosok) { const lista = document.getElementById('jatekos-hud-lista'); lista.innerHTML = ''; jatekosok.forEach(jp => { const li = document.createElement('li'); li.className = 'jatekos-hud-elem'; li.innerHTML = `<span class="jp-szin-gomb" style="background:${jp.szin}"></span><span>${jp.nev}</span><span style="color:var(--p-accent);font-size:.8rem;margin-left:auto;">${jp.pont}</span>`; lista.appendChild(li); }); }

function chat_kuldes() { const input = document.getElementById('chat-input'); const szoveg = input.value.trim(); if (!szoveg || !ws) return; ws.send(JSON.stringify({ tipus: 'chat', szoveg })); input.value = ''; }

function chat_uzenet_hozzaad(nev, szoveg, szin) { const uzenetek = document.getElementById('chat-uzenetek'); const div = document.createElement('div'); div.className = 'chat-uzenet'; div.innerHTML = `<strong style="color:${szin||'var(--p-green)'}">${nev}:</strong> ${szoveg}`; uzenetek.appendChild(div); uzenetek.scrollTop = uzenetek.scrollHeight; while (uzenetek.children.length > 20) { uzenetek.removeChild(uzenetek.firstChild); } }

function ertesites_mutat(szoveg, hatter) { const tartaly = document.getElementById('ertesitesek'); const div = document.createElement('div'); div.className = 'ertesites'; div.textContent = szoveg; if (hatter) div.style.backgroundColor = hatter; tartaly.appendChild(div); setTimeout(() => div.remove(), 4200); }

function kepernyo_valt(id) { 
  document.querySelectorAll('.kepernyo').forEach(k => k.classList.remove('aktiv')); 
  document.getElementById(id).classList.add('aktiv'); 
  document.querySelectorAll('.betolt').forEach(b => b.classList.remove('betolt'));
}

function kod_masol(element) { const kod = document.getElementById('szoba-kod-jel').textContent; if (navigator.clipboard) { navigator.clipboard.writeText(kod).then(() => { ertesites_mutat('Kód vágólapra másolva: ' + kod); const originalText = element.innerHTML; element.innerHTML = 'Másolva!'; element.style.background = 'var(--p-green)'; element.style.color = 'white'; setTimeout(() => { element.innerHTML = originalText; element.style.background = ''; element.style.color = ''; }, 1500); }); } else { ertesites_mutat('A másolás nem támogatott ezen a böngészőn.'); } }

function jatek_inditasa(btn) { 
  if (btn) btn.classList.add('betolt');
  const nev = document.getElementById('nev-input').value.trim() || `Játékos_${Math.floor(Math.random()*1000)}`; 
  sajat_nev = nev; 
  ws_csatlakozes(nev, null); 
}

function szobaba_csatlakozas(btn) { 
  if (btn) btn.classList.add('betolt');
  const nev = document.getElementById('nev-input').value.trim() || `Játékos_${Math.floor(Math.random()*1000)}`; 
  const szoba = document.getElementById('szoba-input').value.trim(); 
  sajat_nev = nev; 
  ws_csatlakozes(nev, szoba || null); 
}

function tutorial_mutat() { kepernyo_valt('tutorial'); }

function jatek_indit_keres() { if (!ws) return; ws.send(JSON.stringify({ tipus: 'jatek_indit' })); audioInit(); }

function ujra_jatek(btn) { 
  if (btn) btn.classList.add('betolt');
  if (ws) ws.send(JSON.stringify({ tipus: 'ujra_jatek' })); 
}

window.addEventListener('load', () => { setTimeout(() => { kepernyo_valt('fomenu'); }, 2200); });
</script>
</body>
</html>
"""

class HTMLSzerver(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.end_headers()
        
        # Determine local IP for sharing
        local_ip = '127.0.0.1'
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(('10.255.255.255', 1))
            local_ip = s.getsockname()[0]
            s.close()
        except Exception:
            pass
            
        final_html = HTML_TARTALOM.replace('{{LOCAL_IP}}', local_ip)
        
        self.wfile.write(final_html.encode('utf-8'))
    
    def log_message(self, format, *args):
        pass

def http_szerver_indit():
    szerver = HTTPServer(('', 8764), HTMLSzerver)
    szerver.serve_forever()

def start_async_loop(loop):
    asyncio.set_event_loop(loop)
    async def start_ws():
        async with websockets.serve(kezel, "0.0.0.0", 8765):
            await asyncio.Future()
    loop.run_until_complete(start_ws())

if __name__ == "__main__":
    try:
        print("""
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║   🌲  ERDŐVÉDŐK - Standalone Edition  🌲                ║
║                                                           ║
║   Tiszta, szórakoztató, akadálypályás kaland!           ║
║                                                           ║
╠═══════════════════════════════════════════════════════════╣
║                                                           ║
║   🎮 Standalone ablak nyílik...                           ║
║   🌐 HTTP: localhost:8764 | 🔌 WS: localhost:8765        ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
        """)
    except UnicodeEncodeError:
        print("Erdovedok - Standalone Edition indul...")
        print("HTTP: localhost:8764 | WS: localhost:8765")
    
    try:
        # Start HTTP server
        http_thread = threading.Thread(target=http_szerver_indit, daemon=True)
        http_thread.start()
        
        # Start WebSocket server in a separate thread
        loop = asyncio.new_event_loop()
        ws_thread = threading.Thread(target=start_async_loop, args=(loop,), daemon=True)
        ws_thread.start()
        
        # Open standalone window
        webview.create_window(
            'Erdővédők 🌳', 
            'http://localhost:8764', 
            width=1100, 
            height=800,
            background_color='#fefae0'
        )
        webview.start()
        
    except KeyboardInterrupt:
        print("\n🍂 Játék leállítva. Viszlát!")
    except Exception as e:
        print(f"❌ Hiba történt: {e}")
