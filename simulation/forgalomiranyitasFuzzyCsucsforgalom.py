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
    peak_vehicles = ctrl.Antecedent(np.arange(0, 200, 1), 'peak_vehicles')
    green_duration = ctrl.Consequent(np.arange(5, 60, 1), 'green_duration')

    num_vehicles.automf(3)
    waiting_time.automf(3)
    peak_vehicles.automf(3)

    green_duration['poor'] = fuzz.trimf(green_duration.universe, [5, 5, 15])
    green_duration['average'] = fuzz.trimf(green_duration.universe, [10, 25, 40])
    green_duration['good'] = fuzz.trimf(green_duration.universe, [30, 55, 55])

    rule1 = ctrl.Rule(num_vehicles['poor'] & waiting_time['poor'], green_duration['poor'])
    rule2 = ctrl.Rule(num_vehicles['poor'] & waiting_time['average'], green_duration['average'])
    rule3 = ctrl.Rule(num_vehicles['good'] & waiting_time['good'] & peak_vehicles['good'], green_duration['good'])
    rule4 = ctrl.Rule(num_vehicles['good'] & waiting_time['good'], green_duration['average'])

    traffic_ctrl = ctrl.ControlSystem([rule1, rule2, rule3, rule4])
    return ctrl.ControlSystemSimulation(traffic_ctrl)

def run_simulation():
    """SUMO szimuláció futtatása és fuzzy lámpavezérlés."""
    print("SUMO szimuláció indítása...")

    try:
        traci.start(["sumo-gui", "-c", sumo_cfg_file])
    except Exception as e:
        print(f"Hiba a szimuláció indításakor: {e}")
        return

    fuzzy_system = setup_fuzzy_system()

    last_green_time = None
    change_threshold = 3.0

    lane_green_times = {lane: None for lane in incoming_lanes}

    time_stamps = []
    green_times = []
    jam_lengths = []
    peak_vehicle_counts = []

    peak_period = 300
    peak_vehicle_threshold = 100

    start_time = 1800  # 5 óra (másodpercben)
    end_time = 2160    # 6 óra (másodpercben)

    total_vehicle_count = 0  # Összes áthaladt jármű száma
    simulation_total_vehicles = 0 # Összes áthaladt jármű a teljes szimuláció alatt

    while traci.simulation.getMinExpectedNumber() > 0:
        current_time = traci.simulation.getTime()
        traci.simulationStep()

        for lane in incoming_lanes:
            simulation_total_vehicles += traci.lane.getLastStepVehicleNumber(lane)

        if start_time <= current_time <= end_time:  # Csúcsforgalmi időszak
            for lane in incoming_lanes:
                total_vehicle_count += traci.lane.getLastStepVehicleNumber(lane)

            total_vehicles = sum(traci.lane.getLastStepVehicleNumber(lane) for lane in incoming_lanes)
            avg_waiting_time = np.mean([traci.lane.getWaitingTime(lane) for lane in incoming_lanes])
            jam_length = sum(traci.lane.getLastStepHaltingNumber(lane) for lane in incoming_lanes)

            if current_time % peak_period == 0:
                peak_vehicle_count = sum(traci.lane.getLastStepVehicleNumber(lane) for lane in incoming_lanes)
                peak_vehicle_counts.append(peak_vehicle_count)
            else:
                peak_vehicle_count = peak_vehicle_counts[-1] if peak_vehicle_counts else 0

            fuzzy_system.input['num_vehicles'] = total_vehicles
            fuzzy_system.input['waiting_time'] = avg_waiting_time
            fuzzy_system.input['peak_vehicles'] = peak_vehicle_count
            fuzzy_system.compute()

            try:
                green_time = fuzzy_system.output['green_duration']

                for lane in incoming_lanes:
                    if lane_green_times[lane] is None or abs(lane_green_times[lane] - green_time) >= change_threshold:
                        print(f" Sáv: {lane} - Zöld idő változott: {green_time:.1f} mp (Autók: {total_vehicles}, Várakozás: {avg_waiting_time:.1f}s, Csúcs: {peak_vehicle_count})")
                        traci.trafficlight.setPhaseDuration(junction_id, green_time)
                        lane_green_times[lane] = green_time

                time_stamps.append(current_time)
                green_times.append(green_time)
                jam_lengths.append(jam_length)

            except KeyError:
                print("Hiba a kimenet lekérésében, ellenőrizd a fuzzy rendszert!")
                continue

    traci.close()

    print(f"Összes áthaladt jármű a csúcsforgalmi időszakban (5-6 óra): {total_vehicle_count}")
    print(f"Összes áthaladt jármű a teljes szimuláció alatt: {simulation_total_vehicles}")

    plt.figure(figsize=(12, 8))  # Növeljük a figura méretét a plusz szöveg miatt

    plt.subplot(2, 1, 1)
    plt.plot(time_stamps, green_times, label="Zöld idő")
    plt.xlabel("Idő (másodperc)")
    plt.ylabel("Zöld idő (másodperc)")
    plt.title("Zöld idő változás a szimuláció során")
    plt.legend()

    plt.subplot(2, 1, 2)
    plt.plot(time_stamps, jam_lengths, label="Torlódás hossza")
    plt.xlabel("Idő (másodperc)")
    plt.ylabel("Torlódás hossza (járművek száma)")
    plt.title("Forgalmi torlódás")
    plt.legend()

    plt.tight_layout()
    plt.figtext(0.5, 0.01, f"Összes áthaladt jármű a teljes szimuláció alatt: {simulation_total_vehicles}", ha="center", fontsize=10)
    plt.show()

if __name__ == "__main__":
    run_simulation()
