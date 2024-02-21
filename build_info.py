Import("env")
import shutil
import os
import struct
import re

# 定义固件信息
version = "2.0.0"
name = "MQ-7"
description = "用于探测一氧化碳浓度"
FIRMWARE_VERSION_LENGTH = 10
FIRMWARE_NAME_LENGTH = 20
FIRMWARE_DESC_LENGTH = 60


firmware_info = (version.encode('utf-8'), name.encode('utf-8'), description.encode('utf-8'))
# 定义固件信息结构
firmware_format = f'{FIRMWARE_VERSION_LENGTH}s{FIRMWARE_NAME_LENGTH}s{FIRMWARE_DESC_LENGTH}s'
firmware_struct = struct.Struct(firmware_format)


# 生成版本信息.h文件内容
header_content = f'''#ifndef BINFIRMWAREINFO_H
#define BINFIRMWAREINFO_H

#define FIRMWARE_VERSION_LENGTH {FIRMWARE_VERSION_LENGTH}
#define FIRMWARE_NAME_LENGTH {FIRMWARE_NAME_LENGTH}
#define FIRMWARE_DESC_LENGTH {FIRMWARE_DESC_LENGTH}

// 符号导出声明
const char firmware_version[FIRMWARE_VERSION_LENGTH] __attribute__((section(".firmware_version"))) =  "{version}";
const char firmware_name[FIRMWARE_NAME_LENGTH] __attribute__((section(".firmware_name"))) = "{name}";
const char firmware_desc[FIRMWARE_DESC_LENGTH] __attribute__((section(".firmware_desc"))) = "{description}";


// 定义固件信息结构体
struct FirmwareInfo_struct{{
    FirmwareInfo_struct();
    char version[FIRMWARE_VERSION_LENGTH];
    char name[FIRMWARE_NAME_LENGTH];
    char description[FIRMWARE_DESC_LENGTH];
    unsigned int version_address;
    unsigned int name_address;
    unsigned int desc_address;
}};

// 定义固件信息结构体
struct binFirmwareInfo {{
    char version[FIRMWARE_VERSION_LENGTH];
    char name[FIRMWARE_NAME_LENGTH];
    char description[FIRMWARE_DESC_LENGTH];
}};

extern FirmwareInfo_struct FirmwareInfo;
#endif
'''
# 写入头文件
header_file = open("./src/binFirmwareInfo.h", "w", encoding='utf-8')
header_file.write(header_content)
header_file.close()


# 生成版本信息.cpp文件内容
header_content = f'''#include "binFirmwareInfo.h"
#include "Arduino.h"

FirmwareInfo_struct::FirmwareInfo_struct(){{
    this->version_address = (uint32_t)&firmware_version;
    // 创建一个临时的字符数组来存储复制的数据
    char firmware_version_Data[FIRMWARE_VERSION_LENGTH];
    // 使用内存复制功能将数据从指针复制到字符数组
    memcpy(firmware_version_Data, firmware_version, FIRMWARE_VERSION_LENGTH);
    strcpy(this->version,firmware_version_Data);
    //Serial.printf("当前固件版本[0x%x] %s\\n", this->version_address, this->version);

    this->name_address = (uint32_t)&firmware_name;
    // 创建一个临时的字符数组来存储复制的数据
    char firmware_name_Data[FIRMWARE_NAME_LENGTH];
    // 使用内存复制功能将数据从指针复制到字符数组
    memcpy(firmware_name_Data, firmware_name, FIRMWARE_NAME_LENGTH);
    strcpy(this->name,firmware_name_Data);
    //Serial.printf("当前固件名称[0x%x]  %s\\n", this->name_address, this->name);


    this->desc_address = (uint32_t)&firmware_desc;
    // 创建一个临时的字符数组来存储复制的数据
    char firmware_desc_Data[FIRMWARE_DESC_LENGTH];
    // 使用内存复制功能将数据从指针复制到字符数组
    memcpy(firmware_desc_Data, firmware_desc, FIRMWARE_DESC_LENGTH);
    strcpy(this->description,firmware_desc_Data);
    //Serial.printf("当前固件名称[0x%x]  %s\\n", this->desc_address, this->description);
}}

FirmwareInfo_struct FirmwareInfo;
'''
# 写入头文件
header_file = open("./src/binFirmwareInfo.cpp", "w", encoding='utf-8')
header_file.write(header_content)
header_file.close()


# 对ld文件添加内容
def modify_LD(ld_Text, ld_Section, ld_Content):
    block_pattern = re.compile(re.escape(ld_Section) + r"\s*\{(.+?)\n\s*}\n", re.DOTALL)
    # 首先判断是否存在 block_pattern
    block_match = re.search(block_pattern, ld_Text)
    if block_match:
        #print(block_match.group(1))
        _pattern = re.compile(re.escape(ld_Content), re.MULTILINE)
        existing_content_match = re.search(_pattern, block_match.group(1))
        if existing_content_match:
            print(f"[自定义编译过程] LD文件中'{ld_Section}'节所需配置信息已存在")
            return ld_Text
        else:
            # 在匹配到的区块的末尾添加新内容
            updated_Content = f'{block_match.group(1)}\n{ld_Content}'
            ld_Text = ld_Text.replace(block_match.group(1), updated_Content)
            
                
            print(f"[自定义编译过程] 成功在 {ld_Section} 区块中添加 '{ld_Content}'")
            #print(updated_ld_content)
            return ld_Text
    else:
        print(f"[自定义编译过程] LD文件中不存在{ld_Section}节")
        return ld_Text


#在生成firmware.elf文件前的钩子函数
def hook_Linking(source, target, env):
    # 在这里编写您希望在链接步骤执行的自定义操作
    file_dir = os.path.dirname(str(target[0]))
    ld_file_path = f"{file_dir}\\ld\\local.eagle.app.v6.common.ld"
    print("[自定义编译过程] 开始编译固件......")
    if os.path.exists(ld_file_path):
        print(f"[自定义编译过程] {ld_file_path} 文件存在.")
        MEMORY  = "MEMORY"
        MEMORY_add = '''  iram1_1_seg : org = 0x40108000, len = 0x1000'''
        SECTIONS = "SECTIONS"
        SECTIONS_add = '''  .firmware_info : ALIGN(4)
  {    
    *(.firmware_version)
    *(.firmware_name)
    *(.firmware_desc)
  } >iram1_1_seg :dram0_0_phdr'''

        # 读取.ld文件内容
        with open(ld_file_path, 'r') as ld_file:
            ld_text = ld_file.read()
        ld_text = modify_LD(ld_text, MEMORY, MEMORY_add)
        ld_text = modify_LD(ld_text, SECTIONS, SECTIONS_add)
        # 重新写入更新后的内容到.ld文件
        with open(ld_file_path, 'w') as ld_file:
            ld_file.write(ld_text)
    else:
        print(f"[自定义编译过程] {ld_file_path} 文件不存在.")


# 在生成firmware.bin文件后的钩子函数
def hook_Building(source, target, env):
    # 获取固件文件路径
    firmware_file = str(target[0])
    firmware_file_size_before = os.path.getsize(firmware_file)
    print("[自定义编译过程] 需要处理的固件文件[", firmware_file_size_before , "]:" , firmware_file)
    
    # 将固件信息写入固件文件
    with open(firmware_file, "ab") as f:
        firmware_data = firmware_struct.pack(*firmware_info)
        print("[自定义编译过程] 实际写入的 FirmwareInfo 大小为:", len(firmware_data), "字节")
        f.write(firmware_data)
        # 复制固件文件到 data 目录中
        #data_dir = "data\\Update"  # 定义用于上传到 LittleFS 文件系统的 data 目录
        #if not os.path.exists(data_dir):
        #    os.makedirs(data_dir)  # 如果 data 目录不存在，创建它
    
    firmware_file_size_before = os.path.getsize(firmware_file)
    base_name = os.path.basename(name)
    #destination_file = os.path.join(data_dir, os.path.basename(base_name +".bin"))
    destination_file = os.path.join(".\\", os.path.basename(base_name +".bin"))
    print("[自定义编译过程] 复制固件[" , firmware_file_size_before ,"字节]到:", destination_file)
    shutil.copy(firmware_file, destination_file)


# 在生成firmware.elf文件前钩子
env.AddPreAction("$BUILD_DIR/${PROGNAME}.elf", hook_Linking)
# 在生成firmware.bin文件后钩子
env.AddPostAction("$BUILD_DIR/${PROGNAME}.bin", hook_Building)


#https://docs.platformio.org/en/latest/scripting/actions.html
#MEMORY
#{
#  iram1_1_seg : org = 0x40108000, len = 0x1000
#}

#SECTIONS
#{
#  .firmware_info : ALIGN(4)
#  {    
#    *(.firmware_version)
#    *(.firmware_name)
#    *(.firmware_desc)
#  } >iram1_1_seg :dram0_0_phdr
#}