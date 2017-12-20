import cv2 as cv
import numpy as np
from skimage import morphology
from pytesseract import pytesseract


class TrainOCR(object):
    pass


class PreProc(object):

    def denoise(self, file):
        bgrimg = cv.imread(file)
        grayimg = np.ndarray([bgrimg.shape[0], bgrimg.shape[1]], dtype='B')
        marks = []
        noise = set()
        if bgrimg.data:
            for row in range(bgrimg.shape[0]):
                for col in range(bgrimg.shape[1]):
                    # 如果BGR空间中的G的值是101，就标记这个点
                    if bgrimg[row][col][1] == 101:
                        marks.append((row, col))
                    grayimg[row][col] = bgrimg[row][col][1]
            for p in marks:
                rect = [p, (p[0] + 1, p[1]), (p[0], p[1] + 1), (p[0] + 1, p[1] + 1)]
                cross = [(p[0], p[1] - 1), (p[0], p[1] + 1), (p[0] - 1, p[1]), (p[0] + 1, p[1])]
                # 如果P的右边，下边，右下都具有干扰线的颜色则P及另外3个点都是干扰线上的点。
                if rect[1] in marks and rect[2] in marks and rect[3] in marks:
                    noise.update(rect)
                else:
                    flag = True
                    for c in cross:
                        if (c not in marks) and (
                                c[0] < grayimg.shape[0] and c[1] < grayimg.shape[1] and grayimg[c[0], c[1]] != 255):
                            flag = False
                    if flag:
                        noise.add(p)
            # 将干扰线图成白色即去除
            for nsp in noise:
                grayimg[nsp] = 255
            grayimg = cv.resize(grayimg, None, fx=10, fy=10)
            # cv.Laplacian(grayimg, 5, grayimg, 15)
            # cv.Sobel(grayimg, 8, 1, 1, grayimg)
            # cv.findContours()
            grayimg = cv.Canny(grayimg,0,120)
            cv.imshow('image', grayimg)
            cv.waitKey(0)

            new = grayimg.copy()
            mser = cv.MSER_create()
            regions = mser.detectRegions(new)
            hull = [cv.convexHull(p.reshape(-1, 1, 2)) for p in regions[0]]
            cv.polylines(new, hull, 1, (0, 255, 0))
            cv.imshow('image', new)
            cv.waitKey(0)
            return grayimg


if __name__ == '__main__':
    cimg = PreProc().denoise(r'D:\Users\admin\Desktop\5PNyG.png')
    cv.imwrite(r'D:\Users\admin\Desktop\test2.png', cimg)
