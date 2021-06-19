import sys, time, win32com.client, pythoncom

from socket import socket, AF_INET, SOCK_STREAM
from PyQt5 import QtWidgets, uic
from PyQt5.QtCore import QTimer, QThread
from pyqtgraph import PlotWidget
from astropy import units as u
from astropy.coordinates import SkyCoord
from datetime import datetime

import pyqtgraph as pg
import numpy as np

# Connect to the telescope

# sys.coinit_flags = 0
# pythoncom.CoInitialize()    

# telescope = win32com.client.Dispatch("TheSkyXAdaptor.RASCOMTele")
# telescope.Connect()

# ccd = win32com.client.Dispatch("	CCDSoft2XAdaptor.ccdsoft5Camera")
# ccd.Connect()

def send_command(command):
    """Send a command to KoepelX."""
    HOST = 'Hercules'
    PORT = 65000
    BUFSIZ = 1024
    ADDR = (HOST, PORT)

    tcpCliSock = socket(AF_INET, SOCK_STREAM)
    tcpCliSock.connect(ADDR)

    tcpCliSock.send(command.encode('utf-8'))
    response = tcpCliSock.recv(BUFSIZ)
    tcpCliSock.close()

    return response

def get_dome_pos():
    """Get the dome position (azimuth)"""
    pos = send_command('POSITION')
    angle = float((pos.split('\n'))[0])
    
    if angle < 0.: angle = angle + 360.
    if angle > 360.: angle = angle % 360.

    return angle

def is_dome_busy():
    """Return whether the dome is busy (moving)"""
    res = send_command('DOMEBUSY')
    busy = int((res.split('\n'))[0])

    return busy

def polar_to_cart(radius, theta):
    """
    Convert polar to cartesian coordinates,
    since Qt can't draw polar graphs...
    """
    x = radius * np.cos(theta)
    y = radius * np.sin(theta)

    return x, y

def justify(pos):
    """
    Adjust the polar graph, s.t. 0 deg is north, 
    90 deg is east, 180 south, and 270 west.
    """
    pos = 360 - pos
    pos += 90

    if pos >= 360:
        pos %= 360

    if pos < 0:
        pos += 360

    return pos

class InitThread(QThread):
    """
    Thread to run the initialization procedure: 
    moving the dome to +35 and calibrating.
    """
    def __init__(self):
        super().__init__(self)

    def __del__(self):
        self.wait()

    def run(self):
        jnk = send_command('goto +40')

        time.sleep(1)
        
        while is_dome_busy() == 1:
            time.sleep(1)
        
        jnk = send_command('calibrate')
        time.sleep(1)
        
        while is_dome_busy() == 1:
            time.sleep(1)


class ParkThread(QThread):
    """
    Thread to execute commands to park the dome at 
    -30 deg from the calibration point.
    """
    def __init__(self):
        super().__init__(self)

    def __del__(self):
        self.wait()

    def run(self):
        jnk = send_command('calibrate')
        time.sleep(1)
        
        while is_dome_busy() == 1:
            time.sleep(1)
        
        jnk = send_command('goto -30')
        time.sleep(1)
        
        while is_dome_busy() == 1:
            time.sleep(1)

class TrackThread(QThread):
    """
    Control thread, for the dome tracking the telescope.
    """
    def __init__(self):
        super().__init__(self)

    def __del__(self):
        self.wait()

    def run(self):
        pass

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        
        # Load the UI
        uic.loadUi('blaauw_dome_control.ui', self)

        self._log_message('Started dome control software...')

        # Listeners for the control buttons
        self.initButton.clicked.connect(self.init_clicked)
        self.calibrateButton.clicked.connect(self.calibrate_clicked)
        self.parkButton.clicked.connect(self.park_clicked)
        self.trackButton.clicked.connect(self.track_clicked)
        self.stopButton.clicked.connect(self.stop_clicked)

        self.gotoButton.clicked.connect(self.goto_clicked)
        self.azEdit.returnPressed.connect(self.goto_clicked)
        self.plusButton.clicked.connect(self.plus_5_clicked)
        self.minButton.clicked.connect(self.min_5_clicked)

        # Update outputs periodically (every 200 ms)
        update_timer = QTimer(self)
        update_timer.timeout.connect(self.update_widgets)
        update_timer.start(200)

    # def plot(self, dome_pos, scope_pos):
    #     """Plot a polar graph w/ the telescope & dome."""
    #     self.domeRadar.clear()

    #     self.domeRadar.hideAxis('left')
    #     self.domeRadar.hideAxis('bottom')

    #     self.domeRadar.setLimits(xMin=-1.5, xMax=1.5, yMin=-1.5, yMax=1.5)

    #     self.domeRadar.addLine(x=0, pen=0.2, bounds=(-1, 1))
    #     self.domeRadar.addLine(y=0, pen=0.2, bounds=(-1, 1))

    #     self.domeRadar.addLine(angle=45, pen=0.2, bounds=(-1, 1))
    #     self.domeRadar.addLine(angle=-45, pen=0.2, bounds=(-1, 1))
    
    #     dome_r = 1
    #     mount_r = 0.05
        
    #     mount = pg.QtGui.QGraphicsEllipseItem(-mount_r, -mount_r, mount_r * 2, 2*mount_r)
    #     mount.setPen(pg.mkPen(color='r', width=10))
    #     self.domeRadar.addItem(mount)

    #     dome = pg.QtGui.QGraphicsEllipseItem(-dome_r, -dome_r, dome_r * 2, 2*dome_r)
    #     dome.setPen(pg.mkPen(0.2))
    #     self.domeRadar.addItem(dome)

    #     # Generate dome/scope data
    #     slit_size = 30
        
    #     dome_az = np.arange(np.radians(dome_pos - slit_size/2), np.radians(dome_pos + slit_size/2), 0.01)
    #     dome_radius = np.ones(dome_az.size)

    #     scope_r = np.arange(0, 1.1, 0.1)
    #     scope_az = np.radians(scope_pos) * np.ones(scope_r.size)

    #     # Transform to cartesian and plot
    #     dome_coords = polar_to_cart(dome_radius, dome_az)
    #     scope_coords = polar_to_cart(scope_r, scope_az)

    #     self.domeRadar.plot(*dome_coords, pen=pg.mkPen(width=5))
    #     self.domeRadar.plot(*scope_coords, pen=pg.mkPen(color='r', width=5))
    
    def _log_message(self, msg):
        timestamp = datetime.now().strftime('%H:%M:%S')
        text = '[{}] {}'.format(timestamp, msg)

        self.log.append(text)

    def update_widgets(self):
        """
        Get the current dome/telescope position/status 
        and update the counter and the graph.
        """
        dome_az = 158.0 #get_dome_pos()

        # telescope.GetAzAlt()   
        # scope_az  = telescope.dAz
        # scope_alt = telescope.dAlt

        # telescope.GetRaDec()   
        scope_ra  = 2.4 #telescope.dRa
        scope_dec = 45.1  #telescope.dDec

        scope_coords = SkyCoord(ra=scope_ra*u.hour, dec=scope_dec*u.degree)

        # Update dome position
        self.azIndicator.setProperty('text', '{:.1f} deg'.format(dome_az))

        # Update tracking status
        is_tracking = False # TODO: retrieve tracking status
        tracking_status = 'Active' if True else 'Inactive'
        self.trackingIndicator.setProperty('text', tracking_status)
        
        # Update movement info
        is_idle = False # TODO: retrieve dome idle/move status
        idle_status = 'Yes' if is_idle else 'No'
        self.movingIndicator.setProperty('text', idle_status)

        # Update telescope status
        ra_fmt, dec_fmt = scope_coords.to_string('hmsdms').split(' ')
        self.raIndicator.setProperty('text', ra_fmt)
        self.decIndicator.setProperty('text', dec_fmt)

        # Update CCD info (useful for displaying when the dome should not move!)
        # TODO: Get CCD info
        # ccd_status = ccd.ExposureStatus
        ccd_status = 'Exposed'
        self.ccdIndicator.setProperty('text', ccd_status)

        # Update the plot
        # self.plot(justify(dome_az), justify(scope_az))

    def init_clicked(self):
        """Initialize & run the dome calibration routine"""
        self._log_message('Initializing the dome...')
        try:
            if self.thread.isRunning(): 
                    self.thread.terminate()
        except:
            pass
        
        self.thread = InitThread()
        self.thread.finished.connect(lambda: self._log_message('Dome initialized!'))
        self.thread.start()

    def calibrate_clicked(self):
        """Run KoepelX's calibration routine"""
        # msg = send_command('calibrate')
        msg = 'Calibration started'
        self._log_message(msg)

    def park_clicked(self):
        """Park the dome"""
        self._log_message('Parking dome')

        try:
            if self.thread.isRunning(): 
                    self.thread.terminate()
        except:
            pass
        
        self.thread = ParkThread()
        self.thread.finished.connect(lambda: self._log_message('Dome is parked!'))
        self.thread.start()

    def track_clicked(self):
        """Init. telescope tracking via KoepelX"""
        
        self._log_message('Dome is now tracking the telescope')

        try:
            if self.thread.isRunning(): 
                    self.thread.terminate()
        except:
            pass
        
        self.thread = TrackThread()
        self.thread.finished.connect(lambda: self._log_message('Disengaged telescope tracking!'))
        self.thread.start()

    def stop_clicked(self):
        """Informs KoepelX and tries to stop other threads"""
        try:
            if self.thread.isRunning(): 
                    self.thread.terminate()
        except:
            pass
        
        # msg = send_command('stop')
        msg = 'Stopping dome movement!'
        self._log_message(msg)

    def goto_clicked(self):
        """Go to azimuth (deg) input via azEdit"""
        if self.azEdit.text() == '':
            self._log_message('Dome has nowhere to go to!')
        else:
            # msg = send_command('goto ' + self.azEdit.text())
            msg = 'Go to {} deg'.format(self.azEdit.text())
            self._log_message(msg)
            
            # Reset the TextEdit
            self.azEdit.setText('')


    def plus_5_clicked(self):
        """Move the azimuth by +5 deg"""
        # msg = send_command('goto +5')
        msg = 'Change azimuth by +5 degrees'
        self._log_message(msg)

    def min_5_clicked(self):
        """Move the azimuth by -5 deg"""
        # msg = send_command('goto -5')
        msg = 'Change azimuth by -5 degrees'
        self._log_message(msg)

    def on_aperture_changed(self, aperture):
        """
        Ran when the aperture selection combobox 
        state is changed.
        """

        if aperture == 'Telescope':
            self._log_message('Change tracking to focus on the telescope..!')
        elif aperture == 'Telescope + Guider':
            self._log_message('Change tracking to focus on the telescope & autoguider..!')
        elif aperture == 'Finder':
            self._log_message('Change tracking to focus on the finder..!')
        else:
            self._log_message('ERROR... Selecting unknown aperture!')

def main():
    """Launching the Qt app"""
    app = QtWidgets.QApplication([])
    main = MainWindow()
    main.show()

    sys.exit(app.exec_())

if __name__ == '__main__':         
    main()