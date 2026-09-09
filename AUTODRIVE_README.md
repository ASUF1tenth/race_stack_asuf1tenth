# AutoDRIVE RoboRacer — IROS 2026 Sim Racing League (team status)

This branch (`merge/ethAutoDrive-Hamsa-humble`) ports the ForzaETH race_stack to
ROS 2 Humble and integrates it with the official AutoDRIVE RoboRacer devkit, for the
IROS 2026 Sim Racing League (Qualification Round + Time-Attack Race). Competition rules
are in `docs/Competition_Rules.md` — read it before changing anything related to the
submission container, restricted topics, or timing/collision logic.

## Setup

**Prerequisites:**

- Ubuntu (this integration has only been tested there)
- Docker Engine — not Docker Desktop (Desktop's VM layer sometimes hides GPU access; if
  `docker context ls` shows `desktop-linux`, run `docker context use default`)
- X11 display for the simulator GUI (`echo $DISPLAY` should print something, e.g. `:0`)
- NVIDIA GPU + NVIDIA Container Toolkit (optional, only needed for `--gpus all`)

**Clone the repo and submodules:**

```bash
git clone --recurse-submodules https://github.com/ASUF1tenth/race_stack_asuf1tenth.git
cd race_stack_asuf1tenth
git checkout merge/ethAutoDrive-Hamsa-humble
git submodule update --init --recursive
```

**Dev environment, for continued development (e.g. the mapping work below)** — this is
separate from the final submission container in `submission/`, and is what you actually
want for iterating/driving/debugging:

```bash
docker build -f .devcontainer/Dockerfile -t race_stack:humble_x86 \
  --build-arg PLATFORM=x86 --build-arg USER=$(whoami) \
  --build-arg UID=$(id -u) --build-arg GID=$(id -g) .
```

Easiest path: open this repo in VS Code with the **Dev Containers** extension — it builds
this image, bind-mounts the repo, and runs `.install_utils/post_create_command.sh`
automatically (rosdep installs, F1TENTH Gym sim setup, first colcon build). Without VS
Code, do the equivalent by hand:

```bash
docker run -it --rm --network=host --ipc=host \
  -v $(pwd):/home/$(whoami)/ws/src/race_stack \
  -v /tmp/.X11-unix:/tmp/.X11-unix:rw --env DISPLAY --gpus all \
  race_stack:humble_x86
# then inside the container:
bash ~/ws/src/race_stack/.install_utils/post_create_command.sh
```

**Pull the official competition images**, pinned to the exact digest (not a moving tag,
per the rules):

```bash
docker pull autodriveecosystem/autodrive_roboracer_api@sha256:6e4c29536b7283a1a7322473d46dab2d4ad5513cf40d1bdfc908ee9d408e26e9
docker pull autodriveecosystem/autodrive_roboracer_sim@sha256:b4bbda41fdb1da7a2eadba4350ed3a0cb5020e7eb783454e78399ef5852dbd76
docker tag $(docker images --no-trunc --format '{{.ID}}' autodriveecosystem/autodrive_roboracer_api | head -1) autodriveecosystem/autodrive_roboracer_api:2026-iros-practice
docker tag $(docker images --no-trunc --format '{{.ID}}' autodriveecosystem/autodrive_roboracer_sim | head -1) autodriveecosystem/autodrive_roboracer_sim:2026-iros-practice
```

## Running the submission container

**Build the submission image** (from the repo root):

```bash
docker build -f submission/Dockerfile -t <dockerhub-user>/<image-name>:<tag> .
```

**Run it against the real competition images**, simulator first (required launch order
per the rules):

```bash
xhost local:root

# 1. Simulator
docker run -d --name autodrive_roboracer_sim --network=host --ipc=host \
  -v /tmp/.X11-unix:/tmp/.X11-unix:rw --env DISPLAY --privileged --gpus all \
  --entrypoint /bin/bash autodriveecosystem/autodrive_roboracer_sim:2026-iros-practice \
  -c 'cd /home/autodrive_simulator && ./AutoDRIVE\ Simulator.x86_64'

# 2. Our team container (auto-launches everything via submission/autodrive_devkit.sh)
docker run -d --name autodrive_roboracer_api --network=host --ipc=host \
  <dockerhub-user>/<image-name>:<tag>
```

Then hit **Connect** on the simulator's Menu Panel. A fresh `docker exec -it
autodrive_roboracer_api bash` session is safe at any time (for `ros2 bag record`,
`rqtgraph`, etc.) — it will not re-launch our stack, per the competition rules'
requirement.

## Repo map (what matters for this integration)

- `submission/Dockerfile`, `submission/autodrive_devkit.sh` — the actual submission
  container build and entrypoint. This is what gets pushed to Docker Hub.
- `utilities/nodes/autodrive_bridge_adapter/` — translates AutoDRIVE's bridge topics to
  ForzaETH's topic conventions (drive commands, IMU/LiDAR renaming, encoder+steering
  wheel odometry). Only touches runtime-permitted AutoDRIVE topics.
- `stack_master/launch/autodrive_launch.xml`, `base_system_launch.xml`,
  `mapping_launch.xml` — the `autodrive:=True` launch wiring.
- `stack_master/config/NUC2/slam/` — Cartographer tuning for the AutoDRIVE integration
  (see "Mapping" below for what's already been tuned here).
- `stack_master/maps/iros2026_practice/` — the practice-track map folder (in progress).
  `stack_master/maps/glc_ot_ez/` is a complete, finished map from other work — useful as
  a reference for what a finished map folder should contain.
- `planner/global_planner/` — generates the raceline from a finished map
  (`create_map:=False`) or runs mapping mode (`create_map:=True`).

**Note on this fork:** this repo's default branch (`ros2-jazzy`) has its own, separate
AutoDRIVE integration (`base_system/simulators/autodrive/f110_autodrive/`), built
independently on a restructured layout. That is different work on a different branch —
unrelated to this README and this branch's `autodrive_bridge_adapter` package. Worth
reconciling with that effort at some point, but out of scope here since the competition
requires ROS 2 Humble and that work is on Jazzy.

## Status checklist (chronological, since the project's first commit)

- [x] ForzaETH race_stack forked and set up on ROS 2 Jazzy (devcontainer, sim, base
      hardware stack)
- [x] RL/Optuna parameter-tuning pipeline built and validated against the gym simulator
      (head-to-head PP evaluation, Optuna/CMA-ES search, PPO training runs)
- [x] AutoDRIVE devkit integrated into the devcontainer; submodule repointed to our fork
- [x] AutoDRIVE bridge adapter node + `autodrive` launch-file wiring written (Jazzy)
- [x] Entire AutoDRIVE integration ported onto ROS 2 Humble (the competition's required
      base image), including a from-scratch port of `global_planner` for headless
      mapping support (Humble's own version was real-hardware/interactive-only)
- [x] Humble build verified: colcon-builds clean, both mapping and base-system launch
      files bring up their full node graphs with zero crashes in a headless dry run
- [x] Live connection dry run against the real competition images: Connect, full topic
      graph populated, round-trip drive command confirmed (car moved), and reconnect
      after a simulator-side restart confirmed working
- [x] Obtained and reviewed the official `Competition_Rules.md`; confirmed launch order,
      collision tolerance (≤10), container/entrypoint requirements, and restricted-topic
      constraints against what was already built
- [x] Built the actual submission container: Dockerfile FROM the exact digest-pinned
      base image, our packages added alongside the existing devkit (never modifying it),
      custom entrypoint that never touches `~/.bashrc` and launches everything
      automatically
- [x] Verified the submission container's complete node graph (bridge, adapter, EKF,
      Cartographer, map server, waypoint publisher, sector tuner, lap analyser,
      controller, state machine) comes up and stays up with zero crashes end-to-end on a
      complete map
- [x] Verified the submission container live against the real AutoDRIVE simulator: real
      sensor data flowing (LiDAR/IMU/odometry), connection stable, no defects found
      outside of what's still pending on the map (see below)
- [x] Migrated all of the above onto this new, clean fork (branch history cherry-picked
      cleanly off a shared `ros2-humble` base; uncommitted work and gitignored map data
      carried over manually)
- [ ] **Mapping the official practice track** — in progress. Several real bugs already
      found and fixed along the way (see "Mapping" below); this is the current focus.
- [ ] Run and pass the official 10-lap qualification attempt once the map/raceline for
      the practice track is finished
- [ ] Push the final submission image to Docker Hub with a repo overview — mechanically
      ready to go, just needs the finished map swapped in first

## Mapping — where things stand and how to continue

The map folder for the practice track is `stack_master/maps/iros2026_practice/`. Compare
against `stack_master/maps/glc_ot_ez/` for what a *finished* map folder should contain:
`<name>.pbstream`, `<name>.yaml`/`.png`, `global_waypoints.json`, `speed_scaling.yaml`,
`ot_sectors.yaml`.

To run mapping mode against the live AutoDRIVE simulator:
```bash
ros2 launch stack_master mapping_launch.xml autodrive:=True racecar_version:=NUC2 \
  map_name:=iros2026_practice
```
Drive with FTG (`ctrl_algo:=FTG` in the controller launch) to build up the map, then
finalize **once, at the very end**: call `/finish_trajectory` then `/write_state` (see
gotcha below — do not call `/finish_trajectory` more than once). Generate the raceline
from the finished map with:
```bash
ros2 launch global_planner ... create_map:=False
```

**Known gotchas already solved — worth knowing before re-discovering them:**
- `use_odometry=false` in `stack_master/config/NUC2/slam/f110_2d.lua` — the dead-reckoned
  odometry (encoder+steering, not IPS — IPS/ground-truth topics are off-limits per
  `docs/Competition_Rules.md` §2.4) was corrupting Cartographer's scan matcher when fed
  in.
- `POSE_GRAPH.constraint_builder.max_constraint_distance` widened 15→30 and
  `global_sampling_ratio` 0.003→0.01 in the same config — the default constraint search
  radius was narrower than the gaps between map segments; widen it if segments aren't
  linking up (verify via `/constraint_list`, don't just guess).
- `global_planner` has a headless GUI-button dependency and a missing `finish_map.sh`
  that need working around in a headless/containerized setup.
- Calling `/finish_trajectory` more than once permanently freezes `/tracked_pose` — call
  it exactly once, after mapping is complete.
- Two shortcuts were investigated and parked, not because they don't work mechanically,
  but because of rules constraints: ground-truth-assisted mapping
  (`docs/Competition_Rules.md` §2.4 states simulation ground truth is "not allowed,"
  pending confirmation from the Technical Guide document referenced there but not yet
  obtained), and reusing a public legacy Porto map (wrong geometry for the actual
  competition track, and this stack's Cartographer-native localization needs a real
  `.pbstream` from an actual SLAM run anyway — a foreign occupancy grid can't produce
  one).

Once the map folder is complete, no other change is needed to ship — `map_name` in
`submission/autodrive_devkit.sh` is already set to `iros2026_practice`. Just rebuild the
submission image and re-run the Quickstart above to confirm before pushing.

## Uncommitted work — commit this before/when handing off

These exist in the working tree but aren't committed yet:
- `submission/Dockerfile`, `submission/autodrive_devkit.sh`, `.dockerignore` (untracked —
  the entire submission container setup)
- `stack_master/config/NUC2/slam/f110_2d.lua` (modified — the Cartographer tuning above)
- `stack_master/maps/iros2026_practice/` is **not tracked by git at all** — this repo's
  `.gitignore` excludes `stack_master/maps/*` by default (only two other maps are
  explicitly allow-listed). Once this map is finished, either add an allow-list entry for
  it in `.gitignore` (same pattern as the existing ones) or it will never get committed.
- `docs/Competition_Rules.md` — copied in from the old workspace so it travels with the
  branch; untracked until committed.
