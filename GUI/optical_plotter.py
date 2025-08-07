import numpy as np
import pyqtgraph as pg
from pyqtgraph import LinearRegionItem
import copy
from PyQt5.QtWidgets import QMessageBox

from PyQt5 import QtCore

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
        
        # NEU: Flag für Update-Schutz
        self._updating_plot = False
        
        # Gespeicherte Parameter
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
            # EINFACH: Stumme Prüfung ohne Debug-Ausgabe
            if main_window.setupList.count() == 0:
                return  # Stiller Return ohne Meldung
                
            beam_item = main_window.setupList.currentItem()
            if beam_item is None:
                beam_item = main_window.setupList.item(0)
                
            if beam_item is None:
                return  # Stiller Return
                
            # KORRIGIERT: Prüfe UserRole-Daten
            beam_data = beam_item.data(QtCore.Qt.UserRole)
            if beam_data is None:
                QMessageBox.warning(self, "Error", "No data found in beam item")
                return
                
            if hasattr(main_window, '_property_fields'):
                # KORRIGIERT: Verwende die geerbte Methode aus PropertiesHandler
                updated_beam = main_window.save_properties_to_component(beam_data)
                if updated_beam is not None:
                    beam_item.setData(QtCore.Qt.UserRole, updated_beam)
                    beam_data = updated_beam
        
            optical_system_sag = main_window.build_optical_system_from_setup_list(mode="sagittal")
            optical_system_tan = main_window.build_optical_system_from_setup_list(mode="tangential")
            
            # KORRIGIERT: Verwende bereits validierte beam_data
            props = beam_data.get("properties", {})
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
            except Exception as e:
                print(f"Error in plot_optical_system: {e}")
        except Exception as e:
            print(f"Error in update_live_plot: {e}")
        finally:
            main_window._plot_busy = False

    def plot_optical_system(self, z_start_sag, z_start_tan, wavelength, waist_sag, waist_tan, n, optical_system_sag, optical_system_tan):
        """Plot the optical system with sagittal and tangential beams"""
        # KORRIGIERT: Verhindere Rekursion während Initialisierung
        if self._updating_plot:
            return
        
        self._updating_plot = True
        
        try:
            # Speichere Parameter
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

            # ViewBox holen
            vb = self.plotWidget.getViewBox()
            
            # Wenn ein Signal bereits verbunden ist, trenne NUR dieses eine
            try:
                vb.sigXRangeChanged.disconnect(self.update_plot_for_visible_range)
            except (TypeError, RuntimeError):
                # Signal war nicht verbunden, ignorieren
                pass
        
            # Bestimme initialen Bereich aus optischem System
            z_max = sum([p[1][0] for p in optical_system_sag 
                        if hasattr(p[0], "__func__") and p[0].__func__ is self.matrices.free_space.__func__])
            z_min = 0
            
            # Setze ViewBox-Range ohne Signal
            vb.setXRange(z_min, z_max, padding=0.02)
            
            # Initiale Plot-Berechnung
            self._update_plot_internal(z_min, z_max)
            
            # Signal wieder verbinden NACH der Initialisierung
            vb.sigXRangeChanged.connect(self.update_plot_for_visible_range)
            
        finally:
            self._updating_plot = False

    def update_plot_for_visible_range(self, view_box, view_range):
        """Update plot for the currently visible range"""
        # KORRIGIERT: Verhindere Rekursion
        if self._updating_plot:
            return
        
        if not hasattr(self, 'optical_system_sag') or self.optical_system_sag is None:
            return
    
        self._updating_plot = True
    
        try:
            # Aktueller sichtbarer Bereich
            z_min, z_max = view_range
            
            # Begrenze auf positiven Bereich
            z_min = max(0, z_min)
            z_max = max(z_min + 1e-6, z_max)
            
            if not np.isfinite(z_min) or not np.isfinite(z_max):
                return
            
            # Interne Update-Funktion aufrufen
            self._update_plot_internal(z_min, z_max)
            
        finally:
            self._updating_plot = False

    def _update_plot_internal(self, z_min, z_max):
        """Interne Plot-Update-Funktion ohne Signal-Behandlung"""
        FIXED_RESOLUTION = 1000
        z_visible = np.linspace(z_min, z_max, FIXED_RESOLUTION)
        
        # q-Werte berechnen
        q_sag = self.beam.q_value(self.waist_pos_sag, self.waist_sag, self.wavelength, self.n)
        q_tan = self.beam.q_value(self.waist_pos_tan, self.waist_tan, self.wavelength, self.n)
        
        try:
            # Beam-Propagation berechnen
            self.z_data, self.w_sag_data, z_setup = self.beam.propagate_through_system(
                self.wavelength, q_sag, self.optical_system_sag, z_visible, FIXED_RESOLUTION, n=self.n)
            _, self.w_tan_data, _ = self.beam.propagate_through_system(
                self.wavelength, q_tan, self.optical_system_tan, z_visible, FIXED_RESOLUTION, n=self.n)
            
            self.z_setup = z_setup
            
            # Plot aktualisieren oder erstellen
            if hasattr(self, "curve_sag") and self.curve_sag is not None:
                # Nur Daten aktualisieren
                self.curve_sag.setData(self.z_data, self.w_sag_data)
                self.curve_tan.setData(self.z_data, self.w_tan_data)
            else:
                # Initialer Plot
                self._create_initial_plot()
                
        except Exception as e:
            print(f"Error in plot calculation: {e}")

    def _create_initial_plot(self):
        """Erstelle initialen Plot - OHNE ViewBox-Manipulation"""
        self.plotWidget.setBackground('w')
    
        # Legend nur hinzufügen wenn noch nicht vorhanden
        if not hasattr(self.plotWidget, '_legend') or self.plotWidget._legend is None:
            self.plotWidget.addLegend()
        
        self.plotWidget.showGrid(x=True, y=True)
        self.plotWidget.setLabel('left', 'Waist radius', units='m', color='#333333')
        self.plotWidget.setLabel('bottom', 'z', units='m', color='#333333')
        self.plotWidget.setTitle("Gaussian Beam Propagation", color='#333333')
        
        # Setup-Region (OHNE ViewBox-Änderung)
        if hasattr(self, 'z_setup') and self.z_setup > 0:
            region = LinearRegionItem(values=[0, self.z_setup], orientation='vertical', 
                                    brush=(100, 100, 255, 30), movable=False)
            self.plotWidget.addItem(region)
        
        # Kurven erstellen (OHNE Auto-Range)
        if hasattr(self, 'z_data') and hasattr(self, 'w_sag_data') and hasattr(self, 'w_tan_data'):
            self.curve_sag = self.plotWidget.plot(self.z_data, self.w_sag_data, 
                                                pen=pg.mkPen('r', width=1.5), name="Sagittal")
            self.curve_tan = self.plotWidget.plot(self.z_data, self.w_tan_data, 
                                                pen=pg.mkPen('b', width=1.5), name="Tangential")
        
        # Vertikale Linien (mit Fehlerbehandlung)
        try:
            self.update_vertical_lines()
        except Exception as e:
            print(f"Warning: Could not update vertical lines: {e}")

    def scale_visible_setup(self):
        """Scale the visible setup elements to the current view"""
        if self._updating_plot:
            return
        
        self._updating_plot = True
        
        try:
            vb = self.plotWidget.getViewBox()
            
            # EINFACHER: Direkte Range-Setzung ohne Signal-Manipulation
            if hasattr(self, 'z_setup') and self.z_setup > 0:
                # X-Range auf Setup-Bereich setzen
                vb.setXRange(0, self.z_setup, padding=0.02)
                    
                max_w_sag = np.max(self.w_sag_data) if len(self.w_sag_data) > 0 else 0
                max_w_tan = np.max(self.w_tan_data) if len(self.w_tan_data) > 0 else 0
                ymax = max(max_w_sag, max_w_tan)
                if ymax > 0:
                    vb.setYRange(0, ymax * 1.1, padding=0.05)
        
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Error in scale_visible_setup: {e}")
        finally:
            self._updating_plot = False

    def plot_optical_system_from_resonator(self, optical_system):
        """Plot optical system from resonator setup"""
        self.plot_optical_system(optical_system=optical_system)

    def update_vertical_lines(self):
        """Update vertical lines for optical elements"""
        # Alte Linien entfernen
        for vline in getattr(self, "vlines", []):
            self.plotWidget.removeItem(vline)
        self.vlines = []
        
        # Neue Linien hinzufügen
        if hasattr(self, 'optical_system_sag') and self.optical_system_sag:
            z_element = 0
            for idx, (element, param) in enumerate(self.optical_system_sag):
                if hasattr(element, "__func__") and element.__func__ is self.matrices.free_space.__func__:
                    # Freiraum-Segment - Position erhöhen
                    z_element += param[0]
                else:
                    # Optisches Element - vertikale Linie zeichnen
                    vline = pg.InfiniteLine(pos=z_element, angle=90, pen=pg.mkPen(width=2, color="#FF0000"))
                    self.plotWidget.addItem(vline)
                    self.vlines.append(vline)

    def get_element_positions(self):
        """Get z-positions of all optical elements"""
        positions = []
        if hasattr(self, 'optical_system_sag') and self.optical_system_sag:
            z_current = 0
            for element, param in self.optical_system_sag:
                if hasattr(element, "__func__") and element.__func__ is self.matrices.free_space.__func__:
                    z_current += param[0]
                else:
                    positions.append(z_current)
        return positions

    def clear_vertical_lines(self):
        """Clear all vertical lines from the plot"""
        for vline in getattr(self, "vlines", []):
            self.plotWidget.removeItem(vline)
        self.vlines = []