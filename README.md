# SumoTraffic
**Traffic Automation via ANFIS in SUMO Simulation**

## 📋 Projekt leírás

Ez a projekt egy **Takagi-Sugeno (ANFIS) fuzzy logikán** alapuló forgalomirányítási rendszer szimulációját valósítja meg a **SUMO (Simulation of Urban Mobility)** platform segítségével.

A cél:
- A jelzőlámpák zöld idejének dinamikus beállítása a forgalmi sűrűség alapján,
- A forgalmi torlódások mértékének csökkentése,
- A forgalom áramlásának optimalizálása a hagyományos, fix idejű vezérléssel szemben.

## 🛠️ Használt technológiák
- Python 3
- SUMO Traffic Simulator
- TraCI API (SUMO vezérléséhez)
- Fuzzy logikai modell (Takagi-Sugeno ANFIS)

## 🚀 Projekt indítása

### Telepítési lépések:
1. Telepítsd a szükséges Python csomagokat:
   ```bash
   pip install traci
   ```
2. Győződj meg róla, hogy a **SUMO** telepítve van, és a `sumo-gui` parancs elérhető.

### Futtatás:

Indítsd el a szimulációt az alábbi paranccsal:
```bash
python main.py
```
A szimuláció elindítja a **SUMO GUI-t**, és automatikusan kezeli a jelzőlámpák fázisidejét a fuzzy vezérlés alapján.

## 📈 Fő funkciók
- Forgalmi adatok begyűjtése szenzorokból (laneAreaDetectors)
- Forgalomsűrűség alapján adaptív zöldidő-számítás
- Jelzőlámpák valós idejű dinamikus vezérlése
- Grafikus elemzés: zöldidő változása és torlódási szintek vizualizálása

## 👩‍💻 Készítette
- Osváth Katalin
- Projekt keretében: **Traffic Automation via Fuzzy Logic (2025)**
- Access Documentation: https://docs.google.com/document/d/1lIEeY24DT67xbaSy4n_E8bk36o8pfLyyaalM22omWRo/edit?usp=sharing
