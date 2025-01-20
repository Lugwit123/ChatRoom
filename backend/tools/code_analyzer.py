"""代码分析工具，用于提取Python文件中的函数和方法信息"""
import os
import ast
from typing import List, Dict, Any, Tuple, Set
from datetime import datetime
import Lugwit_Module as LM

lprint = LM.lprint

class CodeAnalyzer:
    def __init__(self, backup_dir: str, new_dir: str, output_file: str):
        """
        初始化代码分析器
        
        Args:
            backup_dir: 备份目录的路径
            new_dir: 新代码目录的路径
            output_file: 输出文件的路径
        """
        self.backup_dir = backup_dir
        self.new_dir = new_dir
        self.output_file = output_file
        
    def get_python_files(self, directory: str) -> List[str]:
        """获取所有Python文件的路径"""
        python_files = []
        for root, _, files in os.walk(directory):
            for file in files:
                if file.endswith('.py'):
                    python_files.append(os.path.join(root, file))
        return python_files
    
    def parse_file(self, file_path: str, base_dir: str) -> List[Dict[str, Any]]:
        """
        解析单个Python文件，提取函数和方法信息
        
        Args:
            file_path: Python文件路径
            base_dir: 基础目录路径
            
        Returns:
            包含函数和方法信息的列表
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                tree = ast.parse(f.read())
                
            functions = []
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    # 函数定义
                    functions.append({
                        'name': node.name,
                        'type': 'function',
                        'line': node.lineno,
                        'file': os.path.relpath(file_path, base_dir),
                        'is_async': isinstance(node, ast.AsyncFunctionDef)
                    })
                elif isinstance(node, ast.ClassDef):
                    # 类定义，提取其方法
                    for item in node.body:
                        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                            functions.append({
                                'name': f"{node.name}.{item.name}",
                                'type': 'method',
                                'line': item.lineno,
                                'file': os.path.relpath(file_path, base_dir),
                                'is_async': isinstance(item, ast.AsyncFunctionDef)
                            })
            
            return functions
            
        except Exception as e:
            lprint(f"解析文件 {file_path} 时出错: {str(e)}")
            return []
    
    def analyze_code(self, directory: str) -> List[Dict[str, Any]]:
        """分析指定目录中的所有Python文件"""
        all_functions = []
        python_files = self.get_python_files(directory)
        
        for file_path in python_files:
            functions = self.parse_file(file_path, directory)
            all_functions.extend(functions)
            
        return all_functions
    
    def get_function_signature(self, func: Dict[str, Any]) -> str:
        """获取函数的唯一标识"""
        return f"{'async ' if func['is_async'] else ''}{func['type']}:{func['name']}"
    
    def compare_code(self) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        比较新旧代码的差异
        
        Returns:
            (missing_functions, new_functions, moved_functions)
        """
        backup_functions = self.analyze_code(self.backup_dir)
        new_functions = self.analyze_code(self.new_dir)
        
        # 创建函数签名集合
        backup_signatures = {self.get_function_signature(f): f for f in backup_functions}
        new_signatures = {self.get_function_signature(f): f for f in new_functions}
        
        # 找出丢失的函数
        missing_functions = [
            f for sig, f in backup_signatures.items()
            if sig not in new_signatures
        ]
        
        # 找出新增的函数
        added_functions = [
            f for sig, f in new_signatures.items()
            if sig not in backup_signatures
        ]
        
        # 找出移动的函数（名称相同但文件位置不同）
        moved_functions = [
            (backup_signatures[sig], new_signatures[sig])
            for sig in set(backup_signatures) & set(new_signatures)
            if backup_signatures[sig]['file'] != new_signatures[sig]['file']
        ]
        
        return missing_functions, added_functions, moved_functions
    
    def write_comparison_to_markdown(self):
        """将比较结果写入Markdown文件"""
        missing_functions, added_functions, moved_functions = self.compare_code()
        
        with open(self.output_file, 'w', encoding='utf-8') as f:
            f.write("# 代码迁移差异分析报告\n\n")
            f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            # 写入丢失的函数
            f.write("## 丢失的函数和方法\n\n")
            if missing_functions:
                for func in sorted(missing_functions, key=lambda x: (x['file'], x['line'])):
                    prefix = 'async ' if func['is_async'] else ''
                    f.write(f"- {prefix}`{func['name']}` ({func['type']}) - 在文件 `{func['file']}` 第 {func['line']} 行\n")
            else:
                f.write("*没有丢失的函数和方法*\n")
            f.write("\n")
            
            # 写入新增的函数
            f.write("## 新增的函数和方法\n\n")
            if added_functions:
                for func in sorted(added_functions, key=lambda x: (x['file'], x['line'])):
                    prefix = 'async ' if func['is_async'] else ''
                    f.write(f"- {prefix}`{func['name']}` ({func['type']}) - 在文件 `{func['file']}` 第 {func['line']} 行\n")
            else:
                f.write("*没有新增的函数和方法*\n")
            f.write("\n")
            
            # 写入移动的函数
            f.write("## 移动的函数和方法\n\n")
            if moved_functions:
                for old_func, new_func in sorted(moved_functions, key=lambda x: x[0]['name']):
                    prefix = 'async ' if old_func['is_async'] else ''
                    f.write(f"- {prefix}`{old_func['name']}` ({old_func['type']}):\n")
                    f.write(f"  - 从: `{old_func['file']}` 第 {old_func['line']} 行\n")
                    f.write(f"  - 到: `{new_func['file']}` 第 {new_func['line']} 行\n")
            else:
                f.write("*没有移动的函数和方法*\n")

def main():
    """主函数"""
    # 获取目录路径
    base_dir = os.path.dirname(os.path.dirname(__file__))
    backup_dir = os.path.join(base_dir, 'backup', '20250111_154510')
    new_dir = os.path.join(base_dir, 'app')
    output_file = os.path.join(base_dir, 'docs', 'code_migration_diff.md')
    
    analyzer = CodeAnalyzer(backup_dir, new_dir, output_file)
    analyzer.write_comparison_to_markdown()
    lprint(f"分析完成，结果已写入到: {output_file}")

if __name__ == '__main__':
    main()
