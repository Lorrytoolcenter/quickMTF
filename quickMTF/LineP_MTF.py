# -*- coding: utf-8 -*-
"""
line pair_MTF- Calculate frequency response  for line pair chart test.
written in 2022 by lorry Rui  Lorryruizhihua@Gmail.com
To the extent possible under law, the author(s) have dedicated all copyright
Line_pair_Mtf
The equation for MTF is derived from the sine pattern contrast C(f) at spatial frequency f, where

𝐶(𝑓)=(𝑉𝑚𝑎𝑥−𝑉𝑚𝑖𝑛)/(𝑉𝑚𝑎𝑥+𝑉𝑚𝑖𝑛)    for luminance (“modulation”)

𝑀𝑇𝐹(𝑓)=100%×𝐶(𝑓)𝐶(0)      Note: this normalizes MTF to 100% at low spatial frequencies.
Traditional resolution measurements involve observing an image of bar patterns, most frequently the USAF 1951 chart and
 estimating the highest spatial frequency (lp/mm) where bar patterns are visibly distinct.
https://www.imatest.com/support/docs/23-1/sharpness/

"""

from scipy.signal import  find_peaks
import matplotlib.pyplot as plt
import numpy as np

class Line_pair_Mtf:
    def __init__(self):
        self.timer=0
        self.peak_distances=[]
        self.slopedata=[]
        pass

    def rgb_to_luminance(self, rgb_value, library='PIL'):
        if library not in {'PIL', 'cv2'}:
            raise ValueError("Invalid library option. Use 'PIL' or 'cv2'.")

        if library == 'PIL':
            r, g, b = rgb_value
        elif library == 'cv2':
            b, g, r = rgb_value

        luminance = 0.2126 * r + 0.7152 * g + 0.0722 * b
        return luminance

    def get_image_pixel(self,image, library='PIL'):
        if library not in {'PIL', 'cv2'}:
            raise ValueError("Invalid library option. Use 'PIL' or 'cv2'.")
        if library == 'PIL':
            pixel_access = image.load()
            get_pixel = lambda x, y: pixel_access[x, y]
        elif library == 'cv2':
            get_pixel = lambda x, y: image[y, x]
        return get_pixel

    def angle_from_slope(self,slope):
        return np.rad2deg(np.arctan(slope))

    def mtfcal(self,image,ROI_width,ROI_height=1,library='PIL'):
        alldata, alldata1=[],[]
        get_pixel = self.get_image_pixel(image, library)
        for i in range(ROI_width):
            PixelValue = get_pixel(i,ROI_height)
            sensorlevel=self.rgb_to_luminance(PixelValue,library)
            alldata.append(sensorlevel)
            alldata1.append(sensorlevel*-1)
        peaks = find_peaks(alldata, height=30, width= 2,prominence=20)
        peaks_indices = peaks[0]  # Extract the indices from the tuple
        # Calculate the average distance between neighboring peaks
        if len(peaks_indices) > 1:
            peak_distances = np.mean(np.diff(peaks_indices))
        else:
            peak_distances=np.nan
        self.peak_distances.append(peak_distances)
        trough,_=find_peaks(alldata1,threshold=1, width= 2)
        return alldata, peaks,trough


    def linepaire_mtf(self,image,ROI_width,ROI_height=1,plotflag=1,library='PIL'):
        MTF=0
        # Crop the image using the calculated coordinate
        alldata,peaka,trougha =self.mtfcal(image, ROI_width,ROI_height,library)
        pak_pos=peaka[0][2:]
        height=peaka[1]['peak_heights'][2:]
        trough_pos,height2=[],[]
        for i in range(1,len(trougha)):
            trough_pos.append(trougha[i])
            height2.append(alldata[trougha[i]])
        if len(height) !=0 and len(height2)!=0:
            MTF=(sum(height) / len(height)-sum(height2) / len(height2))/(sum(height) / len(height)+sum(height2) / len(height2))
        if plotflag >0:
            plt.style.use('dark_background')
            plt.plot(alldata)
            plt.plot(pak_pos, height, "x")
            plt.plot(trough_pos, height2, "d")
        return round(MTF,2)

    def Processing_MTF(self,cropimage,ROI_width=100,ROI_height=10,plotflag=0,library='PIL'):
        MTF_ave,angle=0,0
        self.slopedata=[]
        for i in range(ROI_height):
            MTF=self.linepaire_mtf(cropimage,ROI_width,i,plotflag,library)
            MTF_ave=MTF_ave+MTF/ROI_height
        MTF_ave=round(MTF_ave,3)*100
        peak_distances1=0  if len(self.peak_distances)<2 or np.all(np.isnan(self.peak_distances)) else np.nanmean(self.peak_distances)
        ' if no peak found or nan value . we need to set 0  and do exception'
        self.peak_distances=[]
        return round(MTF_ave,2),round(peak_distances1,1)


if __name__ == '__main__':
    pass

