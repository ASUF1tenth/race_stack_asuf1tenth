# Competition Submission Container (Phase D)

This builds the image submitted to the competition organizers. It is built
`FROM autodriveecosystem/autodrive_roboracer_api:<tag>` (the official
AutoDRIVE Devkit container, per rules §3.1) with only the ASUF1tenth race
stack packages added on top — nothing inside the base image is modified.

All launch logic lives in [`autodrive_devkit.sh`](./autodrive_devkit.sh),
which is the container's `ENTRYPOINT`. It auto-launches the full stack the
instant `docker run` starts the container. It intentionally does **not**
live in `~/.bashrc`, since that would re-run on every new interactive
shell and re-trigger the stack whenever an organizer opens a second bash
session for rosbag recording or `rqtgraph` inspection (§2.3).

## Build

```bash
docker build --tag <TEAM_USERNAME>/<IMAGE_NAME>:<TAG> -f submission/Dockerfile .
```

Run this from the repo root (build context = whole repo, since the
Dockerfile does `COPY . ${WS}/src/race_stack/`).

## Run

```bash
xhost local:root
docker run --name asuf1tenth_api --rm -it \
  --network=host --ipc=host \
  -v /tmp/.X11-unix:/tmp/.X11-unix:rw --env DISPLAY \
  --privileged --gpus all \
  <TEAM_USERNAME>/<IMAGE_NAME>:<TAG>
```

No `--entrypoint /bin/bash` override is needed or should be used — the
stack launches automatically. Override the default map/car/controller at
run time if needed:

```bash
docker run ... -e MAP_NAME=iros_2026 -e RACECAR_VERSION=NUC2 -e CTRL_ALGO=PP <IMAGE>
```

## Opening additional inspection shells

Organizers (or teammates) can open as many additional bash sessions as
needed without re-triggering the stack:

```bash
docker exec -it asuf1tenth_api bash
```

From there, the usual competition workflow applies (rosbag recording,
`rqtgraph`, etc.):

```bash
ros2 bag record -a -o qualification.bag
rqtgraph
```

## Retrieving race artifacts

```bash
docker cp asuf1tenth_api:/home/autodrive_devkit/qualification.bag .
docker cp asuf1tenth_api:/home/autodrive_devkit/competition.bag .
docker cp asuf1tenth_api:/home/autodrive_devkit/rosgraph.png .
```

## Push

```bash
docker login
docker push <TEAM_USERNAME>/<IMAGE_NAME>:<TAG>
```
