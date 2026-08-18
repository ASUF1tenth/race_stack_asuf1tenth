cmake_minimum_required(VERSION 3.5)
project(asuf1tenth_vehicle_interface)

find_package(ament_cmake REQUIRED)

# Install Python node script as executable
install(PROGRAMS
  scripts/asuf1tenth_vehicle_interface.py
  DESTINATION lib/${PROJECT_NAME}
)

# Install launch and params directories
install(DIRECTORY
  launch
  params
  DESTINATION share/${PROJECT_NAME}
)

ament_package()
