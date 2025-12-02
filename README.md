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
4. Configure rosdep
5. Install rosdep dependencies
6. Install and fix non-rosdep dependencies
7. Installing pyrealsense (for ARM users) – Build from Source
8. Setup CycloneDDS
9. Build your workspace
10. Installing the webapp
11. Running the Software
12. Work in Progress Notes
13. Troubleshooting

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

