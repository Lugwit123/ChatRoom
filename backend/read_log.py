import sys
import os
import chardet

# 设置控制台编码为UTF-8
sys.stdout.reconfigure(encoding='utf-8')

def read_log_file(file_path):
    try:
        # 以二进制模式读取文件
        with open(file_path, 'rb') as file:
            # 读取文件内容
            raw_data = file.read()
            
            # 检测编码
            result = chardet.detect(raw_data)
            encoding = result['encoding']
            confidence = result['confidence']
            
            print(f"\n检测到的编码: {encoding}, 置信度: {confidence:.2f}\n")
            
            # 解码文件内容
            content = raw_data.decode(encoding)
            
            print("=== 日志文件内容 (" + file_path + ") ===\n")
            print(content)
            print("\n=== 日志文件结束 ===\n")
            
    except Exception as e:
        print(f"读取日志文件时出错: {str(e)}")

if __name__ == "__main__":
    # 获取日志文件路径
    log_file = os.path.join(os.getcwd(), "logs", "server.log")
    read_log_file(log_file)