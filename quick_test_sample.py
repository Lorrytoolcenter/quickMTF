from quickMTF.quickMTF import quickMTF
import cv2
if __name__ == '__main__':
    test = quickMTF()
    ROI_width = 600
    ROIX = 1593
    ROIY = 1500
    image = cv2.imread("image/test.jpg")
    image = image[ROIY:ROIY+10, ROIX:ROIX+ROI_width]

    print(test.quicklinepairMTF(image,library='cv2')) # linepair chart MTF value and pixels/line pair
    print(test.quicksfrMTF(image,cp=0.5)) # CP means cycles/pixel and out MTF value per c/p and slant angle
    print(test.quicksfrCP(image, mtf_indx=30))# MTFindex means MTF and out Cycles/pixel per MTF value and slant angle


