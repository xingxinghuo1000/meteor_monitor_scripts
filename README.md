

## 简介

流星雨监控程序
目标是代替ufohd2capture，可以用于配置比较低的小机器
相对于ufocapturehd2的优势， 需要配置较低

在2.0GHz的2核心4线程 cpu(Intel J2900)上，可以跑30FPS 1920x1080 视频



## 推荐硬件

主机: 

windows系统,win10 win11. 小主机, cpu 2.4GHz, 4核心. 

不推荐Linux系统, 因为显卡驱动不容易安装,需要较高的技术水平.

不推荐树莓派, 原因同Linux系统. 



摄像头的选择: 

推荐使用 索尼 MX291 摄像头. CMOS底比较大,适合拍摄星空

如果您的摄像头CMOS尺寸太小, 则噪点会比较多. 所以推荐IMX291这款, 如果使用IMX485, 则更好.



## 如何使用


建议在windows使用,原因是显卡驱动程序比较容易安装. 在Ubuntu下intel核心显卡驱动安装比较困难,无法使用h264_qsv编码



本程序默认使用mjpeg码流， 如果cpu支持硬件编码h264，则可以尝试使用h264_qsv编码器


如果是windows环境 , 且是 Intel核心显卡, 则可以尝试h264_qsv编码, nvdia显卡尝试 h264_nvenc, amd显卡尝试 h264_amf

如果是Ubuntu环境, 请尝试 mjpeg 编码, 经过我的测试, 2.4GHzCPU 只能达到15fps, 如果需要更高比如30fps,则对CPU要求也会很高.

如果您在Ubuntu环境,安装好了显卡驱动程序, Intel核心显卡可以尝试 h264_qsv 编码, nvdia显卡尝试 h264_nvenc, amd显卡尝试 h264_amf

如果是树莓派, 且编译了带h264_omx编码的ffmpeg, 则编码器使用 h264_omx


### 安装ffmpeg

本程序依赖ffmpeg命令, 

Windows环境,需要到ffmpeg官网下载ffmpeg可执行程序, 下载压缩包,解压缩到某个目录, 并将目录添加到环境变量. 如何验证安装是否成功, 可以打开cmd, 输入 ffmpeg -v 看看是否能正常看到输出的版本号

Linux环境, sudo yum install ffmpeg 或者 sudo apt install ffmpeg, 验证方法, 在shell中输入 ffmpeg -v 看看是否正常显示版本号

如果是树莓派, 则需要手工编译ffmpeg, 启用h264_omx编码, 比较麻烦, 不推荐.


### 插入usb摄像头

将usb摄像头插入主机的usb口, 执行下面的命令, 检查系统是否能正常识别摄像头

Windows中, 打开cmd 输入  ffmpeg -list_devices true -f dshow -i dummy 看看返回结果

Linux系统中, 在shell中输入  ffmpeg -hide_banner -sources v4l2 看看返回结果



## 如何修改配置文件.config

参考.config.xx文件,对应你的操作系统, 配置 文件中都有说明

比如win11系统,可以参考.config.win

如果是Ubuntu系统,可以参考.config.linux


如何设置分辨率和fps?

根据自己的硬件性能,逐步调整fps到可用的程序

还要看摄像头支持哪些分辨率.如果设置错误,则无法录制视频


### 查看摄像头信息


根据ffmpeg显示出来的信息, 查看摄像头支持哪些分辨率和fps. 配置到.config 文件中



## 配置Python环境

版本: 推荐使用Python 3.10及以上


### 步骤1

新建virtual env. 在 detect_meteor目录下, 执行如下命令

windows下, python3 -m venv venv

Linux下, python3 -m venv venv


### 步骤2

安装依赖

windows下, 打开 cmd,  在 detect_meteor 目录下, 执行命令  .\venv\Script\python  -m pip install -r requirement.txt

Linux下, 在 detect_meteor目录下, 执行命令 ./venv/bin/python -m pip install -r requirement.txt


### 步骤3

运行本程序

windows下, 双击 offline_detect_from_mp4.bat 

Linux下, 在detect_meteor目录下, 执行 sh run.sh


### 步骤4

配置开机自动启动, 

Windows下, 右键点击 offline_detect_from_mp4.bat, 发送到桌面快捷方式, 将 快捷方式,复制到 开始菜单的 启动 目录

Linux下, crontable中配置 */5 * * * *  cd /home/yourname/workspace/meteor_monitor_script/detect_meteor && sh run.sh 


