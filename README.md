

## 简介

流星雨监控程序
目标是代替ufohd2capture，可以用于配置比较低的小机器
相对于ufocapturehd2的优势， 需要配置较低

在2.0GHz的2核心4线程 cpu上，可以跑30FPS 1920x1080 视频



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


## 如何修改配置文件.config

参考.config.xx文件,对应你的操作系统, 配置 文件中都有说明

比如win11系统,可以参考.config.win

如果是Ubuntu系统,可以参考.config.linux


如何设置分辨率和fps?

根据自己的硬件性能,逐步调整fps到可用的程序

还要看摄像头支持哪些分辨率.如果设置错误,则无法录制视频


### 查看摄像头信息


根据ffmpeg显示出来的信息, 查看摄像头支持哪些分辨率和fps. 配置到.config 文件中


