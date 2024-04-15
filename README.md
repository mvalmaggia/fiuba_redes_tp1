# fiuba_redes_tp1

# Alexis, Matias
## Protocolo cliente para el upload

UPLOAD:
* Nombre_archivo

DATA:
* Sec number
* Datos
* Nombre_archivo

FIN_DOWNLOAD:
* Nombre_archivo

## Protocolo servidor para el upload

UPLOAD (confirmación):
* Nombre_archivo

ACK:
* Sec number
* Nombre_archivo

FIN_DOWNLOAD (confirmación):
* Nombre_archivo

# Gabriel, Ramiro
## Protocolo cliente para el download

DOWNLOAD:
* Nombre_archivo

ACK:
* Sec number
* nombre_archivo

FIN_UPLOAD:
* Nombre_archivo

## Protocolo servidor para el download

DATA:
* Sec number
* Nombre_archivo
* Datos

FIN_UPLOAD:
* Nombre_archivo
* Sec number

# Preguntas:
- Asumimos port fijo por cada conexión?
