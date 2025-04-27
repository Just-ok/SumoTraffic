
import traci
import time
import numpy as np
import pandas as pd

sumo_cfg_file = "osm.sumocfg"
junction_id = "cluster_249821091_249821092_249821094_26003449_#13more"
incoming_lanes = [
    "1015631885#1_0", "188302703#1_0", "188302703#1_1", "188302703#1_2",
    "-869087990_0", "-869087990_1", "1015631891#1_0"
]

data_records = []

def simple_green_time_model(num_vehicles, waiting_time, peak_vehicles):
    # Ez csak ideiglenes - az ANFIS ezt fogja majd megtanulni
    return min(60, max(5, 10 + 0.5 * num_vehicles + 0.2 * waiting_time + 0.1 * peak_vehicles))

def run_simulation():
    print("SUMO szimuláció indítása...")

    try:
        traci.start(["sumo-gui", "-c", sumo_cfg_file])
    except Exception as e:
        print(f"Hiba a szimuláció indításakor: {e}")
        return

    start_time = 1800
    end_time = 2160

    while traci.simulation.getMinExpectedNumber() > 0:
        current_time = traci.simulation.getTime()
        traci.simulationStep()

        if start_time <= current_time <= end_time:
            total_vehicles = sum(traci.lane.getLastStepVehicleNumber(lane) for lane in incoming_lanes)
            avg_waiting_time = np.mean([traci.lane.getWaitingTime(lane) for lane in incoming_lanes])
            peak_vehicles = max([traci.lane.getLastStepVehicleNumber(lane) for lane in incoming_lanes])

            green_time = simple_green_time_model(total_vehicles, avg_waiting_time, peak_vehicles)
            traci.trafficlight.setPhaseDuration(junction_id, green_time)

            data_records.append({
                "num_vehicles": total_vehicles,
                "waiting_time": avg_waiting_time,
                "peak_vehicles": peak_vehicles,
                "green_duration": green_time
            })

    traci.close()
    df = pd.DataFrame(data_records)
    df.to_csv("anfis_training_data.csv", index=False)
    print("Adatok mentve: anfis_training_data.csv")

if __name__ == "__main__":
    run_simulation()
