import os
import webbrowser

def main(file_name):
    # Ruta del archivo HTML
    file_path = os.path.abspath(file_name)
    # Abrir en navegador predeterminado
    webbrowser.open(f"file://{file_path}")