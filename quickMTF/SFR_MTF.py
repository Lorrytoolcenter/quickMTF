# -*- coding: utf-8 -*-
"""
SFR_MTF- Calculate spatial frequency response (SFR) for a slanted edge.
Modified in 2023 by lorry Rui  Lorryruizhihua@Gmail.com
and thanks for Carl Asplund
To the extent possible under law, the author(s) have dedicated all copyright
class sfr_mtfcal has madded  some exception when no slant detection
Calculate spatial frequency response (SFR), MTF, for a slanted edge.
And I do ignore some none slant edge which less than 0.9 degree
* input: image patch with slanted edge to be analyzed (2-d Numpy array of float)
* input (optional): oversampling (integer), default is 4
* input (optional): show_plots (integer), a kind of "verbosity" for plots, default is 0, i.e. no plots
* input (optional): angle (degrees) of the edge, if not specified a fitted value will be used
* input (optional): offset (px) of the edge, if not specified a fitted value will be used
* input (optional): quadratic_fit, if True fit a second order polynomial to the slanted edge
* output: MTF organized as a 2-d array where first column is spatial frequency, and second column contains MTF values
* output: status dict with fitted edge angle (c.w. from vertical), offset, image rotation etc.
NB: SFR calculations will fail for edge angles of 0°, 45°, and 90° (an inherent limitation of the method)
"""

import numpy as np
import scipy.signal
import matplotlib.pyplot as plt

class sfr_mtfcal:
    def __init__(self):
        pass
    def angle_from_slope(self,slope):
        return np.rad2deg(np.arctan(slope))

    def slope_from_angle(self,angle):
        return np.tan(np.deg2rad(angle))

    def centroid(self,arr, conv_kernel=3, win_width=5):
        height, width = arr.shape

        win = np.zeros(arr.shape)
        for i in range(height):
            win_c = np.argmax(np.abs(np.convolve(arr[i, :], np.ones(conv_kernel), 'same')))
            win[i, win_c - win_width:win_c + win_width] = 1.0
        x, _ = np.meshgrid(np.arange(width), np.arange(height))
        sum_arr = np.sum(arr * win, axis=1)
        sum_arr_x = np.sum(arr * win * x, axis=1)
        with np.errstate(divide='ignore', invalid='ignore'):
            return sum_arr_x / sum_arr  # divide-by-zero warnings are suppressed


    def differentiate(self,arr, kernel):
        if len(arr.shape) == 2:
            # Use 2-d convolution, but with a one-dimensional (row-oriented) kernel
            out = scipy.signal.convolve2d(arr, [kernel], 'same', 'symm')
        else:
            # Input is a one-dimensional array
            out = np.convolve(arr, kernel, 'same')
            out[0] = 0.0
        return out


    def find_edge(self,centr, patch_shape, rotated, angle=None, show_plots=False, verbose=False):

        idx = np.where(np.isfinite(centr))[0][1:-1]
        if angle is None:
            slope, offset = np.polyfit(idx, centr[idx], 1)
        else:
            slope = self.slope_from_angle(angle)
            offset = np.polyfit(idx, centr[idx] - slope * idx, 0)
        pcoefs = np.polyfit(idx, centr[idx], 2)
        angle = self.angle_from_slope(slope)


        if show_plots == 5:
            verbose and print("showing plots!")
            fig, ax = plt.subplots()
            if rotated:
                ax.plot(idx, patch_shape[1] - centr[idx], '.k', label="centroids")
                ax.plot(idx, patch_shape[1] - np.polyval([slope, offset], idx), '-', label="linear fit")
                ax.plot(idx, patch_shape[1] - np.polyval(pcoefs, idx), '--', label="quadratic fit")
                ax.set_xlim([0, patch_shape[0]])
                ax.set_ylim([0, patch_shape[1]])
            else:
                ax.plot(centr[idx], idx, '.k', label="centroids")
                ax.plot(np.polyval([slope, offset], idx), idx, '-', label="linear fit")
                ax.plot(np.polyval(pcoefs, idx), idx, '--', label="quadratic fit")
                ax.set_xlim([0, patch_shape[1]])
                ax.set_ylim([0, patch_shape[0]])
            #ax.text("{angle}")
            ax.set_aspect('equal', 'box')
            ax.legend(loc='best')
            ax.invert_yaxis()
            #plt.show()

        return pcoefs, slope, offset,angle


    def midpoint_slope_and_curvature_from_polynomial(self,a, b, c, y0, y1):
        # Describe input 2nd degree polynomial f(y) = a*y**2 + b*y + c in
        # terms of midpoint, slope (at midpoint), and curvature (at midpoint)
        y_mid = (y1 + y0) / 2
        x_mid = a * y_mid ** 2 + b * y_mid + c
        # Calculated slope as first derivative of x = f(y) at y = y_mid
        slope = 2 * a * y_mid + b
        # Calculate the curvature as k(y) = f''(y) / (1 + f'(y)^2)^(3/2)
        curvature = 2 * a / (1 + slope ** 2) ** (3 / 2)
        return y_mid, x_mid, slope, curvature


    def polynomial_from_midpoint_slope_and_curvature(self,y_mid, x_mid, slope, curvature):
        # Calculate a 2nd degree polynomial x = f(y) = a*y**2 + b*y + c that passes
        # through the midpoint (x_mid, y_mid) with the given slope and curvature
        a = curvature * (1 + slope ** 2) ** (3 / 2) / 2
        b = slope - 2 * a * y_mid
        c = x_mid - a * y_mid ** 2 - b * y_mid
        return [a, b, c]


    def cubic_solver(self,a, b, c, d):
        # Solve the equation a*x**3 + b*x**2 + c*x + d = 0 for a
        # real-valued root x by Cardano's method
        # (https://en.wikipedia.org/wiki/Cubic_equation#Cardano's_formula)

        p = (3 * a * c - b ** 2) / (3 * a ** 2)
        q = (2 * b ** 3 - 9 * a * b * c + 27 * a ** 2 * d) / (27 * a ** 3)

        # A real root exists if 4 * p**3 + 27 * q**2 > 0
        sr = np.sqrt(q ** 2 / 4 + p ** 3 / 27)
        t = np.cbrt(-q / 2 + sr) + np.cbrt(-q / 2 - sr)
        x = t - b / (3 * a)
        return x


    def dot(self,a, b):
        return a[0] * b[0] + a[1] * b[1]


    def calc_distance(self,data_shape, p, quadratic_fit=False, verbose=False):
        # Calculate the distance (with sign) from each point (x, y) in the
        # image patch "data" to the slanted edge described by the polynomial p.
        # It is assumed that the edge is approximately vertically orientated
        # (between -45° and 45° from the vertical direction).
        # Distances to points to the left of the edge are negative, and positive
        # to points to the right of the edge.
        x, y = np.meshgrid(range(data_shape[1]), range(data_shape[0]))

        #verbose and print(f'quadratic fit: {str(quadratic_fit):s}')

        if not quadratic_fit or p[0] == 0.0:
            slope, offset = p[1], p[2]  # use linear fit to edge
            a, b, c = 1, -slope, -offset
            a_b = np.sqrt(a ** 2 + b ** 2)

            # |ax+by+c| / |a_b| is the distance from (x,y) to the slanted edge:
            dist = (a * x + b * y + c) / a_b
        else:
            # Define a cubic polynomial equation for the y-coordinate
            # y0 at the point (x0, y0) on the curved edge that is closest to (x, y)
            d = -y + p[1] * p[2] - x * p[1]
            c = 1 + p[1] ** 2 + 2 * p[2] * p[0] - 2 * x * p[0]
            b = 3 * p[1] * p[0]
            a = 2 * p[0] ** 2

            if p[0] == 0.0:
                y0 = -d / c  # solution if edge is straight (quadratic term is zero)
            else:
                y0 = self.cubic_solver(a, b, c, d)  # edge is curved

            x0 = p[0] * y0 ** 2 + p[1] * y0 + p[2]
            dxx_dyy = np.array(2 * p[0] * y0 + p[1])  # slope at (x0, y0)
            r2 = self.dot([1, -dxx_dyy], [1, -dxx_dyy])
            # distance between (x, y) and (x0, y0) along normal to curve at (x0, y0)
            dist = self.dot([x - x0, y - y0], [1, -dxx_dyy]) / np.sqrt(r2)
        return dist


    def project_and_bin(self,data, dist, oversampling, verbose=True):


        bins = np.round(dist * oversampling).astype(int)
        bins = bins.flatten()
        bins -= np.min(bins)  # add an offset so that bins start at 0
        if np.max(bins) <=4 or np.max(bins) >=10000 :
            return False
        esf = np.zeros(np.max(bins) + 1)  # Edge spread function
        cnts = np.zeros(np.max(bins) + 1).astype(int)
        data_flat = data.flatten()
        for b_indx, b_sorted in zip(np.argsort(bins), np.sort(bins)):
            esf[b_sorted] += data_flat[b_indx]  # Collect pixel contributions in this bin
            cnts[b_sorted] += 1  # Keep a tab of how many contributions were made to this bin
        # Calculate mean by dividing by the number of contributing pixels. Avoid
        # division by zero, in case there are bins with no content.
        esf[cnts > 0] /= cnts[cnts > 0]
        if np.any(cnts == 0):
            if verbose:
                print("Warning: esf bins with zero pixel contributions were found. Results may be inaccurate.")
                print(f"Try reducing the oversampling factor, which currently is {oversampling:d}.")
            # Try to save the situation by patching in values in the empty bins if possible
            patch_cntr = 0
            for i in np.where(cnts == 0)[0]:  # loop through all empty bin locations
                j = [i - 1, i + 1]  # indices of nearest neighbors
                if j[0] < 0:  # Is left neighbor index outside esf array?
                    j = j[1]
                elif j[1] == len(cnts):  # Is right neighbor index outside esf array?
                    j = j[0]
                if np.all(cnts[j] > 0):  # Now, if neighbor bins are non-empty
                    esf[i] = np.mean(esf[j])  # use the interpolated value
                    patch_cntr += 1
            if patch_cntr > 0 and verbose:
                print(f"Values in {patch_cntr:d} empty ESF bins were patched by "
                      f"interpolation between their respective nearest neighbors.")
                # gui.window.log_message(f"Values in {patch_cntr:d} empty ESF bins were patched by "
                #       f"interpolation between their respective nearest neighbors.")
        return esf


    def peak_width(self,y, rel_threshold):
        # Find width of peak in y that is above a certain fraction of the maximum value
        val = np.abs(y)
        val_threshold = rel_threshold * np.max(val)
        indices = np.where(val - val_threshold > 0.0)[0]
        return indices[-1] - indices[0]


    def filter_window(self,lsf, oversampling, lsf_centering_kernel_sz=9,
                      win_width_factor=1.5, lsf_threshold=0.10):
        # The window ('hann_win') returned by this function will be used as a filter
        # on the LSF signal during the MTF calculation to reduce noise

        nn0 = 20 * oversampling  # sample range to be used for the FFT, intial guess
        mid = len(lsf) // 2
        i1 = max(0, mid - nn0)
        i2 = min(2 * mid, mid + nn0)
        nn = (i2 - i1) // 2  # sample range to be used, final


        # Filter LSF curve with a uniform kernel to better find center and
        # determine an appropriate Hann window width for noise reduction
        lsf_conv = np.convolve(lsf[i1:i2], np.ones(lsf_centering_kernel_sz), 'same')

        # Base Hann window half width on the width of the filtered LSF curve
        hann_hw = max(np.round(win_width_factor * self.peak_width(lsf_conv, lsf_threshold)).astype(int), 5 * oversampling)


        bin_c = np.argmax(np.abs(lsf_conv))  # center bin, corresponding to LSF max

        # Construct Hann window centered over the LSF peak, crop if necessary to
        # the range [0, 2*nn]
        crop_l = max(hann_hw - bin_c, 0)
        crop_r = min(2 * nn - (hann_hw + bin_c), 0)
        hann_win = np.zeros(2 * nn)  # default value outside Hann function
        hann_win[bin_c - hann_hw + crop_l:bin_c + hann_hw + crop_r] = \
            np.hanning(2 * hann_hw)[crop_l:2 * hann_hw + crop_r]
        return hann_win, 2 * hann_hw, [i1, i2]


    def calc_mtf(self,lsf, hann_win, idx, oversampling, diff_ft):
        # Calculate MTF using the LSF as input and use the supplied window function
        # as filter to remove high frequency noise originating in regions far from
        # the edge

        i1, i2 = idx
        mtf = np.abs(np.fft.fft(lsf[i1:i2] * hann_win))
        nn = (i2 - i1) // 2
        mtf = mtf[:nn]
        mtf /= mtf[0]  # normalize to zero spatial frequency
        f = np.arange(0, oversampling / 2, oversampling / nn / 2)  # spatial frequencies (cy/px)
        # Compensate for finite impulse response of the numerical differentiaion
        # step used to derive the LSF from the ESF
        # NB: This compensation function is incorrect in both ISO 12233:2014
        # and ISO 12233:2017, Annex D
        mtf *= (1 / np.sinc(4 * f / (diff_ft * oversampling))).clip(0.0, 1.0)
        return np.column_stack((f, mtf))


    def calc_sfr(self,image, oversampling=2, show_plots=0, offset=None, angle=None,
                 difference_scheme='central', verbose=False, return_fig=False,
                 quadratic_fit=False):
        """"
        Calculate spectral response function (SFR)
        """

        if difference_scheme == 'backward':
            diff_kernel = np.array([1.0, -1.0])
            diff_offset = -0.5
            diff_ft = 4  # factor used in the correction of the numerical derivation
        elif difference_scheme == 'central':
            diff_kernel = np.array([0.5, 0.0, -0.5])
            diff_offset = 0.0
            diff_ft = 2

        # Calculate centroids for the edge transition of each row
        sample_diff = self.differentiate(image, diff_kernel)
        centr = self.centroid(sample_diff) + diff_offset

        # Calculate centroids also for the 90° right rotated image
        image_rot90 = image.T[:, ::-1]  # rotate by transposing and mirroring
        sample_diff = self.differentiate(image_rot90, diff_kernel)
        centr_rot = self.centroid(sample_diff) + diff_offset

        # Use rotated image if it results in fewer rows without edge transitions
        if np.sum(np.isnan(centr_rot)) < np.sum(np.isnan(centr)):
            verbose and print("Rotating image by 90°")
            image, centr = image_rot90, centr_rot
            rotated = True
        else:
            rotated = False

        pcoefs, slope, offset,angle = self.find_edge(centr, image.shape, rotated, angle=angle,
                                          show_plots=show_plots, verbose=verbose)

        if abs(angle) < 0.9 : # ingore the less than 0.9 degree slant edge
            return False,   {'rotated': rotated,
                  'angle': angle,
                  'offset': offset}

        pcoefs = [0.0, slope, offset] if not quadratic_fit else pcoefs

        # Calculate distance (with sign) from each point (x, y) in the
        # image patch "data" to the slanted edge
        dist = self.calc_distance(image.shape, pcoefs, quadratic_fit=quadratic_fit, verbose=verbose)

        esf = self.project_and_bin(image, dist, oversampling, verbose=verbose)  # edge spread function
        if esf is False:
            return False,  {'rotated': rotated,
                  'angle': angle,
                  'offset': offset}

        lsf = self.differentiate(esf, diff_kernel)  # line spread function

        hann_win, hann_width, idx = self.filter_window(lsf, oversampling)  # define window to be applied on LSF
        if hann_width >350:  # sorting out no slant edge
            return False,  {'rotated': rotated,
                  'angle': angle,
                  'offset': offset}

        mtf = self.calc_mtf(lsf, hann_win, idx, oversampling, diff_ft)

        if show_plots == 4 or return_fig:
            i1, i2 = idx
            nn = (i2 - i1) // 2
            lsf_sign = np.sign(np.mean(lsf[i1:i2] * hann_win))

            fig, ax = plt.subplots()
            ax.plot(esf[i1:i2], 'b.-', label=f"ESF, oversampling: {oversampling:2d}")
            ax.plot(lsf_sign * lsf[i1:i2], 'r.-', label=f"{'-' if lsf_sign < 0 else ''}LSF")
            ax.plot(hann_win * ax.axes.get_ylim()[1] * 1.1, 'g.-', label=f"Hann window, width: {hann_width:d}")
            ax.set_xlim(0, 2 * nn)
            ax2 = ax.twinx()
            ax2.get_yaxis().set_visible(False)
            ax.grid()
            ax.legend(loc='upper left')
            ax.set_xlabel('Bin no.')
            if verbose:
                textstr = '\n'.join([f"Curved edge fit: {quadratic_fit}",
                                     f"Difference scheme: {difference_scheme}"])
                props = dict(facecolor='wheat', alpha=0.5)
                ax.text(0.05, 0.50, textstr, transform=ax.transAxes,
                        verticalalignment='top', bbox=props)

        #angle = angle_from_slope(slope)
        angle_cw = rotated * 90.0 - angle  # angle clockwise (c.w.) from vertical axis
        if angle_cw > 90.0:
            angle_cw -= 180.0
        status = {'rotated': rotated,
                  'angle': angle_cw,
                  'offset': offset}
        if return_fig:
            status.update({'fig': fig, 'ax': ax})

        return mtf, status


