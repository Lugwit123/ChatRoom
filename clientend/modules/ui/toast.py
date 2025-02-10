import sys
from PySide6.QtWidgets import QApplication, QMainWindow
from PySide6.QtWebEngineWidgets import QWebEngineView

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("HTML5 视频播放器")
        self.resize(800, 600)

        # 创建 QWebEngineView 实例
        self.browser = QWebEngineView()
        # 加载包含 HTML5 视频的网页
        self.browser.setUrl("https://www.example.com/your_video_page.html")

        self.setCentralWidget(self.browser)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
