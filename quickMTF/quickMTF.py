# -*- coding: utf-8 -*-
"""
line pair_MTF- Calculate frequency response  for line pair chart test.
written in 2022 by lorry Rui  Lorryruizhihua@Gmail.com
To the extent possible under law, the author(s) have dedicated all copyright
Line_pair_Mtf with SFR

"""
from .import SFR_MTF
from .import LineP_MTF
import matplotlib.pyplot as plt
import numpy as np



class quickMTF:
    def __init__(self):
        self.Angle = 0
        self.cp_filter = 0
        self.sfr_mtf_calculator = SFR_MTF.sfr_mtfcal()
        self.lineMTF = LineP_MTF.Line_pair_Mtf()

    def add_noise(self, sample_edge, n_well_FS=10000, output_FS=1.0):
        np.random.seed(0)  # make the noise deterministic in order to facilitate comparisons and debugging
        return np.random.poisson(sample_edge / output_FS * n_well_FS) / n_well_FS

    def get_image_size(self, image, library='PIL'):
        if library not in {'PIL', 'cv2'}:
            raise ValueError("Invalid library option. Use 'PIL' or 'cv2'.")

        if library == 'PIL':
            width, height = image.size
        elif library == 'cv2':
            height, width, _ = image.shape

        return width, height

    def relative_luminance(self, rgb_image):
        rgb_w = (0.2126, 0.7152, 0.0722)
        if rgb_image.ndim == 2:
            return rgb_image  # do nothing, this is an MxN image without color data
        else:
            return rgb_w[0] * rgb_image[:, :, 0] + rgb_w[1] * rgb_image[:, :, 1] + rgb_w[2] * rgb_image[:, :, 2]


    def sfr_GUI(self, image, oversampling=2, sequence=0, mtf_indx=0.3, show_plots=5, return_fig=False):
        " this one is for GUI use only "
        sample = self.relative_luminance(image)
        mtf, status = self.sfr_mtf_calculator.calc_sfr(sample, oversampling, show_plots=show_plots, verbose=True,
                                                       return_fig=return_fig)
        if mtf is False:
            print("mtf failed")
            return -1, status['angle'], -1
        mtf_quadr, status_quadr = self.sfr_mtf_calculator.calc_sfr(sample, oversampling, show_plots=0, verbose=True,
                                                                   return_fig=return_fig, quadratic_fit=True)
        if mtf_quadr is False:
            print("mtf_quadr failed")
            return -1, status['angle'], -1
        self.Angle = status['angle']
        filtered_first_elements = mtf[:, 1]
        absolute_diff = np.abs(filtered_first_elements - mtf_indx)
        closest_index = np.argmin(absolute_diff)
        self.cp_filter = mtf[closest_index, 0]
        filtered_first_elements = mtf[:, 0]
        absolute_diff = np.abs(filtered_first_elements - 0.5)
        closest_index = np.argmin(absolute_diff)
        mtf_nyquist = mtf[closest_index, 1] * 100
        if show_plots >= 1:
            plt.figure()
            # Set dark mode color scheme
            plt.style.use('classic')
            plt.plot(mtf[:, 0], mtf[:, 1], '.-', label="linear fit to edge")
            plt.plot(mtf_quadr[:, 0], mtf_quadr[:, 1], '.-', label="quadratic fit to edge")
            f = np.arange(0.0, 1.0, 0.01)
            mtf_sinc = np.abs(np.sinc(f))
            plt.plot(f, mtf_sinc, 'k-', label="sinc")
            plt.xlim(0, 1.2)
            plt.ylim(0, 1.2)
            textstr = f"Edge angle: {status['angle']:.1f}°"
            props = dict(facecolor='w', alpha=0.5)
            ax = plt.gca()
            plt.text(0.65, 0.60, textstr, transform=ax.transAxes,
                     verticalalignment='top', bbox=props)
            plt.grid()
            shape = f'{sample.shape[1]:d}x{sample.shape[0]:d} px'
            noise = 'out noise'
            plt.title(
                f'seq:{sequence}:SFR from {shape:s} curved slanted edge\nwith{noise:s}, edge angle={self.Angle:.1f}°')
            plt.ylabel('MTF')
            plt.xlabel('Spatial frequency (cycles/pixel)')
            plt.legend(loc='best')
            plt.show()
        self.cp_filter = self.cp_filter.ravel()[0]
        return round(self.cp_filter, 2), round(self.Angle, 2), round(mtf_nyquist, 2)

    def linepairMTF_Gui(self, image, ROIX, ROIY, ROI_width, ROI_height=1, plotflag=0, timmer=0, flip=False,library='cv2'):
        " this one is for GUI use only "
        cropped_image = image[ROIY:ROIY + ROI_height , ROIX:ROIX + ROI_width]
        if flip==True:
            if library == 'PIL':
                image = cropped_image.rotate(-90, expand=True)
            elif library == 'cv2':
                image = np.rot90(cropped_image, k=-1)
            # Rotate the image by transposing and mirroring
            ROI_width, ROI_height = self.get_image_size(image,library)
        MTF_ave,pl=self.lineMTF.Processing_MTF(image,ROI_width, ROI_height ,plotflag,library)
        if plotflag == 1:
            plt.title(f'seq:{timmer}: MTF:{MTF_ave}, pixel/pair:{pl}')
        return MTF_ave, pl

    def quicklinepairMTF(self, image, flip=False,library='cv2'):
        if flip==True:
            if library == 'PIL':
                image = image.rotate(-90, expand=True)
            elif library == 'cv2':
                image = np.rot90(image, k=-1)
        ROI_width, ROI_height = self.get_image_size(image,library)
        MTF_ave,pl=self.lineMTF.Processing_MTF(image,ROI_width, ROI_height ,0,library)
        return MTF_ave, pl

    def quicksfrMTF(self, image,cp=0.5, oversampling=2):
        sample = self.relative_luminance(image)
        mtf, status = self.sfr_mtf_calculator.calc_sfr(sample, oversampling, show_plots=0, verbose=True,
                                                       return_fig=False)
        if mtf is False:
            print("mtf failed")
            return -1, status['angle']
        self.Angle = status['angle']
        filtered_first_elements = mtf[:, 0]
        # Calculate the absolute differences between each element and the target value
        absolute_diff = np.abs(filtered_first_elements - cp)
        # Get the index of the element with the smallest absolute difference
        closest_index = np.argmin(absolute_diff)
        mtf_filter =mtf[closest_index,1]*100
        return round(mtf_filter.ravel()[0], 2), round(self.Angle, 2)

    def quicksfrCP(self, image ,mtf_indx=30, oversampling=2):
        sample = self.relative_luminance(image)
        mtf, status = self.sfr_mtf_calculator.calc_sfr(sample, oversampling, show_plots=0, verbose=True,
                                                       return_fig=False)
        if mtf is False:
            print("mtf failed")
            return -1, status['angle']
        filtered_first_elements = mtf[:,1]
        absolute_diff = np.abs(filtered_first_elements - mtf_indx/100)
        closest_index = np.argmin(absolute_diff)
        cp_filter =mtf[closest_index,0]
        cp_filter = cp_filter.ravel()[0]
        return round(cp_filter, 2), round(self.Angle, 2)


if __name__ == '__main__':
    pass




