import os
import webbrowser

def main(project_address, file_name):
    file_address = os.path.join(project_address, file_name)
    # Ruta del archivo HTML
    file_path = os.path.abspath(file_address)
    # Abrir en navegador predeterminado
    webbrowser.open(f"file://{file_path}")