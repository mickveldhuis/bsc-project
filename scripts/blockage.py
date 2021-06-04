import argparse

from aperture import TelescopeAperture, GuiderAperture, FinderAperture

parser = argparse.ArgumentParser(
            allow_abbrev=True, 
            description='Compute the % obstruction of the main aperture/finder/guider by the dome'
        )

# Add arguments
parser.add_argument('--az', action='store', type=float, default=0.0, help='dome azimuth: 0 to 360 deg | default: 0 deg')
parser.add_argument('--ha', action='store', type=float, default=0.0, help='telescope hour angle: -180 to 180 deg | default: 0 deg')
parser.add_argument('--dec', action='store', type=float, default=0.0, help='telescope declination -90 to 90 deg | default: 0 deg')
parser.add_argument('-a', '--aperture', action='store', type=str, default='telescope', help='select aperture: telescope, finder, guider | default: telescope')
parser.add_argument('-r', '--rate', action='store', type=int, default=100, help='no. rays (for decent results >100; preferably 1000+) | default: 100')

args = parser.parse_args()

if __name__ == '__main__':
    # TODO: don't input inventor az, but actual az... only for testing rn...
    dome_az = (360 - args.az) % 360 # args.az = inventor azimuth -> convert to true azimuth
    
    blockage = None

    if args.aperture == 'telescope':
        telescope = TelescopeAperture()
        telescope.set_rate(args.rate)
        blockage = telescope.obstruction(args.ha, args.dec, dome_az)

    elif args.aperture == 'guider':
        guider = GuiderAperture()
        guider.set_rate(args.rate)
        blockage = guider.obstruction(args.ha, args.dec, dome_az)

    elif args.aperture == 'finder':
        finder = FinderAperture()
        finder.set_rate(args.rate)
        blockage = finder.obstruction(args.ha, args.dec, dome_az)

    if blockage is not None:
        print('obstruction = {:.2%}'.format(blockage))
    else:
        print('the % obstruction could not be computed..!')