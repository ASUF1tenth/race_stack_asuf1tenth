# Usage

After connecting to the Jetson (Find the IP Address and connect using README_GUI.md) and accessing a terminal, you should start by using

```bash
dock
```
Here, you're now connected to the stack container within the Jetson.
You can source all the files and built packages by using

```bash
sauce
```

# Multi Terminal Access
In a new terminal, Connect to the jetson and open another terminal by using

```bash
sh
```

If you run `dock` again you'll be accessing the same old container terminal as the one you accessed in the previous steps


# Running Stack and get stuff going

Start by running base_system with any map (check Maps folder in stack master) by using

```bash
ros2 launch stack_master base_system_launch.xml racecar_version:=NUC2 map_name:=room
```

in another terminal (even from your pc) you can run the commands to run all the teleop and the keyboard