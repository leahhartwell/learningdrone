import logging
import time

import cflib.crtp
from cflib.crazyflie import Crazyflie
from cflib.crazyflie.syncCrazyflie import SyncCrazyflie

from cflib.crazyflie.log import LogConfig
from cflib.crazyflie.syncLogger import SyncLogger

# URI to the Crazyflie to connect to
uri = "radio://0/80/2M/E7E7E7E7E7"

# Only output errors from the logging framework
logging.basicConfig(level=logging.ERROR)


def param_stab_est_callback(name, value):
    print("The crazyflie has parameter " + name + " set at number: " + value)


def simple_param_async(scf, groupstr, namestr):
    cf = scf.cf
    full_name = groupstr + "." + namestr

    cf.param.add_update_callback(
        group=groupstr, name=namestr, cb=param_stab_est_callback
    )
    time.sleep(1)
    cf.param.set_value(full_name, 2)
    time.sleep(1)
    cf.param.set_value(full_name, 1)
    time.sleep(1)


def simple_log(scf, logconf):

    with SyncLogger(scf, logconf) as logger:

        for log_entry in logger:

            timestamp = log_entry[0]
            data = log_entry[1]
            logconf_name = log_entry[2]

            print("[%d][%s]: %s" % (timestamp, logconf_name, data))

            break


if __name__ == "__main__":
    # Initialize the low-level drivers
    cflib.crtp.init_drivers()

    lg_state_est = LogConfig(name="StateEstimateZ", period_in_ms=10)
    lg_state_est.add_variable("stateEstimateZ.x", "float")
    lg_state_est.add_variable("stateEstimateZ.y", "float")
    lg_state_est.add_variable("stateEstimateZ.z", "float")
    lg_state_est.add_variable("stateEstimateZ.vx", "float")
    lg_state_est.add_variable("stateEstimateZ.vy", "float")
    lg_state_est.add_variable("stateEstimateZ.vz", "float")
    lg_state_est.add_variable("stateEstimateZ.ax", "float")
    lg_state_est.add_variable("stateEstimateZ.ay", "float")
    lg_state_est.add_variable("stateEstimateZ.az", "float")

    group = "stateEstimateZ"
    names = ["x", "y", "z", "vx", "vy", "vz", "ax", "ay", "az"]

    with SyncCrazyflie(uri, cf=Crazyflie(rw_cache="./cache")) as scf:

        # simple_log_sync(scf, lg_state_est)

        for name in names:
            simple_param_async(scf, group, name)
