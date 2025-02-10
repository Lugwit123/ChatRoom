import os
import shutil

files_to_move = [
    'test.py',
    'test1.py',
    'sendAbcMessage.py',
    'send_message.py',
    'pyqt_runjs.py',
    'client_app.py',
    '这里是Python客户端.txt',
    'temp_geometry.txt',
    'handler.py',
    'call_pyqt_chatroom.py'
]

# 确保temp目录存在
if not os.path.exists('temp'):
    os.makedirs('temp')

# 移动文件
for file in files_to_move:
    try:
        if os.path.exists(file):
            shutil.move(file, os.path.join('temp', file))
            print(f'Moved {file} to temp/')
    except Exception as e:
        print(f'Error moving {file}: {e}') 