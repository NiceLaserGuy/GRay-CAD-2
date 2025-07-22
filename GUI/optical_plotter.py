import numpy as np
import pyqtgraph as pg
from pyqtgraph import LinearRegionItem
import copy

from PyQt5.QtCore import Qt

class OpticalSystemPlotter:
    def __init__(self, plotWidget, beam, matrices, vc):
        self.plotWidget = plotWidget
        self.beam = beam
        self.matrices = matrices
        self.vc = vc
        self.curve_sag = None
        self.curve_tan = None
        self.vlines = []
        self.z_setup = 0
        
        # Gespeicherte Parameter für update_plot_for_visible_range
        self.wavelength = None
        self.waist_sag = None
        self.waist_tan = None
        self.waist_pos_sag = None
        self.waist_pos_tan = None
        self.n = None
        self.optical_system_sag = None
        self.optical_system_tan = None
        self.z_data = None
        self.w_sag_data = None
        self.w_tan_data = None
        self.z_visible = None

    def update_live_plot(self, main_window):
        """Update the live plot based on current setup"""
        if main_window._plot_busy:
            return
        main_window._plot_busy = True
        try:
            if hasattr(main_window, '_live_plot_update_timer'):
                main_window._live_plot_update_timer.stop()
            beam_item = main_window.setupList.currentItem()
            if beam_item is None:
                beam_item = main_window.setupList.item(0)
            if beam_item is not None and hasattr(main_window, '_property_fields'):
                updated_beam = main_window.save_properties_to_component(beam_item.data(Qt.UserRole))
                if updated_beam is not None:
                    beam_item.setData(Qt.UserRole, updated_beam)
            optical_system_sag = main_window.build_optical_system_from_setup_list(mode="sagittal")
            optical_system_tan = main_window.build_optical_system_from_setup_list(mode="tangential")
            # Hole Startparameter aus dem Beam (immer an Position 0)
            beam_item = main_window.setupList.item(0)
            beam = beam_item.data(Qt.UserRole)
            props = beam.get("properties", {})
            wavelength = props.get("Wavelength", 514E-9)
            waist_sag = props.get("Waist radius sagittal", 1E-3)
            waist_tan = props.get("Waist radius tangential", 1E-3)
            waist_pos_sag = props.get("Waist position sagittal", 0.0)
            waist_pos_tan = props.get("Waist position tangential", 0.0)
            n = 1  # Optional: aus Beam-Properties holen
            try:
                self.plot_optical_system(
                    z_start_sag=waist_pos_sag,
                    z_start_tan=waist_pos_tan,
                    wavelength=wavelength,
                    waist_sag=waist_sag,
                    waist_tan=waist_tan,
                    n=n,
                    optical_system_sag=optical_system_sag,
                    optical_system_tan=optical_system_tan
                )
            except Exception:
                pass
        finally:
            main_window._plot_busy = False

    def plot_optical_system(self, z_start_sag, z_start_tan, wavelength, waist_sag, waist_tan, n, optical_system_sag, optical_system_tan):
        """Plot the optical system with sagittal and tangential beams"""
        # Speichere die aktuellen Parameter als Attribute, damit update_plot_for_visible_range darauf zugreifen kann
        self.wavelength = wavelength
        self.waist_sag = waist_sag
        self.waist_tan = waist_tan
        self.waist_pos_sag = z_start_sag
        self.waist_pos_tan = z_start_tan
        self.n = n
        self.optical_system_sag = optical_system_sag
        self.optical_system_tan = optical_system_tan
        
        self.curve_sag = None
        self.curve_tan = None
        self.plotWidget.clear()

        # Initialplot (z.B. gesamter Bereich)
        z_min, z_max = self.plotWidget.getViewBox().viewRange()[0]
        if not np.isfinite(z_min) or not np.isfinite(z_max) or z_min == z_max:
            # Fallback: Bereich aus optischem System bestimmen
            z_min = 0
            z_max = sum([p[1][0] for p in optical_system_sag if hasattr(p[0], "__func__") and p[0].__func__ is self.matrices.free_space.__func__])

        self.update_plot_for_visible_range(z_min, z_max)

    def update_plot_for_visible_range(self, *args, **kwargs):
        """Update plot for the currently visible range"""
        z_min, z_max = self.plotWidget.getViewBox().viewRange()[0]
        if not np.isfinite(z_min) or not np.isfinite(z_max) or z_min == z_max:
            z_min = 0
            z_max = sum([p[1][0] for p in self.optical_system_sag
                        if hasattr(p[0], "__func__") and p[0].__func__ is self.matrices.free_space.__func__])
        
        n_points = 2000
        self.z_visible = np.linspace(z_min, z_max, n_points)

        # Hole gespeicherte Parameter
        wavelength = self.wavelength
        waist_sag = self.waist_sag
        waist_tan = self.waist_tan
        waist_pos_sag = self.waist_pos_sag
        waist_pos_tan = self.waist_pos_tan
        n = self.n
        optical_system_sag = self.optical_system_sag
        optical_system_tan = self.optical_system_tan
        self.vb = self.plotWidget.getViewBox()

        # q-Werte berechnen und propagieren
        q_sag = self.beam.q_value(waist_pos_sag, waist_sag, wavelength, n)
        q_tan = self.beam.q_value(waist_pos_tan, waist_tan, wavelength, n)
        try:
            self.z_data, self.w_sag_data, z_setup = self.beam.propagate_through_system(wavelength, q_sag, optical_system_sag, self.z_visible, n_points, n=n)
            self.z_data, self.w_tan_data, z_setup = self.beam.propagate_through_system(wavelength, q_tan, optical_system_tan, self.z_visible, n_points, n=n)
            self.z_setup = z_setup
        except Exception:
            self.vb.setXRange(0, 1, padding=0.02)
            #self.show_error()

        # Plot aktualisieren oder neu erstellen
        if not hasattr(self, "curve_sag") or self.curve_sag is None:
            self.plotWidget.clear()
            self.plotWidget.setBackground('w')
            self.plotWidget.addLegend()
            self.plotWidget.showGrid(x=True, y=True)
            self.plotWidget.setLabel('left', 'Waist radius', units='m', color='#333333')
            self.plotWidget.setLabel('bottom', 'z', units='m', color='#333333')
            self.plotWidget.setTitle("Gaussian Beam Propagation", color='#333333')
            axis_pen = pg.mkPen(color='#333333')
            self.plotWidget.getAxis('left').setTextPen(axis_pen)
            self.plotWidget.getAxis('bottom').setTextPen(axis_pen)
            self.plotWidget.setDefaultPadding(0.02)  # 2% padding around the plot
            region = LinearRegionItem(values=[0, z_setup], orientation='vertical', brush=(100, 100, 255, 30), movable=False)
            self.plotWidget.addItem(region)

            self.curve_sag = self.plotWidget.plot(self.z_data, self.w_sag_data, pen=pg.mkPen('r', width=1.5), name="Sagittal")
            self.curve_tan = self.plotWidget.plot(self.z_data, self.w_tan_data, pen=pg.mkPen('b', width=1.5), name="Tangential")
        else:
            self.curve_sag.setData(self.z_data, self.w_sag_data)
            self.curve_tan.setData(self.z_data, self.w_tan_data)

        # → Immer X-Achse an sichtbaren Bereich anpassen
        current_range = self.plotWidget.getViewBox().viewRange()[0]
        if abs(current_range[0] - z_min) > 1e-9 or abs(current_range[1] - z_max) > 1e-9:
            try:
                self.vb.sigXRangeChanged.disconnect(self.update_plot_for_visible_range)
            except TypeError:
                pass
            self.vb.sigXRangeChanged.connect(self.update_plot_for_visible_range)
            self.vb.setXRange(0, z_setup, padding=0.02)

        # Vertikale Linien aktualisieren
        for vline in getattr(self, "vlines", []):
            self.plotWidget.removeItem(vline)
        self.vlines = []
        z_element = 0
        for idx, (element, param) in enumerate(optical_system_sag):
            if hasattr(element, "__func__") and element.__func__ is self.matrices.free_space.__func__:
                z_element += param[0]
            else:
                vline = pg.InfiniteLine(pos=z_element, angle=90, pen=pg.mkPen(width=2, color="#FF0000"))
                self.plotWidget.addItem(vline)
                self.vlines.append(vline)

    def scale_visible_setup(self):
        """Scale the visible setup elements to the current view"""
        self.vb = self.plotWidget.getViewBox()
        self.vb.setXRange(0, self.z_setup, padding=0.02)
        xRange = self.vb.viewRange()[0]
        visible_mask = (self.z_data >= xRange[0]) & (self.z_data <= xRange[1])
        visible_y = self.w_sag_data[visible_mask]
        if len(visible_y) > 0:
            ymax = visible_y.max()
            self.vb.setYRange(0, ymax, padding=0.1)

    def plot_optical_system_from_resonator(self, optical_system):
        """Plot optical system from resonator setup"""
        self.plot_optical_system(optical_system=optical_system)