from docx import Document

class ReadDoc:
    def __init__(self, file_path):
        self.file_path = file_path

    def read(self):
        with open(self.file_path, 'r') as file:
            content = file.read()
        return content
    
    def read_lines(self):
        with open(self.file_path, 'r') as file:
            lines = file.readlines()
        return lines 