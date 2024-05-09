#!/bin/bash

# Crear o vaciar el archivo de resultados si ya existe
echo "" > benchmark_results.txt

# Lista de tamaños de archivos
sizes=("1kb" "10kb" "100kb" "500kb" "1000kb")

# Bucle para ejecutar cada comando y guardar el tiempo
for size in ${sizes[@]}; do
    echo "Running benchmark for $size file..."
    # Ejecutar el comando y capturar tanto stdout como stderr
    # python download.py -n 1kb_server.txt -d data/downloads/1kb_downloaded.txt -v
    { time python3 download.py -d data/downloads/${size}_downloaded.txt -n ${size}_server.txt -v; } 2>&1 | tee temp_time.txt
    # Verificar si hubo errores
    if [ $? -ne 0 ]; then
        echo "Error running benchmark for $size file."
        cat temp_time.txt
    else
        # Extraer solo las líneas de tiempo
        real_time=$(grep real temp_time.txt | awk '{print $2}')
        # Guardar en el archivo de resultados
        echo "$size: $real_time" >> benchmark_results.txt
    fi
done

# Eliminar el archivo temporal
rm temp_time.txt

echo "Benchmarks completed."
