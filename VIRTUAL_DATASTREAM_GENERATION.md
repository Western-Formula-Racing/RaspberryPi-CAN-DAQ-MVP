# Virtual CAN Datastream Generation
If you don't have the hardware, you can still generate a reliable datastream and build a DAQ testbed, right from the comfort of your own virtual machine. This uses virtual CAN interfaces provided by the SocketCAN Linux module to mimick a physical CAN controller, combined with tools from `can-utils` to generate the datastream.  

## Depedencies
- ``can-utils`` package (use command `sudo apt-get install can-utils`)
- ``net-tools`` package (use command `sudo apt-get install net-tools`)
- ``vcan`` linux module (use command `sudo modprobe vcan`, it should return nothing)

## Initialize Virtual CAN Network Interface 
First, a virtual CAN (vcan) interface must be initialized to emulate the exposure of the physical interface of a real CAN connection to the operating system. CAN interfaces, as used in the above section on drivers, are the real CAN connection equivalent of this. 

To do this, use this command: `sudo ip link add type vcan`, which uses the iproute2 Linux command-line utility to initialize a ``vcan`` interface, just as if you'd initialize any TCP or UDP interface. 

The default naming scheme for creation of this interface is `vcanX`, where X is the current number of other vcan's you have running on the machine.

You can **delete** this interface with the command `sudo ip link del vcan0`.

After the interface is created, it still needs to be turned on. To do this, we set it to an up state by using the command: `sudo ip link set up vcan0`. 

To view details about the interface, you can use the command `ifconfig vcan0`. If things go right, you will see something like this:

<img src="https://user-images.githubusercontent.com/70295347/234086585-22eea4eb-9471-43dc-84d5-902ed370da38.png" width="800">

## Maximum Transmission Unit (MTU)
The default MTU of `vcan0` is 72 bytes. Since we are using classic CAN and not CAN Flexible Data-rate (CAN FD), we only need an MTU of 16 bytes. 

To change this, we need to 1. turn off the interface, 2. change MTU setting to 16, 3. turn the socket on again:  

<img src="https://user-images.githubusercontent.com/70295347/234093116-df71077a-3e69-456f-9da8-b466f780489e.png" width="800">

This doesn't change much, but I thought it worth noting in case CAN FD is considered/necessary/implemented in the future. Also, it helps you understand that the socket is similar to a faucet in that once it's on, it needs to be turned off first if you want to alter it.

## Generate the Datastream
Next, the datastream is generated using the `cangen` tool from the `can-utils` package.

To generate a stream of random data over the `vcan0` interface, you can use the command `cangen vcan0`. Nothing will happen in the terminal -- you will have the cursor blinking at you on a blank line, not able to type anything in the terminal -- but something is happening inside the machine.

To view the output of the datastream over the `vcan0` interface, allow the `cangen` process to operate in the current terminal tab/window, and open a new terminal tab/window.

In that new terminal, use the command `candump vcan0`. If everything is working properly, you'll see something like this:

<img src="https://user-images.githubusercontent.com/70295347/234086888-a2c09447-c1af-425d-b4a5-947ca0de0191.png" width="800">

The columns represent, respectively, the name of the interface, the ID of the device sending the message, the [size of the data in bytes], and the bytewise data itself. 

## Using the Virtual Datastream with DAQ Software
Now that we have a datastream running, we need to allow our DAQ software to use it, in lieu of the physical CAN interface it was designed to accomodate.

Firstly, the CAN protocol specified for use in `canInterface` takes only CAN frames originating from a device with the ID `0x036`. This detail is found in the `filters` object declaration in `canInterface`. 

**[Optional theory for further conceptual clarification, feel free to skip paragraph]** These filters will eventually route down the chain of abstraction into the Linux kernel via the SocketCAN API into the CAN device driver. If a real CAN controller is connected, the filter is applied directly to this electrical device to physically accept or reject CAN frames by using a minterm of the binary representation of the ID specified in this object. This is simulated in the software-only rendition of things also, since `vcan` mimicks a physical CAN controller, as mentioned earlier.

Anyway, this means we need to generate CAN data using only this fixed identifier in the CAN header. So, where before we had random identifiers somewhere in the valid CAN ID range, we will now only have a CAN identifier of `0x036`. This is done simply by running `cangen vcan0`, using the additional flag, `-I 036`. 

Next, the code CAN socket needs to use `vcan` instead of the regular CAN interface. Since `vcan` is provided with SocketCAN, all we do is change the `channel` parameter in the interface instantiation to `vcan0`. With virtual CAN, we don't need to worry about bitrate, so we remove this parameter. Filters stay, since they are CAN protocol-dependent, and we want this testbed to represent the real CAN protocol used in the car, as closely as possible. For your convenience, the `channel = vcan0` instantiation has been provided in `canInterface.py`, but commented out. Simply uncomment it, and comment the `channel = can` instantiation, and start the program as normal. Try to avoid committing to the main branch the `channel = vcan` version if you can. (That's mostly a message to me... :)

After that, install everything in `root/pythonAPI` with `pipenv install` as above, enter the shell via the command `pipenv shell`, and then run the program using `python3 canInterface.py`. Note that the program requires an installation of Python 3.9, and if you're on Ubuntu 22.02, you'll need to use add [deadsnakesPPA]() repository to your apt upstream to get it. Use `update-alternatives` to allow coexistence with other Python version. [This is a helpful article,](https://web.archive.org/web/20230424193817/https://towardsdatascience.com/installing-multiple-alternative-versions-of-python-on-ubuntu-20-04-237be5177474?gi=b452d19fbee6) even though it's for an older version of Ubuntu. 

# Weird Behaviour?
I think things are working nominally now, but Mosquitto is still broken. I am going to try and fix this.

# Information Sources
- https://python-can.readthedocs.io/en/stable/interfaces/socketcan.html
- https://docs.kernel.org/networking/can.html 

# [Optional] Brief SocketCAN/OS Theory
Drivers allow the operating system's kernel (software) to interface with peripheral devices (hardware). 

Drivers are normally not accessible from the user space of the OS (the space we are currently programming in) because they are sensitive components of the machine, and require special treatment by the OS's core. Hence, they remain entirely under the kernel's control, where the kernel is layer below the user space. The kernel is effectively the brain of the operating system.

The question naturally arises: "how do we use peripheral devices from a user space program if we don't have control of the software that runs those devices?". The answer is *system calls* -- calls from the user space to the kernel asking for a specific functionality, with kernel functionality exposed via an API. 

More accurately, it is exposed via a set of APIs. Sockets are an example of a Linux network layer API from the user space to the kernel. The Linux network layer in the kernel is what actually takes care of most of the nitty gritty software-hardware communication. In SocketCAN, the driver controlling the physical CAN controller is in a sublayer of the Linux kernel, below the network layer. SocketCAN introduces support for the CAN protocol, but *in the network layer*, so there is now software control over the CAN controller with the Linux network layer, which makes CAN much easier to work with in the user space. 

You as the programmer don't need to worry about the complexity of writing code to handle queuing of CAN messages. You also can read from MANY can devices at a time, since each "socket" is basically a connection with a unique device, and you can have thousands of sockets going at a time, all of them orchestrated and controlled by the beautiful Linux kernel. This is a tremendous feat of systems programming, and saves us from having to dive into networking hell in the user space.      
