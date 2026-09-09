 # Competition Rules

 ## RoboRacer Sim Racing

 This document describes the rules and regulations for the RoboRacer Sim Racing League. It goes over the definitions, requirements and evaluation criteria as well as general dos and don'ts for the competition.

 > **Warning**
>
>  Rules are subject to change. Organizers reserve the right to amend existing rules and, if situation demands, create new rules on the go.

 ## 1\. General Guidelines

 RoboRacer Sim Racing League is a virtual competition, which accompanies the physical RoboRacer Autonomous Racing Competition. It leverages AutoDRIVE Ecosystem to model and simulate the digital twin of an RoboRacer racecar within a virtual racetrack. The main goal of this competition is to make autonomous racing accessible to everyone across the globe.

 ### 1.1. Eligibility Criteria

 This competition is open to everyone around the world - students, researchers, hobbyists, professionals, or anyone else who is interested. There are no restrictions on age, sex, nationality, profession, etc. A team can consist of single or multiple participants. Multiple teams from the same organization are also allowed. However, each participant can be a member of strictly one team.

 Registration for the Sim Racing League is free of cost and separate from the Physical Racing League and the conference registrations themselves. Although teams can participate in the Sim Racing League without attending the conference, we strongly encourage all competition participants to attend the conference in person. This will allow the teams to participate in competition-related events at the conference and connect with the broader community!

 ### 1.2. Competition Structure

 Each team will be provided with a standardized simulation setup (in the form of a digital twin of the RoboRacer vehicle, and a digital twin of the Porto racetrack) within the high-fidelity AutoDRIVE Simulator.

 Additionally, teams will also be provided with a working implementation of the AutoDRIVE Devkit to get started with developing their autonomy algorithms.

 Teams will have to develop perception, planning, and control algorithms to parse the real-time sensor data streamed from the simulator and generate control commands to be fed back to the simulated vehicle.

 ### 1.3. Competition Timeline

 The competition will take place in 2 stages:

 - **Qualification Race:** Teams will demonstrate their ability to complete multiple laps around the practice track without colliding with the track bounds at run time.
- **Time-Attack Race:** Teams will compete against the clock, on a previously unseen racetrack, to secure a position on the leaderboard.

 Following is a summary of the main events of the competition:

 1. **Registration:** Interested teams will register for the Sim Racing League.
2. **Qualification Round:** Teams will demonstrate successful completion of 10 laps around the practice track provided ahead of time.
3. **Qualification Results Declared:** Standings of all the qualified teams will be released.
4. **Competition Track Released:** Organizers will release the actual "competition track", which will be used for the final race. This track may be replicated in the physical race as well.
5. **Final Race:** Organizers will collect containerized algorithms from each team and connect them with the containerized simulator. Performance metrics of each team will be recorded.
6. **Competition Results Declared:** Standings of all the teams for the final race will be released.

 ## 2\. Competition Guidelines

 This competition will adhere to the time-attack racing format, wherein each team will compete against the clock independently, on the same racetrack.

 Each race will comprise a total of 12 laps: the vehicles will start with a warm-up lap, followed by 10 race laps, and finally a cool-down lap.

 ### 2.1. Competition Requirements

 Following are the requirements to progress along each phase of the competition:

 - **Registration:** Interested teams must register for the competition before the deadline. Organizers may extend registration deadlines in certain cases; however, direct requests for deadline extension from any team(s) will not be entertained. It is recommended to register your team well in advance to avoid last-minute rush.
- **Qualification:** Teams will have to demonstrate successful completion of 10 autonomous laps around the practice track provided ahead of time. During this phase, speed is not very important, but failure to complete 10 consecutive autonomous laps without exceeding the collision count tolerance will result in disqualification of that team. Passing the qualification session entitles a team for the final race.
- **Competition:** During this phase, the clock will be ticking, and the objective would be to complete 10 consecutive autonomous laps as fast as possible without exceeding the collision count tolerance. Failure to respect the collision count tolerance will result in disqualification of that team. Teams will be ranked on a leaderboard in the ascending order of their time to completion (10 autonomous racing laps).

 ### 2.2. Competition Terminology

 Following are the definitions of some competition terminologies:

 - **Collision:** Any contact between the colliders of the simulated vehicle and the racetrack bounds (except the wheels touching the ground) is considered a collision. A collision will incur a penalty of 10 seconds (i.e., 10 seconds after first collision, 20 seconds after the second, 30 seconds after the third, and so on). Colliding more than 10 times in a single racing event will lead to disqualification. Each collision will automatically reset the vehicle to the last checkpoint (your localization algorithm will have to be robust against this re-setting action). Lap timer will not reset upon collision.
- **Warm-Up Lap:** This is the first lap of a race. The time or collisions during the warm-up lap will not be considered. This lap acts as a buffer since your algorithms may take time to launch and connect with the simulator, while the lap timer is on.
- **Race Laps:** These are a set of 10 laps immediately following the warm-up lap. The race laps start as soon as the vehicle crosses the finish line in the warm-up lap. The time and collisions of the race laps will be considered.
- **Cool-Down Lap:** This is the last lap of a race. The time or collisions during the cool-down lap will not be considered. Completing this lap is not required for the competition, but this can be a good time to "show-off" your skills without worrying about collisions!
- **Checkpoints:** The racetrack has several "virtual" checkpoints, spaced approximately equally along the track. These checkpoints cover the entire width of the racetrack and are triggered as the vehicle passes through them. The start/finish line is the final "special" checkpoint. The exact location of the checkpoints will not be revealed to the participants.
- **Lap Time:** This is the amount of time that the vehicle takes to complete one full lap around the racetrack. The timer starts as soon as the previous lap ends and stops after the current lap ends. Failing to pass all the checkpoints before crossing the finish line (e.g., driving in opposite direction) will not stop the lap timer.
- **Race Time:** This is the cumulative time that the vehicle takes to complete 10 race laps around the racetrack. The timer starts as soon as the warm-up lap ends and stops after the 10th race lap ends. Collision penalties are added separately.
- **Best Lap Time:** This is the amount of time that the vehicle took to complete the fastest race lap around the racetrack. This is the minimum lap time across all the 10 race laps.
- **Average Lap Time:** This is the average time that the vehicle took to complete a race laps (out of 10 race laps) around the racetrack. This is the statistical mean of all the 10 race lap times.

 ### 2.3. Competition Execution

 Following is a summary of a typical racing event:

 1. **Inspection:** Race stewards will examine the team's submission according to race standards.
2. **Simulator:** Containerized AutoDRIVE Simulator will be launched. Communication bridge parameters will be set (communication channel will not be opened yet). Vehicle will be engaged in autonomous mode. Graphics quality will be set to "Ultra".
3. **Devkit:** Containerized AutoDRIVE Devkit with the team's autonomous racing algorithm submission will be launched. A new Bash session will be opened within the container to start recording a ROS 2 bag of all the available topics.
4. **Recording:** A screen recorder application as well as the ROS 2 bag recording will run in the background.
5. **Communication:** The bi-directional communication channel between simulator container and devkit container will be established. This should make all the data available on the relevant ROS 2 topics and automatically start the race.
6. **Race:** Each race will comprise a total of 12 laps: the vehicles will start with a warm-up lap, followed by 10 race laps, and finally a cool-down lap. The lap times or collisions during the warm-up and cool-down laps will not be considered, only those during the 10 race laps will be considered.
7. **Data:** Performance metrics of the team will be recorded and stored along with the screen recording of the simulator as well as the comprehensive ROS 2 bag.

 ### 2.4. Inspection Rules

 > **Warning**
>
>  Organizers reserve the right to reject any submission that they deem illegal due to unethical exploitation of the competition framework. All submissions will be examined by the race stewards prior to the race.

 > **Warning**
>
>  Teams breaching the code of conduct will face direct disqualification with a publicly visible "malpractice" citation on the competition website.

 This competition is intended to be a battle of algorithms, and hence any modifications to the competition framework including (but not limited to) the simulator executable, vehicle (chassis, powertrain, sensors, etc.), environment (track, layout, ground, weather, time, etc.), communication interface (use of protocols other than WebSocket), devkit (use of APIs other than ROS 2) or the containerization approach (use of tools besides Docker, Dockerfile configuration, etc.) are strictly prohibited.

 Any modification to the competition framework shall result in direct disqualification of the responsible team without admission to the qualification/competition session.

 Any kind of autonomous racing algorithm that makes use of raw perception data to generate control commands for the simulated vehicle is permissible - including (but not limited to) reactive planning, map-based localization, raceline optimization, deep learning, reinforcement learning as well as hybrid algorithms.

 However, utilizing simulation ground truth data or controlling aspects other than the vehicle actuators is not allowed. Furthermore, exploiting the competition framework unethically (e.g., tapping into the back-end, frame-grabbing the front-end, finding loop-holes in the framework, tampering with data streaming/logging, etc.) is considered a serious malpractice.

 > **Info**
>
>  Please refer to the Technical Guide for more information about permissible and restricted data streams.

 Since this is a global event held at some of the world's premier conferences, we ask all teams to observe ethical integrity and abide by the code of conduct of this competition.

 Any malpractice or plagiarism in terms of submission code or other material shall be considered a serious breach of the code of conduct.

 Depending upon the situation, organizers reserve the right to issue a warning, public citation, and/or disqualification of the responsible team(s) from the competition.

 ### 2.5. Evaluation Criteria

 Following are the evaluation criteria for the competition:

 - The ultimate evaluation criterion for the race is total race time. However, best lap time and/or other metrics may be used in case of a tie.
- A collision will incur a penalty of 10 seconds (i.e., 10 seconds after first collision, 20 seconds after the second, 30 seconds after the third, and so on).
- The maximum number of collisions permissible for a race (qualification/competition) is 10, beyond which the team will be disqualified.
- Lap times or collisions during the warm-up and cool-down laps will not be considered, only those during the 10 race laps will be considered.

 > **Note**
>
>  Race referee's decision is final! In extreme cases, rebuttals with supporting evidence may be entertained at the organizers' discretion.

 ## 3\. Submission Guidelines

 Each team is expected to submit a containerized version of their autonomous racing software stack. Submissions for each phase of the competition will be handled separately.

 > **Note**
>
>  We expect that upon running your submitted container, all the necessary nodes should start up (the autodrive\_devkit API we have included as well as your team's racing stack). Once we hit the Connection Button on the Menu Panel of AutoDRIVE Simulator, the simulated vehicle should start running.
>
>  Please make sure that you include all the necessary commands (for sourcing workspaces, setting environment variables, launching nodes, etc.) within the entrypoint script (autodrive\_devkit.sh file) provided within the autodrive\_roboracer\_api container.
>
>  Please do NOT use \~/.bashrc or other means to automate the algorithm execution!
>
>  Competition organizers should be able to start additional bash session(s) within your submitted container (without your codebase executing every time a new bash session is initialized) for data recording and inspection purposes.
>
>  Also, make sure to add detailed instructions to your Docker Hub repository overview, which explains how to download (specific tag) and run your container image step-by-step.

 ### 3.1. Submission Requirements

 Following are the requirements for submitting an entry to the competition:

 - Each team is expected to submit a Docker container image of their autonomous racing software stack.
- The submitted container should be self-sustainable in terms of all the dependencies and should be configured to run all the necessary commands automatically when launched.
- The submitted container must be based off of the official AutoDRIVE Devkit container released for the competition.
- Teams are permitted to add/modify ROS 2 package(s) within the provided AutoDRIVE Devkit container for implementing their autonomous racing algorithm(s). However, any modifications to the existing container elements are strictly off the limits.
- Teams do not need to submit the simulator container.

 > **Tip**
>
>  Teams can test their algorithms locally before containerizing them. However, don't forget to test your containers before pushing them upstream and submitting them!

 ### 3.2. Submission Process

 Following are the key milestones for submitting an entry to the competition:

 1. Teams will containerize their autonomous racing software stack using Docker.
2. Teams will push their self-sustainable Docker container image to DockerHub.
3. Teams will share the link of the upstream repository with the organizers via a secure submission form (separate forms for each stage of the competition).

 ### 3.3. Submission Privacy

 This is a competition, and all teams have the right to keep their source code hidden from their competitors. Here are a few strategies to keep in mind:

 - **Source Code:** Teams can host their source code in a private GitHub repository for collaboration and version control. GitHub now allows hosting unlimited private repositories for personal accounts and organizations.
- **Containers:** Teams can push their Docker container images to a private DockerHub repository. As of now, DockerHub allows hosting one free private repository for each user account.
- **Data:** Teams can store their data in an encrypted and secure cloud storage platform with link-sharing disabled. Alternatively, storing data locally (with a hard-drive backup) is also an option.

 However, after the competition, we encourage teams to publish their source code on GitHub under an open-source license. We also encourage teams to make their Docker containers public on DockerHub.

 Teams can also choose to make other race data (e.g., videos, logs, reports, etc.) publicly available. This will increase the visibility of their work and increase the quality of the future competitions.

 ## 4\. Citation

 We encourage you to read and cite the following papers if you use any part of the competition framework for your research:

 ### AutoDRIVE: A Comprehensive, Flexible and Integrated Digital Twin Ecosystem for Enhancing Autonomous Driving Research and Education

```
@article{AutoDRIVE-Ecosystem-2023,
author = {Samak, Tanmay and Samak, Chinmay and Kandhasamy, Sivanathan and Krovi, Venkat and Xie, Ming},
title = {AutoDRIVE: A Comprehensive, Flexible and Integrated Digital Twin Ecosystem for Autonomous Driving Research & Education},
journal = {Robotics},
volume = {12},
year = {2023},
number = {3},
article-number = {77},
url = {https://www.mdpi.com/2218-6581/12/3/77},
issn = {2218-6581},
doi = {10.3390/robotics12030077}
}
```

 This work has been published in MDPI Robotics. The open-access publication can be found on MDPI.

 ### AutoDRIVE Simulator: A Simulator for Scaled Autonomous Vehicle Research and Education

```
@inproceedings{AutoDRIVE-Simulator-2021,
author = {Samak, Tanmay Vilas and Samak, Chinmay Vilas and Xie, Ming},
title = {AutoDRIVE Simulator: A Simulator for Scaled Autonomous Vehicle Research and Education},
year = {2021},
isbn = {9781450390453},
publisher = {Association for Computing Machinery},
address = {New York, NY, USA},
url = {https://doi.org/10.1145/3483845.3483846},
doi = {10.1145/3483845.3483846},
booktitle = {2021 2nd International Conference on Control, Robotics and Intelligent System},
pages = {1–5},
numpages = {5},
location = {Qingdao, China},
series = {CCRIS'21}
}
```

 This work has been published at 2021 International Conference on Control, Robotics and Intelligent System (CCRIS). The publication can be found on ACM Digital Library.

---

 **April 13, 2026**

 Copyright © 2026 Tinker Twins
