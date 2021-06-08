import numpy as np
import pickle

from joblib import Parallel, delayed, dump
from datetime import datetime

from aperture import TelescopeAperture, GuiderAperture, FinderAperture

file_name = lambda n: 'data/blocked_grid_az_' + str(n) + '.joblib'

# sample HA from -12 h to 12 h; Dec from -90 to 90 deg
h = np.linspace(-179, 180, 360) 
dec = np.linspace(-90, 90, 181)
az = np.linspace(0, 359, 360)

az_range = np.arange(0, 360, 1)

def slow(h, dec, az, has_print=False):
    p = np.zeros((h.size, dec.size, az.size))

    for i in range(h.size):
        for j in range(dec.size):
            for k in range(az.size):
                percentage = telescope.obstruction(h[i], dec[j], az[k])
                # percentage = calculate_blocked_percentage(h[i], dec[j], az[k])
                p[i, j, k] = percentage

                if has_print:
                    print('{:.2%} for HA = {:.2f} deg, Dec = {:.2f} deg, Ad = {:.2f} deg'.format(percentage, h[i], dec[j], az[k]))
        
        return p

# Global variable
telescope = TelescopeAperture(rate=4)

def fast(n_az):
    p = np.zeros((h.size, dec.size))

    for i in range(h.size):
        for j in range(dec.size):
            percentage = telescope.obstruction(h[i], dec[j], n_az)

            # percentage = calculate_blocked_percentage(h[i], dec[j], n_az)
            p[i, j] = percentage

    print('finished az =', str(n_az), 'at', datetime.now().hour, 'hours and', datetime.now().minute, 'minutes')

    with open(file_name(n_az), 'wb') as f:
        dump(p, f)

# with open('obstruction_grid.npy', 'rb') as f:
#     p = np.load(f)

if __name__ == '__main__':
    # p = np.zeros((h.size, dec.size))
    
    # for i in range(h.size):
    #     for j in range(dec.size):
    #         percentage = calculate_blocked_percentage(h[i], dec[j], 0)
    #         p[i, j] = percentage

    #         print('{:.2%} for HA = {:.2f} deg, Dec = {:.2f} deg, Ad = {:.2f} deg'.format(percentage, h[i], dec[j], 0))

    # results = Parallel(n_jobs=-1, backend='threading')(delayed(fast)(i) for i in az_range)
    print('Start run at', datetime.now().hour, 'hours and', datetime.now().minute, 'minutes')
    results = Parallel(n_jobs=-1)(delayed(fast)(i) for i in az_range)

    