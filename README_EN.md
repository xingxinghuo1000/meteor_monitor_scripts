## Introduction

Meteor shower monitoring program

The goal is to replace ufohd2capture and can be used on small machines with relatively low configurations.

Compared with the advantages of ufocapturehd2, it requires lower configuration


After testing, it can run 30FPS 1920x1080 video on a 2.4GHz 4-core 4-thread CPU (Intel J2900)



## Recommended hardware

Host:

Windows system, win10 win11. Small host, cpu 2.4GHz, 4 cores.

Linux systems are not recommended because the graphics card driver is not easy to install and requires a high technical level.

Raspberry Pi is not recommended for the same reason as Linux system.



### disk space


If you use h264 encoding for recording

Single channel recording, mechanical hard drive 200GB is enough

For dual-channel recording, a mechanical hard drive with a capacity of 500GB is most likely acceptable. A solid-state drive is more recommended.

Three-way recording requires you to try and explore. I haven’t tried it either. I guess a 1TB solid-state drive can guarantee stable recording.



If you use mjpeg encoding for recording

The disk space required is twice that of h264.



### Camera selection


It is recommended to use Sony IMX291 camera. The CMOS base is relatively large and suitable for shooting stars.

If the CMOS size of your camera is too small, there will be more noise. Therefore, IMX291 is recommended. If you use IMX485, it will be better.



## how to use


It is recommended to use it in Windows because the graphics driver is easier to install. It is difficult to install the Intel core graphics driver under Ubuntu, and h264_qsv encoding cannot be used.



This program uses mjpeg code stream by default. If the CPU supports hardware encoding h264, you can try to use the h264_qsv encoder


If it is a windows environment and it is an Intel core graphics card, you can try h264_qsv encoding, nvdia graphics card try h264_nvenc, amd graphics card try h264_amf

If it is an Ubuntu environment, please try mjpeg encoding. After my testing, a 2.4GHz CPU can only achieve 15fps. If it needs to be higher, such as 30fps, the CPU requirements will be very high.

If you are in Ubuntu environment and have installed the graphics card driver, you can try h264_qsv encoding for Intel core graphics cards, h264_nvenc for nvdia graphics cards, and h264_amf for amd graphics cards.

If it is a Raspberry Pi and ffmpeg with h264_omx encoding is compiled, the encoder uses h264_omx


### Install ffmpeg

This program relies on the ffmpeg command,

I have only tested the 4.x.x version of ffmpeg so far. I cannot guarantee that 5.x and 6.x will also work properly.

For Windows environment, you need to download the ffmpeg executable program from the ffmpeg official website (https://ffmpeg.org/download.html), download the compressed package, decompress it to a directory, and add the directory to the environment variable. How to verify whether the installation is successful , you can open cmd and enter ffmpeg -v to see if you can see the output version number normally.

Linux environment, sudo yum install ffmpeg or sudo apt install ffmpeg, verification method, enter ffmpeg -v in the shell to see if the version number is displayed normally

If it is a Raspberry Pi, you need to manually compile ffmpeg and enable h264_omx encoding, which is quite troublesome and not recommended.





### Plug in USB camera
                                                                                                                                   
Insert the USB camera into the USB port of the host computer and execute the following command to check whether the system can recognize the camera normally.
                                                                                                                                   
In Windows, open cmd and enter ffmpeg -list_devices true -f dshow -i dummy to see the returned results
                                                                                                                                   
In Linux system, enter ffmpeg -hide_banner -sources v4l2 in the shell to see the return result




## How to modify the configuration file .config

Refer to the .config.xx file, which corresponds to your operating system. There are instructions in the configuration file.
                                                                                                                                   
For example, in win11 system, you can refer to .config.win
 
If it is an Ubuntu system, you can refer to .config.linux



                                                                                                                                   
## Description of .config file


To view specific instructions, you need to look at the existing remarks in the .config file. Only the more critical contents are listed here.



### DEVICE_NAME

This configuration is used to specify which camera to use,

If it is a Linux system, it may be something similar to /dev/video0. You need to try more specifically.




###ENCODER

Set the encoding format of the recorded video. For details on how to configure it, see the "How to use" section.

### LATITUDE LONGITUDE

GPS coordinates of your location,

You can use search engines to get your approximate geographical location. First, know the coordinates of your country's capital, and then calculate the approximate location of your city. Then you can further check your coordinates through search engines or apps such as Google Maps. Fill in Configuration file
                                                                                                                                   
If you do not fill it in, the default location is the coordinates of Beijing, China.


                                                                                                                                   
### IP_ADDR

You can leave it blank by default, and the program will automatically obtain it.



###PYTHON_BIN
                                                                                                                                   
The location of your python executable file, full path
                                                                                                                                   
If it is a windows system, we recommend using the venv function, then .\venv\Scripts\python should be filled in here
                                                                                                                                   
If it is a Linux system, we also recommend using the venv function, so ./venv/bin/python should be filled in here.


If you don't use venv,
                                                                                                                                   
Windows needs to fill in the full path, such as D:\python311\python
                                                                                                                                   
Linux needs to fill in the full path, such as /usr/bin/python3



### EXECUTOR_NUM

During offline analysis, how many processes are used for parallel execution? If your system configuration is relatively high, you can try setting it to 4 or 8.
                                                                                                                                   
If your system configuration is relatively low, such as a small mini host, set it to 1



### ENABLE_FTP_SERVER
                                                                                                                                   
Whether to enable the ftp service, it is not enabled by default. If you want to enable it, set it to 1. But you need to pay attention to modifying the password in the source code. The default password is 123456, which is relatively simple and easy to be attacked.




## How to set resolution and fps?
                                                                                                                                   
According to your own hardware performance, gradually adjust fps to a usable level. If the ffmpeg log indicates frame loss, the fps setting is too large and you need to reduce fps to ensure a smooth picture.

It also depends on which resolutions the camera supports. If the settings are wrong, video cannot be recorded.



## View camera information



Question: I don’t know the name of my camera, what should I do?

You can execute the script to check which cameras are currently connected to the system and display the camera names.

For Windows systems, double-click show_video_device.bat in the detect_meteor directory

For Linux systems, cd detect_meteor, execute sh show_video_device.sh

Note: If you only have one camera connected to your current device, you don’t need to configure it in Windows. In Linux, you must configure it. You can try it from /dev/video0.



Question: I don’t know what resolutions and fps my camera supports, what should I do?

answer:                                                                                                                              

The default is automatic recognition. You can not configure it, so that the highest resolution supported by the camera will be used by default.

                                                                                                                                   
If you want to specify resolution and fps:

First configure the camera name. If you only have one camera, you do not need to configure it, or the configuration is empty.
                                                                                                                                   
For Windows systems, double-click show_video_format_support.bat in the detect_meteor directory

For linux systems, cd detect_meteor, sh show_video_format_support.sh
                                                                                                                                   
Based on the displayed information, check which resolutions and fps the camera supports. Configure it in the .config file
                                                                                                                                   


                                                                                                                                   

## Configure Python environment
                                                                                                                                   
Version: Python 3.10 and above recommended



### step 1
                                                                                                                                   
Create a new virtual env.
                                                                                                                                   
under windows,
                                                                                                                                   
In the explorer, right-click in the blank space of the detect_meteor directory -> run cmd here.

It is assumed that your Python is installed in the D:\python311 directory

In the pop-up command, enter D:\python311\python.exe -m venv venv.



Under Linux,

cd detect_meteor, python3 -m venv venv




### Step 2

Install dependencies
                                                                                                                                   
For windows system,

In the detect_meteor directory, double-click install_dep.bat

                                                                                                                                   
For Linux systems,
                                                                                                                                   
In the detect_meteor directory, execute the command sh install_dep.sh




### Step 3

Run this program

Under windows, double-click offline_detect_from_mp4.bat

Under Linux, in the detect_meteor directory, execute sh run.sh




### Step 4
                                                                                                                                   
Configure automatic startup at boot,
                                                                                                                                   
Under Windows, right-click offline_detect_from_mp4.bat, send to desktop shortcut, and copy the shortcut to the startup directory of the start menu.
                                                                                                                                   
Under Linux, configure */5 * * * * cd /home/yourname/workspace/meteor_monitor_script/detect_meteor && sh run.sh in crontable




### Step 5 Optional
                                                                                                                                   
Configure the mask-1280-720.bmp mask image to exclude some non-sky parts of the picture, which may cause False Positive and false alarms of meteors.
                                                                                                                                   
For example, changes in the lighting of distant buildings in the picture may make the program think that there is a change in the picture.

Question: In which directory do I create a new mask image?

Answer: In the video target output directory, in the base_output_path option of the configuration file, the path is specified by you

Question: What does it mean when the mask image is black and white?
                                                                                                                                   
Answer: Black indicates the part to be covered, and white indicates the part to be detected.






## Principle introduction

                                                                                                                                   
### Efficiently record mp4 videos

Use ffmpeg to record videos efficiently. I don’t have enough ability to use python to implement this part, so I use the ability of ffmpeg

ffmpeg supports multiple encoding formats, and h264 supports multiple hardware accelerations, such as Intel core graphics, nvdia graphics, and AMD graphics.

Note: I once used a solution to record videos using the camera app that comes with Windows. This solution was not stable enough and has been abandoned. This solution uses sikuli for UI automation, which is very unstable.





### Offline analysis of meteors

Why not do real-time analysis?

Because the hardware performance is not enough. My purpose is to run this program on low-configuration hardware. If your hardware performance is already very powerful, it is recommended to use ufohd2 directly.




Principles of offline analysis
                                                                                                                                   
step 1                                                                                                                              
                                                                                                                                   
Use the typical opencv motion detection algorithm: frame difference method to identify changes in the picture

Step 2

Based on some characteristics, filter out things that are not meteors, such as bats, small flying insects, etc.

Step 3
                                                                                                                                   
Use ffmpeg to slice the original video and store it separately after slicing





