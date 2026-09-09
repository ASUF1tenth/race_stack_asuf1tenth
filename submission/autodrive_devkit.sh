#!/bin/bash
set -e

# Setup Development Environment
source /opt/ros/humble/setup.bash
source /home/autodrive_devkit/install/setup.bash
source /home/race_stack/install/setup.bash

export RACECAR_VERSION=NUC2

cd /home/autodrive_devkit

# AutoDRIVE devkit bridge + our translation/state-estimation stack.
# map_name is a placeholder until Phase C produces a finished closed-loop map for the
# actual practice track — swap this arg (and nothing else) before final submission.
ros2 launch stack_master base_system_launch.xml \
    racecar_version:=$RACECAR_VERSION \
    map_name:=iros2026_practice \
    autodrive:=True \
    autodrive_mapping:=False &

# Give the base system a moment to come up before the controller/state machine attach.
sleep 5

# Controller + state machine, driving with Pure Pursuit against the loaded map.
ros2 launch stack_master time_trials_launch.xml \
    racecar_version:=$RACECAR_VERSION \
    ctrl_algo:=PP &

# Keep the container alive without exiting, so organizer `docker exec` sessions for bag
# recording / rqtgraph stay usable without re-triggering this script.
wait
