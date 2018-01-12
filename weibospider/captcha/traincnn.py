import os
import random

import cv2 as cv
import numpy as np
from skimage import morphology
from keras.models import *
from keras.layers import *
from weibospider.utils import TailRecursion

LEN_CAPTCHA = 5
HEIGHT = 40
WIDTH = 100
CHARSET = '23456789ABCDEFGHKLMNPQRSUVWXYZabcdefhkmnopqrsuvwxyz'


class PreProcImg(object):

    def __init__(self, file, height=HEIGHT, width=WIDTH, len_captcha=LEN_CAPTCHA, charset=CHARSET):
        # self.threshold = 200
        self.file = file
        bgr_img = cv.imread(self.file)
        if bgr_img is not None:
            # 只保留G通道，B和R通道的值一个与G相等，另一个等于254，并且随机交换
            self.gray_img = bgr_img[:, :, 1]
        else:
            raise RuntimeError('文件读取失败')
        self.height = height or self.gray_img.shape[0]
        self.width = width or self.gray_img.shape[1]
        self.len_captcha = len_captcha
        self.charset = charset

    def find_noise(self):
        height = self.height
        width = self.width
        marks = []
        noise = set()
        for row in range(height):
            for col in range(width):
                # 如果值是101，就标记这个点
                if self.gray_img[row][col] == 101:
                    marks.append((row, col))
        for p in marks:
            rect = [p, (p[0] + 1, p[1]), (p[0], p[1] + 1), (p[0] + 1, p[1] + 1)]
            cross = [(p[0], p[1] - 1), (p[0], p[1] + 1), (p[0] - 1, p[1]), (p[0] + 1, p[1])]
            # 如果P的右边，下边，右下都具有干扰线的颜色则P及另外3个点都是干扰线上的点。
            if rect[1] in marks and rect[2] in marks and rect[3] in marks:
                noise.update(rect)
            else:
                flag = True
                for c in cross:
                    if (c not in marks) and (c[0] < height and c[1] < width and self.gray_img[c[0], c[1]] != 255):
                        flag = False
                if flag:
                    noise.add(p)
        return noise

    def division(self, threshold, minsize, maxsize, bgcolor=255, findslant=False):
        """把颜色大于等于阈值的相连的点组成区域，并去除不满足面积大小限制的区域"""
        height = self.height
        width = self.width
        gray_img = self.gray_img
        new_img = gray_img.copy()
        # 1 创建区域list
        # 2 遍历矩阵，每当找到一个白色点，创建一个区域，执行3
        # 3 将白点涂黑，放入区域中，寻找当前白点周围4点的中的白点，如果发现白点重复3 （递归）
        # 4 将2的区域追加到区域list中，继续2，直到遍历完成
        # 5 返回区域list
        arealist = []

        @TailRecursion.tail_call_optimized
        def makearea(points, area, thresh, slant):
            neighbors = set()
            for point in points:
                r, c = point
                new_img[point] = 0
                area.append(point)
                if r - 1 >= 0 and new_img[r - 1, c] >= thresh: neighbors.add((r - 1, c))
                if r + 1 < height and new_img[r + 1, c] >= thresh: neighbors.add((r + 1, c))
                if c - 1 >= 0 and new_img[r, c - 1] >= thresh: neighbors.add((r, c - 1))
                if c + 1 < width and new_img[r, c + 1] >= thresh: neighbors.add((r, c + 1))
                if slant:
                    if r - 1 >= 0 and c - 1 >= 0 and new_img[r - 1, c - 1] >= thresh: neighbors.add((r - 1, c - 1))
                    if r - 1 >= 0 and c + 1 < width and new_img[r - 1, c + 1] >= thresh: neighbors.add((r - 1, c + 1))
                    if r + 1 >= 0 and c - 1 >= 0 and new_img[r + 1, c - 1] >= thresh: neighbors.add((r + 1, c - 1))
                    if r + 1 >= 0 and c + 1 < width and new_img[r + 1, c + 1] >= thresh: neighbors.add((r + 1, c + 1))

            if len(neighbors) == 0:
                return
            makearea(neighbors, area, thresh, slant)

        for row in range(height):
            for col in range(width):
                if new_img[row][col] >= threshold:
                    _area = []
                    arealist.append(_area)
                    makearea([(row, col)], _area, threshold, findslant)
        gray_img.fill(bgcolor)
        for a in arealist[:]:
            if minsize < len(a) < maxsize:
                for p in a:
                    gray_img[p] = 255 - bgcolor
                arealist.remove(a)
        return arealist

    def fix_noise(self, noise_point):
        """去除图像中的噪点"""
        for _np in noise_point:
            self.gray_img[_np] = 255

    def fix_crack(self, noise_point):
        """修复去除噪点后留下的缝隙"""
        gray_img = self.gray_img
        height = self.height
        width = self.width
        for _np in noise_point:
            if _np[0] - 1 >= 0 and _np[0] + 2 < height:
                # 修复垂直方向双间隔噪点
                if (_np[0] + 1, _np[1]) in noise_point and gray_img[_np[0] - 1, _np[1]] == gray_img[
                    _np[0] + 2, _np[1]] == 0:
                    gray_img[_np] = gray_img[_np[0] + 1, _np[1]] = 0
                # 修复正斜向双间隔噪点
                # if _np[1]-1>=0 and _np[1]+2<x:
                #     if (_np[0]+1,_np[1]+1) in noise and gray_img[_np[0]-1,_np[1]-1]==gray_img[_np[0]+2,_np[1]+2]==0:
                #         gray_img[_np]=gray_img[_np[0]+1,_np[1]+1]=0
                # 修复反斜向双间隔噪点
                # if _np[1]-2>=0 and _np[1]+1<x:
                #     if (_np[0]+1,_np[1]-1) in noise and gray_img[_np[0]-1,_np[1]+1]==gray_img[_np[0]+2,_np[1]-2]==0:
                #         gray_img[_np]=gray_img[_np[0]+1,_np[1]-1]=0
            if _np[0] - 1 >= 0 and _np[0] + 1 < height:
                # 修复垂直方向单间隔噪点
                if gray_img[_np[0] - 1, _np[1]] == gray_img[_np[0] + 1, _np[1]] == 0:
                    gray_img[_np] = 0
                # 修复斜向单间隔噪点
                # if _np[1]-1>=0 and _np[1]+1<x:
                #     if gray_img[_np[0]-1,_np[1]-1]==gray_img[_np[0]+1,_np[1]+1]==0 or gray_img[_np[0]-1,_np[1]+1]==gray_img[_np[0]+1,_np[1]-1]==0:
                #         gray_img[_np]=0

    def skeletonize(self, threshold=0):
        gray_img = self.gray_img
        bin_img = 1 - cv.threshold(gray_img, threshold, 1, cv.THRESH_BINARY)[1]
        gray_img = morphology.skeletonize(bin_img) * 255
        self.gray_img = gray_img.astype(np.uint8)

    def open(self, ksize=(2, 2)):
        kernel = cv.getStructuringElement(cv.MORPH_CROSS, ksize)
        self.gray_img = cv.morphologyEx(self.gray_img, cv.MORPH_OPEN, kernel)

    def close(self, ksize=(2, 2)):
        kernel = cv.getStructuringElement(cv.MORPH_CROSS, ksize)
        self.gray_img = cv.morphologyEx(self.gray_img, cv.MORPH_CLOSE, kernel)

    @staticmethod
    def gen_batch(path, batch_size=32):
        """
        x:(batch_size,height,width,1)
        y:(batch_size,len_charset)
        :param path:
        :param batch_size:
        :return:
        """
        path = path if path.endswith('\\') else '{}\\'.format(path)
        file_list = os.listdir(path)
        random.shuffle(file_list)
        if len(file_list) > 0:
            img = PreProcImg(path + file_list[0])
            height = img.height
            width = img.width
            len_captcha = img.len_captcha
            len_charset = len(img.charset)
            shape_x = [batch_size, height, width, 1]
            shape_y = [batch_size, len_charset]
            cnt = 0
            while len(file_list) - cnt >= batch_size:
                x = np.zeros(shape_x, dtype=np.uint8)
                y = [np.zeros(shape_y, dtype=np.uint8) for c in range(len_captcha)]
                for i in range(batch_size):
                    file = file_list[cnt]
                    cnt += 1
                    img = PreProcImg(path + file)
                    _np = img.find_noise()
                    img.gray_img=cv.threshold(img.gray_img,200,255,cv.THRESH_BINARY)[1]
                    img.fix_noise(_np)
                    img.fix_crack(_np)
                    img.gray_img = img.gray_img // 255
                    capt = file[:-4]
                    x[i] = np.resize(img.gray_img, (height, width, 1))
                    for k in range(len_captcha):
                        y[k][i][img.charset.find(capt[k])] = 1
                yield x, y
            raise RuntimeError('Sample Not Enough')


class TrainCnn(object):
    def __init__(self, height=HEIGHT, width=WIDTH, charset=CHARSET):
        self.height = height
        self.width = width
        self.charset = charset
        self.model = self.get_model()

    def get_model(self):
        input_tensor = Input((self.height, self.width, 1))
        x = input_tensor
        for i in range(2):
            x = Conv2D(32, (3, 3), activation='relu')(x)
            # x = Conv2D(32 * 1 ** i, (3, 3), activation='relu')(x)
            # x = Conv2D(32 * 1 ** i, (3, 3), activation='relu')(x)
            x = MaxPool2D((2, 2))(x)
        x = Flatten()(x)
        x = Dropout(0.25)(x)
        x = [Dense(len(self.charset), activation='softmax', name='c%d' % (i + 1))(x) for i in range(5)]
        model = Model(inputs=input_tensor, outputs=x)
        model.compile(loss='categorical_crossentropy',
                      optimizer='adadelta',
                      metrics=['accuracy'])
        return model

    def train_model(self, gen_train, gen_valid):
        # x,y =next(gen_train)
        self.model.fit_generator(gen_train, steps_per_epoch=25, epochs=2, validation_data=gen_valid, validation_steps=1,
                                 workers=1)
        self.model.save('model.h5')


def main():
    gen_train = PreProcImg.gen_batch('D:\marked_train')
    gen_valid = PreProcImg.gen_batch('D:\marked_valid')
    TrainCnn().train_model(gen_train, gen_valid)


if __name__ == '__main__':
    main()
