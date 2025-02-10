from pywinauto import Application

# 启动 VNC Viewer 并连接到指定地址
app = Application().start(r'"D:\TD_Depot\Software\ProgramFilesLocal\RealVNC\VNC Viewer\vncviewer.exe" 192.168.110.26:5900')

# 等待认证窗口加载
dlg = app.window(title='Authentication')
dlg.wait('exists', timeout=2)  # 等待窗口加载完成


# 定位 Password 输入框并输入密码
password_input = dlg.child_window(class_name="Edit", found_index=1)  # 第二个输入框是 Password
password_input.type_keys("OC.123456", with_spaces=True)  # 输入密码

# 定位 OK 按钮并点击
ok_button = dlg.child_window(title="OK", class_name="Button")
ok_button.click()  # 点击 OK 按钮