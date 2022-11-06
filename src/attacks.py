import numpy as np
from skimage import filters
from cv2 import resize as cv2_resize, IMWRITE_JPEG_QUALITY as cv2_IMWRITE_JPEG_QUALITY, imwrite as cv2_imwrite, imread as cv2_imread, medianBlur as cv2_medianBlur, COLOR_RGB2BGR as cv2_COLOR_RGB2BGR, COLOR_BGR2RGB as cv2_COLOR_BGR2RGB, cvtColor as cv2_cvtColor
from os import remove as os_remove
from random import choice as random_choice

# Wrapper to call every attack function
# Params: img (cv2.imread obj), attack_name (string), attack_parmas (tuple)
# Return: success (boolean), attacked (cv2.imread obj)
#         failure (boolean), error (error obj)
def attack_image(attack_name, attack_params):
    try:
        attacks = {'awgn' : awgn, 'blur' : blur, 'sharpening' : sharpening, 'median' : median, 'resizing' : resizing, 'jpeg_compression' : jpeg_compression}
        attacked = attacks[attack_name](*attack_params)
        return (True, attacked)
    except Exception as error:
        return (False, error)


def awgn(img, std):
    mean = 0.0
    attacked = img + np.random.normal(mean, std, img.shape)
    attacked = np.clip(attacked, 0, 255)
    return attacked


def blur(img, sigma):
    attacked = filters.gaussian(img, sigma = sigma, channel_axis = 2)
    return attacked


def sharpening(img, sigma, alpha):
    filter_blurred_f = filters.gaussian(img, sigma = sigma, channel_axis = 2)
    attacked = img + alpha * (img - filter_blurred_f)
    return attacked


def median(img, kernel_size):
    temp = cv2_cvtColor(img, cv2_COLOR_RGB2BGR)
    attacked = cv2_medianBlur(temp, kernel_size)
    attacked = cv2_cvtColor(attacked, cv2_COLOR_BGR2RGB)
    return attacked


def resizing(img, scale):
    x = img.shape[1]
    y = img.shape[0]
    new_x = int(x*scale)
    new_y = int(y*scale)
    attacked = cv2_resize(img, (new_x, new_y))
    attacked = cv2_resize(attacked, (x, y))
    return attacked


def jpeg_compression(img, QF):
    random_string = ''.join(random_choice('abcdefghilmnopqrstuvz1234567890') for _ in range(7))
    cv2_imwrite(random_string + '.jpg', img, [int(cv2_IMWRITE_JPEG_QUALITY), QF])
    attacked = cv2_imread(random_string + '.jpg', 1)
    os_remove(random_string + '.jpg')
    return attacked
