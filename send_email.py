import os
import win32com.client
from bs4 import BeautifulSoup

# Embeber imagenes para que se visualice por correo con "cid"
def embedir_imagenes_en_html(soup, mail, ruta_base_imagenes):
    """
    Inserta imágenes embebidas en el HTML de un correo de Outlook (usando cid),
    reemplazando espacios por guiones bajos en los nombres de archivo.

    Args:
        soup (BeautifulSoup): Contenido HTML del correo como objeto BeautifulSoup.
        mail: Objeto mail de Outlook (MailItem).
        ruta_base_imagenes (str): Ruta donde están almacenadas las imágenes referenciadas con cid.
    """
    img_tags = soup.find_all("img", src=True)
    
    for img_tag in img_tags:
        src = img_tag["src"]
        if src.startswith("cid:"):
            raw_cid = src[4:]
            full_path = os.path.join(ruta_base_imagenes, raw_cid)

            if not os.path.isfile(full_path):
                print(f"[!] Imagen no encontrada: {full_path}")
                continue

            # Agrega la imagen como attachment embebido
            attachment = mail.Attachments.Add(full_path)
            attachment.PropertyAccessor.SetProperty(
                "http://schemas.microsoft.com/mapi/proptag/0x3712001F", raw_cid
            )

# Enviar correo atravéz de outlook
def main(project_address, MAIL_TO, MAIL_CC, html_name, subject):
    # Crear instancia de Outlook
    outlook = win32com.client.Dispatch("Outlook.Application")
    mail = outlook.CreateItem(0) # 0 = MailItem

    # Leer el archivo HTML
    with open(os.path.join(project_address, f'{html_name}'), "r", encoding="utf-8") as f:
        html_body = f.read()

    # Embebe todas las imágenes antes de guardar o enviar
    soup = BeautifulSoup(html_body, "html.parser")
    embedir_imagenes_en_html(soup, mail, ruta_base_imagenes=project_address)

    # Guardar o usar el HTML final
    html_body = str(html_body)

    # Asunto
    mail.Subject = subject
    
    # Destinatarios principales
    mail.To = MAIL_TO

    # Con copia (CC)
    mail.CC = MAIL_CC

    # Cuerpo en HTML
    mail.HTMLBody = html_body

    # (Opcional) Agregar archivo adjunto
    # mail.Attachments.Add("C:\\ruta\\al\\archivo.pdf")

    # Enviar el correo
    mail.Send()

    # Mensaje Exitoso
    print("\n" + "="*60)
    print("📄 Reporte generado")
    print("-" * 60)
    print(f"📝 Reporte : {html_name}")
    print(f"✉️ Correo  : {subject}")
    print("✅ Enviado exitosamente.")
    print("="*60 + "\n")