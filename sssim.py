import os
import sys
import cv2
import matplotlib.pyplot as plt
from skimage.measure import compare_ssim

# [SSIM]:
# https://towardsdatascience.com/image-classification-using-ssim-34e549ec6e12
# https://scikit-image.org/docs/dev/auto_examples/transform/plot_ssim.html
# [Tensor Flow SSIM]:
# https://www.tensorflow.org/api_docs/python/tf/image/ssim
# [Motion Detection]:
# http://www.robindavid.fr/opencv-tutorial/motion-detection-with-opencv.html

# 3. Load the two input images
imageA = cv2.imread('square_bobber/square_bobber_3.png')
#imageB = cv2.imread('square_bobber/square_bobber_7.png') # 3|7 close
imageB = cv2.imread('square_bobber/square_bobber_6.png')  # 3|6 far

# 4. Convert the images to grayscale
grayA = cv2.cvtColor(imageA, cv2.COLOR_BGR2GRAY)
grayB = cv2.cvtColor(imageB, cv2.COLOR_BGR2GRAY)

# 5. Compute the Structural Similarity Index (SSIM) between the two
#    images, ensuring that the difference image is returned
(score, diff) = compare_ssim(grayA, grayB, full=True)
diff = (diff * 255).astype("uint8")

# 6. You can print only the score if you want
print("SSIM: {}".format(score))

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