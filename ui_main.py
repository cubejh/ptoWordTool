import sys
import os

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QMessageBox, QCheckBox, QTextEdit
)
from PyQt5.QtCore import QObject, Qt, QThread, pyqtSignal
from load_content_manager import APIKeyManager
from load_content_manager import ModelManager
from pdf_loader import PDFLoader
from process_main import process_mainflow


class ProcessThread(QThread):
    finished = pyqtSignal(bool)
    
    def __init__(self, api_key, pdf_dict, options,minarea_val, paddling_val, addition_prompt, selected_model):
        super().__init__()
        self.api_key = api_key
        self.pdf_dict = pdf_dict
        self.options = options
        self.minarea_val=minarea_val
        self.paddling_val=paddling_val
        self.addition_prompt=addition_prompt
        self.selected_model = selected_model
        
    def run(self):
        success = process_mainflow(self.api_key, self.pdf_dict, self.options,self.minarea_val,self.paddling_val,self.addition_prompt, self.selected_model)
        self.finished.emit(success)

class EmittingStream(QObject):
    new_text = pyqtSignal(str)

    def __init__(self):
        super().__init__()

    def write(self, text):
        if text.strip():
            self.new_text.emit(text)

    def flush(self):
        pass

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("PDF轉Word工具")
        self.resize(1600, 900)
        self.setStyleSheet("""
            QWidget {
                background-color: #222;
                color: #EEE;
                font-size: 13pt;
            }

            QLineEdit {
                background-color: #333;
                color: #FFF;
                border: 1px solid #555;
                padding: 3px;
            }

            QPushButton {
                background-color: #444;
                color: #FFF;
                border: 1px solid #666;
                padding: 5px;
                border-radius: 5px;
            }

            QPushButton:hover {
                background-color: #555;
            }

            QCheckBox {
                color: #EEE;
            }

            QLabel {
                color: #EEE;
            }
        """)

        
        self.log_box = QTextEdit()
        self.log_box.setReadOnly(True) 
        self.log_box.setMinimumHeight(300) 
        self.log_box.setLineWrapMode(QTextEdit.NoWrap)  
        self.log_box.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded) 

        font = self.log_box.font()
        font.setFamily("Consolas")
        font.setPointSize(12)
        self.log_box.setFont(font)
        self.stdout_stream = EmittingStream()
        self.stderr_stream = EmittingStream()
        self.stdout_stream.new_text.connect(self.append_log)
        self.stderr_stream.new_text.connect(self.append_log)
        sys.stdout = self.stdout_stream
        sys.stderr = self.stderr_stream

        self.key_manager = APIKeyManager()
        self.model_manager = ModelManager()
        self.pdf_loader = PDFLoader()

        central = QWidget()
        main_layout = QVBoxLayout(central)

        main_layout.setContentsMargins(10, 5, 10, 10)

        # =======================================================
        #  API Key
        # =======================================================
        row = QHBoxLayout()

        self.label = QLabel("🔑 API Key：")
        row.addWidget(self.label)

        self.key_input = QLineEdit()
        self.key_input.setFixedWidth(700)
        self.key_input.setText(self.key_manager.read_key())
        row.addWidget(self.key_input)

        self.save_button = QPushButton("更新")
        self.save_button.setFixedWidth(80)
        self.save_button.clicked.connect(self.save_api_key)
        row.addWidget(self.save_button)

        row.addStretch()
        main_layout.addLayout(row)

        # =======================================================
        #  some conditions and check box
        # =======================================================
        black_frame_row = QHBoxLayout()

        self.frame_label = QLabel("外黑框(掃描建議勾選)")
        self.frame_enable = QCheckBox("")
        self.frame_enable.setChecked(False)
        black_frame_row.addWidget(self.frame_enable)
        black_frame_row.addWidget(self.frame_label)

        black_frame_row.addSpacing(25) 

        self.slowdown_label = QLabel("降速輸出(單頁/圖內容量少時勾選)")
        self.slowdown_enable = QCheckBox("")
        self.slowdown_enable.setChecked(False)
        black_frame_row.addWidget(self.slowdown_enable)
        black_frame_row.addWidget(self.slowdown_label)
        
        black_frame_row.addSpacing(25) 

        self.crop_label = QLabel("輔助圖片輸出(")
        self.crop_enable = QCheckBox("")
        self.crop_enable.setChecked(False)
        black_frame_row.addWidget(self.crop_enable)
        black_frame_row.addWidget(self.crop_label)
        
        black_frame_row.addWidget(QLabel("最小面積:"))
        self.minarea = QLineEdit()
        self.minarea.setFixedWidth(75)
        self.minarea.setText("10000")
        black_frame_row.addWidget(self.minarea)

        black_frame_row.addSpacing(10) 

        black_frame_row.addWidget(QLabel("向外延伸:"))
        self.paddling = QLineEdit()
        self.paddling.setFixedWidth(50)
        self.paddling.setText("60")
        black_frame_row.addWidget(self.paddling)
        black_frame_row.addWidget(QLabel(")"))
        
        black_frame_row.addStretch()
        main_layout.addLayout(black_frame_row)
        main_layout.addWidget(QLabel(""))
        
        # =======================================================
        #  model choosing 2.5 pro, 2.5 flash 2.5 flash-lite(fastest)
        # =======================================================
        model_list = self.model_manager.loadModel()
        self.models_controls = []

        if model_list:
            model_section = QVBoxLayout()
            model_section.addWidget(QLabel("選擇使用的 Model：(建議使用flash)"))

            for model_name in model_list:
                row = QHBoxLayout()

                chk = QCheckBox()
                chk.setChecked(False)

                lbl = QLabel(model_name)

                row.addWidget(chk)
                row.addWidget(lbl)
                row.addStretch()

                model_section.addLayout(row)

                self.models_controls.append({
                    "name": model_name,
                    "enable": chk
                })
            self.selected_model = None 
            for item in self.models_controls:
                item["enable"].stateChanged.connect(self.on_model_checked)
            main_layout.addLayout(model_section)
            main_layout.addWidget(QLabel(""))
        # =======================================================
        #  image and checkbox
        # =======================================================
        image_row = QHBoxLayout()
        img_count = self.count_images()
        self.image_label = QLabel(f"📷圖片：共 {img_count} 張")   
        self.enable_transcribe = QCheckBox("")
        self.enable_transcribe.setChecked(True)
        image_row.addWidget(self.enable_transcribe)
        image_row.addWidget(self.image_label)
        image_row.addStretch()

        main_layout.addLayout(image_row)

        # =======================================================
        #  PDF and check box
        # =======================================================
        self.build_pdf_section(main_layout)
        main_layout.addWidget(QLabel(""))

        # =======================================================
        #  additional prompt
        # =======================================================
        prompt_row = QVBoxLayout()

        self.prompt_label = QLabel("額外需求:")
        prompt_row.addWidget(self.prompt_label)

        self.prompt_txt = QTextEdit()
        self.prompt_txt.setMinimumHeight(100)
        self.prompt_txt.setLineWrapMode(QTextEdit.WidgetWidth) 
        prompt_row.addWidget(self.prompt_txt)
        self.log_label = QLabel("輸出進度:")
        prompt_row.addWidget(self.log_label)
        main_layout.addLayout(prompt_row)

        # =======================================================
        #  log
        # =======================================================
        
        main_layout.addWidget(self.log_box)
        main_layout.addStretch()
        # =========================
        # execution button
        # =========================
        bottom_row = QHBoxLayout()
        bottom_row.addStretch()  

        self.run_button = QPushButton("開始執行")
        self.run_button.setFixedWidth(120)
        self.run_button.clicked.connect(self.on_run_clicked)
        bottom_row.addWidget(self.run_button)

        main_layout.addLayout(bottom_row)

        self.setCentralWidget(central)


    def save_api_key(self):
        new_key = self.key_input.text().strip()
        self.key_manager.write_key(new_key)
        QMessageBox.information(self, "成功", "API Key 更新")

    def append_log(self, text):
        self.log_box.append(text)
        self.log_box.verticalScrollBar().setValue(
            self.log_box.verticalScrollBar().maximum()
        )

    def count_images(self):
        input_dir = "input"
        if not os.path.exists(input_dir):
            return 0

        exts = {".jpg", ".jpeg", ".png", ".bmp", ".gif"}

        return sum(
            1 for f in os.listdir(input_dir)
            if os.path.splitext(f.lower())[1] in exts
        )

    def build_pdf_section(self, layout):
        pdf_info_list = self.pdf_loader.get_pdf_info()

        if not pdf_info_list:
            return

        title_row = QHBoxLayout()
        layout.addLayout(title_row)

        self.pdf_controls = []

        for info in pdf_info_list:
            row = QHBoxLayout()

            chk = QCheckBox()
            chk.setChecked(True)
            row.addWidget(chk)

            row.addWidget(QLabel("📄"+info["name"]))

            row.addWidget(QLabel("從"))
            start_input = QLineEdit()
            start_input.setFixedWidth(50)
            row.addWidget(start_input)

            row.addWidget(QLabel("到"))
            end_input = QLineEdit()
            end_input.setFixedWidth(50)
            row.addWidget(end_input)

            row.addWidget(QLabel(f"(共 {info['pages']} 頁)"))

            row.addStretch()
            layout.addLayout(row)

            self.pdf_controls.append(
                {
                    "name": info["name"],
                    "pages": info["pages"],
                    "enable": chk,
                    "start": start_input,
                    "end": end_input
                }
            )

    def on_run_clicked(self):
        api_key = self.key_input.text().strip()
        addition_prompt = self.prompt_txt.toPlainText().strip() 
        if not api_key:
            QMessageBox.warning(self, "錯誤", "請輸入 API Key！")
            return
        if not self.selected_model:
            QMessageBox.warning(self, "錯誤", "未選擇模型")
            return
        for item in self.pdf_controls:
            if not item["enable"].isChecked():
                continue
            try:
                start = int(item["start"].text())
                end = int(item["end"].text())
            except ValueError:
                QMessageBox.warning(self, "錯誤",
                                    f"{item['name']} 請輸入的頁碼！")
                return

            if not (1 <= start <= end <= item["pages"]):
                QMessageBox.warning(
                    self, "錯誤",
                    f"{item['name']} 的頁碼範圍錯誤！"
                )
                return

        QMessageBox.information(self, "成功", "準備執行")
        api_key = self.key_input.text().strip()

        pdf_to_process = []
        for item in self.pdf_controls:
            if not item["enable"].isChecked():
                continue
            pdf_to_process.append({
                "name": item["name"],
                "start": int(item["start"].text()),
                "end": int(item["end"].text())
            })

        options = {
            "transcribe": self.enable_transcribe.isChecked(),
            "black_frame": self.frame_enable.isChecked(),
            "crop": self.crop_enable.isChecked(),
            "slowdown": self.slowdown_enable.isChecked()
        }

        pdf_file_start_end_dict = {}

        for item in self.pdf_controls:
            if item["enable"].isChecked():  
                pdf_file_start_end_dict[item["name"]] = (
                    int(item["start"].text()),
                    int(item["end"].text())
                )
        self.minarea_val = int(self.minarea.text())
        self.paddling_val = int(self.paddling.text())
        self.run_button.setEnabled(False)  
        self.thread = ProcessThread(api_key, pdf_file_start_end_dict, options,self.minarea_val, self.paddling_val, addition_prompt, self.selected_model)
        self.thread.finished.connect(self.on_process_finished)
        self.thread.start()

    def on_process_finished(self, success):
        if success:
            QMessageBox.information(self, "完成", "PDF 處理完成！")
            self.close()
        else:
            QMessageBox.warning(self, "錯誤", "處理失敗！")
            self.close()


    def on_model_checked(self):
        sender = self.sender()

        if not sender.isChecked():
            self.selected_model = None
            return

        for item in self.models_controls:
            chk = item["enable"]
            if chk is not sender:
                chk.blockSignals(True)
                chk.setChecked(False)
                chk.blockSignals(False)


        for item in self.models_controls:
            if item["enable"] is sender:
                self.selected_model = item["name"]
                break
