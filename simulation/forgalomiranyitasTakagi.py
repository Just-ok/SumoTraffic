import traci                 # TRACI interfész, amivel irányítjuk a SUMO szimulációt Pythonból
import numpy as np           # Numerikus számításokhoz
import skfuzzy as fuzz       # Fuzzy logikához szükséges könyvtár

# SUMO konfigurációs fájl és a forgalomirányító csomópont (kereszteződés) azonosítója
sumo_cfg_file = "osm.sumocfg"
junction_id = "cluster_249821091_249821092_249821094_26003449_#13more"

# A kereszteződéshez tartozó bejövő sávok listája (ezeken figyeljük a forgalmat)
incoming_lanes = [
    "1015631885#1_0", "188302703#1_0", "188302703#1_1", "188302703#1_2",
    "-869087990_0", "-869087990_1", "1015631891#1_0"
]

# A "Fortuna" nevű kritikus sáv(ok), amelyek teljesítményét külön vizsgáljuk
fortuna_lanes = ["188302703#1_0", "188302703#1_1", "188302703#1_2"]

# Egy segédfüggvény, ami egy adott értékre (x) visszaadja a tagsági értéket egy fuzzy halmazban (mf)
def fuzzify(x, mf):
    return fuzz.interp_membership(mf[0], mf[1], x)

# Fuzzy tagsági függvények és Sugeno szabályrendszer létrehozása
def setup_membership_functions():
    vehicle_universe = np.arange(0, 51, 1)  # Járműszám tartomány: 0–50
    wait_universe = np.arange(0, 101, 1)    # Várakozási idő tartomány: 0–100 mp

    # Járműszám fuzzy halmazok
    vehicle_mfs = {
        'low': (vehicle_universe, fuzz.trimf(vehicle_universe, [0, 0, 20])),
        'medium': (vehicle_universe, fuzz.trimf(vehicle_universe, [10, 25, 40])),
        'high': (vehicle_universe, fuzz.trimf(vehicle_universe, [30, 50, 50]))
    }

    # Várakozási idő fuzzy halmazok
    wait_mfs = {
        'short': (wait_universe, fuzz.trimf(wait_universe, [0, 0, 30])),
        'medium': (wait_universe, fuzz.trimf(wait_universe, [20, 50, 80])),
        'long': (wait_universe, fuzz.trimf(wait_universe, [60, 100, 100]))
    }

    # Sugeno típusú szabályrendszer (output: zöld idő mp-ben)
    rules = [
        (('low', 'short'), 10),
        (('low', 'medium'), 20),
        (('low', 'long'), 30),
        (('medium', 'short'), 25),
        (('medium', 'medium'), 35),
        (('medium', 'long'), 45),
        (('high', 'short'), 35),
        (('high', 'medium'), 45),
        (('high', 'long'), 55)
    ]

    return vehicle_mfs, wait_mfs, rules

# Sugeno fuzzy következtető rendszer kiértékelése (kimenet: zöld idő mp-ben)
def compute_takagi_sugeno(vehicles, waiting_time, vehicle_mfs, wait_mfs, rules):
    weights = []
    values = []

    # Minden szabályra: tagsági érték számítása és hozzájárulás kiszámítása
    for (veh_level, wait_level), output in rules:
        mu_veh = fuzzify(vehicles, vehicle_mfs[veh_level])
        mu_wait = fuzzify(waiting_time, wait_mfs[wait_level])
        strength = min(mu_veh, mu_wait)  # Sugeno: minimum operátor

        weights.append(strength)
        values.append(output)

    if sum(weights) == 0:
        return 10  # Ha nincs aktív szabály, akkor alapértelmezett zöld idő

    return np.dot(weights, values) / sum(weights)  # Súlyozott átlag alapján végső döntés

# Szimuláció futtatása TRACI segítségével
def run_simulation():
    try:
        traci.start(["sumo-gui", "-c", sumo_cfg_file])  # SUMO-GUI elindítása
    except Exception as e:
        print(f"Hiba a szimuláció indításakor: {e}")
        return

    # Tagsági függvények és szabályrendszer beállítása
    vehicle_mfs, wait_mfs, rules = setup_membership_functions()

    # Minden sávhoz zöld idő naplózása (az előző értékhez képest nézzük a változást)
    lane_green_times = {lane: None for lane in incoming_lanes}
    change_threshold = 3.0  # Ha legalább ennyit változik a zöld idő, akkor frissítjük

    # Fortuna sáv járműszámának előző állapotai
    fortuna_prev2 = 0
    fortuna_prev = 0

    # Új fájl megnyitása írásra: eredmények mentése
    with open("data.txt", "w") as f:
        f.write("step; fortuna\n")  # Fejléc

    step = 0  # Szimulációs lépés számláló

    # Ameddig van elvárt jármű a szimulációban
    while traci.simulation.getMinExpectedNumber() > 0:
        traci.simulationStep()  # Lépünk egyet a szimulációban

        # Minden sávból összes jármű és átlagos várakozási idő
        total_vehicles = sum(traci.lane.getLastStepVehicleNumber(lane) for lane in incoming_lanes)
        avg_waiting_time = np.mean([traci.lane.getWaitingTime(lane) for lane in incoming_lanes])

        # Sugeno logika alapján új zöld idő meghatározása
        green_time = compute_takagi_sugeno(total_vehicles, avg_waiting_time, vehicle_mfs, wait_mfs, rules)

        # Minden sávra alkalmazzuk, ha jelentősen megváltozott az érték
        for lane in incoming_lanes:
            if lane_green_times[lane] is None or abs(lane_green_times[lane] - green_time) >= change_threshold:
                print(f"Sáv: {lane} – Zöld idő (Sugeno): {green_time:.1f} mp")
                traci.trafficlight.setPhaseDuration(junction_id, green_time)
                lane_green_times[lane] = green_time

        # Minden 150. szimulációs lépésnél naplózzuk a Fortuna sáv változását
        if step % 150 == 0:
            fortuna_current = sum(traci.lane.getLastStepVehicleNumber(lane) for lane in fortuna_lanes)
            fortuna_delta = fortuna_current - fortuna_prev2  # változás a két ciklussal korábbihoz képest

            with open("data.txt", "a") as f:
                f.write(f"{step}; {fortuna_delta}\n")  # Idő és változás rögzítése

            fortuna_prev2 = fortuna_prev  # Állapotfrissítés a következő ciklushoz
            fortuna_prev = fortuna_current

        step += 1  # Lépésszámláló növelése

    traci.close()  # Szimuláció lezárása

# Ha közvetlenül futtatjuk a fájlt, akkor indítja a szimulációt
if __name__ == "__main__":
    run_simulation()
