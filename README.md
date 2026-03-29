# ADA Setup Documentation

## Overview

This documentation explains how to set up the **ADA Feeding System** in the Robot Studio lab. We are adapting the Personal Robotics Lab’s setup to support a **Gen3 robot**.  

Currently, following this guide will allow you to set up ADA Feeding on your system and run the simulation with a **Jaco2 robot**. For additional details, refer to the **Work in Progress** section.  

Regarding Gen3 functionality, at this stage you can only control motion plans for the Gen3 robot within the `ada_ros2` directory.

### Note
- The Robot Studio GitHub repo is linked [here](https://github.com/studiorobot/ada_feeding/tree/ros2-devel).  
- These steps are edited from the original Personal Robotics Lab’s `ada_feeding` setup, which can be found [here](https://github.com/personalrobotics/ada_feeding) or within the `PRsetup` folder.  
- Replace all instances of `YOUR_WORKSPACE_PATH` with your actual workspace directory.

## Table of Contents
1. Installing Virtual Ubuntu 22.04
2. Installing ROS2 Humble
3. Clone pr-rosinstalls
4. Install repositories
5. Configure rosdep
6. Install rosdep dependencies
7. Install and fix non-rosdep dependencies
8. Installing pyrealsense (for ARM users) – Build from Source
9. Setup CycloneDDS
10. Build your workspace
11. Installing the webapp
12. Running the Software
13. Work in Progress Notes
14. Troubleshooting

---

## 1. Installing Virtual Ubuntu 22.04

### Overview
Ensure your environment runs **Ubuntu 22.04**, either natively or through WSL for Windows users.

### Check Ubuntu Version
```bash
lsb_release -a
```
### Installing Ubuntu 22.04 on WSL:
```bash
wsl --install Ubuntu-22.04 
```

## 2. Installing ROS2 Humble

### Overview
ROS2 Humble is the middleware for robot communication and motion planning. These steps will configure your system locale, install ROS2 packages, and verify the installation.

Check whether ROS2 is installed (or follow the rest of the steps).

---

### A. Pre-check: Is ROS2 already installed?

#### A1. Check if ROS2 is installed
```bash
printenv ROS_DISTRO
```

* Expected output for Humble: `humble`
* If Humble is already installed, skip to **Verify ROS2 Works**.
* If empty, ROS2 is not sourced yet.
* You can also check `/opt/ros/` for any ROS distributions.
* If none exist, continue with the installation steps below.

#### A2. Verify Python environment

```bash
which python3
```

* ROS2 Humble should use system Python: `/usr/bin/python3`
* If it shows a conda/miniforge path, deactivate conda before proceeding:

```bash
conda deactivate
```

#### A3. Verify locale (UTF-8)

```bash
locale
```

* Ensure UTF-8 is enabled (`en_US.UTF-8`).
* If not, run:

```bash
sudo apt update && sudo apt install locales
sudo locale-gen en_US en_US.UTF-8
sudo update-locale LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8
export LANG=en_US.UTF-8
locale  # verify settings
```

---

### B. Install ROS2 Humble Packages

```bash
sudo apt install software-properties-common
sudo add-apt-repository universe
sudo apt update && sudo apt install curl -y

export ROS_APT_SOURCE_VERSION=$(curl -s https://api.github.com/repos/ros-infrastructure/ros-apt-source/releases/latest | grep -F "tag_name" | awk -F\" '{print $4}')
curl -L -o /tmp/ros2-apt-source.deb "https://github.com/ros-infrastructure/ros-apt-source/releases/download/${ROS_APT_SOURCE_VERSION}/ros2-apt-source_${ROS_APT_SOURCE_VERSION}.$(. /etc/os-release && echo ${UBUNTU_CODENAME:-${VERSION_CODENAME}})_all.deb"
sudo dpkg -i /tmp/ros2-apt-source.deb
sudo apt update
sudo apt upgrade
sudo apt install ros-humble-desktop
sudo apt install ros-humble-ros-base
sudo apt install ros-dev-tools
source /opt/ros/humble/setup.bash
```

---

### C. Verify ROS2 Works

Open **two terminals**:

**Terminal 1:**

```bash
source /opt/ros/humble/setup.bash
ros2 run demo_nodes_cpp talker
```

**Terminal 2:**

```bash
source /opt/ros/humble/setup.bash
ros2 run demo_nodes_py listener
```

* The talker should publish messages, and the listener should print out:

```
I heard ...
```

> **Tip:** Refer to the Troubleshooting section if you encounter any errors.


## 3. Clone `pr-rosinstalls`

This will install the `ada_feeding`, `ada_ros2`, and other repositories required for the program.

```bash
cd ~
git clone https://github.com/studiorobot/pr-rosinstalls.git
```

---

## 4. Install Repositories

Replace `<https/ssh>` with your preferred authentication method.
**Note:** You must have access rights to Robot Studio — see troubleshooting for help.

```bash
sudo apt install python3-wstool   # if not already installed
cd YOUR_WORKSPACE_PATH             # create a workspace/src for project
wstool init
wstool merge ~/pr-rosinstalls/ada-feeding.<https/ssh>.rosinstall
wstool up
```

---

## 5. Configure `rosdep`

```bash
sudo apt install python3-rosdep   # if not already installed
sudo rosdep init                  # only needed the first time using rosdep
```

---

## 6. Install `rosdep` Dependencies (if you have sudo access)

```bash
rosdep update
cd YOUR_WORKSPACE_PATH
rosdep install --from-paths src -y --ignore-src --as-root=pip:false
```

---

## 7. Install and Fix Non-`rosdep` Dependencies

```bash
cd ~/YOUR_WORKSPACE_PATH/src/ada_feeding
python3 -m pip install -r requirements.txt
```

* Upgrade `transforms3d` (Ubuntu package is outdated):

```bash
python3 -m pip install transforms3d -U
```

* Remove the duplicate matplotlib pip installation caused by installing scikit-spatial with pip (some accounts have required sudo access for this command, other have not. If you do not have sudo access and encounter this, contact a lab member who does):

```bash
python3 -m pip uninstall matplotlib
```

* `pyrealsense2` is [not released for ARM systems](https://github.com/realsenseai/librealsense/issues/6449#issuecomment-650784066). ARM users must build from [source](https://github.com/realsenseai/librealsense/blob/master/wrappers/python/readme.md#building-from-source) (see Step 8).
  You may need to add `-DPYTHON_EXECUTABLE=/usr/bin/python3` to the `cmake` command.
  When running `sudo make install`, ensure the installation path is added to your `PYTHONPATH` (usually `/usr/local/lib`).

---

## 8. Installing `pyrealsense2` for ARM Users (Build from Source)

### a. Update Your System

```bash
sudo apt-get update && sudo apt-get dist-upgrade
```

> Use `dist-upgrade` instead of `upgrade` if running an older Ubuntu version.

### b. Install Python and Development Files

```bash
sudo apt-get install python3 python3-dev
```

### c. Clone the `librealsense` Repository

```bash
git clone https://github.com/IntelRealSense/librealsense.git
cd librealsense
```

### d. Configure and Build (5–10 minutes)

```bash
mkdir build
cd build
cmake ../ -DBUILD_PYTHON_BINDINGS:bool=true -DPYTHON_EXECUTABLE=$(which python3)
make -j4
sudo make install
```

**Optional CMake Flags:**

* Build a self-contained (statically compiled) library:

```text
-DBUILD_SHARED_LIBS=false
```

* Use a specific Python executable:

```text
-DPYTHON_EXECUTABLE=[full path to desired python executable]
```

### e. Update Your `PYTHONPATH`

```bash
export PYTHONPATH=$PYTHONPATH:/usr/local/lib
```

> If the above doesn’t work:

```bash
export PYTHONPATH=$PYTHONPATH:/usr/local/lib/[python version]/pyrealsense2
```

---

### f. Alternative Method

Copy the build output (`librealsense2.so` and `pyrealsense2.so`) next to your script.

> Python 3 module filenames may include additional info, e.g.,
> `pyrealsense2.cpython-35m-arm-linux-gnueabihf.so`

---

## 9. Setup CycloneDDS

They recommend using CycloneDDS as your ROS2 midleware, with a custom configuration file that enables multicast on loopback and prioritizes loopback.

1. Install CycloneDDS:

```bash
sudo apt install ros-humble-rmw-cyclonedds-cpp
````

2. Add the following lines to your `~/.bashrc`:

```bash
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
export CYCLONEDDS_URI=~/YOUR_WORKSPACE_PATH/src/ada_feeding/cyclonedds.xml
```

3. Create the `cyclonedds.xml` file (not tracked by Robot Studio GitHub as it varies per environment):

```bash
cd ~/YOUR_WORKSPACE_PATH/src/ada_feeding/
nano cyclonedds.xml
sudo chown $USER:$USER cyclonedds.xml
```

4. Copy and paste the following into `cyclonedds.xml`:

```xml
<?xml version="1.0" encoding="utf-8"?>
<CycloneDDS
  xmlns="https://cdds.io/config"
  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
  xsi:schemaLocation="https://cdds.io/config https://raw.githubusercontent.com/eclipse-cyclonedds/cyclonedds/master/etc/cyclonedds.xsd"
>
  <Domain Id="any">
    <General>
      <Interfaces>
        <NetworkInterface name="lo" priority="default" multicast="true"/>
        <NetworkInterface name="wlp0s20f3" priority="default" multicast="true"/>
      </Interfaces>
    </General>
  </Domain>
</CycloneDDS>
```

> **Notes:**
>
> * You may need to change the fallback interface if `lo` does not work. To do so, run ifconfig and either use the name of your ethernet network or WiFi network, depending on how your computer is connected to the internet.
> * After updating `cyclonedds.xml`, rebuild your workspace from scratch.
> * IF YOU HAVE BOTH KINOVA KORTEX AND ADA SETUP:
Adding the CYCLONEDDS_URI will cause DDS in Kortex files/program to fail so you must unset the URI when running Kortex API

```bash
unset CYCLONEDDS_URI
```

---

## 10. Build Your Workspace

> Note: Currently, communication with hardware is not set up. Therefore, the following command will only build the packages needed for simulation 

```bash
cd ~/YOUR_WORKSPACE_PATH
colcon build --symlink-install --packages-skip KinovaExample ada_hardware
```

> To build all packages (if hardware is ready):

```bash
colcon build --symlink-install
```

---

## 11. Installing the Web App

1. **Install Node Version Manager [nvm] (https://github.com/nvm-sh/nvm?tab=readme-ov-file#install--update-script):**

```bash
wget -qO- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.3/install.sh | bash
```

2. **Install and use NodeJS 21:**

```bash
nvm install 21
nvm use 21
```

> If you have just installed nvm using the previous command, you will need to source your .bashrc or open a new terminal to run these commands

3. **(Only for users with sudo access; this should already be configured on PRL computers) Make Node available to all users, including root:**

```bash
sudo ln -s "$NVM_DIR/versions/node/$(nvm version)/bin/node" "/usr/local/bin/node"
sudo ln -s "$NVM_DIR/versions/node/$(nvm version)/bin/npm" "/usr/local/bin/npm"
sudo ln -s "$NVM_DIR/versions/node/$(nvm version)/bin/npx" "/usr/local/bin/npx"
```

4. **(Only for users with sudo access; this should already be configured on PRL computers) Install serve and pm2 globally. Root access is necessary for serve so it can access port 80.**

```bash
sudo npm install -g serve
npm install -g pm2@latest
```

5. **Install the web app dependencies. (Note: there will be some vulnerabilities in dependencies. This is okay, since access to the web app is shielded behind our secure router.)**

```bash
cd ~/YOUR_WORKSPACE_PATH/src/feeding_web_interface/feedingwebapp
npm install --legacy-peer-deps
npx playwright install
```

6. **(Optional; this should already be configured on PRL computers) To access the web app on a device other than the one hosting it, enable the desired port for HTTP [access](https://www.digitalocean.com/community/tutorials/ufw-essentials-common-firewall-rules-and-commands#allow-all-incoming-http-port-80)**

```bash
sudo ufw enable
sudo ufw allow 80
sudo ufw allow 3000
```

---

## 12. Running the Software

> Currently, we are testing using Option B: Mock Robot as the real robot has not been configured to use yet.
> We use the convenience script start.py to launch the software. This script has several command-line arguments, which can be seen by passing the -h flag when running the script.

### Option A: Web App with Real Robot

> This option starts the web app and the real robot code, and can be used to test the entire system. This will by default start the web app on port 80, and requires sudo access. The robot's HDMI connection must be plugged into your computer, and your computer should be connected to the robot's router with an ethernet cable.
> NOTE: If not running on the production machine i.e., lovelace, it's recommended that you append the command line flag --dev to the start script. This will launch RVIZ, will not require the e-stop button to be plugged in, and will not require sudo access to launch the web app.

```bash
cd ~/YOUR_WORKSPACE_PATH
python3 src/ada_feeding/start.py
```

* In a browser, access `127.0.0.1` (if on the same device serving the web app), or the IP address of the device hosting the web app (if on a different device connected to the same network, e.g. a cell phone connected to the LOVELACE_5g network). You should now be able to run the system! Note that upon startup, the watchdog is in a failing state until the e-stop is clicked exactly once, allowing the system to verify that it is connected and working.

* To close:

```bash
python3 src/ada_feeding/start.py -c
```

---

### Option B: Web App with Mock Robot

> This option starts the web app, runs dummy nodes for perception, runs the real robot motion code, but runs a mock robot in MoveIt. This is useful for testing robot motion code in simulation before moving onto the real robot. This will start the web app on port 3000 and does not require sudo access.

**For Gen2 Jaco Robot:**

```bash
cd ~/YOUR_WORKSPACE_PATH
python3 src/ada_feeding/start.py --sim mock_jaco
```

* In a browser, access `127.0.0.1:3000` (if on the same device serving the web app), or the IP address of the device hosting the web app at port `3000` (if on a different device connected to the same network). You should now be able to run the system!
* You should see the webapp and a simulation in RVIZ with the Jaco2 robot. You should be able to choose different actions through the webapp and see the execution in the simulation.

* To close:

```bash
python3 src/ada_feeding/start.py --sim mock_jaco -c
```

**For Gen3 Kortex Robot (Not functional yet):**

```bash
cd ~/YOUR_WORKSPACE_PATH
python3 src/ada_feeding/start.py --sim mock_kortex
```
* In a browser, access 127.0.0.1:3000 (if on the same device serving the web app), or the IP address of the device hosting the web app at port 3000 (if on a different device connected to the same network). You should now be able to run the system!

* Close with:

```bash
python3 src/ada_feeding/start.py --sim mock_kortex -c
```

---

### Option C: Web App with All Dummy Nodes

> This option starts the web app, and runs dummy nodes for all perception and robot motion code. This is useful to test the web app in isolation. This will start the web app on port 3000 and does not require sudo access.

```bash
cd ~/YOUR_WORKSPACE_PATH
python3 src/ada_feeding/start.py --sim dummy
```

* In a browser, access 127.0.0.1:3000 (if on the same device serving the web app), or the IP address of the device hosting the web app at port 3000 (if on a different device connected to the same network). You should now be able to run the system!
* To close:

```bash
python3 src/ada_feeding/start.py --sim dummy -c
```

# 13. Work in Progress

## Current Status

- The feeding setup is currently functional for **older Jaco 2 robots**.  
- **Food acquisition** is the only action not working, likely because there is no actual plate of food for the robot to acquire.

---

## Converting to Gen 3 Kortex in `ada_ros2`

`ada_ros2` is compatible with the **Gen 3 Kortex robot**. Its responsibilities include:

- Launching the robot and correlated sensors.
- Setting up the ROS 2 environment.
- Handling communication with the robot in both simulation and real hardware.

### Testing in Simulation

Within the `ada_ros2` directory, you can test simulation using:

```bash
ros2 launch ada_moveit demo.launch.py sim:=mock
```

> This works for Jaco2 robots.

### Running Gen 3 in Simulation

To run the Gen 3 robot in simulation, temporarily switch the description files in `ada_description`:

1. Navigate to the `urdf` folder.
2. Rename files:

   ```text
   ada.xacro → ada.jaco2.txt
   ada.gen3.txt → ada.xacro
   ```
3. In the `rviz` folder, rename:

   ```text
   view_robot.rviz → view_robot.jaco2.txt
   view_robot.gen3.txt → view_robot.rviz
   ```

> This swaps in the Gen 3 description while preserving Jaco2 files. Currently working on a way to do this without having to switch config files between Jaco2 vs Gen3. 

### After Switching Files

1. Build the workspace:

```bash
colcon build
```

2. Navigate to `ada_ros2` and source the setup script:

```bash
source ../install/setup.bash
```

3. Launch the Gen 3 simulation:

```bash
ros2 launch ada_moveit_kortex demo.launch.py sim:=mock
```

> This will allow you to see ada_ros2 working with Gen 3 in simulation. You should be able to plan motions for the Gen 3 robot in RVIZ. 
> The orientation of the fork and camera mount need to be fixed.

---

## Next Steps for Full Simulation Integration with `ada_feeding`

* A planning scene needs to be created that defines where and when the Gen 3 robot should move.
* This ensures coordinated operation with the feeding application.

---

## Next Steps for Full Hardware Integration with `ada_feeding`

1. The **Kortex API** is installed in the repository.
2. Write a `gen3.cpp` file using the **Kortex API** to control the Gen 3 hardware.


# 14. Troubleshooting

## Debugging with Screens

The ADA Feeding system launches multiple isolated workspaces, called **screens**, to handle different components independently.  
These include feeding logic, robot simulation, sensors, and the web interface. Each screen runs in its own terminal session, making it easier to manage and debug specific parts of the system.

### Viewing Logs

To attach to a running screen and see real-time logs:

```bash
screen -r <screen_name>
```

Replace `<screen_name>` with the component you want to monitor (e.g., `feeding`, `robot_sim`, `sensors`, `web_interface`).

---

### Saving Logs for Later

1. Attach to the desired screen:

```bash
screen -r <screen_name>
```

2. Start logging the session:

```
Ctrl-A H
```

> This will save output to `screenlog.0` in the current directory.

3. To stop logging:

```
Ctrl-A H
```

4. Rename and move the log file for later reference:

```bash
mv screenlog.0 ~/logs/<screen_name>_$(date).log
```

---

## Robot Launch / Topics Not Publishing

**Common error:**

```
Waiting for robot_description to be published on the robot_description topic
```

### Troubleshooting Steps

1. Source the proper workspaces/repos before launching files.
2. Check if ROS 2 nodes are communicating:

```bash
ros2 node list
```

* If nodes/topics appear correctly, it’s not a ROS 2 DDS issue.

3. Test minimal `talker`/`listener` nodes.
4. On Linux, check firewall status:

```bash
sudo ufw status
sudo ufw allow 7400:7500/udp
```

5. Launch your file again.

---

## Dead Screen Sessions

Clear inactive screens:

```bash
screen -wipe
```

---

## Python Module Errors

**Example:** `ModuleNotFoundError: No module named 'yourdfpy'`

```bash
pip3 install yourdfpy
```

---

## Setting Up Git + SSH Key Access

1. Check if you already have an SSH key:

```bash
ls ~/.ssh
```

Look for `id_ed25519` / `id_ed25519.pub` or `id_rsa` / `id_rsa.pub`.

2. If no SSH key exists, generate one:

```bash
ssh-keygen -t ed25519 -C "your_email@example.com"
```
Hit Enter through all prompts unless you want a custom path/passphrase.

3. Start the SSH agent:

```bash
eval "$(ssh-agent -s)"
```

4. Add your SSH key to the agent:

```bash
ssh-add ~/.ssh/id_ed25519
```

5. Copy your public key:

```bash
cat ~/.ssh/id_ed25519.pub
```

6. Add the key to GitHub:

* GitHub → Settings → SSH and GPG keys → New SSH key → Paste → Save

7. Verify GitHub SSH access:

```bash
ssh -T git@github.com
```

Expected output:
`Hi <username>! You've successfully authenticated...`

8. Clone the repo using SSH:

```bash
git clone git@github.com:<user>/<repo>.git
```

9. Check Git installation:

```bash
git --version
```

10. Set global Git identity:

```bash
git config --global user.name "Your Name"
git config --global user.email "your_email@example.com"
```

---

## Conan Executable Not Found

1. Uninstall Conan 2.x:

```bash
python3 -m pip uninstall -y conan
```

2. Install Conan 1.x:

```bash
python3 -m pip install "conan<2.0" --user
```

3. Add Conan to PATH:

```bash
export PATH=$HOME/.local/bin:$PATH
```

4. Verify version:

```bash
conan --version
```

5. Detect system settings:

```bash
conan profile detect
```

6. Verify default profile exists:

```bash
conan profile list
```

7. Navigate to workspace:

```bash
cd ~/YOUR_WORKSPACE_PATH
```

8. Clean previous builds:

```bash
rm -rf build/ install/ log/
```

9. Rebuild all packages:

```bash
colcon build --symlink-install
```

---

## Fatal Error: `Killed signal terminated program cc1plus`

* Cause: Build took too much memory and crashed.
* Solution: Remove build logs and build with 1 parallel worker.

```bash
rm -rf build log install
colcon build --symlink-install
```

---

## Resetting MoveIt

If sourcing older configs, reset MoveIt:

```bash
rm -rf ~/.moveit
```
---

## Web App Stuck on “Robot is Thinking”

If everything seems to load correctly but the **web app never gets past “thinking”** and **simulation does not move**, first verify that **ROS2 and the action servers are actually responding**.

1. From the `ada_feeding/ada_feeding` directory, run the following tests (from the original PRL README):

  ```bash
   ros2 action send_goal /MoveAbovePlate ada_feeding_msgs/action/MoveTo "{}" --feedback
   ros2 action send_goal /AcquireFood ada_feeding_msgs/action/AcquireFood "{header: {stamp: {sec: 0, nanosec: 0}, frame_id: ''}, detected_food: {roi: {x_offset: 0, y_offset: 0, height: 0, width: 0, do_rectify: false}, mask: {header: {stamp: {sec: 0, nanosec: 0}, frame_id: ''}, format: '', data: []}, item_id: '', confidence: 0.0}}" --feedback
   ros2 action send_goal /MoveToRestingPosition ada_feeding_msgs/action/MoveTo "{}" --feedback
   ros2 action send_goal /MoveToStagingConfiguration ada_feeding_msgs/action/MoveTo "{}" --feedback
   ros2 action send_goal /MoveToMouth ada_feeding_msgs/action/MoveToMouth "{}" --feedback
   ros2 action send_goal /MoveFromMouth ada_feeding_msgs/action/MoveTo "{}" --feedback
   ros2 action send_goal /MoveToStowLocation ada_feeding_msgs/action/MoveTo "{}" --feedback
  ```

2. If these actions return feedback, then **MoveIt + ROS2 + simulation are working correctly**.

Next steps:

* If running the **Web App locally**, try clearing your browser cache:

  * Open browser history
  * Delete cached data
  * Restart the program

This often resolves the web app getting stuck after successful ROS2 startup.

---