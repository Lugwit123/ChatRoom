@echo off
echo 从git仓库中删除.vscode文件夹...
git rm -r --cached .vscode
echo 确保.gitignore包含.vscode/...
echo .vscode/ >> .gitignore
echo 提交更改...
git add .gitignore
git commit -m "chore: remove .vscode directory from git tracking"
git push origin main
echo 完成！
pause 