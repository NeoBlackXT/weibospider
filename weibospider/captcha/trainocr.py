try:
    import Image
except ImportError:
    from PIL import Image
import cv2 as cv
import os
import pytesseract

from weibospider.captcha.preprocimg import PreProcImg

pytesseract.pytesseract.tesseract_cmd = 'D:\\Dev\\Tesseract-OCR\\tesseract'

# 输入原始图像
INPUT_PATH = r'D:\marked_train'
# 输出二值图像
OUTPUT_PATH = r'D:\output_valid'
# 合并为TIFF图像
TIFF_PATH = r'D:\tiff'
# 每个TIFF图像的页数
BATCH_SIZE = 32


def main():
    # trans_img()
    # make_box_tesseract()
    make_box_tag()


def make_box_tag():
    """从tag标签创建box文件，使用默认字符位置"""
    # box文件格式
    # 每一行标记一个字符，坐标原点是左下角，tiff图像文件可有多页，其box文件也是多页的
    # 字符 左下角点x 左下角点y 右上角点x 右上角点y 页码
    # 5 6 4 23 33 0
    # v 24 4 40 33 0
    # B 41 4 59 33 0
    # C 60 4 75 33 0
    # x 76 4 93 33 0
    os.makedirs(TIFF_PATH, exist_ok=True)
    file_names = os.listdir(OUTPUT_PATH)
    n_batch = len(file_names) // BATCH_SIZE
    file_names = filter(lambda x: x.endswith('.png'), file_names)
    for n in range(n_batch):
        tiff_name = '{:04}.tif'.format(n)
        tiff_name = os.path.join(TIFF_PATH, tiff_name)
        box_name = '{:04}.box'.format(n)
        box_name = os.path.join(TIFF_PATH, box_name)
        pngs = []
        captchas = []
        for i in range(BATCH_SIZE):
            captcha = next(file_names)
            png_name = os.path.join(OUTPUT_PATH, captcha)
            png = Image.open(png_name)
            pngs.append(png)
            captchas.append(os.path.splitext(captcha)[0])
        pngs[0].save(tiff_name, save_all=True, append_images=pngs[1:])
        with open(box_name, 'w') as f:
            for i in range(BATCH_SIZE):
                captcha = list(captchas[i])
                captcha[0] = '{} 6 4 23 33 {}\n'.format(captcha[0], i)
                captcha[1] = '{} 24 4 40 33 {}\n'.format(captcha[1], i)
                captcha[2] = '{} 41 4 59 33 {}\n'.format(captcha[2], i)
                captcha[3] = '{} 60 4 75 33 {}\n'.format(captcha[3], i)
                captcha[4] = '{} 76 4 93 33 {}\n'.format(captcha[4], i)
                captchas[i] = ''.join(captcha)
            captchas = ''.join(captchas)
            f.write(captchas)


def make_box_tesseract():
    """从tesseract创建box文件"""
    file_names = os.listdir(OUTPUT_PATH)
    file_names = filter(lambda x: x.endswith('.png'), file_names)
    for file_name in file_names:
        img = Image.open(os.path.join(OUTPUT_PATH, file_name))
        config = '--psm 8 --user-patterns captcha.user-patterns'
        box = pytesseract.image_to_string(img, lang='eng', boxes=True, config=config)
        box_file = os.path.join(OUTPUT_PATH, os.path.splitext(file_name)[0] + '.box')
        with open(box_file, mode='w', encoding='utf-8') as f:
            f.write(box)


def trans_img():
    """将INPUT中的验证码降噪并二值化图像后另存至OUTPUT中"""
    os.makedirs(OUTPUT_PATH, exist_ok=True)
    for file_name in os.listdir(INPUT_PATH):
        ppimg = PreProcImg(os.path.join(INPUT_PATH, file_name))
        _np = ppimg.find_noise()
        ppimg.threshold(200)
        ppimg.fix_noise(_np)
        ppimg.fix_crack(_np)
        cv.imwrite(os.path.join(OUTPUT_PATH, file_name), ppimg.gray_img)


if __name__ == '__main__':
    main()
