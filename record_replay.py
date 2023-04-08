import time
import logging
import keyboard
import math
import csv
import datetime
import cflib.crtp
from cflib.crazyflie import Crazyflie
from cflib.crazyflie.log import LogConfig
from cflib.crazyflie.syncCrazyflie import SyncCrazyflie
from cflib.positioning.motion_commander import MotionCommander

# URI to the Crazyflie to connect to
uri = "radio://0/79/2M/E7E7E7E7E6"

# Only output errors from the logging framework
logging.basicConfig(level=logging.ERROR)

POSITION_LOG_INTERVAL_MS = 10
record_kinematics_log = []
replay_kinematics_log = []

# Define the log configuration for recording kinematic data
def log_kin_config():
    log_config = LogConfig(name="KinematicsLog", period_in_ms=POSITION_LOG_INTERVAL_MS)
    log_config.add_variable("stateEstimate.x", "float")
    log_config.add_variable("stateEstimate.y", "float")
    log_config.add_variable("stateEstimate.z", "float")
    # log_config.add_variable("stateEstimate.vx", "float")
    # log_config.add_variable("stateEstimate.vy", "float")
    # log_config.add_variable("stateEstimate.vz", "float")
    # log_config.add_variable("stateEstimate.ax", "float")
    # log_config.add_variable("stateEstimate.ay", "float")
    # log_config.add_variable("stateEstimate.az", "float")
    return log_config


# Callback function for recording kinematic data
def log_record_kin_callback(timestamp, data, logconf):
    x, y, z = (
        data["stateEstimate.x"],
        data["stateEstimate.y"],
        data["stateEstimate.z"],
    )
    # vx, vy, vz = (
    #     data["stateEstimate.vx"],
    #     data["stateEstimate.vy"],
    #     data["stateEstimate.vz"],
    # )
    # ax, ay, az = (
    #     data["stateEstimate.ax"],
    #     data["stateEstimate.ay"],
    #     data["stateEstimate.az"],
    # )
    # record_kinematics_log.append((timestamp, x, y, z, vx, vy, vz, ax, ay, az))
    record_kinematics_log.append((timestamp, x, y, z))
    # print(
    #     f"Time: {timestamp}, Position: ({x}, {y}, {z}), Velocity: ({vx}, {vy}, {vz}), Acceleration: ({ax}, {ay}, {az})"
    # )
    # print(f"Time: {timestamp}, Position: ({x}, {y}, {z})")


# Callback function for replaying kinematic data
def log_replay_kin_callback(timestamp, data, logconf):
    x, y, z = (
        data["stateEstimate.x"],
        data["stateEstimate.y"],
        data["stateEstimate.z"],
    )
    # vx, vy, vz = (
    #     data["stateEstimate.vx"],
    #     data["stateEstimate.vy"],
    #     data["stateEstimate.vz"],
    # )
    # ax, ay, az = (
    #     data["stateEstimate.ax"],
    #     data["stateEstimate.ay"],
    #     data["stateEstimate.az"],
    # )
    # record_kinematics_log.append((timestamp, x, y, z, vx, vy, vz, ax, ay, az))
    replay_kinematics_log.append((timestamp, x, y, z))
    # print(
    #     f"Time: {timestamp}, Position: ({x}, {y}, {z}), Velocity: ({vx}, {vy}, {vz}), Acceleration: ({ax}, {ay}, {az})"
    # )
    # print(f"Time: {timestamp}, Position: ({x}, {y}, {z})")


# Function to handle logging of kinematic data asynchronously
def log_kin_async(logconf, scf, mode, stop_logging=False):
    cf = scf.cf
    cf.log.add_config(logconf)

    if mode == "record":
        logconf.data_received_cb.add_callback(log_record_kin_callback)
        print('Press "s" to start logging position data.')
        keyboard.wait("s")
        # keyboard.read_event()
        logconf.start()

        print('Logging position data. Press "s" again to stop logging.')
        keyboard.wait("s")
        # keyboard.read_event()
        logconf.stop()
    elif mode == "replay":
        logconf.data_received_cb.add_callback(log_replay_kin_callback)
        logconf.start()

    if stop_logging:
        logconf.stop()


def save_logs_to_csv(record_arr, replay_arr):
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"kinematics_log_{timestamp}.csv"

    with open(filename, "w", newline="") as csvfile:
        csv_writer = csv.writer(csvfile)
        csv_writer.writerow(
            ["timestamp", "x", "y", "z", "vx", "vy", "vz", "ax", "ay", "az"]
        )

        csv_writer.writerow(["Record"])
        for row in record_arr:
            csv_writer.writerow(row)

        csv_writer.writerow([])

        csv_writer.writerow(["Record"])
        for row in replay_arr:
            csv_writer.writerow(row)


if __name__ == "__main__":
    cflib.crtp.init_drivers()

    # Connect to Crazyflie and set up a SyncCrazyflie object
    with SyncCrazyflie(uri, cf=Crazyflie(rw_cache="./cache")) as scf:

        # Create a log configuration for recording and start recording
        log_record_config = log_kin_config()
        log_kin_async(log_record_config, scf, "record")

        # Create a log configuration for replaying and start replaying
        log_replay_config = log_kin_config()
        log_kin_async(log_replay_config, scf, "replay")

        print('Press "s" to start replay.')
        keyboard.wait("s")
        # keyboard.read_event()

        # Use the MotionCommander to move the Crazyflie based on the recorded kinematic data
        with MotionCommander(scf) as mc:
            # Iterate through the kinematics_log and calculate distances and velocities
            for i in range(1, len(record_kinematics_log)):
                t1, x1, y1, z1 = record_kinematics_log[i - 1][:4]
                t2, x2, y2, z2 = record_kinematics_log[i][:4]
                dt = (t2 - t1) / 1000.0
                dx = x2 - x1
                dy = y2 - y1
                dz = z2 - z1
                try:
                    v = math.sqrt(dx**2 + dy**2 + dz**2) / dt
                except ZeroDivisionError:
                    v = 0

                if v != 0:
                    # Move Crazyflie using the calculated distances and velocities
                    mc.move_distance(dx, dy, dz, v)
                else:
                    print("Skipped moving due to zero velocity...")

                # Sleep for the duration of the move or a short period if velocity is zero
                if v != 0:
                    time.sleep(dt)
                else:
                    time.sleep(0.01)  # Sleep for a short period if velocity is zero

        # Stop logging and disconnect from the Crazyflie
        log_kin_async(log_replay_config, scf, "replay", stop_logging=True)

    save_logs_to_csv(record_kinematics_log, replay_kinematics_log)
