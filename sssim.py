import os
import sys
import cv2
import glob
import matplotlib.pyplot as plt
from skimage.measure import compare_ssim

# [Splash]:
# square_bobber_64.png
# square_bobber_70.png

file_mask = 'bobber_movie/square_bobber_{0}.png'
path, dirs, files = next(os.walk('bobber_movie/'))
_file_cnt = len(files)

# SSIM both 1 => 64 as well as 63 => 64 for 2 data points to guess with?

'''
f = open('ssim_log_vs_first.txt','w+')
for x in range(1, _file_cnt):
    imageA = cv2.imread(file_mask.format(1))
    imageB = cv2.imread(file_mask.format(x))
    grayA = cv2.cvtColor(imageA, cv2.COLOR_BGR2GRAY)
    grayB = cv2.cvtColor(imageB, cv2.COLOR_BGR2GRAY)
    (score, diff) = compare_ssim(grayA, grayB, full=True)
    diff = (diff * 255).astype("uint8")
    ssim_score = 'SSIM: {0} | img1: {1} / img2: {2}'.format(score, x, x+1)
    f.write(ssim_score+'\n')
    #print ssim_score
f.close()
'''

'''
f = open('ssim_log_stepwise.txt','w+')
for x in range(1, _file_cnt, 2):
    if x+1 < _file_cnt:
        imageA = cv2.imread(file_mask.format(x))
        imageB = cv2.imread(file_mask.format(x+1))
        grayA = cv2.cvtColor(imageA, cv2.COLOR_BGR2GRAY)
        grayB = cv2.cvtColor(imageB, cv2.COLOR_BGR2GRAY)
        (score, diff) = compare_ssim(grayA, grayB, full=True)
        diff = (diff * 255).astype("uint8")
        ssim_score = 'SSIM: {0} | img1: {1} / img2: {2}'.format(score, x, x+1)
        f.write(ssim_score+'\n')
        #print ssim_score
f.close()
'''








'''
# https://www.pyimagesearch.com/2017/06/19/image-difference-with-opencv-and-python/
# threshold the difference image, followed by finding contours to
# obtain the regions of the two input images that differ
thresh = cv2.threshold(diff, 0, 255,
cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)[1]
cnts = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL,
cv2.CHAIN_APPROX_SIMPLE)
cnts = imutils.grab_contours(cnts)

# loop over the contours
for c in cnts:
    # compute the bounding box of the contour and then draw the
    # bounding box on both input images to represent where the two
    # images differ
    (x, y, w, h) = cv2.boundingRect(c)
    cv2.rectangle(imageA, (x, y), (x + w, y + h), (0, 0, 255), 2)
    cv2.rectangle(imageB, (x, y), (x + w, y + h), (0, 0, 255), 2)

# show the output images
cv2.imshow("Original", imageA)
cv2.imshow("Modified", imageB)
cv2.imshow("Diff", diff)
cv2.imshow("Thresh", thresh)
cv2.waitKey(0)
'''