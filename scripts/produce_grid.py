import numpy as np
import pickle

from joblib import Parallel, delayed, dump
from datetime import datetime

from aperture_blockage import calculate_blocked_percentage

# _h = np.linspace(-180, 180, 361)
# _dec = np.linspace(-90, 90, 181)
# _az = np.linspace(0, 360, 361)

# h, dec, az = np.meshgrid(_h, _dec, _az, indexing='ij')

file_name = lambda n: 'data/blocked_grid_az_' + str(n) + '.joblib'

h = np.linspace(-180, 180, 181) # -6 h to 6 h
dec = np.linspace(-90, 90, 91)
# az = np.linspace(0, 359, 180)

def slow(h, dec, az, has_print=False):
    p = np.zeros((h.size, dec.size, az.size))

    for i in range(h.size):
        for j in range(dec.size):
            for k in range(az.size):
                percentage = calculate_blocked_percentage(h[i], dec[j], az[k])
                p[i, j, k] = percentage

                if has_print:
                    print('{:.2%} for HA = {:.2f} deg, Dec = {:.2f} deg, Ad = {:.2f} deg'.format(percentage, h[i], dec[j], az[k]))
        
        return p

def fast(n_az):
    p = np.zeros((h.size, dec.size))

    for i in range(h.size):
        for j in range(dec.size):
            percentage = calculate_blocked_percentage(h[i], dec[j], n_az)
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
    az_range = np.arange(0, 360, 2)
    # results = Parallel(n_jobs=-1, backend='threading')(delayed(fast)(i) for i in az_range)
    print('Start run at', datetime.now().hour, 'hours and', datetime.now().minute, 'minutes')
    results = Parallel(n_jobs=-1)(delayed(fast)(i) for i in az_range)

    