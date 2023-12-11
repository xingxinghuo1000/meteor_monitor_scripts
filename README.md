

## 简介

流星雨监控程序

目标是代替ufohd2capture，可以用于配置比较低的小机器

相对于ufocapturehd2的优势， 需要配置较低


经测试, 在2.4GHz的4核心4线程 cpu(Intel J2900)上，可以跑30FPS 1920x1080 视频



## 推荐硬件

主机: 

windows系统,win10 win11. 小主机, cpu 2.4GHz, 4核心. 

不推荐Linux系统, 因为显卡驱动不容易安装,需要较高的技术水平.

不推荐树莓派, 原因同Linux系统. 



### 磁盘空间


如果使用h264编码进行录制

单路录制, 机械硬盘200GB即可

双路录制, 机械硬盘500GB大概率也可以, 比较推荐固态硬盘

三路录制, 需要您进行尝试和探索, 我也没试过. 猜测1TB固态硬盘才能保障稳定录制



如果使用mjpeg编码进行录制

需要的磁盘空间是h264的两倍即可



### 摄像头的选择


推荐使用 索尼 IMX291 摄像头. CMOS底比较大,适合拍摄星空

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

我目前只测试过 4.x.x 版本的ffmpeg, 不能保证 5.x 和 6.x也能正常工作

Windows环境,需要到ffmpeg官网(https://ffmpeg.org/download.html) 下载ffmpeg可执行程序, 下载压缩包,解压缩到某个目录, 并将目录添加到环境变量. 如何验证安装是否成功, 可以打开cmd, 输入 ffmpeg -v 看看是否能正常看到输出的版本号

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


## .config 文件的说明

要查看具体说明,需要看.config文件中已有的备注内容, 这里仅列出比较关键的内容

### DEVICE_NAME 

该配置用于指定用哪个摄像头,

如果是linux系统,则可能是/dev/video0类似的内容,具体需要您多尝试


### ENCODER

设置录制视频的编码格式, 具体如何配置,参见 "如何使用" 部分的内容

### LATITUDE LONGITUDE

您所在位置的 GPS 坐标, 

您可以通过搜索引擎, 来获取您的大概地理位置, 首先知道您国家的首都的坐标, 进而推算您的城市大概得位置, 然后进一步通过搜索引擎或者 谷歌地图等app, 查看您的坐标. 填入配置文件

如果您不填写,则默认的地点, 是中国北京的坐标

### IP_ADDR

默认可以不填写，  程序会自动获取


### PYTHON_BIN

您的python可执行文件的位置,全路径

如果是windows系统, 我们建议使用venv功能, 则这里应该填写 .\venv\Scripts\python

如果是Linux系统,我们也建议使用venv功能, 则这里应该填写./venv/bin/python


如果您不使用venv,

windows需要填写全路径,比如D:\python311\python

Linux需要填写全路径,比如 /usr/bin/python3

### EXECUTOR_NUM

离线分析时, 使用多少个进程并行执行,如果您的系统配置比较高,则可以尝试设置为4或者8

如果您的系统配置比较低,例如小型mini主机, 则设置为1

### ENABLE_FTP_SERVER

是否开启ftp服务, 默认不开, 如果您想开启,则设置为1. 但需要注意修改源代码中的密码, 默认密码是123456, 比较简单,容易被攻击


### FTP_BASE_DIR

ftp服务的根目录

搭配 ENABLE_FTP_SERVER 选项一起使用. 当且仅当ENABLE_FTP_SERVER设置为1时有效.





如何设置分辨率和fps?

根据自己的硬件性能,逐步调整fps到可用的程度. 如果 ffmpeg 日志中提示丢帧, 则fps设置过大, 需要降低fps, 以保证画面流畅

还要看摄像头支持哪些分辨率.如果设置错误,则无法录制视频



### 查看摄像头信息



问题: 我不知道我的摄像头叫什么名字, 怎么办?

可以执行脚本, 来查看系统当前连接了哪些摄像头, 显示出摄像头名称

对于windows系统, 双击 detect_meteor目录中的 show_video_device.bat

对于linux系统, cd detect_meteor, 执行 sh show_video_device.sh

注意: 如果您当前设备上只接了一个摄像头,在windows下可以不配置, 在Linux中,必须配置可以从/dev/video0 开始尝试




问题: 我不知道我的摄像头支持哪些分辨率和fps,怎么办?

回答: 

默认是自动识别,您可以不配置, 这样默认会使用摄像头支持的最高分辨率


如果您想指定分辨率和fps:

首先配置好摄像头名称, 如果您只有一个摄像头,则可以不配置,或者配置为空

对于windows系统, 双击 detect_meteor目录中的 show_video_format_support.bat

对于linux系统, cd detect_meteor, sh show_video_format_support.sh

根据显示出来的信息, 查看摄像头支持哪些分辨率和fps. 配置到.config 文件中





## 配置Python环境

版本: 推荐使用Python 3.10及以上


### 步骤1

新建virtual env. 

windows下, 

资源管理器中在detect_meteor目录空白处,点击右键 -> 在此处运行cmd, 

这里假定您的Python安装在D:\python311目录

在弹出的 command 中输入 D:\python311\python.exe -m venv venv. 



Linux下, 

cd detect_meteor, python3 -m venv venv


### 步骤2

安装依赖

对于 windows系统, 

在 detect_meteor 目录下, 鼠标双击 install_dep.bat


对于 Linux 系统, 

在 detect_meteor 目录下, 执行命令 sh install_dep.sh


### 步骤3

运行本程序

windows下, 双击 offline_detect_from_mp4.bat 

Linux下, 在detect_meteor目录下, 执行 sh run.sh


### 步骤4

配置开机自动启动, 

Windows下, 右键点击 offline_detect_from_mp4.bat, 发送到桌面快捷方式, 将 快捷方式,复制到 开始菜单的 启动 目录

Linux下, crontable中配置 */5 * * * *  cd /home/yourname/workspace/meteor_monitor_script/detect_meteor && sh run.sh 


### 步骤5 可选

配置 mask-1280-720.bmp 遮罩图像, 目的是排除掉画面中的一些非天空部分, 这部分可能会引起False Positive, 流星的误报

比如 画面中远处楼宇的灯光变化, 可能会让程序以为是有画面变化

问题: 在哪个目录新建 遮罩图像?

答: 在视频目标输出目录, 在配置文件的 base_output_path 选项, 该路径由您指定

问题: 遮罩图像黑色白色代表什么意思?

答: 黑色表示要遮盖的部分, 白色表示要检测的部分



## 原理介绍


### 高效的录制mp4视频

使用ffmpeg, 高效录制视频. 这部分,我没有足够能力使用python实现, 所以借助ffmpeg的能力

ffmpeg 支持多种编码格式, h264支持多种硬件加速, 比如Intel核心显卡, nvdia显卡, AMD显卡

备注: 曾经使用过一个方案 使用windows自带的相机app,进行录像. 这个方案不够稳定, 已被废弃. 该方案使用sikuli进行UI自动化操作, 非常不稳定.


### 离线分析流星

为什么不做实时分析?

因为硬件性能不够. 我的目的是在低配置的硬件上,运行本程序. 如果您的硬件性能已经很强悍, 则建议直接使用ufohd2


离线分析的原理

步骤1

使用典型的opencv 运动检测算法: 帧差法, 识别画面的变化

步骤2

根据一些特征,过滤掉不是流星的东西, 比如蝙蝠, 小飞虫等.

步骤3

使用ffmpeg 将原始视频切片, 切片后单独存储起来


