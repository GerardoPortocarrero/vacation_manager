import os
import polars as pl
from datetime import datetime

# Reporte personal (se muestra informacion por DNI)
def generate_personal_report(df, months, initial_year, this_year, VACACION_GOZADA_ACTUAL_ESTADOS, DNI):
    persona = df.filter(pl.col("DNI") == DNI).to_dicts()[0]
    mes_vacaciones = persona[f'Vacaciones {this_year-1}-{this_year}']

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

# Reporte de alertas para las personas proximas a entrar en vacaciones
def generate_vacation_alert(df: pl.DataFrame, this_year: int) -> str:
    colores = {
        '< 1 semana': '#e74c3c',
        '< 1 mes': '#f1c40f',
    }

    html = f"""
    <html>
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {{
                font-family: Arial, sans-serif;
                background-color: #f4f6f8;
                margin: 0;
                padding: 0;
            }}
            .container {{
                max-width: 900px;
                margin: auto;
                padding: 20px 30px;
                background-color: #ffffff;
                border-radius: 12px;
                box-shadow: 0 0 15px rgba(0,0,0,0.08);
            }}
            h1 {{
                text-align: center;
                font-size: 30px;
                color: #2c3e50;
                margin-bottom: 5px;
            }}
            .description {{
                text-align: center;
                font-size: 16px;
                color: #7f8c8d;
                margin-bottom: 30px;
            }}
            .section {{
                margin-top: 30px;
                padding-top: 20px;
                border-top: 2px solid #ecf0f1;
            }}
            .section-title {{
                text-align: center;
                font-size: 22px;
                color: #34495e;
                position: relative;
                margin-bottom: 25px;
            }}
            .section-title::after {{
                content: "";
                display: block;
                width: 60px;
                height: 3px;
                background-color: #3498db;
                margin: 8px auto 0 auto;
                border-radius: 2px;
            }}
            h3 {{
                margin: 20px 0 5px 0;
                padding: 10px;
                color: white;
                border-radius: 5px;
                font-size: 15px;
                text-align: center;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin-bottom: 25px;
            }}
            th, td {{
                border: 1px solid #ccc;
                padding: 6px;
                text-align: center;
                font-size: 13px;
            }}
            th {{
                background-color: #2c3e50;
                color: white;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📊 Alerta de Vacaciones</h1>
            <p class="description">Personal con vacaciones programadas próximamente.</p>
            <div class="section">
    """

    for rango in ['< 1 semana', '< 1 mes']:
        df_rango = df.filter(pl.col("ALERTA_VACACIONES") == rango)
        if df_rango.is_empty():
            continue

        columnas = ['NOMBRE_COMPLETO', 'CARGO', 'VACACIONES_ACUMULADAS', f'Vacaciones {this_year-1}-{this_year}']
        rows = df_rango.select(columnas).rows()

        # Generar tabla HTML manualmente
        tabla_html = "<table><tr>" + "".join(f"<th>{col}</th>" for col in columnas) + "</tr>"
        for row in rows:
            tabla_html += "<tr>" + "".join(f"<td>{cell}</td>" for cell in row) + "</tr>"
        tabla_html += "</table>"

        html += f"""
                <h3 style="background-color:{colores[rango]};">{rango.upper()}</h3>
                {tabla_html}
        """

    html += """
            </div>
        </div>
    </body>
    </html>
    """

    return html

# Reporte de alertas para las personas proximas a cumplir aniversario
def generate_anniversary_alert(df: pl.DataFrame) -> str:
    color = '#3498db'

    html = f"""
    <html>
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {{
                font-family: Arial, sans-serif;
                background-color: #f4f6f8;
                margin: 0;
                padding: 0;
            }}
            .container {{
                max-width: 900px;
                margin: auto;
                padding: 20px 30px;
                background-color: #ffffff;
                border-radius: 12px;
                box-shadow: 0 0 15px rgba(0,0,0,0.08);
            }}
            h1 {{
                text-align: center;
                font-size: 30px;
                color: #2c3e50;
                margin-bottom: 5px;
            }}
            .description {{
                text-align: center;
                font-size: 16px;
                color: #7f8c8d;
                margin-bottom: 30px;
            }}
            .section {{
                margin-top: 30px;
                padding-top: 20px;
                border-top: 2px solid #ecf0f1;
            }}
            .section-title {{
                text-align: center;
                font-size: 22px;
                color: #34495e;
                position: relative;
                margin-bottom: 25px;
            }}
            .section-title::after {{
                content: "";
                display: block;
                width: 60px;
                height: 3px;
                background-color: #3498db;
                margin: 8px auto 0 auto;
                border-radius: 2px;
            }}
            h3 {{
                margin: 20px 0 5px 0;
                padding: 10px;
                color: white;
                border-radius: 5px;
                font-size: 15px;
                text-align: center;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin-bottom: 25px;
            }}
            th, td {{
                border: 1px solid #ccc;
                padding: 6px;
                text-align: center;
                font-size: 13px;
            }}
            th {{
                background-color: #2c3e50;
                color: white;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📌 Alerta de Aniversarios</h1>
            <p class="description">Personal a punto de cumplir un nuevo año en la empresa.</p>
            <div class="section">
    """

    df_rango = df.filter(pl.col("ALERTA_ANIVERSARIO") == "< 1 semana")
    if not df_rango.is_empty():
        columnas = ['NOMBRE_COMPLETO', 'CARGO', 'Fecha Ingreso']
        rows = df_rango.select(columnas).rows()

        tabla_html = "<table><tr>" + "".join(f"<th>{col}</th>" for col in columnas) + "</tr>"
        for row in rows:
            tabla_html += "<tr>" + "".join(f"<td>{cell}</td>" for cell in row) + "</tr>"
        tabla_html += "</table>"

        html += f"""
                <h3 style="background-color:{color};">A UNA SEMANA</h3>
                {tabla_html}
        """
    else:
        html += """
            <div style="background-color:#ecf0f1; color:#7f8c8d; padding:12px; border-radius:6px; text-align:center;">
                No hay trabajadores próximos a cumplir aniversario esta semana.
            </div>
        """

    html += """
            </div>
        </div>
    </body>
    </html>
    """
    return html

# Reporte del consolidado de trabajadores
def generate_consolidated_report(df: pl.DataFrame, initial_year: int, this_year: int, VACACION_GOZADA_ACTUAL_ESTADOS: dict) -> str:
    columnas = [
        'NOMBRE_COMPLETO', 'DNI', 'CARGO', 'Fecha Ingreso',
        'Vacaciones 2020-2021', 'Vacaciones 2021-2022', 'Vacaciones 2022-2023',
        'Vacaciones 2023-2024', 'Vacaciones 2024-2025',
        'VACACION_GOZADA_ACTUAL', 'VACACIONES_ACUMULADAS',
        'ALERTA_VACACIONES', 'ALERTA_ANIVERSARIO'
    ]

    # Preprocesar el DataFrame
    vacation_years = [f"Vacaciones {y}-{y+1}" for y in range(initial_year, this_year)]
    vacation_columns = [pl.col(col).cast(pl.Utf8).fill_null("") for col in vacation_years]

    df = df.with_columns([
        pl.when(pl.col("VACACION_GOZADA_ACTUAL") == 0).then(VACACION_GOZADA_ACTUAL_ESTADOS[0])
        .when(pl.col("VACACION_GOZADA_ACTUAL") == 1).then(VACACION_GOZADA_ACTUAL_ESTADOS[1])
        .when(pl.col("VACACION_GOZADA_ACTUAL") == 2).then(VACACION_GOZADA_ACTUAL_ESTADOS[2])
        .when(pl.col("VACACION_GOZADA_ACTUAL") == 3).then(VACACION_GOZADA_ACTUAL_ESTADOS[3])
        .otherwise("Desconocido")
        .alias("ESTADO_VACACION_ACTUAL"),
        *vacation_columns
    ])

    rows = df.select(columnas).rows()

    # Armar HTML
    html = f"""
    <html>
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {{
                font-family: Arial, sans-serif;
                background-color: #f4f6f8;
                margin: 0;
                padding: 0;
            }}
            .container {{
                max-width: 95%;
                margin: auto;
                padding: 20px 30px;
                background-color: #ffffff;
                border-radius: 12px;
                box-shadow: 0 0 15px rgba(0,0,0,0.08);
                overflow-x: auto;
            }}
            h1 {{
                text-align: center;
                font-size: 28px;
                color: #2c3e50;
                margin-bottom: 20px;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin-bottom: 25px;
                table-layout: auto;
            }}
            th, td {{
                border: 1px solid #ccc;
                padding: 6px;
                text-align: center;
                font-size: 13px;
                vertical-align: middle;
            }}
            th {{
                background-color: #2c3e50;
                color: white;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📋 Consolidado de Vacaciones</h1>
            <table>
                <tr>
    """

    # Encabezados
    for col in columnas:
        html += f"<th>{col}</th>"
    html += "</tr>"

    # Filas
    for row in rows:
        html += "<tr>"
        for cell in row:
            value = "" if cell is None else str(cell)
            html += f"<td>{value}</td>"
        html += "</tr>"

    html += """
            </table>
        </div>
    </body>
    </html>
    """

    return html

# Función que genera el HTML personalizado
def main(
        project_address, 
        df, 
        months,
        VACACION_GOZADA_ACTUAL_ESTADOS,
        CONSOLIDADO,
        PERSONAL, 
        VACACION, 
        ANIVERSARIO,
        group_option
    ):
    initial_year = 2020
    today = datetime.today().date()
    this_year = today.year

    if group_option == 1:
        conglomerado_report = generate_consolidated_report(df, initial_year, this_year, VACACION_GOZADA_ACTUAL_ESTADOS)
        with open(os.path.join(project_address, CONSOLIDADO), 'w', encoding='utf-8') as f:
            f.write(conglomerado_report)

    elif group_option == 2:
        DNI = int(input("\n>> Ingresa DNI de personal: "))
        personal_report = generate_personal_report(df, months, initial_year, this_year, VACACION_GOZADA_ACTUAL_ESTADOS, DNI)
        with open(os.path.join(project_address, PERSONAL), 'w', encoding='utf-8') as f:
            f.write(personal_report)

    elif group_option == 3:
        vacacion_alert = generate_vacation_alert(df, this_year)
        with open(os.path.join(project_address, VACACION), 'w', encoding='utf-8') as f:
            f.write(vacacion_alert)

    elif group_option == 4:
        anniversary_alert = generate_anniversary_alert(df)
        with open(os.path.join(project_address, ANIVERSARIO), 'w', encoding='utf-8') as f:
            f.write(anniversary_alert)
