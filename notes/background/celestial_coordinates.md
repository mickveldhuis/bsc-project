# Celestial Coordinates

## Equatorial Coordinates

We define the absolute position of an object by the right ascension (RA or $\alpha$) and declination (Dec or $\delta$) with respect to the celestial north and south poles (NCP and SCP), and the celestial equator. Note that the celestial equator coincides with Earth's equator and similarly NCP and SCP point in the same direction as the Earth's poles.

- RA: measured in hours $0^h$ to $24^h$, measured eastward.
- Dec: measured in degrees, $\pm 90\ \text{deg}$ at the NCP and SCP respectively.

Note that depending on $\delta$, the angle one hour of RA traverses shrinks by a factor $\cos\delta$. I.e.,

$$\alpha=1^h=15\ \text{deg}\times\delta$$

Rather than the RA, we use the hour angle (HA or $h$) to point a telescope on an equatorial mount. The hour angle is simply defined as,

$$h=\text{LST}-\alpha$$

where LST is the local sidereal time. Thus, when the RA equals the LST, the object of interest is along the meridian of the observer. Example:

- $\text{HA}=+1^h$: the object is 1 hour west from the local meridian.
- $\text{HA}=-1^h$: the object is 1 hour east from the local meridian.

## Horizontal Coordinates

We can also describe the pointing of a telescope by its altitude and azimuth.
