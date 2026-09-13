####################################################
#
#   ASUF1tenth Competition Submission Container
#
#   Built FROM the official AutoDRIVE Devkit image
#   per competition rules §3.1 — we only add our own
#   ROS 2 packages on top, we never modify anything
#   that already exists inside the base image.
#
####################################################

FROM autodriveecosystem/autodrive_roboracer_api:2026-iros-practice

# Overlay workspace for the ASUF1tenth race stack, mirroring the team's
# own dev convention (.docker_utils/main_dock.sh mounts this repo at
# ~/ws/src/race_stack) but baked into the image instead of a dev volume.
ENV WS=/home/autodrive_devkit_ws
COPY . ${WS}/src/race_stack/

# linux_req.txt hardcodes ros-jazzy-* package names for the team's own
# Jazzy dev container (e.g. robot_localization, tf_transformations - used
# directly by nodes but not declared in any package.xml, so rosdep won't
# catch them). This base image is Humble, so substitute the distro name
# at build time instead of duplicating/rewriting the checked-in file.
RUN /bin/bash -c "sed \"s/ros-jazzy-/ros-\$ROS_DISTRO-/g\" ${WS}/src/race_stack/.install_utils/linux_req/linux_req.txt > /tmp/linux_req_resolved.txt && \
    apt-get update && xargs apt-get install -y --no-install-recommends < /tmp/linux_req_resolved.txt && \
    rm -rf /var/lib/apt/lists/* /tmp/linux_req_resolved.txt"

RUN /bin/bash -c "source /opt/ros/\$ROS_DISTRO/setup.bash && \
    source /home/autodrive_devkit/install/setup.bash && \
    rosdep update && \
    rosdep install --from-paths ${WS}/src --ignore-src -r -y && \
    bash ${WS}/src/race_stack/.install_utils/gb_opt_setup.sh && \
    cd ${WS} && colcon build --symlink-install --packages-ignore f110_gym"

COPY submission/autodrive_devkit.sh /home/autodrive_devkit.sh
RUN chmod +x /home/autodrive_devkit.sh

WORKDIR /home/autodrive_devkit

# All launch logic lives in the entrypoint script below, never ~/.bashrc,
# so that `docker exec -it <container> bash` (used by organizers to record
# rosbags / inspect rqtgraph per §2.3) opens a plain shell without
# re-triggering the stack.
ENTRYPOINT ["/home/autodrive_devkit.sh"]
