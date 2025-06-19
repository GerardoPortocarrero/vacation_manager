import os
import polars as pl

def generate_vacation_html(df, VACACION_GOZADA_ACTUAL_ESTADOS, dni):
    persona = df.filter(pl.col("DNI") == dni).to_dicts()[0]

    # Alertas
    alerta_vacaciones = ""
    if persona["ALERTA_VACACIONES"] == "< 1 semana":
        alerta_vacaciones = '<div style="background-color: #e74c3c; color: white; padding: 10px; margin-bottom: 10px;">🚨 A una semana de entrar a vacaciones</div>'
    elif persona["ALERTA_VACACIONES"] == "< 1 mes":
        alerta_vacaciones = '<div style="background-color: #f1c40f; color: #000; padding: 10px; margin-bottom: 10px;">⚠️ A un mes de entrar a vacaciones</div>'

    alerta_aniversario = ""
    if persona["ALERTA_ANIVERSARIO"] == "< 1 semana":
        alerta_aniversario = '<div style="background-color: #3498db; color: white; padding: 10px;">📌 A una semana de cumplir aniversario</div>'

    # HTML final
    html = f"""
    <html>
    <body style="font-family: Arial, sans-serif; background-color: #f4f6f8; padding: 30px;">

    <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #fff; padding: 20px 30px; border-radius: 10px; box-shadow: 0 0 10px rgba(0,0,0,0.05);">
      <tr>
        <!-- Columna Izquierda -->
        <td width="40%" valign="top" style="border-right: 1px solid #ddd; padding: 10px 20px;">
            <table width="100%" cellpadding="0" cellspacing="0" style="font-size: 14px;">
                <tr>
                    <!-- IZQUIERDA: Datos personales -->
                    <td valign="top" style="width: 60%; padding-right: 10px;">
                        <!-- Nombre y cargo -->
                        <div style="margin-bottom: 12px;">
                            <h2 style="margin: 0; font-size: 18px; font-weight: bold; color: #2c3e50; line-height: 1.3;">{persona['NOMBRE_COMPLETO']}</h2>
                            <div style="font-size: 13px; color: #7f8c8d;">{persona['CARGO']}</div>
                        </div>

                        <!-- Tabla de info -->
                        <table cellpadding="4" cellspacing="0" border="0" style="font-size: 13px; color: #333; width: 100%;">
                            <tr>
                                <td style="padding: 2px 0; width: 110px;"><strong>DNI:</strong></td>
                                <td style="padding: 2px 0;">{persona['DNI']}</td>
                            </tr>
                            <tr>
                                <td style="padding: 2px 0;"><strong>Estado actual:</strong></td>
                                <td style="padding: 2px 0;">{VACACION_GOZADA_ACTUAL_ESTADOS[persona['VACACION_GOZADA_ACTUAL']]}</td>
                            </tr>
                            <tr>
                                <td style="padding: 2px 0;"><strong>Mes vacaciones:</strong></td>
                                <td style="padding: 2px 0;">{persona['Vacaciones 2024-2025']}</td>
                            </tr>
                        </table>
                    </td>

                    <!-- DERECHA: Vacaciones acumuladas (sin tocar) -->
                    <td valign="middle" align="center" style="width: 40%;">
                        <div style="background-color: #ecf0f1; padding: 12px 8px; border-radius: 8px;">
                            <div style="font-size: 36px; font-weight: bold; color: #2c3e50; line-height: 1;">{round(persona['VACACIONES_ACUMULADAS'])}</div>
                            <div style="font-size: 13px; color: #7f8c8d; margin-top: 4px;">vacaciones acumuladas</div>
                        </div>
                    </td>
                </tr>
            </table>
        </td>

        <!-- Columna Derecha -->
        <td width="60%" valign="top" style="padding-left: 20px;">
            <h3 style="margin-top: 0; color: #34495e;">📅 Historial de Vacaciones</h3>
            <table border="1" cellpadding="6" cellspacing="0" style="border-collapse: collapse; font-size: 13px; width: 100%;">
                <tr style="background-color: #2c3e50; color: white;">
                    <th>Temporada</th><th>Mes</th><th>Estado</th>
                </tr>
                <tr><td>2020-2021</td><td>Abril</td><td>Gozadas</td></tr>
                <tr><td>2021-2022</td><td>Mayo</td><td>Gozadas</td></tr>
                <tr><td>2022-2023</td><td>Abril</td><td>Subsidio</td></tr>
                <tr><td>2023-2024</td><td>Mayo</td><td>Gozado</td></tr>
            </table>

            <h3 style="margin-top: 30px; color: #34495e;">🔔 Alertas</h3>
            {alerta_vacaciones}
            {alerta_aniversario}
        </td>
      </tr>
    </table>

    </body>
    </html>
    """
    return html



# Función que genera el HTML personalizado
def main(project_address, df, VACACION_GOZADA_ACTUAL_ESTADOS, dni):
    html1 = generate_vacation_html(df, VACACION_GOZADA_ACTUAL_ESTADOS, dni)

    with open(os.path.join(project_address, f'vacation.html'), 'w', encoding='utf-8') as f:
        f.write(html1)