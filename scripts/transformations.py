import numpy as np
from pytransform3d import rotations as pr
from pytransform3d import transformations as pt

def vec4(x, y, z):
    """
    Return a 4-element vector, appropriate 
    for coordinate transformations.
    """
    return np.array([x, y, z, 1]) #np.array([x, y, z, 1]).reshape((4,1))

def vec3(v4):
    """
    Convert a 4-element vector to a 3-element vector.
    """
    v3 = v4[:3].reshape(3)

    return v3

def transform(x, y, z):
    """Transform a vector (x', y', z', 1)."""
    return np.array([
        [1, 0, 0, x],
        [0, 1, 0, y],
        [0, 0, 1, z],
        [0, 0, 0, 1],
    ])

def rot_x(angle):
    """
    Rotate a vector (x, y, z, 1) about the x-axis 
    in a right-handed coordinate system.
    """
    angle = np.radians(angle)

    return np.array([
        [1,             0,              0, 0],
        [0, np.cos(angle), -np.sin(angle), 0],
        [0, np.sin(angle),  np.cos(angle), 0],
        [0,             0,              0, 1],
    ])

def rot_y(angle):
    """
    Rotate a vector (x, y, z, 1) about the y-axis 
    in a right-handed coordinate system.
    """
    angle = np.radians(angle)

    return np.array([
        [np.cos(angle),  0,  -np.sin(angle), 0],
        [0,              1,               0, 0],
        [-np.sin(angle), 0,   np.cos(angle), 0],
        [0,              0,               0, 1],
    ])

def rot_z(angle):
    """
    Rotate a vector (x, y, z, 1) about the z-axis 
    in a right-handed coordinate system.
    """
    angle = np.radians(angle)

    return np.array([
        [np.cos(angle),  -np.sin(angle), 0, 0],
        [np.sin(angle),  np.cos(angle), 0, 0],
        [0, 0, 1, 0],
        [0, 0, 0, 1],
    ])

if __name__ == '__main__':
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

    H = pt.concat(pt.concat(pt.concat(pt.concat(H_01, H_12), H_23), H_34), H_45)

    transformed = pt.transform(H, pt.vector_to_point(origin)) 
    print(transformed[:3])