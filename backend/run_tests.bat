@echo off
echo 运行后端测试...

REM 激活虚拟环境（如果有的话）
REM call .venv\Scripts\activate

REM 安装测试依赖
pip install -r requirements-test.txt

REM 运行所有测试
pytest tests\ -v --cov=app --cov-report=html

REM 运行特定类型的测试
REM pytest tests\ -v -m unit  :: 只运行单元测试
REM pytest tests\ -v -m integration  :: 只运行集成测试
REM pytest tests\ -v -m e2e  :: 只运行端到端测试

echo 测试完成！
pause
