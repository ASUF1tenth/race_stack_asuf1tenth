# Submission image for IROS 2026 AutoDRIVE RoboRacer Sim Racing League.
#
# Built FROM the official, digest-pinned devkit image (Competition_Rules.md §3.1: "must
# be based off of the official AutoDRIVE Devkit container ... any modifications to the
# existing container elements are strictly off limits"). This Dockerfile only adds our
# ROS 2 packages alongside the provided autodrive_roboracer package and replaces the
# CONTENT of the entrypoint script (autodrive_devkit.sh) as instructed by §3 — it never
# touches ~/.bashrc and never changes the base image, containerization approach, or any
# file that ships with it.
#
# Build (from the repo root, i.e. one level up from this file):
#   docker build -f submission/Dockerfile -t <dockerhub-user>/<image-name>:<tag> .

FROM autodriveecosystem/autodrive_roboracer_api@sha256:6e4c29536b7283a1a7322473d46dab2d4ad5513cf40d1bdfc908ee9d408e26e9

SHELL ["/bin/bash", "-c"]

# Extra apt/pip deps race_stack needs beyond what ships in the devkit image (e.g.
# robot_localization, cartographer-ros) — not declared in any package.xml, so rosdep
# alone won't catch them. Same gap already found porting to Humble in Phase A/B.
COPY .install_utils/linux_req/linux_req.txt /tmp/linux_req.txt
RUN apt-get update \
    && xargs apt-get install -y --no-install-recommends < /tmp/linux_req.txt \
    && rm -rf /var/lib/apt/lists/*

COPY .install_utils/python_req.txt /tmp/python_req.txt
RUN pip3 install -r /tmp/python_req.txt \
    && pip3 install quadprog~=0.1.11

# Our race_stack source, in its own workspace alongside (never inside) the existing
# /home/autodrive_devkit workspace that ships with the base image.
COPY . /home/race_stack/src/race_stack

RUN source /opt/ros/humble/setup.bash \
    && source /home/autodrive_devkit/install/setup.bash \
    && cd /home/race_stack \
    && rosdep update \
    && (rosdep install --from-paths src --ignore-src -y || true) \
    && colcon build --base-paths /home/race_stack --packages-skip f110_gym --continue-on-error

# Replace only the entrypoint SCRIPT's content, as instructed by the rules.
COPY submission/autodrive_devkit.sh /home/autodrive_devkit.sh
RUN chmod +x /home/autodrive_devkit.sh

WORKDIR /home/autodrive_devkit
ENTRYPOINT ["/home/autodrive_devkit.sh"]
