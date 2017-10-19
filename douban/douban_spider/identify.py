# -*- coding: utf-8 -*-
import pytesseract
from PIL import Image

def initTable(threshold=140):
 table = []
 for i in range(256):
     if i < threshold:
         table.append(0)
     else:
         table.append(1)

 return table

def return_word():
    img = Image.open('1.jpg')
    img = img.convert('L')
    binaryImage = img.point(initTable(), '1')
    # binaryImage.show()
    return pytesseract.image_to_string(binaryImage, config='-psm 7')

if __name__ == '__main__':
    return_word()
