#!/bin/bash
set -e

# Setup Environment
source /opt/ros/$ROS_DISTRO/setup.bash
source /home/autodrive_devkit/install/setup.bash
source /home/autodrive_devkit_ws/install/setup.bash

# Keep rosbag/rosgraph output under /home/autodrive_devkit so the
# `docker cp autodrive_roboracer_api:/home/autodrive_devkit/*.bag` steps
# from the competition workflow keep working unmodified.
cd /home/autodrive_devkit

MAP_NAME="${MAP_NAME:-iros_2026}"
RACECAR_VERSION="${RACECAR_VERSION:-NUC2}"
CTRL_ALGO="${CTRL_ALGO:-PP}"

# Launch base system (AutoDRIVE bridge, state estimation, global planner,
# sector tuner, lap analyser)
ros2 launch stack_master base_system_launch.xml \
  racecar_version:="${RACECAR_VERSION}" sim:=true map_name:="${MAP_NAME}" &
BASE_PID=$!

# Launch time trials mode (controller + state machine) on top of it
ros2 launch stack_master time_trials_launch.xml \
  ctrl_algo:="${CTRL_ALGO}" &
RACE_PID=$!

# Block here (as PID 1) so the container stays up for as long as the
# stack runs. A new `docker exec -it <container> bash` session is
# independent of this process tree and will not re-run this script.
wait -n "$BASE_PID" "$RACE_PID"
