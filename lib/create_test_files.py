import logging
import sys

log = logging.getLogger(__name__)


def create_large_text_file(file_path, size_in_kb):
    content = "A" * 1024  # 1 KB

    with open(file_path, "w") as file:
        while file.tell() < size_in_kb * 1024:
            file.write(content)

    log.debug(
        f"Archivo de texto de {size_in_kb} KB creado exitosamente. "
        f"'{file_path}'."
    )


if __name__ == "__main__":
    # Default values
    file_path = "large_file.txt"
    size_in_kb = 5000

    # Command line arguments
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
    if len(sys.argv) > 2:
        size_in_kb = int(sys.argv[2])

    create_large_text_file(file_path, size_in_kb)
