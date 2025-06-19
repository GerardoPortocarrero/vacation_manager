import os
import polars as pl

def generate_vacation_html(df, VACACION_GOZADA_ACTUAL_ESTADOS, dni):
    persona = df.filter(pl.col("DNI") == dni).to_dicts()[0]

    # Formato de colores para alertas
    alerta_vacaciones = ""
    if persona['PROXIMO_A_VACACIONES'] == "< 1 semana":
        alerta_vacaciones = '<p style="background-color: #e74c3c; color: white; padding: 8px;">🚨 A una semana de entrar a vacaciones</p>'
    elif persona['PROXIMO_A_VACACIONES'] == "< 1 mes":
        alerta_vacaciones = '<p style="background-color: #f1c40f; color: #000; padding: 8px;">⚠️ A un mes de entrar a vacaciones</p>'

    alerta_aniversario = ""
    if persona['ALERTA_ANIVERSARIO'] == "< 1 semana":
        alerta_aniversario = '<p style="background-color: #3498db; color: white; padding: 8px;">📌 A una semana de cumplir aniversario</p>'

    html = f"""
    <html>
    <body style="font-family: Arial, sans-serif;">

        <h2>{persona['NOMBRES']} {persona['APELLIDOS']}</h2>
        <p><strong>DNI:</strong> {persona['DNI']}</p>
        <p><strong>Cargo:</strong> {persona['CARGO']}</p>

        <!-- Número grande + info lateral -->
        <table border="0" cellpadding="0" cellspacing="0" width="100%" style="margin-top: 20px;">
          <tr>
            <td width="150" align="center" valign="top" style="font-size: 48px; font-weight: bold; color: #2c3e50;">
              {round(persona['VACACIONES_PENDIENTES'])}
              <div style="font-size: 14px; color: #7f8c8d;">días</div>
            </td>
            <td valign="top" style="padding-left: 20px;">
              <table cellpadding="4" cellspacing="0" border="0" style="font-size: 14px; color: #333;">
                <tr>
                  <td><strong>Gozadas (Actual):</strong></td>
                  <td>{VACACION_GOZADA_ACTUAL_ESTADOS[persona['VACACION_GOZADA_ACTUAL']]}</td>
                </tr>
                <tr>
                  <td><strong>Vacaciones 2024-2025:</strong></td>
                  
                </tr>
              </table>
            </td>
          </tr>
        </table>

        <!-- Historial -->
        <h3 style="margin-top: 30px;">Historial de Vacaciones</h3>
        <table border="1" cellpadding="5" cellspacing="0" style="border-collapse: collapse; font-size: 14px;">
            <tr><th>Temporada</th><th>Mes</th><th>Estado</th></tr>
            <tr><td>2020-2021</td><td>Abril</td><td>Gozadas</td></tr>
            <tr><td>2021-2022</td><td>Mayo</td><td>Gozadas</td></tr>
            <tr><td>2022-2023</td><td>Abril</td><td>Subsidio</td></tr>
            <tr><td>2023-2024</td><td>Mayo</td><td>Gozado</td></tr>
            
        </table>

        <!-- Alertas -->
        <h3 style="margin-top: 30px;">Alertas</h3>
        {alerta_vacaciones}
        {alerta_aniversario}

    </body>
    </html>
    """
    return html


# Función que genera el HTML personalizado
def main(project_address, df, VACACION_GOZADA_ACTUAL_ESTADOS, dni):
    html1 = generate_vacation_html(df, VACACION_GOZADA_ACTUAL_ESTADOS, dni)

    with open(os.path.join(project_address, f'vacation.html'), 'w', encoding='utf-8') as f:
        f.write(html1)