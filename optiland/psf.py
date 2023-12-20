import numpy as np
from optiland.wavefront import OPD


class FFTPSF(OPD):
    # TODO: add transmission from object to exit pupil

    def __init__(self, optic, field, wavelengths='all',
                 num_rays=128, grid_size=1024):
        super().__init__(optic=optic, fields=[field], wavelengths=wavelengths,
                         num_rays=num_rays)

        self.grid_size = grid_size
        self.psf = self._compute_psf()

    def view(self, projection='2d', log=False, figsize=(6, 5), threshold=0.25):
        min_x, min_y, max_x, max_y = self._find_bounds(threshold)
        psf_zoomed = self.psf[min_x:max_x, min_y:max_y]
        psf_smooth = self._interpolate_psf(psf_zoomed)

        if projection == '2d':
            self._plot_2d(psf_smooth, log, figsize=(6, 5))
        elif projection == '3d':
            self._plot_3d(psf_smooth, log, figsize=(6, 5))
        else:
            raise ValueError('OPD projection must be "2d" or "3d".')

    def _plot_2d(self, image, log, figsize=(6, 5)):
        _, ax = plt.subplots(figsize=figsize)
        if log:
            norm = LogNorm()
        else:
            norm = None

        # x, y = self._get_psf_units(image)  # TODO: complete
        # extent = [-x/2, x/2, -y/2, y/2]

        im = ax.imshow(image, norm=norm)

        ax.set_xlabel('X (µm)')
        ax.set_ylabel('Y (µm)')
        ax.set_title('FFT PSF')

        cbar = plt.colorbar(im)
        cbar.ax.get_yaxis().labelpad = 15
        cbar.ax.set_ylabel('Relative Intensity (%)', rotation=270)
        plt.show()

    def _plot_3d(self, image, log, figsize=(6, 5)):
        fig, ax = plt.subplots(subplot_kw={"projection": "3d"},
                               figsize=figsize)

        x = np.linspace(0, 1, image.shape[1])
        y = np.linspace(0, 1, image.shape[0])
        X, Y = np.meshgrid(x, y)

        formatter = None
        if log:
            image = np.log10(image)
            formatter = mticker.FuncFormatter(self._log_tick_formatter)
            ax.zaxis.set_major_formatter(formatter)
            ax.zaxis.set_major_locator(mticker.MaxNLocator(integer=True))

        surf = ax.plot_surface(X, Y, image, rstride=1, cstride=1,
                               cmap='viridis', linewidth=0, antialiased=False)

        ax.set_xlabel('X (µm)')
        ax.set_ylabel('X (µm)')
        ax.set_zlabel('Relative Intensity (%)')
        ax.set_title('FFT PSF')

        # TODO: update format for scientific units on colorbar
        fig.colorbar(surf, ax=ax, shrink=0.5, aspect=10,
                     pad=0.1, format=formatter)
        fig.tight_layout()
        plt.show()

    def _log_tick_formatter(self, val, pos=None):
        """
        https://stackoverflow.com/questions/3909794/
        plotting-mplot3d-axes3d-xyz-surface-plot-with-log-scale
        """
        return f"$10^{{{int(val)}}}$"

    def _compute_psf(self):
        # TODO: check polychromatic PSF summing when scales are different due
        # to wavelength. Likely need to interpolate to the same grid
        pupils = self._pad_pupils()
        norm_factor = self._get_normalization()

        psf = []
        for pupil in pupils:
            amp = np.fft.fftshift(np.fft.fft2(pupil))
            psf.append(amp * np.conj(amp))

        return np.real(np.sum(psf, axis=0)) / norm_factor * 100

    def _interpolate_psf(self, image, n=128):
        x_orig, y_orig = np.meshgrid(np.linspace(0, 1, image.shape[0]),
                                     np.linspace(0, 1, image.shape[1]))

        x_interp, y_interp = np.meshgrid(np.linspace(0, 1, n),
                                         np.linspace(0, 1, n))

        points = np.column_stack((x_orig.flatten(), y_orig.flatten()))
        values = image.flatten()

        return griddata(points, values, (x_interp, y_interp), method='cubic')

    def _find_bounds(self, threshold=0.25):
        thresholded_psf = self.psf > threshold
        non_zero_indices = np.argwhere(thresholded_psf)

        min_x, min_y = np.min(non_zero_indices, axis=0)
        max_x, max_y = np.max(non_zero_indices, axis=0)
        size = max(max_x - min_x, max_y - min_y)

        peak_x, peak_y = np.unravel_index(np.argmax(self.psf), self.psf.shape)

        min_x = peak_x - size / 2
        max_x = peak_x + size / 2
        min_y = peak_y - size / 2
        max_y = peak_y + size / 2

        min_x = max(0, min_x)
        min_y = max(0, min_y)
        max_x = min(self.psf.shape[0], max_x)
        max_y = min(self.psf.shape[1], max_y)

        return int(min_x), int(min_y), int(max_x), int(max_y)

    def _pad_pupils(self):
        pupils_padded = []
        for pupil in self.pupils:
            pad = (self.grid_size - pupil.shape[0]) // 2
            pupil = np.pad(pupil, ((pad, pad), (pad, pad)),
                           mode='constant', constant_values=0)
            pupils_padded.append(pupil)
        return pupils_padded

    def _get_normalization(self):
        P_nom = self.pupils[0].copy()
        P_nom[P_nom != 0] = 1

        amp_norm = np.fft.fftshift(np.fft.fft2(P_nom))
        psf_norm = amp_norm * np.conj(amp_norm)
        return np.real(np.max(psf_norm) * len(self.pupils))

    def _get_psf_units(self, image):
        """https://www.strollswithmydog.com/
        wavefront-to-psf-to-mtf-physical-units/#iv"""
        D = self.optic.paraxial.XPD()

        if self.optic.object_surface.is_infinite:
            FNO = self.optic.paraxial.FNO()
        else:
            p = D / self.optic.paraxial.EPD()
            m = self.optic.paraxial.magnification()
            FNO *= (1 + np.abs(m) / p)

        Q = self.grid_size / self.num_rays

        # TODO: rework to account for specific wavelength in question
        dx = self.wavelengths[0] * FNO / Q

        x = image.shape[1] * dx
        y = image.shape[0] * dx

        return x, y
