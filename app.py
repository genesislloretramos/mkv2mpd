import datetime
import sys
import os
from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog, QTextEdit, QVBoxLayout, QPushButton, QWidget, QProgressBar
from PyQt5.QtCore import QThread, pyqtSignal
from libs import initialize, process_mkv_file

class Worker(QThread):
    log_signal = pyqtSignal(str)
    progress_signal = pyqtSignal(int)

    def __init__(self, file_path):
        super().__init__()
        self.file_path = file_path

    def run(self):
        result = process_mkv_file(self.file_path, self.log_signal.emit, self.progress_signal.emit)
        if "error" in result:
            self.log_signal.emit(result["error"])
        else:
            self.log_signal.emit("Processing completed successfully.")

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('MKV to RTPM Converter')
        self.setGeometry(100, 100, 600, 400)
        self.initUI()

    def initUI(self):
        self.container = QWidget()
        self.layout = QVBoxLayout()

        self.log_text = QTextEdit(self)
        self.log_text.setReadOnly(True)
        self.layout.addWidget(self.log_text)

        self.progress_bar = QProgressBar(self)
        self.layout.addWidget(self.progress_bar)

        self.button = QPushButton('Select MKV File', self)
        self.button.clicked.connect(self.select_file)
        self.layout.addWidget(self.button)

        self.container.setLayout(self.layout)
        self.setCentralWidget(self.container)

    def select_file(self):
        options = QFileDialog.Options()
        options |= QFileDialog.ReadOnly
        file_path, _ = QFileDialog.getOpenFileName(self, "Select MKV File", "", "MKV Files (*.mkv);;All Files (*)", options=options)
        if file_path:
            self.log_text.append(f"[{self.current_time()}] - Selected file path: {file_path}")
            self.worker = Worker(file_path)
            self.worker.log_signal.connect(self.update_log)
            self.worker.progress_signal.connect(self.update_progress)
            self.worker.start()

    def update_log(self, message):
        self.log_text.append(f"[{self.current_time()}] - {message}")

    def update_progress(self, value):
        self.progress_bar.setValue(value)

    def current_time(self):
        return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def main():
    initialize()
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
