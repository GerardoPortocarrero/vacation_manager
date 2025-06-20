import os
import polars as pl
from datetime import datetime

def generate_vacation_html(df, months, initial_year, this_year, VACACION_GOZADA_ACTUAL_ESTADOS, DNI):
    persona = df.filter(pl.col("DNI") == DNI).to_dicts()[0]
    mes_vacaciones = persona['Vacaciones 2024-2025']

    mes_formateado = ""
    if mes_vacaciones is not None:
        mes_formateado = f"{months[mes_vacaciones.month]} {mes_vacaciones.year}"

    # Alertas
    alertas = []
    if persona["ALERTA_VACACIONES"] == "< 1 semana":
        alertas.append('<div style="background-color: #e74c3c; color: white; padding: 12px; border-radius: 6px; margin-bottom: 10px;">🚨 A una semana de entrar a vacaciones</div>')
    elif persona["ALERTA_VACACIONES"] == "< 1 mes":
        alertas.append('<div style="background-color: #f1c40f; color: #000; padding: 12px; border-radius: 6px; margin-bottom: 10px;">⚠️ A un mes de entrar a vacaciones</div>')

    if persona["ALERTA_ANIVERSARIO"] == "< 1 semana":
        alertas.append('<div style="background-color: #3498db; color: white; padding: 12px; border-radius: 6px; margin-bottom: 10px;">📌 A una semana de cumplir aniversario</div>')

    if not alertas:
        alertas.append('<div style="background-color: #f8f9fa; color: #7f8c8d; padding: 12px; border-radius: 6px; font-style: italic;">ℹ️ No hay alertas importantes por el momento.</div>')

    alertas_html = '<div style="margin-top: 20px;">' + ''.join(alertas) + '</div>'

    # Historial automatizado
    historial_html = ""
    historial_filas = []
    for year in range(initial_year, this_year-1):
        col_fecha = f"Vacaciones {year}-{year+1}"
        if col_fecha in persona:
            fecha = persona[col_fecha]
            if fecha is not None and str(fecha).strip() != "" and "subsidio" not in str(fecha).lower():
                mes = months[fecha.month]
                estado = "Gozado"
                historial_filas.append(f"<tr><td>{year}-{year+1}</td><td>{mes}</td><td>{estado}</td></tr>")
            elif fecha is not None and "subsidio" in str(fecha).lower():
                historial_filas.append(f"<tr><td>{year}-{year+1}</td><td>-</td><td>Subsidio</td></tr>")

    # Agregar el periodo actual si no está en historial
    periodo_actual = f"{this_year-1}-{this_year}"
    estado_actual = VACACION_GOZADA_ACTUAL_ESTADOS[persona['VACACION_GOZADA_ACTUAL']]
    if not any(periodo_actual in fila for fila in historial_filas):
        if mes_formateado:
            historial_filas.append(f"<tr><td>{periodo_actual}</td><td>{mes_formateado.split()[0]}</td><td>{estado_actual}</td></tr>")

    # Formato de fecha de ingreso
    fecha_ingreso = persona.get('Fecha Ingreso', '')
    fecha_ingreso_str = ''
    if fecha_ingreso and hasattr(fecha_ingreso, 'month'):
        dia = fecha_ingreso.day
        mes = months.get(fecha_ingreso.month, '')
        anio = fecha_ingreso.year
        fecha_ingreso_str = f"{dia} de {mes} de {anio}"

    if historial_filas:
        historial_html = f"""
        <table border=\"1\" cellpadding=\"6\" cellspacing=\"0\" style=\"border-collapse: collapse; font-size: 13px; width: 100%;\">
          <tr style=\"background-color: #2c3e50; color: white;\">
            <th>Temporada</th><th>Mes</th><th>Estado</th>
          </tr>
          {''.join(historial_filas)}
        </table>
        """
    else:
        historial_html = """
        <div style=\"background-color: #f8f9fa; color: #7f8c8d; padding: 12px; border-radius: 6px; font-style: italic;\">
        ℹ️ No hay historial disponible por el momento.
        </div>
        """

    # HTML final
    html = f"""
    <html>
    <body style=\"font-family: Arial, sans-serif; background-color: #f4f6f8; padding: 30px;\">

    <table width=\"100%\" cellpadding=\"0\" cellspacing=\"0\" style=\"background-color: #fff; padding: 20px 30px; border-radius: 10px; box-shadow: 0 0 10px rgba(0,0,0,0.05);\">
      <tr>
        <td colspan=\"2\" valign=\"top\" style=\"padding: 0;\">
          <table width=\"100%\" cellpadding=\"0\" cellspacing=\"0\" style=\"font-size: 14px; table-layout: fixed;\">
            <tr>
              <td valign=\"top\" style=\"width: 50%; padding: 20px;\">
                <div style=\"font-size: 20px; font-weight: bold; color: #2c3e50; line-height: 1.2; margin-bottom: 4px;\">{persona['NOMBRE_COMPLETO']}</div>
                <div style=\"font-size: 13px; color: #7f8c8d; margin-bottom: 16px;\">{persona['CARGO']}</div>
                <table cellpadding=\"5\" cellspacing=\"0\" border=\"0\" style=\"font-size: 13px; color: #2c3e50; width: 100%;\">
                  <tr>
                    <td style=\"width: 110px;\"><strong>DNI:</strong></td>
                    <td>{persona['DNI']}</td>
                  </tr>
                  <tr>
                    <td><strong>Fecha ingreso:</strong></td>
                    <td>{fecha_ingreso_str}</td>
                  </tr>
                  <tr>
                    <td><strong>Localidad:</strong></td>
                    <td>Pedregal</td>
                  </tr>
                  <tr>
                    <td><strong>Estado actual:</strong></td>
                    <td>{estado_actual}</td>
                  </tr>
                  <tr>
                    <td><strong>Mes programado:</strong></td>
                    <td>{mes_formateado}</td>
                  </tr>
                </table>
              </td>
              <td valign=\"top\" style=\"width: 50%; padding: 20px; text-align: center;\">
                <div style=\"background-color: #ecf0f1; padding: 24px 16px; border-radius: 10px; display: inline-block; width: 100%;\">
                  <div style=\"font-size: 60px; font-weight: bold; color: #2c3e50; line-height: 1.1;\">{persona['VACACIONES_ACUMULADAS']}<span style=\"font-size: 20px; font-weight: normal; color: #7f8c8d;\"> días</span></div>
                  <div style=\"font-size: 14px; color: #7f8c8d;\">de vacaciones acumuladas</div>
                </div>
              </td>
            </tr>
          </table>

          <div style=\"padding: 20px 30px 10px 30px;\">
            <h3 style=\"margin: 20px 0 10px; color: #34495e;\">🔔 Alertas</h3>
            {alertas_html}
          </div>

          <div style=\"padding: 10px 30px 20px 30px;\">
            <h3 style=\"margin-top: 20px; color: #34495e;\">📅 Historial de Vacaciones</h3>
            {historial_html}
          </div>
        </td>
      </tr>
    </table>

    </body>
    </html>
    """
    return html

# Función que genera el HTML personalizado
def main(project_address, df, months, VACACION_GOZADA_ACTUAL_ESTADOS, DNI):
    initial_year = 2020
    today = datetime.today().date()
    this_year = today.year
    this_month = today.month

    html1 = generate_vacation_html(df, months, initial_year, this_year, VACACION_GOZADA_ACTUAL_ESTADOS, DNI)

    with open(os.path.join(project_address, f'vacation.html'), 'w', encoding='utf-8') as f:
        f.write(html1)
