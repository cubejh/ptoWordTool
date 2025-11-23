import os
from PyPDF2 import PdfReader


class PDFLoader:
    def __init__(self, input_dir="input"):
        self.input_dir = input_dir

    def list_pdfs(self):
        """回傳 input 內所有 PDF 檔案名稱 list"""
        if not os.path.exists(self.input_dir):
            return []

        return [
            f for f in os.listdir(self.input_dir)
            if f.lower().endswith(".pdf")
        ]

    def count_total_pages(self, pdf_file):
        """回傳單一 PDF 的頁面數"""
        try:
            reader = PdfReader(os.path.join(self.input_dir, pdf_file))
            return len(reader.pages)
        except:
            return 0

    def get_pdf_info(self):
        """
        回傳列表，每個元素包含：
        {
            "name" : "xxx.pdf",
            "pages": 12
        }
        """
        pdfs = self.list_pdfs()
        return [
            {
                "name": pdf,
                "pages": self.count_total_pages(pdf),
            }
            for pdf in pdfs
        ]
