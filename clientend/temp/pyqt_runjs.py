import os
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton
from PyQt5.QtWebEngineWidgets import QWebEngineView

# 设置开发者工具端口（绕过 DeveloperExtrasEnabled）
os.environ["QTWEBENGINE_REMOTE_DEBUGGING"] = "9222"

class WebEngineExample(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PyQt 开发者模式")
        self.setGeometry(100, 100, 800, 600)

        # 创建 QWebEngineView
        self.webview = QWebEngineView()
        html = """
        <html>
            <head>
                <title>JavaScript 示例</title>
                <script>
                    function showMessage() {
                        alert("ss")
                        return "Hello from JavaScript!";
                    }
                </script>
            </head>
            <body>
                <h1>PyQt 调用 JavaScript 示例</h1>
            </body>
        </html>
        """
        self.webview.setHtml(html)

        # 添加按钮调用 JS
        self.button = QPushButton("调用 JS")
        self.button.clicked.connect(self.run_js)

        layout = QVBoxLayout()
        layout.addWidget(self.webview)
        layout.addWidget(self.button)
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def run_js(self):
        self.webview.page().runJavaScript("showMessage();", self.js_callback)
        

    def js_callback(self, result):
        print("JavaScript 返回:", result)

if __name__ == "__main__":
    app = QApplication([])
    window = WebEngineExample()
    window.show()
    app.exec_()
