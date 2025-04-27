import traci
import time
import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl
import matplotlib.pyplot as plt

sumo_cfg_file = "osm.sumocfg"
junction_id = "cluster_249821091_249821092_249821094_26003449_#13more"
incoming_lanes = [
    "1015631885#1_0", "188302703#1_0", "188302703#1_1", "188302703#1_2",
    "-869087990_0", "-869087990_1", "1015631891#1_0"
]

def setup_fuzzy_system():
    """Fuzzy szabályok beállítása Takagi-Sugeno modellhez."""
    num_vehicles = ctrl.Antecedent(np.arange(0, 50, 1), 'num_vehicles')
    waiting_time = ctrl.Antecedent(np.arange(0, 100, 1), 'waiting_time')
    green_duration = ctrl.Consequent(np.arange(5, 60, 1), 'green_duration')

    num_vehicles.automf(3)  # Alacsony, Közepes, Magas
    waiting_time.automf(3)  # Rövid, Közepes, Hosszú

    # Finomhangolt tagsági függvények a zöld időhöz
    green_duration['poor'] = fuzz.trimf(green_duration.universe, [5, 5, 15])  # Rövidebb zöld idő
    green_duration['average'] = fuzz.trimf(green_duration.universe, [10, 25, 40]) # Szélesebb átfedés
    green_duration['good'] = fuzz.trimf(green_duration.universe, [30, 55, 55]) # Hosszabb zöld idő

    # Szabályok definiálása
    rule1 = ctrl.Rule(num_vehicles['poor'] & waiting_time['poor'], green_duration['poor'])
    rule2 = ctrl.Rule(num_vehicles['poor'] & waiting_time['average'], green_duration['average'])
    rule3 = ctrl.Rule(num_vehicles['good'] & waiting_time['good'], green_duration['good'])
    rule4 = ctrl.Rule(num_vehicles['good'] & waiting_time['good'], green_duration['good']) 

    traffic_ctrl = ctrl.ControlSystem([rule1, rule2, rule3, rule4])
    return ctrl.ControlSystemSimulation(traffic_ctrl)

def run_simulation():
    """SUMO szimuláció futtatása és fuzzy lámpavezérlés."""
    print("SUMO szimuláció indítása...")

    try:
        traci.start(["sumo-gui", "-c", sumo_cfg_file])  # GUI nélkül: "sumo"
    except Exception as e:
        print(f"Hiba a szimuláció indításakor: {e}")
        return

    fuzzy_system = setup_fuzzy_system()

    last_green_time = None  # Eltároljuk az utolsó zöld időt
    change_threshold = 3.0  # 3 másodperc küszöb, amikor a változást kiírjuk

    lane_green_times = {lane: None for lane in incoming_lanes}  # Minden sávhoz eltároljuk a zöld időt

    time_stamps = []  # Az időpontok
    green_times = []  # A zöld idő értékek
    jam_lengths = []  # Torlódás hossza

    while traci.simulation.getMinExpectedNumber() > 0:
        traci.simulationStep()

        total_vehicles = sum(traci.lane.getLastStepVehicleNumber(lane) for lane in incoming_lanes)
        avg_waiting_time = np.mean([traci.lane.getWaitingTime(lane) for lane in incoming_lanes])
        jam_length = sum(traci.lane.getLastStepHaltingNumber(lane) for lane in incoming_lanes) # Torlódás hossza

        fuzzy_system.input['num_vehicles'] = total_vehicles
        fuzzy_system.input['waiting_time'] = avg_waiting_time
        fuzzy_system.compute()

        try:
            green_time = fuzzy_system.output['green_duration']

            for lane in incoming_lanes:
                if lane_green_times[lane] is None or abs(lane_green_times[lane] - green_time) >= change_threshold:
                    print(f" Sáv: {lane} - Zöld idő változott: {green_time:.1f} mp (Autók: {total_vehicles}, Várakozás: {avg_waiting_time:.1f}s)")
                    traci.trafficlight.setPhaseDuration(junction_id, green_time)
                    lane_green_times[lane] = green_time

            time_stamps.append(traci.simulation.getTime())
            green_times.append(green_time)
            jam_lengths.append(jam_length) # Torlódás hossza

        except KeyError:
            print("Hiba a kimenet lekérésében, ellenőrizd a fuzzy rendszert!")
            continue

    traci.close()

    plt.figure(figsize=(12, 6))

    plt.subplot(1, 2, 1)
    plt.plot(time_stamps, green_times, label="Zöld idő")
    plt.xlabel("Idő (másodperc)")
    plt.ylabel("Zöld idő (másodperc)")
    plt.title("Zöld idő változás a szimuláció során")
    plt.legend()

    plt.subplot(1, 2, 2)
    plt.plot(time_stamps, jam_lengths, label="Torlódás hossza")
    plt.xlabel("Idő (másodperc)")
    plt.ylabel("Torlódás hossza (járművek száma)")
    plt.title("Forgalmi torlódás")
    plt.legend()

    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    run_simulation()
