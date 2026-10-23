# Formatos para Guatemala (sobrescriben los de Django para "es").
# Lo que no se define aquí se toma del idioma español de Django.

# Q 1,250.50 (punto decimal, coma de miles)
DECIMAL_SEPARATOR = "."
THOUSAND_SEPARATOR = ","
NUMBER_GROUPING = 3

DATE_FORMAT = "d/m/Y"
DATETIME_FORMAT = "d/m/Y H:i"
SHORT_DATE_FORMAT = "d/m/Y"
SHORT_DATETIME_FORMAT = "d/m/Y H:i"
FIRST_DAY_OF_WEEK = 1

# El primer formato es el que usan los <input type="date">: debe ser ISO.
DATE_INPUT_FORMATS = ["%Y-%m-%d", "%d/%m/%Y", "%d/%m/%y"]
DATETIME_INPUT_FORMATS = [
    "%Y-%m-%dT%H:%M",
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%d %H:%M",
    "%d/%m/%Y %H:%M:%S",
    "%d/%m/%Y %H:%M",
]
