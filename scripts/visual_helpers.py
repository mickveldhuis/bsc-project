import matplotlib.pyplot as plt

def plot_aperture(ap_x, ap_z, is_blocked, aperture_r, dome_az):
    percentage = is_blocked[is_blocked].size/is_blocked.size

    fig = plt.figure(figsize=(4.5, 4.5))
    frame = fig.add_subplot(1, 1, 1)

    frame.plot(ap_x[is_blocked], ap_z[is_blocked], ls='', marker='o', ms=3, color='xkcd:salmon', label='{:.1%} Blocked'.format(percentage))
    frame.plot(ap_x[~is_blocked], ap_z[~is_blocked], ls='', marker='o', ms=3, color='black', label='{:.1%} Clear'.format(1-percentage))

    frame.set_xlabel(r'$x$', fontsize=18)
    frame.set_ylabel(r'$z$', fontsize=18)
    frame.grid(ls='--', alpha=0.5)

    frame.set_ylim(-2*aperture_r, 2*aperture_r)
    frame.set_xlim(-2*aperture_r, 2*aperture_r)

    frame.set_title('$A_d$ = {:.2f} deg'.format(float(dome_az) % 360), fontsize=18)

    frame.legend(fontsize=12, loc='lower right')
    fig.tight_layout()

    plt.show()

    return percentage