# Trabajo Práctico - Transferencia de archivos usando protocolo UDP

## Integrantes

- Herrera Alexis 104639	
- La Torre Gabriel 87796	 
- Lozano Ramiro 98263
- Valmaggia Matias 105621


Grupo 10
## Servidor
Para empezar a probar el servidor, se debe ejecutar el siguiente comando:
```bash
python start-server.py -v
```
Ese comando por defecto utilizará como repositorio de almacenamiento el directorio `data/server_storage`.
Dicha carpeta se puede cambiar utilizando el parametro `-s` PATH.  
Asi mismo, como lo indicaba la consigna, se pueden utilizar los parametros `-H` y `-p` para cambiar el host y el puerto respectivamente.  
Algo muy **importante** es elegir el algoritmo de retransmisión se puede utilizar el parámetro `-g` para usar Go-Back-N o `-w` para usar Stop and Wait, por defecto se utiliza Go-Back-N.

Para más detalle se puede ejecutar el siguiente comando
```bash
python start-server.py -h
```
## Upload
Para subir archivos al servidor se debe ejecutar el siguiente comando:
```bash
python upload.py -s FILE_PATH
```
También se le puede agregar el parametro `-n FILE_NAME` para indicarle el nombre con el que se guardará el archivo en el servidor.
El algoritmo se puede elegir con el parametro `-g` para Go-Back-N o `-w` para Stop and Wait.  
**Si se elige Stop and Wait, el servidor también deberá utilizar este algoritmo.**
```bash
python upload.py -h
```
## Download
Para descargar archivos del servidor se debe ejecutar el siguiente comando:
```bash
python download.py -n FILE_NAME -d FILE_PATH
```
El FILE_NAME es el nombre del archivo (el nombre del archivo en el storage) que se quiere descargar del servidor y FILE_PATH es la ruta donde se guardará el archivo.
En este caso no se puede elegir el algoritmo de retransmisión ya que solamente se enviarán paquetes de ACKs al servidor (salvo el primero y el último).
Para más detalle se puede ejecutar el siguiente comando
```bash
python download.py -h
```

## Ejemplos
Recomendamos tener la siguiente estructura directorios para probar el servidor:
```
.
├── data/
│   ├── server_storage
│   ├── downloads
│   └── uploads/
│       ├── 1kb.txt
│       ├── 10kb.txt
│       ├── 100kb.txt
│       ├── 500kb.txt
│       └── 1000kb.txt
├── lib/
│   └── ...
├── download.py
├── upload.py
└── start-server.py
```
Empezando con estos 5 archivos, con el upload vamos a pasarlos a server_storage. Y luego con el download vamos a tomar esos archivos y los vamos a pasar a downloads.  
Luego también podremos verificar que los archivos son iguales con el comando `cmp`.

### Probando Go-Back-N
Iniciamos servidor con Go-Back-N y luego esos 5 comandos subira al servidor los archivos. Podemos también verificar que los archivos son iguales con el comando `cmp`.  
De igual manera, se pueden descargar los archivos del servidor en la carpeta downloads y verificar que son iguales con el comando `cmp`.
```bash
python start-server.py -g -v
```
#### Upload
```bash
python upload.py -s data/uploads/1kb.txt -n 1kb_server.txt -g -v
python upload.py -s data/uploads/10kb.txt -n 10kb_server.txt -g -v
python upload.py -s data/uploads/100kb.txt -n 100kb_server.txt -g -v
python upload.py -s data/uploads/500kb.txt -n 500kb_server.txt -g -v
python upload.py -s data/uploads/1000kb.txt -n 1000kb_server.txt -g -v
```

#### Comprobaciones
```bash
cmp data/uploads/1kb.txt data/server_storage/1kb_server.txt
cmp data/uploads/10kb.txt data/server_storage/10kb_server.txt
cmp data/uploads/100kb.txt data/server_storage/100kb_server.txt
cmp data/uploads/500kb.txt data/server_storage/500kb_server.txt
cmp data/uploads/1000kb.txt data/server_storage/1000kb_server.txt
```

#### Download
```bash
python download.py -n 1kb_server.txt -d data/downloads/1kb_downloaded.txt -v
python download.py -n 10kb_server.txt -d data/downloads/10kb_downloaded.txt -v
python download.py -n 100kb_server.txt -d data/downloads/100kb_downloaded.txt -v
python download.py -n 500kb_server.txt -d data/downloads/500kb_downloaded.txt -v
python download.py -n 1000kb_server.txt -d data/downloads/1000kb_downloaded.txt -v
```
#### Comprobaciones
```bash
cmp data/server_storage/1kb_server.txt data/downloads/1kb_downloaded.txt
cmp data/server_storage/10kb_server.txt data/downloads/10kb_downloaded.txt
cmp data/server_storage/100kb_server.txt data/downloads/100kb_downloaded.txt
cmp data/server_storage/500kb_server.txt data/downloads/500kb_downloaded.txt
cmp data/server_storage/1000kb_server.txt data/downloads/1000kb_downloaded.txt
```

### Probando Stop and Wait
Antes de probar Stop and Wait, se debe detener el servidor (con CTRL-c) e iniciarlo en modo Stop and Wait.  
También recomendamos eliminar los archivos de server_storage y de downloads. Sin embargo funcionará igualmente pues se pisarán esos archivos.
```bash
python start-server.py -w -v
```
#### Upload
```bash
python upload.py -s data/uploads/1kb.txt -n 1kb_server.txt -w -v
python upload.py -s data/uploads/10kb.txt -n 10kb_server.txt -w -v
python upload.py -s data/uploads/100kb.txt -n 100kb_server.txt -w -v
python upload.py -s data/uploads/500kb.txt -n 500kb_server.txt -w -v
python upload.py -s data/uploads/1000kb.txt -n 1000kb_server.txt -w -v
```

#### Comprobaciones
```bash
cmp data/uploads/1kb.txt data/server_storage/1kb_server.txt
cmp data/uploads/10kb.txt data/server_storage/10kb_server.txt
cmp data/uploads/100kb.txt data/server_storage/100kb_server.txt
cmp data/uploads/500kb.txt data/server_storage/500kb_server.txt
cmp data/uploads/1000kb.txt data/server_storage/1000kb_server.txt
```

#### Download
```bash
python download.py -n 1kb_server.txt -d data/downloads/1kb_downloaded.txt -v
python download.py -n 10kb_server.txt -d data/downloads/10kb_downloaded.txt -v
python download.py -n 100kb_server.txt -d data/downloads/100kb_downloaded.txt -v
python download.py -n 500kb_server.txt -d data/downloads/500kb_downloaded.txt -v
python download.py -n 1000kb_server.txt -d data/downloads/1000kb_downloaded.txt -v
```
#### Comprobaciones
```bash
cmp data/server_storage/1kb_server.txt data/downloads/1kb_downloaded.txt
cmp data/server_storage/10kb_server.txt data/downloads/10kb_downloaded.txt
cmp data/server_storage/100kb_server.txt data/downloads/100kb_downloaded.txt
cmp data/server_storage/500kb_server.txt data/downloads/500kb_downloaded.txt
cmp data/server_storage/1000kb_server.txt data/downloads/1000kb_downloaded.txt
```