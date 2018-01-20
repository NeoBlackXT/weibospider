try:
    import Image
except ImportError:
    from PIL import Image
import pytesseract

from weibospider.captcha.preprocimg import PreProcImg

__all__ = ['recognize']
pytesseract.pytesseract.tesseract_cmd = 'D:\\Dev\\Tesseract-OCR\\tesseract'
LANG = 'sina'


def recognize(imgfile):
    ppimg = PreProcImg(imgfile)
    _np = ppimg.find_noise()
    ppimg.threshold(200)
    ppimg.fix_noise(_np)
    ppimg.fix_crack(_np)
    image = Image.fromarray(ppimg.gray_img)
    config = '--psm 8'
    return pytesseract.image_to_string(image, LANG, False, config)


def main():
    path = r'D:\marked_valid'
    import os
    files = os.listdir(path)
    n = len(files)
    cnt = 0
    for file in files:
        ocr = recognize(os.path.join(path, file))
        truth = os.path.splitext(file)[0]
        print('{},{}'.format(ocr, truth))
        if ocr.lower() == truth.lower():
            cnt += 1
    print('正确率：{}'.format(cnt / n))


if __name__ == '__main__':
    main()
