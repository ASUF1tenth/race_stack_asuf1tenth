#! /bin/bash

# Script to launch the main docker instance for the pblf110 car

docker exec --tty \
    --interactive \
    asuf1tenth_racestack_ros2_jazzy \
    /bin/bash
