from PIL import Image
import pytesseract

image = Image.open('test.png')
text = pytesseract.image_to_string(image, lang='eng')

print(text)


# for bbox, text, confidence in result:
#     print(f'Text: {text}, Confidence: {confidence:.2f}')