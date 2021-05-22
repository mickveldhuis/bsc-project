import sys
import configparser
import numpy as np
import numpy.linalg as la

# For astro conversions
from astropy.coordinates import EarthLocation
from astropy.time import Time
from astropy import units as u
import datetime

# For coordinate transformations
from transformations import vec3, vec4, transform, rot_x, rot_y, rot_z
from visual_helpers import plot_aperture

# CONSTANTS
config = configparser.ConfigParser()
config.read('config.ini')

# Telescope:
L_1 = config['mount'].getfloat('length_1') # distance floor-HA axis
L_2 = config['mount'].getfloat('length_2') # distance HA axis-Dec axis
L_3 = config['mount'].getfloat('length_3') # distance Dec axis-tube center

APERTURE_RADIUS = config['telescope'].getfloat('diameter')/2 # m

# Dome:
DIAMETER = config['dome'].getfloat('diameter')   # diameter
RADIUS = DIAMETER/2   # radius
EXTENT = config['dome'].getfloat('extent')  # extent of cylindrical dome wall
HEIGHT = RADIUS + EXTENT # height of half capsule repr. dome
SLIT_WIDTH = config['dome'].getfloat('slit_width') # = MODEL / OLD: 1.84 (= measured)  # Slit width

# Obvervatory:
LAT = config['observatory'].getfloat('latitude') # degrees

# ---------------------- #
#  SECTION 1             #
# ---------------------- #

def get_transform(ha, dec, x=0, y=-0.5, z=0):
    H_01 = transform(0, 0, L_1)
    H_12 = rot_x(90-LAT) @ rot_z(-ha) @ transform(0, 0, L_2)
    H_23 = rot_x(dec) @ transform(-L_3, 0, 0)
    H_34 = transform(x, y, z)
    
    H = H_01 @ H_12 @ H_23 @ H_34
    
    return H

def get_aperture(ha, dec, x, z):
    """
    Compute a position in the
    aperture of the telescope.
    """
    origin = vec4(0, 0, 0)
    pose_matrix = get_transform(ha, dec, x=x, y=0, z=z)

    product = pose_matrix @ origin
    
    prod_v3 = vec3(product)

    return prod_v3

def get_origins(ha, dec, y_back=-0.3):
    """Compute the origin of each intermediate ref. frame."""
    origin = vec4(0, 0, 0)
    H_01 = transform(0, 0, L_1)
    H_12 = rot_x(90-LAT) @ rot_z(-ha) @ transform(0, 0, L_2)
    H_23 = rot_x(dec) @ transform(-L_3, 0, 0)
    H_34 = transform(0, y_back, 0)
    H_45 = transform(0, -3*y_back, 0)
    
    pose_0 = origin # Dome origin
    pose_1 = H_01 @ origin # HA axis origin
    pose_2 = H_01 @ H_12 @ origin # Dec axis origin
    pose_3 = H_01 @ H_12 @ H_23 @ origin # Center aperture
    pose_4 = H_01 @ H_12 @ H_23 @ H_34 @ origin # Back aperture
    pose_5 = H_01 @ H_12 @ H_23 @ H_34 @ H_45 @ origin # Front aperture

    return np.array([pose_0, pose_1,pose_2,pose_3,pose_4, pose_5])

def get_direction(p1, p2):
    d = p2 - p1
    d_unit = d/la.norm(d)
    
    return d_unit

def compute_azimuth(x, y):
    """
    Return the azimuth (rad) using
    the north clockwise conv.
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

def semi_intersection(elev):
    k = np.power(RADIUS*np.cos(elev), 2) - np.power(SLIT_WIDTH/2, 2)
    
    # INTRODUCE PROPER SOLUTION!!!
    if k < 0:
        print('Hello neg sqrt here! discriminant =', k, ', (w/2)^2 =', np.power(SLIT_WIDTH/2, 2), ', r*cos(elev) =', RADIUS*np.cos(elev))
        return 0
    
    return np.sqrt(k)

def get_semi_az(p):
    elev = np.arctan2(p[2] - EXTENT, np.sqrt(p[0]**2 + p[1]**2))
    
#     print('elev', np.degrees(elev), ', (x,y) = (', p[0], p[1], ')')
    
    y = semi_intersection(elev)
    x = SLIT_WIDTH/2
    delta = np.pi/2 - np.arctan2(y, x)
    
    return delta

def correct_az(az):
    if az < 0.: 
        az = az + 360.
    if az > 360.: 
        az = az % 360.
    
    return az

def is_blocked(origin, ha, dec, dome_az, has_print=False):
    """
    Return True when the given ray in the aperture is blocked.
    """
    is_b = True
    
    # p = vec3(origin)
    p = origin
    
    # print(p)

    # Get the origins of each ref. frame 
    os = get_origins(ha, dec)[:,:3].reshape(6, 3)

    # Compute dome intersection
    # tube_center = os[[3,5]][0]

    direction = vec3((get_transform(ha, dec, y=1) - get_transform(ha, dec, y=0)) @ vec4(0, 0, 0)) #get_direction(tube_center, os[[3,5]][1])

    try:
        has_intersection, t = find_intersection(p, direction)

        if has_intersection:
            p_s = get_ray_intersection(p, direction, t)
            
            print('ray az = {:.2f} & dome az = {:.2f}'.format(correct_az(np.degrees(compute_azimuth(p_s[0], p_s[1]))), dome_az))
            
            ray_az = np.degrees(compute_azimuth(p_s[0], p_s[1])) - dome_az
            slit_offset = np.degrees(get_semi_az(p_s))


            slit_az_min = -slit_offset #correct_az(dome_az - slit_offset)
            slit_az_max = slit_offset #correct_az(dome_az + slit_offset)

            if has_print:
                print('{:.2f} (min) < {:.2f} (ray) < {:.2f} (max)'.format(slit_az_min, ray_az, slit_az_max))
            
            is_ray_in_slit = ray_az > slit_az_min and ray_az < slit_az_max
            
            if p_s[2] > EXTENT and is_ray_in_slit:
                is_b = False
            
    except Exception as ex:
        print(str(ex))
    
    return is_b
 
v_get_aperture = np.vectorize(get_aperture, signature='(),(),(d),(d)->()') # get_aperture(ha, dec, x, z)
v_is_blocked = np.vectorize(is_blocked, signature='(d),(),(),(),()->()')

def calc_blocked_percentage(ha, dec, dome_az, n_rays):
    if n_rays < 1:
        n_samples = 1
    else:
        n_samples = n_rays

    ap_xz = uniform_disk(APERTURE_RADIUS, n_samples)
    ap_x, ap_z = ap_xz.T
    
    # print(v_get_aperture(ha, dec, -ap_x, ap_z))

    # ap_pos = np.stack(get_aperture(ha, dec, -ap_x, ap_z)).reshape(n_samples, 3) #v_get_aperture(ha, dec, -ap_x, ap_z)
    
    ap_pos = []

    for x, z in zip(ap_x, ap_z):
        p = get_aperture(ha, dec, -x, z)
        ap_pos.append(p)
        
    ap_pos = np.array(ap_pos)
    ap_pos = ap_pos[:, :3]

    # print(type(ap_pos))

    blocked = v_is_blocked(ap_pos, ha, dec, dome_az, has_print=False)
    
    percentage = plot_aperture(ap_x, ap_z, blocked, APERTURE_RADIUS, dome_az)

    return percentage

if __name__ == '__main__':
    # blockage_perc = calc_blocked_percentage(36, 24, 250)
    ray_count = int(sys.argv[1])
    
    inventor_az = sys.argv[2]
    dome_az = 360 - float(inventor_az)
    
    ha, dec = float(sys.argv[3]), float(sys.argv[4])

    # ha_test, dec_test = (-50, 10)

    blockage_perc = calc_blocked_percentage(ha, dec, dome_az, n_rays=ray_count)