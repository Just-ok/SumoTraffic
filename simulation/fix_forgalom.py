import traci
import time
import numpy as np
import matplotlib.pyplot as plt

sumo_cfg_file = "osm.sumocfg"
junction_id = "cluster_249821091_249821092_249821094_26003449_#13more"
incoming_lanes = [
    "1015631885#1_0", "188302703#1_0", "188302703#1_1", "188302703#1_2",
    "-869087990_0", "-869087990_1", "1015631891#1_0"
]

def run_simulation():
    """SUMO szimuláció futtatása és forgalmi torlódások mérése."""
    print("SUMO szimuláció indítása...")

    try:
        traci.start(["sumo-gui", "-c", sumo_cfg_file])  # GUI nélkül: "sumo"
    except Exception as e:
        print(f"Hiba a szimuláció indításakor: {e}")
        return

    time_stamps = []
    green_times = []
    jam_lengths = []

    while traci.simulation.getMinExpectedNumber() > 0:
        traci.simulationStep()

        # Zöld idő lekérdezése
        green_time = traci.trafficlight.getPhaseDuration(junction_id)

        # Torlódás mérése
        jam_length = sum(traci.lane.getLastStepHaltingNumber(lane) for lane in incoming_lanes)

        # Adatok tárolása
        time_stamps.append(traci.simulation.getTime())
        green_times.append(green_time)
        jam_lengths.append(jam_length)

    traci.close()

    # Grafikonok megjelenítése
    plt.figure(figsize=(12, 6))

    plt.subplot(1, 2, 1)
    plt.plot(time_stamps, green_times, label="Zöld idő")
    plt.xlabel("Idő (másodperc)")
    plt.ylabel("Zöld idő (másodperc)")
    plt.title("Zöld idő változás")
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
