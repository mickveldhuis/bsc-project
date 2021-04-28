# Telescope Pointing

Here I describe a method to:

1. compute the position of the telescope aperture in the dome.
2. compute the direction the telescope in pointing to in the telescope-dome frame.

## Telescope Position in the Dome

We use the transformation matrices (defined in one of the other notes), to compute the position of the telescope aperture (on the declination axis of the telescope) in the frame of the dome. Consider the figure below; a rough sketch of the telescope and mount.

![Sketch]()

Assume that the center of the dome's floor defines the origin of the first coordinate system we consider. With origin vector,

$$
\mathbf{r}_0=
\begin{bmatrix}
0\\
0\\
0\\
1
\end{bmatrix}$$

Note that the $y$-axis points along the same direction as the front of the mount and the $z$-axis pointing north from the dome floor. 

Initially, we perform a transformation ${}^0\text{H}_1$,

$$
{}^0\text{H}_1 =
\begin{bmatrix}
1 & 0 & 0 & 0\\
0 & 1 & 0 & 0\\
0 & 0 & 1 & \ell_1\\
0 & 0 & 0 & 1
\end{bmatrix}
$$

Then, from the second reference frame created by that translation, we define,

$$
{}^1\text{H}_2=\text{Rot}(x,-\theta)\text{Trans}(0,0,\ell_2)=
\begin{bmatrix}
1 & 0 & 0 & 0\\
0 & \cos\theta & \sin\theta & 0\\
0 & -\sin\theta & \cos\theta & 0\\
0 & 0 & 0 & 1
\end{bmatrix}
\begin{bmatrix}
1 & 0 & 0 & 0\\
0 & 1 & 0 & 0\\
0 & 0 & 1 & \ell_2\\
0 & 0 & 0 & 1
\end{bmatrix}
$$

Which works out to be,

$$
{}^1\text{H}_2=
\begin{bmatrix}
1 & 0 & 0 & 0\\
0 & \cos\theta & \sin\theta & 0\\
0 & -\sin\theta & \cos\theta & \ell_2\\
0 & 0 & 0 & 1
\end{bmatrix}
$$
