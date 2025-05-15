import json
import os

class ComponentLibrary:
    def __init__(self, library_path):
        self.library_path = library_path
        self.lenses = self.load_lenses()
        self.mirrors = self.load_mirror()

    def load_lenses(self):
        lenses = {}
        for filename in os.listdir(self.library_path):
            if filename.endswith(".json"):
                with open(os.path.join(self.library_path, filename), 'r') as file:
                    data = json.load(file)
                    for component in data.get("components", []):
                        if component["type"] == "Lens":
                            lenses[component["name"]] = component["properties"]
        return lenses
    
    def load_mirror(self):
        mirrors = {}
        for filename in os.listdir(self.library_path):
            if filename.endswith(".json"):
                with open(os.path.join(self.library_path, filename), 'r') as file:
                    data = json.load(file)
                    for component in data.get("components", []):
                        if component["type"] == "Mirror":
                            mirrors[component["name"]] = component["properties"]
        return mirrors
    
    def get_mirror_curvatures(self):
        """Return a list of tuples containing CURVATURE_IN_SAGITTAL and CURVATURE_IN_TANGENTIAL for each lens"""
        curvatures = []
        for lens_name, properties in self.mirrors.items():
            curvature_in_sagittal = properties.get("CURVATURE_IN_SAGITTAL")
            curvature_in_tangential = properties.get("CURVATURE_IN_TANGENTIAL")
            if curvature_in_sagittal is not None and curvature_in_tangential is not None:
                curvatures.append((curvature_in_sagittal, curvature_in_tangential))
        return curvatures

    def get_lens_properties(self, lens_name):
        return self.lenses.get(lens_name, None)