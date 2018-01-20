import os
import random

from keras.models import *
from keras.layers import *

from weibospider.captcha.preprocimg import *


class TrainCnn(object):
    def __init__(self, height=HEIGHT, width=WIDTH, charset=CHARSET, len_captcha=LEN_CAPTCHA):
        self.height = height
        self.width = width
        self.charset = charset
        self.len_captcha = len_captcha
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
        self.model.fit_generator(gen_train, steps_per_epoch=25, epochs=2, validation_data=gen_valid, validation_steps=1,
                                 workers=1)
        self.model.save('model.h5')

    def gen_batch(self, path, batch_size=32):
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
            height = self.height
            width = self.width
            len_captcha = self.len_captcha
            len_charset = len(self.charset)
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
                    img.threshold(200)
                    img.fix_noise(_np)
                    img.fix_crack(_np)
                    img.gray_img = img.gray_img // 255
                    capt = file[:-4]
                    x[i] = np.resize(img.gray_img, (height, width, 1))
                    for k in range(len_captcha):
                        y[k][i][img.charset.find(capt[k])] = 1
                yield x, y
            raise RuntimeError('Sample Not Enough')


def main():
    cnn = TrainCnn()
    gen_train = cnn.gen_batch('D:\marked_train')
    gen_valid = cnn.gen_batch('D:\marked_valid')
    cnn.train_model(gen_train, gen_valid)


if __name__ == '__main__':
    main()
