本脚本一共有 个功能
1、生成binFirmwareInfo.h和binFirmwareInfo.cpp文件(修改platformio.ini保存后生成)，用途是将固件信息存入内存区段中。
2、env.AddPreAction("$BUILD_DIR/${PROGNAME}.elf", hook_Linking)功能是在生成elf文件前进行钩子去修改.ld链接文件从而固定固件信息区段到".firmware_info"区段中。（PS：这里暂时不知道如何在其他程序读取通过固件文件来读取这些信息）
3、env.AddPostAction("$BUILD_DIR/${PROGNAME}.bin", hook_Building)功能是在生成bin固件文件后对其尾部追加固件信息，在其他程序中可以通过生成binFirmwareInfo里的函数读取。
