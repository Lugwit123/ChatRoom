import os
import shutil
from pathlib import Path
import Lugwit_Module as LM

lprint = LM.lprint

def ensure_directory(path: Path):
    """确保目录存在，如果不存在则创建"""
    if not path.exists():
        path.mkdir(parents=True)
        lprint(f"Created directory: {path}")

def create_init_file(path: Path):
    """在目录中创建 __init__.py 文件"""
    init_file = path / '__init__.py'
    if not init_file.exists():
        init_file.touch()
        lprint(f"Created __init__.py in {path}")

def create_directories():
    """创建必要的目录结构"""
    base_dir = Path(__file__).parent
    directories = [
        'app/api/v1/endpoints',
        'app/core/websocket',
        'app/db/repositories',
        'app/services',
        'app/utils',
    ]
    
    for directory in directories:
        dir_path = base_dir / directory
        ensure_directory(dir_path)
        create_init_file(dir_path)
        
        # 为每个父目录也创建 __init__.py
        parent = dir_path.parent
        while parent.name:
            create_init_file(parent)
            parent = parent.parent

def copy_file_with_backup(src: Path, dst: Path):
    """复制文件并创建备份"""
    if src.exists():
        # 确保目标目录存在
        ensure_directory(dst.parent)
        
        # 如果目标文件已存在，先备份
        if dst.exists():
            backup_path = dst.with_suffix('.bak')
            shutil.copy2(dst, backup_path)
            lprint(f"Backed up {dst} to {backup_path}")
        
        # 复制文件
        shutil.copy2(src, dst)
        lprint(f"Copied {src} to {dst}")
        return True
    else:
        lprint(f"Source file not found: {src}")
        return False

def move_files():
    """移动文件到新的位置"""
    base_dir = Path(__file__).parent
    moves = [
        ('connection_manager.py', 'app/core/websocket/manager.py'),
        ('message_handlers.py', 'app/core/websocket/handlers.py'),
        ('message_routes.py', 'app/api/v1/endpoints/messages.py'),
        ('backend_main.py', 'app/main.py'),
        ('encoding_utils.py', 'app/utils/encoding.py'),
        ('logging_config.py', 'app/core/logging.py'),
        ('exception_handlers.py', 'app/core/exceptions.py'),
    ]
    
    success_count = 0
    for src, dst in moves:
        src_path = base_dir / src
        dst_path = base_dir / dst
        
        if copy_file_with_backup(src_path, dst_path):
            success_count += 1
    
    return success_count, len(moves)

def update_imports():
    """更新导入语句"""
    base_dir = Path(__file__).parent
    files_to_update = [
        'app/core/websocket/manager.py',
        'app/core/websocket/handlers.py',
        'app/api/v1/endpoints/messages.py',
        'app/main.py',
    ]
    
    import_updates = {
        'schemas': 'app.db.schemas',
        'user_database': 'app.db.repositories.user',
        'connection_manager': 'app.core.websocket.manager',
        'message_handlers': 'app.core.websocket.handlers',
        'utils': 'app.utils',
        'authenticate': 'app.core.auth',
        'dependencies': 'app.core.dependencies',
        'logging_config': 'app.core.logging',
        'exception_handlers': 'app.core.exceptions',
    }
    
    for file_path in files_to_update:
        full_path = base_dir / file_path
        if full_path.exists():
            try:
                content = full_path.read_text(encoding='utf-8')
                for old, new in import_updates.items():
                    content = content.replace(f"import {old}", f"import {new}")
                    content = content.replace(f"from {old}", f"from {new}")
                full_path.write_text(content, encoding='utf-8')
                lprint(f"Updated imports in {file_path}")
            except Exception as e:
                lprint(f"Error updating imports in {file_path}: {str(e)}")

if __name__ == "__main__":
    try:
        lprint("Starting file reorganization...")
        create_directories()
        success_count, total = move_files()
        lprint(f"Moved {success_count}/{total} files successfully")
        
        if success_count > 0:
            lprint("Updating import statements...")
            update_imports()
            lprint("Import statements updated successfully")
        
        lprint("File reorganization completed!")
    except Exception as e:
        lprint(f"Error during file reorganization: {str(e)}")
        import traceback
        lprint(traceback.format_exc())
