import os
import shutil

# 创建必要的目录
directories = ['static', 'scripts', 'temp']
for directory in directories:
    if not os.path.exists(directory):
        os.makedirs(directory)
        print(f'Created directory: {directory}')

# 定义文件移动规则
moves = {
    'static': [
        'dark_theme.css'
    ],
    'scripts': [
        'run_vnc_install.bat',
        'run_chatroom.bat',
        'run_client.bat'
    ],
    'temp': [
        'move_files.py',
        'organize_files.py'
    ]
}

# 移动文件
for target_dir, files in moves.items():
    for file in files:
        try:
            if os.path.exists(file):
                shutil.move(file, os.path.join(target_dir, file))
                print(f'Moved {file} to {target_dir}/')
        except Exception as e:
            print(f'Error moving {file}: {e}')

print('\nFinal directory structure:')
for root, dirs, files in os.walk('.'):
    level = root.replace('.', '').count(os.sep)
    indent = ' ' * 4 * level
    print(f'{indent}{os.path.basename(root)}/')
    subindent = ' ' * 4 * (level + 1)
    for f in files:
        print(f'{subindent}{f}') 