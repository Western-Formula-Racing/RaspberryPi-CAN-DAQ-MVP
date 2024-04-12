# WFR Data Acquisition System
This repository stores the code and other software resources defining the WFR Data Acquisition System (DAQ). 

## Key Assumption
A key assumption with the system is that it exists connected to a secure network. If not, disabling the WiFi adapter on the Pi and reverting to Ethernet only as a means of connecting to the DAQ is advised.

## Hardware Setup
For hardware setup, please refer to the following excerpt from [THEORY_README.md](./documentation/old_but_useful_for_problem_solving/THEORY_README.md): 

### Physical Layer
#### CAN Interface
This project has been tested to work with a MCP2515-based CAN Bus board, which connects to `SPI0` on the Raspberry Pi Model 4B:  

<img src="https://user-images.githubusercontent.com/25854486/209448905-cbbaac77-50bf-4a75-8132-85bc5a5c5922.png" width="200"> 

The pin connection is as follows:
| MCP2515 Module| Raspberry Pi Pin #| Pin Description  |
| ------------- |:---------------------:| :-----:|
| VCC           | pin 2                 |5V (it's better to use external 5V power)|
| GND           | pin 6                 |   GND |
| SI            | pin 19                |    GPIO 10 (SPI0_MOSI)|
| SO            | pin 21                |    GPIO 9 (SPI0_MISO)|
| SCK           | pin 23                |    GPIO 11 (SPI0_SCLK)|
| INT           | pin 22                |    GPIO 25 |
| CS            | pin 24                |    GPIO 8 (SPI0_CE0_N)|

#### Raspberry Pi System Storage
Due to the relatively rapid read/write speed requirements of the data acquisition use case, a Samsung T7 external SSD is used as the main storage volume. 500 GB storage capacity is recommended, but more is always welcome. The SSD connects to the Raspberry Pi using a USB-C-to-USB-A 3.1 cable. For connection integrity, it is important that the SSD and Raspberry Pi are packaged as a unit, such that the accelerations experienced by the SSD and the Pi are similar. Otherwise, high-variation cable strain may cause physical damage to the SSD, the cable, the Raspberry Pi, or some combination thereof. Even transient disconnection of the SSD could cause catastrophic data loss. Hence, data should be backed up and extracted from the unit as frequently as possible. 

### Driver Layer
#### SocketCAN 
This project heavily relies on [SocketCAN](https://docs.kernel.org/networking/can.html) which is the Linux kernel's default CAN Bus interface implementation. It treats CAN Bus interface devices similar to regular network devices and mimics the TCP/IP protocol to make it easier to use. It also natively supports MCP2515 based controllers. Since this is built-in, nothing needs to be installed, however the `/boot/config.text` needs to have the following line appended to it:
```
dtoverlay=mcp2515-can0,oscillator=8000000,interrupt=25 
```  
This gets the Linux kernel to automatically discover the CAN Controller on the SPI interface. If your interface pin has a different oscillator frequency, you can change that here.  

Now reboot the Pi and check the kernel messsages (you can bring this up in the terminal by using the command: `dmesg | grep spi)` or `dmesg` to view all kernel messages), and you should see the following:
```
[    8.050044] mcp251x spi0.0 can0: MCP2515 successfully initialized.
```  

Finally, to enable the CAN Interface run the following in the terminal:
```
 sudo /sbin/ip link set can0 up type can bitrate 500000 
```  

If you are using a different bitrate on your CAN Bus, you can change the value. You'll need to edit the declarations of `bus_one` and `bus_two` in `data_logger/canInterface.py` to match the new bitrate. 

You will need to run this command after every reboot, however you can set it to run automatically on startup by appending the following to the `/etc/network/interfaces` file:
```
auto can0
iface can0 inet manual
    pre-up /sbin/ip link set can0 type can bitrate 500000 triple-sampling on restart-ms 100
    up /sbin/ifconfig can0 up
    down /sbin/ifconfig can0 down
```  

And that's everything to get the CAN Bus interface working! Since SocketCAN acts like a regular network device, we can get some statistic information by using the `ifconfig` terminal command, which can be obtained with the `net-tools` package using `sudo apt-get install net-tools`.  

#### CAN-utils
[CAN-utils](https://github.com/linux-can/can-utils#basic-tools-to-display-record-generate-and-replay-can-traffic) is a set of super useful CAN debugging tools for the SocketCAN interface. You can install it using the following command:
```
 sudo apt-get install can-utils 
``` 
This allows us to dump CAN Bus traffic to logs, send test messages and simulate random traffic. Please see the readme on their GitHub page for more details.

## Software Environment

### Operating System
Connect the SSD/storage volume to a host computer. Use [Raspberry Pi Imager](https://www.raspberrypi.com/software/) to install Raspberry Pi OS on the volume. Make sure to configure SSH, network, and administrator settings before the Raspberry Pi Imager installation process. Ensure the hostname *(default: "raspberrypi")* of the device is noted **and saved to the `.env` file under the `RPI_HOSTNAME` environment variable.** 

### Network
The Raspberry Pi does not need to be connected to a Layer-3 (IP) communications network to function. However, it is highly recommended that it is. Without connection to a network, data egress, data visualization, and system monitoring are deeply impeded, if not impossible. 

Raspberry Pi can connect to IP networks using WiFi or wired Ethernet. WiFi is vastly more convenient, but note that on networks with high network segregation (e.g., secured enterprise networks, like Western's), interdevice connectivity may not be possible. Hence, it is recommended that an external network is established using a router. The network does not need to be connected to the internet for DAQ use, but the DAQ **does** need an internet connection for initial software setup and updates. 

## Software Setup

**It is expected that the reader is relatively familiar with SSH and SFTP for remote access to the Raspberry Pi.** If not, please refer to the internet for a guide on connecting to a Raspberry Pi via SSH. The recommended application for development is [MobaXTerm](https://mobaxterm.mobatek.net/) on Windows, and [Royal TSX](https://www.royalapps.com/ts/mac/download) on MacOS. These applications are capable of multi-tabbed operation, so many SSH terminals and SFTP file transfer sessions may be open at a time. **The following assumes SSH and SFTP are established and accessible by the user.**

### Cloning the Project
On your own computer (Host), use Git CLI to clone the repository, or download as a zip. Duplicate `.env.example`, rename it `.env`, and add a value for the `INFLUX_PASSWORD` environment variable. Save after editing. Don't worry about the `INFLUX_TOKEN` environment variable for now.

On the Raspberry Pi (RPi), create a folder in the home (`~/`) directory called `daq` with the command `mkdir ~/daq`.

On Host, establish an SFTP session with RPi, and transfer the cloned repository to `~/daq/` on RPi.

### Install Docker
Follow the steps [here](https://docs.docker.com/engine/install/debian/#install-using-the-repository) to install Docker on the RPi.

### Starting the Project
On RPi, navigate to the `daq` folder with the command, `cd ~/daq`. Run the command `docker compose up -d` to build the containers required for the application, and link the containers together. 

You can shut down the application by navigating to the `~/daq` folder and executing the command, `docker compose down -v`. 

### Initializing InfluxDB
First, a database bucket and an authentication token must be generated from InfluxDB. To do this:
1. Run command, `docker exec -it wfrdaq-influxdb-1 /bin/bash`, to get command-line access to the container
2. Set up InfluxDB by running the command: 
```
influx setup \
    --username $INFLUX_USERNAME \
    --password $INFLUX_PASSWORD \
    --org $INFLUX_ORGANIZATION \
    --bucket $INFLUX_BUCKET \
    --force
```
3. Get the authorization token by running the command:
```
influx auth list \
    --user $INFLUX_USERNAME
    --hide-headers | cut -f 3
```
4. Copy the string output from step 3, and on the Host computer, paste this into `.env` as the value for `$INFLUX_TOKEN`, and save the `.env` file 
5. From the InfluxDB command line, go back to the Pi's CLI by entering the command, `exit`
6. Shutdown the docker project (from within the `~/daq` directory) with the command `docker compose down -v`
7. Transfer the `.env` file with the `$INFLUX_TOKEN` environment variable from Host to `~/daq` on RPi
8. Recompose the Docker project with `docker compose up -d`

InfluxDB is now set up.

### Initializing Grafana

1. On Host, open a web browser, and navigate to the URL, `http://raspberrypi.local:3000/`, replacing "raspberrypi" with the hostname you selected during Raspberry Pi OS installation if you changed it from the default
2. Enter "admin" for both prompts
3. Change the password to whatever password you chose for the `$INFLUX_PASSWORD` environment variable
4. Click the stacked vertical bars in the top left, expand the "connections" item in the dropdown, and click "add new connection"
5. Search "influxdb", click it, and then click the "add new data source" button 
6. Set the following:
    - Query Language: `Flux`
    - URL: `http://influxdb:8086`
    - User: `grafana`
    - Password: whatever password you set for the `$INFLUX_PASSWORD` environment variable in .env file
    - Organization: whatever organization you set for the `$INFLUX_ORGANIZATION` environment variable in .env file 
    - Token: whatever token was generated in [Initializing InfluxDB](#initializing-influxdb)
    - Default Bucket: `RaceData`
8. Click "save & test" in the bottom. You should see a box appear at the bottom of the screen that says "datasource is working. 0 measurements found" with a green checkmark on the left. This means the connection from Grafana to InfluxDB is working
9. Click "add new connection" on the left-hand side of the page, then search for "MQTT" and click it
10. On the MQTT data source page, click the "install" button. After installed, click the "add new datasource" button
11. On the configuration page, for the "URL" field, enter `tcp://mqtt_broker:1883`, and click "save & test". You should get the same confirmation box in as in step 8

#### Grafana Dashboards
Now you can make visualizations in Grafana with MQTT and influxdb data sources. Note that MQTT topic subscription is case-sensitive. Also, MQTT topics are defined as [CAN Device Name as per DBC]/[Measurement Name], e.g. "Sensor_board_2_1/Sensor1". 

For panels where InfluxDB is the data source, you'll need to use Flux queries to get data from the DB. Most common operations can be done by changing some values in the templates you get when selecting "sample query" in the "query" tab when creating a new panel:  
<img src="https://github.com/Western-Formula-Racing/daq-2023/assets/70295347/988ee54d-a6a1-4b96-b74d-b40735aba74d" width="500">

In the above example, the base query was "simple query", and I just changed the bucket name to our main bucket's name, the measurement name to the device I'm interested in querying, and the field I want to look at. `v.timeRange[...]` are taken from grafana's time range settings:  
<img src="https://github.com/Western-Formula-Racing/daq-2023/assets/70295347/7ca7c7a1-02a0-48e1-ad43-9fb5f8cf25c2" width="500">

The Flux language reference can be found by clicking the "Flux language syntax" button near the query field of the grafana panel addition window. **Make sure to save dashboards frequently.**

### DAQ User Interface
The DAQ user interface is provided by a web application, which can be accessed from a computer attached to the same network as the Raspberry Pi. On a web browser, enter the URL: `http://[hostname].local`. If the Raspberry Pi's hostname as selected in the Raspberry Pi Imager is `raspberrypi`, the link is [http://raspberrypi.local](http://raspberrypi.local). As long as the Docker project is composed, you'll be able to access the site. It will look like this:  

<img src="https://github.com/Western-Formula-Racing/daq-2023/assets/70295347/a7f3740e-2d41-49f7-a55e-c6861e5aff2f" width="500">  

The UI is self-explanatory. The webpage refreshes once every minute to update the session hash to make sure it's reflective of the current state.  

Currently, CSVs are the only download method. Motec LD downloads will be added in the near future.  

### Testing Software Configuration with Virtual CAN Datastreams
Refer to the document, [VIRTUAL_DATASTREAM_GENERATION.md](./documentation/VIRTUAL_DATASTREAM_GENERATION.md), for information about how to do this.

### Motec Conversion
Motec log generator was originally written by stevendaniluk and is available here: https://github.com/stevendaniluk/MotecLogGenerator. 

## External SSD
1. Connect SSD to pi
2. Do command lsblk and find the appropriate device/part that corresponds to your external SSD. Mine had the disk name "UNTITLED" here:  

<img src="https://github.com/Western-Formula-Racing/daq-2023/assets/70295347/565edff4-68ae-472f-9c12-585c70d25e4c" width="200">  

3. Reformat the disk: sudo mkfs -t ext4 /dev/sda1. If it's mounted, unmount it with umount /dev/sda1, then try the mkfs command again  

4. Do lsblk -f, find and note the UUID

<img src="https://github.com/Western-Formula-Racing/daq-2023/assets/70295347/0fdf0884-22c3-4aa8-ad7e-653d8f1a6039" width="500">  

5. Edit fstab to automatically mount the disk if it's available at boot with sudo nano /etc/fstab. Add the line: 

UUID=[uuid from step 4] /home/pi/daq-2023 ext4 defaults,nofail 0 0  

6. Make the daq-2023 folder with mkdir /home/pi/daq-2023

7. Reload fstab config with sudo systemctl daemon-reload  

8. Mount the drive with sudo mount /dev/sda1 /home/pi/daq-2023  

9. Change the ownership of the mountpoint with sudo chown pi /home/pi/daq-2023  

10. Go into daq-2023 directory with cd /home/pi/daq-2023, and then create a test document with touch test.txt. You should be able to do this without the sudo command

11. Add content to the test document with nano test.txt, type something, and then save with ctrl+s. 

12. Reboot the pi to test that A. the SSD is automounted, and B. that the test.txt file has the same contents as before. Reboot with sudo shutdown -r now  

13. When the pi boots up again, cd back into /home/pi/daq-2023, and do nano test.txt to make sure the file exists and that it has the same content as before. This verifies the addition of an externally mounted SSD and a correct fstab config. 

14. Clone the daq-2023 GitHub repository into the /home/pi/daq-2023 folder with git clone https://github.com/Western-Formula-Racing/daq-2023.git 

15. A new folder is created inside /home/pi/daq-2023, also called daq-2023

If booting with an SSD that does not have its filesystem UUID entered in the fstab configuration, or if no SSD is connected, the Raspberry Pi will still boot properly because of the nofail option we had in the fstab config. The DAQ software will not run, assuming the DAQ software is stored on the SSD. Follow the above steps with your new SSD to get it working properly.