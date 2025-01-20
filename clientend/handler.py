import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QMessageBox

class SimpleWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        # 设置窗口标题和尺寸
        self.setWindowTitle('简单的PyQt窗口')
        self.setGeometry(200, 200, 400, 300)

        # 创建按钮并设置属性
        self.button = QPushButton('点击我', self)
        self.button.setGeometry(150, 120, 100, 40)
        self.button.clicked.connect(self.show_message)

    def show_message(self):
        # 显示消息框
        QMessageBox.information(self, '提示', '按钮被点击了！')

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = SimpleWindow()
    window.show()
    with open("D:/aa.txt",'w') as f:
        f.write("123")
    sys.exit(app.exec_())
