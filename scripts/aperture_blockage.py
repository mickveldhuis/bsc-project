from math import exp
import sys
import enum
import configparser
import numpy as np
import numpy.linalg as la

# For astro conversions
from astropy.coordinates import EarthLocation
from astropy.time import Time
from astropy import units as u
import datetime

# For coordinate transformations
from transformations import vec3, vec4, transform, rot_x, rot_z
from visual_helpers import plot_aperture

# CONSTANTS
config = configparser.ConfigParser()
config.read('config.ini')

# Telescope:
L_1 = config['mount'].getfloat('length_1') # distance floor-HA axis
L_2 = config['mount'].getfloat('length_2') # distance HA axis-Dec axis
L_3 = config['mount'].getfloat('length_3') # distance Dec axis-tube center
L_4 = config['guider'].getfloat('offset') # distance primary tube center-guider center
L_5 = config['finder'].getfloat('offset') # distance guider center-finder center

GUIDER_ANGLE = np.radians(config['guider'].getfloat('angle'))
FINDER_ANGLE =  np.radians(config['finder'].getfloat('angle'))

APERTURE_RADIUS = config['telescope'].getfloat('diameter')/2
GUIDER_RADIUS = config['guider'].getfloat('diameter')/2
FINDER_RADIUS = config['finder'].getfloat('diameter')/2

# Dome:
RADIUS = config['dome'].getfloat('diameter')/2   # radius
EXTENT = config['dome'].getfloat('extent')  # extent of cylindrical dome wall
SLIT_WIDTH = config['dome'].getfloat('slit_width') # = MODEL / OLD: 1.84 (= measured)  # Slit width

# Observatory:
LAT = config['observatory'].getfloat('latitude') # degrees

class Instruments(enum.Enum):
    """
    Enum for selecting what aperture
    to use in the transformation.
    """
    TELESCOPE = enum.auto()
    GUIDER = enum.auto()
    FINDER = enum.auto()

    @classmethod
    def get_default(c):
        return c.TELESCOPE

# ---------------------- #
#  SECTION 1             #
# ---------------------- #

def get_transform(ha, dec, x=0, y=0, z=0, instrument=Instruments.TELESCOPE):
    H_01 = transform(0, 0, L_1)
    H_12 = rot_x(90-LAT) @ rot_z(-ha) @ transform(0, 0, L_2)
    H_23 = rot_x(dec) @ transform(-L_3, 0, 0)
    H_34 = transform(x, y, z)
    H_45 = transform(L_4*np.cos(GUIDER_ANGLE), 0, L_4*np.sin(GUIDER_ANGLE))
    H_56 = transform(-L_5*np.cos(FINDER_ANGLE), 0, L_5*np.sin(FINDER_ANGLE))
    
    H = H_01 @ H_12 @ H_23 @ H_34

    if instrument == Instruments.GUIDER:
        H = H @ H_45
    elif instrument == Instruments.FINDER:
        H = H @ H_45 @ H_56
    
    return H

from pytransform3d import rotations as pr
from pytransform3d import transformations as pt

def get_transform_test(ha, dec, x=0, y=0, z=0):
    origin = np.array([0, 0, 0])

    H_01 = pt.transform_from(
        R=pr.matrix_from_axis_angle(np.array([0, 0, 0, 0])),
        p=np.array([0, 0, L_1])
    )

    H_12 = pt.transform_from(
        R=pr.matrix_from_axis_angle(np.array([1, 0, 0, np.radians(90-LAT)])),
        p=np.array([0,0,0])
    )

    H_23 = pt.transform_from(
        R=pr.matrix_from_axis_angle(np.array([0, 0, 1, np.radians(-ha)])),
        p=np.array([0, 0, L_2])
    )

    H_34 = pt.transform_from(
        R=pr.matrix_from_axis_angle(np.array([1, 0, 0, np.radians(dec)])),
        p=np.array([-L_3, 0, 0])
    )

    H_45 = pt.transform_from(
        R=pr.matrix_from_axis_angle(np.array([0, 0, 0, 0])),
        p=np.array([x, y, z])
    )

    # H = pt.concat(pt.concat(pt.concat(pt.concat(H_01, H_12), H_23), H_34), H_45)
    H = H_01 @ H_12 @ H_23 @ H_34 @ H_45

    transformed = pt.transform(H, pt.vector_to_point(origin)) 
    
    return vec3(transformed)

def get_aperture(ha, dec, x, z, instrument=Instruments.TELESCOPE):
    """
    Compute a position in the
    aperture of the telescope.
    """
    y = np.zeros(x.size)
    dummy = np.ones(x.size)
    points = np.column_stack((x, y, z, dummy))
    
    pose_matrix = get_transform(ha, dec, instrument=instrument)

    product = pt.transform(pose_matrix, points)

    return product[:, :3]

def get_direction(p1, p2):
    d = p2 - p1
    d_unit = d/la.norm(d)
    
    return d_unit

def compute_azimuth(x, y):
    """
    Return the azimuth (rad) using
    the north clockwise convension.
    """
    az = np.arctan2(x, y) # note (x,y) rather than (y,x)
    
    if az < 0:
        az += 2*np.pi
    
    return az

# ---------------------- #
#  SECTION 2             #
# ---------------------- #

def find_intersection(point, direction):
    has_intersection = False
    t = None
    
#     if direction.z < 0:
#         return has_intersection, t
    
    if np.isclose(direction[0], 0) and np.isclose(direction[1], 0):
        z = EXTENT + np.sqrt(RADIUS**2 - point[0]**2 - point[1]**2)
        t = z - point[2]
        
        has_intersection = True
        return has_intersection, t
    
    # If the direction vector is not (nearly) parallel to 
    # the z-axis of the capsule
    a2 = direction[0]**2 + direction[1]**2
    a1 = point[0]*direction[0] + point[1]*direction[1]
    a0 = point[0]**2 + point[1]**2 - RADIUS**2
    
    delta = a1**2-a0*a2
    t     = (-a1+np.sqrt(delta))/a2
    
    if point[2] + t * direction[2] >= EXTENT:
        a0 = point[0]**2 + point[1]**2 + (point[2] - EXTENT)**2 - RADIUS**2
        a1 = point[0]*direction[0] + point[1]*direction[1] + (point[2] - EXTENT)*direction[2]
        
        t = -a1+np.sqrt(a1**2-a0)
    
    if t:
        has_intersection = True
    
    return has_intersection, t

def get_ray_intersection(point, direction, t):
    """
    Return the ray intersection, based on the origin 
    (point) and direction vectors.
    """
    return point + t*direction

# ---------------------- #
#  SECTION 3             #
# ---------------------- #

def uniform_disk(r, n):
    radii  = np.random.uniform(0, 1, n)
    angles = np.random.uniform(0, 2*np.pi, n) #np.linspace(0, 2*np.pi, n + 1) #
    
    x = np.sqrt(radii) * np.cos(angles)
    y = np.sqrt(radii) * np.sin(angles)
    
    xy = r*np.column_stack([x, y])
    
    return xy

def correct_az(az):
    if az < 0.: 
        az = az + 360.
    if az > 360.: 
        az = az % 360.
    
    return az

def is_blocked(point, ha, dec, dome_az, has_print=False):
    """
    Return True when the given ray in the aperture is blocked.
    """
    is_b = True

    direction = vec3((get_transform(ha, dec, y=1) - get_transform(ha, dec, y=0)) @ vec4(0, 0, 0)) #get_direction(tube_center, os[[3,5]][1])

    try:
        has_intersection, t = find_intersection(point, direction)

        if has_intersection:
            points = get_ray_intersection(point, direction, t)
            
            ray_az = np.degrees(compute_azimuth(points[0], points[1]))

            if ray_az > dome_az + 180:
                ray_az -= dome_az + 360
            elif ray_az > dome_az or ray_az < dome_az:
                ray_az -= dome_az

            # Compute the dome slit - dome hemisphere intersection
            elev = np.arctan2(points[2] - EXTENT, np.sqrt(points[0]**2 + points[1]**2))
            
            y_length_sq = np.power(RADIUS*np.cos(elev), 2) - np.power(SLIT_WIDTH/2, 2)

            if y_length_sq < 0:
                is_b = False

                return is_b

            y_length = np.sqrt(y_length_sq)
            x_length = SLIT_WIDTH/2
            slit_offset_rad = np.pi/2 - np.arctan2(y_length, x_length)
            
            # Compute off-set and compare ray az w/ dome position
            slit_offset = np.degrees(slit_offset_rad)

            slit_az_min = -slit_offset
            slit_az_max = slit_offset

            if has_print:
                print('ray az = {:.2f} & dome az = {:.2f}'.format(np.degrees(compute_azimuth(points[0], points[1])), dome_az))
                print('{:.2f} (min) < {:.2f} (ray) < {:.2f} (max)'.format(slit_az_min, ray_az, slit_az_max))
            
            is_ray_in_slit = ray_az > slit_az_min and ray_az < slit_az_max
            
            if points[2] > EXTENT and is_ray_in_slit:
                is_b = False

            if not is_ray_in_slit and (ray_az < -90 or ray_az > 90):

                rot = rot_z(dome_az)

                dummy = np.ones(points[0].size)
                pp = np.column_stack((points[0], points[1], points[2], dummy))

                product = pt.transform(rot, pp)
                
                if np.abs(product[:, 0]) < SLIT_WIDTH/2 and np.abs(product[:,1]) < SLIT_WIDTH/2:
                    is_b = False
         
    except Exception as ex:
        print(str(ex))
    
    return is_b

v_is_blocked = np.vectorize(is_blocked, signature='(d),(),(),(),()->()')

def calc_blocked_percentage(ha, dec, dome_az, n_rays, instrument=Instruments.TELESCOPE):
    if n_rays < 1:
        n_samples = 1
    else:
        n_samples = n_rays

    ap_xz = None

    if instrument == Instruments.TELESCOPE:
        ap_xz = uniform_disk(APERTURE_RADIUS, n_samples)
    elif instrument == Instruments.GUIDER:
        ap_xz = uniform_disk(GUIDER_RADIUS, n_samples)
    elif instrument == Instruments.FINDER:
        ap_xz = uniform_disk(FINDER_RADIUS, n_samples)
        
    ap_x, ap_z = ap_xz.T
    
    ap_pos = get_aperture(ha, dec, -ap_x, ap_z, instrument=instrument)

    blocked = v_is_blocked(ap_pos, ha, dec, dome_az, has_print=False)
    
    percentage = plot_aperture(ap_x, ap_z, blocked, APERTURE_RADIUS, dome_az)

    return percentage

if __name__ == '__main__':
    ray_count = int(sys.argv[1])
    inventor_az = sys.argv[2]
    dome_az = (360 - float(inventor_az)) % 360
    ha, dec = float(sys.argv[3]), float(sys.argv[4])

    try:
        instr = str(sys.argv[5])
    except:
        instr = None

    instrument = Instruments.TELESCOPE # Default

    if instr is not None:
        if instr == 'telescope':
            instrument = Instruments.TELESCOPE
        elif instr == 'guider':
            instrument = Instruments.GUIDER
        elif instr == 'finder':
            instrument = Instruments.FINDER    

    # Calculate the % blockage by the dome
    blockage = calc_blocked_percentage(ha, dec, dome_az, n_rays=ray_count, instrument=instrument)
    print('There\'s', invalid_counter, 'invalid points in the aperture')