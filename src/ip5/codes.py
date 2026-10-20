# Parameter and unit codes sent by the Philips IntelliVue Expression IP5 (MR400)
# over its serial data export.

# parameter name -> code
DATA_CODES = {
    'Heart rate': '0002-4182',
    'P1 – Systolic': '0002-f0a5',
    'P1 – Mean': '0002-f0a7',
    'P1 – Diastolic': '0002-f0a6',
    'P2 – Systolic': '0002-f0a9',
    'P2 – Mean': '0002-f0ab',
    'P2 – Diastolic': '0002-f0aa',
    'SPO2': '0002-4bb8',
    'Respiration rate': '0002-5012',
    'Expired CO2': '0002-50b0',
    'Inspired CO2': '0002-50ba',
    'Inspired N2O': '0002-5280',
    'Expired N2O': '0002-522c',
    'Inspired O2': '0002-7498',
    'Expired Desflurane': '0002-5214',
    'Expired Enflurane': '0002-5218',
    'Expired Isoflurane': '0002-5224',
    'Expired Sevoflurane': '0002-5220',
    'Expired Halothane': '0002-521c',
    'Inspired Desflurane': '0002-5268',
    'Inspired Enflurane': '0002-526c',
    'Inspired Isoflurane': '0002-5278',
    'Inspired Sevoflurane': '0002-5274',
    'Inspired Halothane': '0002-5270',
    'Temperature': '0002-4b48',
    'NIBP – Systolic': '0002-4a05',
    'NIBP – Mean': '0002-4a07',
    'NIBP – Diastolic': '0002-4a06',
}

# non periodic data (only sent when a measurement is made)
NON_PERIODIC_DATA = ('NIBP – Systolic', 'NIBP – Mean', 'NIBP – Diastolic')

# unit name -> code
UNIT_CODES = {
    'BPM': '0004-0aa0',
    'Breaths/min': '0004-0ae0',
    'kPa': '0004-0f03',
    'mmHg': '0004-0f20',
    '%': '0004-0220',
    '°C': '0004-17a0',
    '°F': '0004-1140',
}

# reverse lookups, code -> name
CODE_TO_DATA = {code: name for name, code in DATA_CODES.items()}
CODE_TO_UNIT = {code: name for name, code in UNIT_CODES.items()}


def dataName(code):
    # unknown parameters are kept, named after their code
    return CODE_TO_DATA.get(code, f'Unknown {code}')


def unitName(code):
    return CODE_TO_UNIT.get(code, code)
