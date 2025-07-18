import re

class cleantext:
    def cleanText(text:str=None):
        return re.sub(r"`+\w+|`+","", text)
