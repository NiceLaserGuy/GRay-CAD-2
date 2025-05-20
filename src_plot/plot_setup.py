import numpy as np
import pyqtgraph as pg
from PyQt5.QtWidgets import QApplication

# Input parameters
w0 = 1e-3  # Input beam radius in meters
lambda_ = 632.8e-9  # Wavelength in meters (HeNe laser)
z_R = np.pi * w0**2 / lambda_
q0 = 1j * z_R

def abcd_free_space(d):
    return np.array([[1, d],
                     [0, 1]])

def abcd_thin_lens(f):
    """
    ABCD matrix for a thin lens with focal length f (in meters)
    """
    return np.array([[1, 0],
                     [-1/f, 1]])

def propagate_q(q_in, ABCD):
    A, B, C, D = ABCD.flatten()
    return (A * q_in + B) / (C * q_in + D)

def beam_radius(q, lambda_):
    return np.sqrt(-lambda_ / (np.pi * np.imag(1/q)))

def propagate_through_system(q_initial, elements):
    """
    Propagate beam through a sequence of optical elements
    
    Args:
        q_initial: Initial q parameter
        elements: List of tuples (element_function, parameter)
    Returns:
        z_positions, w_values: Lists of positions and beam radii
    """
    q = q_initial
    z_total = 0
    z_positions = [z_total]
    w_values = [beam_radius(q, lambda_)]
    
    for element, param in elements:
        if element == abcd_free_space:
            # For free space, calculate multiple points
            steps = 200
            dz = param / steps
            for i in range(steps):
                ABCD = abcd_free_space(dz)
                q = propagate_q(q, ABCD)
                z_total += dz
                z_positions.append(z_total)
                w_values.append(beam_radius(q, lambda_))
        else:
            # For other elements (like lenses), just propagate once
            ABCD = element(param)
            q = propagate_q(q, ABCD)
            w_values.append(beam_radius(q, lambda_))
            z_positions.append(z_total)
    
    return z_positions, w_values

def plot_beam_radius():
    # Create PyQtGraph window
    app = QApplication([])
    win = pg.GraphicsLayoutWidget(show=True)
    win.setWindowTitle('Gaussian Beam Propagation Through Optical System')
    
    # Create plot item
    plot = win.addPlot()
    plot.setLabel('left', "Beam radius w(z)", units='mm')
    plot.setLabel('bottom', "Position z", units='mm')
    plot.setTitle("Gaussian Beam Propagation")
    plot.showGrid(x=True, y=True)
    
    # Add crosshair
    vLine = pg.InfiniteLine(angle=90, movable=False)
    hLine = pg.InfiniteLine(angle=0, movable=False)
    plot.addItem(vLine, ignoreBounds=True)
    plot.addItem(hLine, ignoreBounds=True)
    vLine.setVisible(False)
    hLine.setVisible(False)
    
    # Add text item for coordinates
    text = pg.TextItem(text='', anchor=(0.5, 2.0))
    plot.addItem(text)
    
    # Define optical system: propagation(0.1m) -> lens(f=0.05m) -> propagation(0.2m)
    optical_system = [
        (abcd_free_space, 0.05),    # Propagate 5cm
        (abcd_thin_lens, 0.1),      # Lens with f = 10cm
        (abcd_free_space, 0.15),    # Propagate 15cm
        (abcd_thin_lens, 0.05),     # Lens with f = 5cm
        (abcd_free_space, 0.1),     # Propagate 10cm
        (abcd_thin_lens, 0.05),     # Lens with f = 5cm
        (abcd_free_space, 0.1),     # Propagate 10cm
    ]
    
    # Calculate beam propagation
    z_vals, w_vals = propagate_through_system(q0, optical_system)
    
    # Convert to mm for plotting
    z_vals = np.array(z_vals) * 1e3  # meters to mm
    w_vals = np.array(w_vals) * 1e3  # meters to mm
    
    # Plot data
    plot.plot(z_vals, w_vals, pen=pg.mkPen('b', width=2))
    
    # Add vertical lines at optical element positions
    z_element = 0
    for element, param in optical_system:
        if element == abcd_thin_lens:
            plot.addLine(x=z_element*1e3, pen=pg.mkPen('r'))
        z_element += param if element == abcd_free_space else 0
    
    # Update crosshair and text position
    def mouseMoved(evt):
        pos = evt
        if plot.sceneBoundingRect().contains(pos):
            mousePoint = plot.vb.mapSceneToView(pos)
            # Finde den Index des nächsten x-Werts
            x = mousePoint.x()
            idx = (np.abs(z_vals - x)).argmin()
            x_val = z_vals[idx]
            y_val = w_vals[idx]
            vLine.setPos(x_val)
            hLine.setPos(y_val)
            text.setPos(x_val, y_val)
            text.setText(f'z = {x_val:.1f} mm\nw = {y_val:.1f} mm')
    
    # Connect signal to function
    plot.scene().sigMouseMoved.connect(mouseMoved)
    
    # Start Qt event loop
    app.exec_()

if __name__ == '__main__':
    plot_beam_radius()