TEMP_FILE_PATH_LIB = None  # Initialisierung der globalen Variable
TEMP_RESONATOR_SETUP = None  # Initialisierung der globalen Variable

def set_temp_file_path(path):
    global TEMP_FILE_PATH_LIB
    TEMP_FILE_PATH_LIB = path

def get_temp_file_path():
    return TEMP_FILE_PATH_LIB

def set_temp_file_resonator_setup(*args):
    global TEMP_RESONATOR_SETUP
    TEMP_RESONATOR_SETUP = args
    
def get_temp_file_resonator_setup():
    return TEMP_RESONATOR_SETUP