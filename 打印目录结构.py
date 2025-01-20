import os

def print_directory_structure(directory, indent=""):
    """
    递归打印目录结构。
    
    Args:
        directory (str): 要打印结构的目录路径。
        indent (str): 用于缩进的字符串，每递归一层增加缩进。
    """
    # 列出目录中的所有文件和文件夹
    items = os.listdir(directory)
    for item in items:
        ignore = False
        item_path = os.path.join(directory, item)
        for x in ['node_modules','myapp','Old','web','.git']:
            if x in item_path:
                ignore = True
                break
        if ignore:
            continue
        # 判断是文件还是文件夹
        if os.path.isdir(item_path):
            # 打印文件夹名称，并增加缩进继续递归打印
            print(f"{indent}📂 {item}")
            print_directory_structure(item_path, indent + "    ")
        else:
            # 打印文件名称
            print(f"{indent}📄 {item}")

# 使用当前目录
print(f"当前目录{os.getcwd()}结构：")
print_directory_structure(os.getcwd())
