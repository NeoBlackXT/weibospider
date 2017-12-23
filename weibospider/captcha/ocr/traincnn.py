import os
import cv2 as cv
import numpy as np
from skimage import morphology
from pytesseract import pytesseract
from weibospider.utils import TailRecursion


class TrainCnn(object):
    pass


class PreProc(object):
    def __init__(self, file):
        # self.threshold = 200
        self.file = file
        self.grayimg = self.__g2gary()
        self.y = self.grayimg.shape[0]
        self.x = self.grayimg.shape[1]

    def __g2gary(self):
        bgrimg = cv.imread(self.file)
        if bgrimg is not None:
            grayimg = np.ndarray([bgrimg.shape[0], bgrimg.shape[1]], dtype='B')
            for row in range(bgrimg.shape[0]):
                for col in range(bgrimg.shape[1]):
                    grayimg[row][col] = bgrimg[row][col][1]
            return grayimg
        else:
            raise RuntimeError('文件读取失败')

    def find_noise(self):
        y = self.y
        x = self.x
        marks = []
        noise = set()
        for row in range(y):
            for col in range(x):
                # 如果值是101，就标记这个点
                if self.grayimg[row][col] == 101:
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
                    if (c not in marks) and (c[0] < y and c[1] < x and self.grayimg[c[0], c[1]] != 255):
                        flag = False
                if flag:
                    noise.add(p)
        return noise

    def division(self, threshold, minsize, maxsize,bgcolor=255, findslant=False):
        y = self.y
        x = self.x
        grayimg = self.grayimg
        newimg = grayimg.copy()
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
                newimg[point] = 0
                area.append(point)
                if r - 1 >= 0 and newimg[r - 1, c] >= thresh: neighbors.add((r - 1, c))
                if r + 1 < y and newimg[r + 1, c] >= thresh: neighbors.add((r + 1, c))
                if c - 1 >= 0 and newimg[r, c - 1] >= thresh: neighbors.add((r, c - 1))
                if c + 1 < x and newimg[r, c + 1] >= thresh: neighbors.add((r, c + 1))
                if slant:
                    if r - 1 >= 0 and c - 1 >= 0 and newimg[r - 1, c - 1] >= thresh: neighbors.add((r - 1, c - 1))
                    if r - 1 >= 0 and c + 1 < x and newimg[r - 1, c + 1] >= thresh: neighbors.add((r - 1, c + 1))
                    if r + 1 >= 0 and c - 1 >= 0 and newimg[r + 1, c - 1] >= thresh: neighbors.add((r + 1, c - 1))
                    if r + 1 >= 0 and c + 1 < x and newimg[r + 1, c + 1] >= thresh: neighbors.add((r + 1, c + 1))

            if len(neighbors) == 0:
                return
            makearea(neighbors, area, thresh, slant)

        for row in range(y):
            for col in range(x):
                if newimg[row][col] >= threshold:
                    _area = []
                    arealist.append(_area)
                    makearea([(row, col)], _area, threshold, findslant)
        grayimg.fill(bgcolor)
        for a in arealist[:]:
            if minsize<len(a) < maxsize:
                for p in a:
                    grayimg[p] = 255-bgcolor
                arealist.remove(a)
        return arealist

    def fixup(self, noise):
        grayimg = self.grayimg
        y = self.y
        x = self.x
        for np in noise:
            if np[0] - 1 >= 0 and np[0] + 2 < y:
                # 修复垂直方向双间隔噪点
                if (np[0] + 1, np[1]) in noise and grayimg[np[0] - 1, np[1]] == grayimg[np[0] + 2, np[1]] == 0:
                    grayimg[np] = grayimg[np[0] + 1, np[1]] = 0
                # 修复正斜向双间隔噪点
                # if np[1]-1>=0 and np[1]+2<x:
                #     if (np[0]+1,np[1]+1) in noise and newimg[np[0]-1,np[1]-1]==newimg[np[0]+2,np[1]+2]==0:
                #         newimg[np]=newimg[np[0]+1,np[1]+1]=0
                # 修复反斜向双间隔噪点
                # if np[1]-2>=0 and np[1]+1<x:
                #     if (np[0]+1,np[1]-1) in noise and newimg[np[0]-1,np[1]+1]==newimg[np[0]+2,np[1]-2]==0:
                #         newimg[np]=newimg[np[0]+1,np[1]-1]=0
            if np[0] - 1 >= 0 and np[0] + 1 < y:
                # 修复垂直方向单间隔噪点
                if grayimg[np[0] - 1, np[1]] == grayimg[np[0] + 1, np[1]] == 0:
                    grayimg[np] = 0
                # 修复斜向单间隔噪点
                # if np[1]-1>=0 and np[1]+1<x:
                #     if newimg[np[0]-1,np[1]-1]==newimg[np[0]+1,np[1]+1]==0 or newimg[np[0]-1,np[1]+1]==newimg[np[0]+1,np[1]-1]==0:
                #         newimg[np]=0

    def skeletonize(self, threshold=0):
        grayimg = self.grayimg
        binimg = 1 - cv.threshold(grayimg, threshold, 1, cv.THRESH_BINARY)[1]
        grayimg = morphology.skeletonize(binimg) * 255
        self.grayimg = grayimg.astype('B')


if __name__ == '__main__':
    l = os.listdir(r'D:\Users\admin\Desktop\t')
    for f in l:
        if f.startswith('t') or not f.endswith('png'):
            continue
        name = f
        pre = PreProc(r'D:\Users\admin\Desktop\t\%s' % name)

        # 查找噪点
        noi = pre.find_noise()
        # 划分图形区域
        div = pre.division(threshold=200, minsize=0, maxsize=150)

        # cv.imshow('img', cv.resize(pre.grayimg, None, fx=10, fy=10))
        # cv.waitKey(0)

        # 修复被噪点破环的部分
        pre.fixup(noi)

        # cv.imshow('img', cv.resize(pre.grayimg, None, fx=10, fy=10))
        # cv.waitKey(0)

        # 二值化查找骨骼
        pre.skeletonize()

        # cv.imshow('img', cv.resize(pre.grayimg, None, fx=10, fy=10))
        # cv.waitKey(0)

        # 去掉长度较短的线条
        pre.division(threshold=255,minsize=4,maxsize=100,bgcolor=0,findslant=True)

        # cv.imshow('img', cv.resize(pre.grayimg, None, fx=10, fy=10))
        # cv.waitKey(0)

        # kernel = cv.getStructuringElement(cv.MORPH_CROSS, (2, 2))
        # kernel2 = cv.getStructuringElement(cv.MORPH_CROSS, (2, 2))
        # pre.grayimg = cv.morphologyEx(pre.grayimg, cv.MORPH_CLOSE, kernel)
        # cimg = cv.morphologyEx(cimg, cv.MORPH_CLOSE, kernel)
        # cimg = cv.morphologyEx(cimg, cv.MORPH_CLOSE, kernel)
        # eimg = cv.dilate(cimg, kernel2, iterations=1)
        #
        # cv.imshow('img', cv.resize(cimg, None, fx=10, fy=10))
        # cv.waitKey(0)
        #
        # cv.imshow('img', cv.resize(eimg, None, fx=10, fy=10))
        # cv.waitKey(0)

        # cv.destroyAllWindows()
        cv.imwrite(r'D:\Users\admin\Desktop\s\%s' % name, pre.grayimg)
