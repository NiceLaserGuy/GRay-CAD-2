TEMP_FILE_PATH_LIB = None  # Initialisierung der globalen Variable
TEMP_RESONATOR_SETUP = None  # Initialisierung der globalen Variable
TEMP_RESONATOR_TYPE = None
TEMP_LIGHT_FIELD_PARAMETERS = None

def set_temp_file_path(path):
    global TEMP_FILE_PATH_LIB
    TEMP_FILE_PATH_LIB = path

def get_temp_file_path():
    return TEMP_FILE_PATH_LIB

def set_temp_resonator_setup(*args):
    global TEMP_RESONATOR_SETUP
    TEMP_RESONATOR_SETUP = args
    
def get_temp_resonator_setup():
    return TEMP_RESONATOR_SETUP

def set_temp_resonator_type(resonator_type):
    global TEMP_RESONATOR_TYPE
    TEMP_RESONATOR_TYPE = resonator_type
    
def get_temp_resonator_type():
    return TEMP_RESONATOR_TYPE

def set_temp_light_field_parameters(*args):
    global TEMP_LIGHT_FIELD_PARAMETERS
    TEMP_LIGHT_FIELD_PARAMETERS = args
    
def get_temp_light_field_parameters():
    return TEMP_LIGHT_FIELD_PARAMETERS