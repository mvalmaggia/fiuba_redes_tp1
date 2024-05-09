# Trabajo Práctico - Transferencia de archivos usando protocolo UDP

## Integrantes

- Herrera Alexis 104639	
- La Torre Gabriel 87796	 
- Lozano Ramiro 98263
- Valmaggia Matias 105621

## Servidor
Para empezar a probar el servidor, se debe ejecutar el siguiente comando:
```bash
python start-server.py
```
Por defecto el servidor utilizara como repositorio de archivos la carpeta data/server_storage.
Para cambiar la carpeta de almacenamiento se debe puede pasar el parametro -s <path>
Asi mismo, como lo indicaba la consigna, se pueden utilizar los parametros -H y -p para cambiar el host y el puerto respectivamente.
Por último para elegir el algoritmo de retransmisión se puede utilizar el parámetro -g para usar Go-Back-N o -w para usar Stop and Wait.
Para más detalle se puede ejecutar el siguiente comando
```bash
python start-server.py -h
```
## Upload
Para subir archivos al servidor se debe ejecutar el siguiente comando:
```bash
python upload.py -s FILE_PATH
```
También se le puede agregar el parametro -n FILE_NAME para indicarle el nombre con el que se guardará el archivo en el servidor.
El algoritmo se puede elegir con el parametro -g para Go-Back-N o -w para Stop and Wait. Debe ser el mismo que el del servidor.
Para más detalle se puede ejecutar el siguiente comando
```bash
python upload.py -h
```
## Download
Para descargar archivos del servidor se debe ejecutar el siguiente comando:
```bash
python download.py -n FILE_NAME -d FILE_PATH
```
El FILE_NAME es el nombre del archivo (no path) que se quiere descargar del servidor y FILE_PATH es la ruta donde se guardará el archivo.
En este caso no se puede elegir el algoritmo de retransmisión ya que solamente se enviarán paquetes de ACKs al servidor (salvo el primero y el último).
Para más detalle se puede ejecutar el siguiente comando
```bash
python download.py -h
```
