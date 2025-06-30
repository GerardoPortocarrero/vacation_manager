import os
import polars as pl
import re
from datetime import datetime, date

# Reporte del consolidado de trabajadores
def generate_consolidated_report(df: pl.DataFrame, initial_year: int, this_year: int, VACACION_GOZADA_ACTUAL_ESTADOS: dict, months: dict, LOGO_AYA) -> str:
    # Automatizar columnas de vacaciones
    vacation_years = [f"Vacaciones {y}-{y+1}" for y in range(initial_year, this_year - 1)]
    vacation_columns = [col for col in vacation_years if col in df.columns]

    def format_period_and_date(period: str, date_str: str) -> str:
        if not date_str:
            return ""
        try:
            y1, y2 = period.split()[-1].split('-')
            date = str(date_str).split(" ")[0]
            year, month, *_ = date.split("-")
            month_name = months.get(int(month), "")
            return f"{y1}-{y2} {month_name}"
        except:
            return f"{period}: {date_str}"

    def format_fecha_ingreso(date_str: str) -> str:
        try:
            date = str(date_str).split(" ")[0]
            year, month, day = date.split("-")
            month_name = months.get(int(month), "")
            return f"{int(day)} de {month_name} de {year}"
        except:
            return date_str

    df = df.with_columns([
        pl.struct(vacation_columns).map_elements(
            lambda row: "<ul style='margin: 0; padding-left: 16px;'>" +
            "".join([
                f"<li style='margin-bottom: 4px;'>{format_period_and_date(col, row[col])}</li>"
                for col in vacation_columns if row.get(col)
            ]) + "</ul>"
        ).alias("HISTORIAL_VACACIONES"),
        pl.col("Fecha Ingreso").map_elements(format_fecha_ingreso).alias("Fecha Ingreso")
    ])

    estado_col = (
        pl.when(pl.col("VACACION_GOZADA_ACTUAL") == 0).then(pl.lit(VACACION_GOZADA_ACTUAL_ESTADOS[0]))
        .when(pl.col("VACACION_GOZADA_ACTUAL") == 1).then(pl.lit(VACACION_GOZADA_ACTUAL_ESTADOS[1]))
        .when(pl.col("VACACION_GOZADA_ACTUAL") == 2).then(pl.lit(VACACION_GOZADA_ACTUAL_ESTADOS[2]))
        .when(pl.col("VACACION_GOZADA_ACTUAL") == 3).then(pl.lit(VACACION_GOZADA_ACTUAL_ESTADOS[3]))
        .otherwise(pl.lit("Desconocido"))
        .alias("ESTADO_VACACION_ACTUAL")
    )

    df = df.with_columns([estado_col])

    columnas = [
        'NOMBRE_COMPLETO', 'DNI', 'CARGO', 'Fecha Ingreso',
        'HISTORIAL_VACACIONES', 'ESTADO_VACACION_ACTUAL', 'VACACIONES_ACUMULADAS',
        'ALERTA_VACACIONES', 'ALERTA_ANIVERSARIO'
    ]

    header_labels = {
        'NOMBRE_COMPLETO': 'Nombre',
        'DNI': 'DNI',
        'CARGO': 'Cargo',
        'Fecha Ingreso': 'Fecha ingreso',
        'HISTORIAL_VACACIONES': 'Historial',
        'ESTADO_VACACION_ACTUAL': 'Estado',
        'VACACIONES_ACUMULADAS': 'Días acumulados',
        'ALERTA_VACACIONES': 'Proximidad',
        'ALERTA_ANIVERSARIO': 'Aniversario'
    }

    rows = df.select(columnas).rows()

    html = f"""
    <html>
    <div style="text-align: center;">
        <img src="cid:{LOGO_AYA}" alt="Logo" width="160" style="display: block; margin: auto; border: 0; outline: none; text-decoration: none;">
    </div>
    <body style=\"font-family: Arial, sans-serif; background-color: #f4f6f8; padding: 30px;\">
      <div style=\"margin: auto; background-color: #fff; border-radius: 10px; box-shadow: 0 0 10px rgba(0,0,0,0.05); overflow-x: auto;\">        
        <table width=\"100%\" cellpadding=\"0\" cellspacing=\"0\" style=\"font-size: 14px; border-collapse: collapse; border: 1px solid #ccc;\">
          <tr>
    """

    for col in columnas:
        html += f"<th style=\"background-color: #2c3e50; color: white; padding: 10px; border: 1px solid #ccc;\">{header_labels.get(col, col)}</th>"
    html += "</tr>"

    for row in rows:
        alerta_vac = row[columnas.index("ALERTA_VACACIONES")]
        alerta_aniv = row[columnas.index("ALERTA_ANIVERSARIO")]

        bg_color = ""
        texto_alerta_vac = alerta_vac
        texto_alerta_aniv = alerta_aniv

        if alerta_vac == "< 1 semana":
            bg_color = "#fdecea"
            texto_alerta_vac = "<span style='color: #c0392b;'>🚨 Vacaciones en menos de una semana</span>"
        elif alerta_vac == "< 1 mes":
            bg_color = "#fff6e5"
            texto_alerta_vac = "<span style='color: #d35400;'>⏰ Vacaciones en menos de un mes</span>"

        if alerta_aniv == "< 1 semana":
            texto_alerta_aniv = "<span style='color: #2980b9;'>🎉 Aniversario en menos de una semana</span>"

        html += f"<tr style='background-color:{bg_color};'>"
        for i, cell in enumerate(row):
            value = "" if cell is None else str(cell)
            if columnas[i] == "ALERTA_VACACIONES":
                value = texto_alerta_vac
            elif columnas[i] == "ALERTA_ANIVERSARIO":
                value = texto_alerta_aniv
            html += f"<td style=\"widht: 90%; border: 1px solid #ccc; padding: 10px; font-size: 13px; vertical-align: top;\">{value}</td>"
        html += "</tr>"

    html += """
        </table>
      </div>
    </body>
    </html>
    """

    return html

# Reporte personal (se muestra informacion por DNI)
def generate_personal_report(df, months, initial_year, this_year, VACACION_GOZADA_ACTUAL_ESTADOS, DNI, LOGO_AYA):
    persona = df.filter(pl.col("DNI") == DNI).to_dicts()[0]
    mes_vacaciones = persona[f'Vacaciones {this_year-1}-{this_year}']

    mes_formateado = ""
    if mes_vacaciones is not None:
        mes_formateado = f"{months[mes_vacaciones.month]} {mes_vacaciones.year}"

    # Alertas
    alertas = []
    if persona["ALERTA_VACACIONES"] == "< 1 semana":
        alertas.append('<div style="background-color: #fdecea; color: #000; padding: 12px; border-radius: 6px; margin-bottom: 10px;">🚨  A una semana de entrar a vacaciones</div>')
    elif persona["ALERTA_VACACIONES"] == "< 1 mes":
        alertas.append('<div style="background-color: #fff6e5; color: #000; padding: 12px; border-radius: 6px; margin-bottom: 10px;">⚠️  A un mes de entrar a vacaciones</div>')

    if persona["ALERTA_ANIVERSARIO"] == "< 1 semana":
        alertas.append('<div style="background-color: #3498db; color: white; padding: 12px; border-radius: 6px; margin-bottom: 10px;">📌  A una semana de cumplir aniversario</div>')

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
        <div style="text-align: center; margin-top: 10px;">
            <img src="cid:{LOGO_AYA}" alt="Logo" width="160" style="display: block; margin: auto; border: 0; outline: none; text-decoration: none;">
        </div>
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
                    <div style=\"background-color: #ecf0f1; padding: 24px 8px; border-radius: 10px; display: inline-block; width: 100%;\">
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
def generate_vacation_alert(df: pl.DataFrame, this_year: int, LOGO_AYA) -> str:
    colores = {
        '< 1 semana': '#e74c3c',
        '< 1 mes': '#f1c40f',
    }

    html = f"""
    <html>
    <div style="text-align: center;">
        <img src="cid:{LOGO_AYA}" alt="Logo" width="160" style="display: block; margin: auto; border: 0; outline: none; text-decoration: none;">
    </div>
    <body style="font-family: Arial, sans-serif; background-color: #f4f6f8; padding: 30px;">

    <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #fff; padding: 30px; border-radius: 10px; box-shadow: 0 0 10px rgba(0,0,0,0.05);">
        <tr>
            <td colspan="2" valign="top" style="padding: 0;">
                <table width="100%" cellpadding="0" cellspacing="0" style="font-size: 14px; table-layout: fixed; border-collapse: collapse;">
                    <tr>
                        <td style="text-align: center; border: none; padding: 0;">
                            <div style="font-size: 28px; font-weight: bold; color: #2c3e50;">Alerta de Vacaciones</div>
                            <div style="font-size: 15px; color: #7f8c8d; margin-top: 6px;">Este informe muestra el personal con vacaciones próximas según su programación.</div>
                        </td>
                    </tr>
                </table>

                <div style="padding: 20px 30px 10px 30px;">
    """

    for rango in ['< 1 semana', '< 1 mes']:
        df_rango = df.filter(pl.col("ALERTA_VACACIONES") == rango)
        if df_rango.is_empty():
            continue

        columnas = ['NOMBRE_COMPLETO', 'CARGO', 'VACACIONES_ACUMULADAS', f'Vacaciones {this_year-1}-{this_year}']
        rows = df_rango.select(columnas).rows()

        tabla_html = "<table border=\"1\" cellpadding=\"6\" cellspacing=\"0\" style=\"border-collapse: collapse; font-size: 13px; width: 100%; margin-bottom: 30px;\">"
        tabla_html += "<tr style=\"background-color: #2c3e50; color: white;\">" + "".join(f"<th>{col}</th>" for col in columnas) + "</tr>"
        for row in rows:
            tabla_html += "<tr>" + "".join(f"<td>{cell}</td>" for cell in row) + "</tr>"
        tabla_html += "</table>"

        mensaje = {
            '< 1 semana': '🚨 Vacaciones en menos de una semana',
            '< 1 mes': '⏰ Vacaciones en menos de un mes'
        }[rango]

        html += f"""
            <h3 style="background-color:{colores[rango]}; color: white; padding: 12px; border-radius: 6px; font-size: 16px; text-align: center; margin: 30px 0 10px;">{mensaje}</h3>
            {tabla_html}
        """

    html += f"""
                </div>
            </td>
        </tr>
    </table>

    </body>
    </html>
    """

    return html

# Reporte de alertas para las personas proximas a cumplir aniversario
def generate_anniversary_alert(df: pl.DataFrame, LOGO_AYA) -> str:
    color = '#3498db'

    html = f"""
    <html>
    <div style="text-align: center;">
        <img src="cid:{LOGO_AYA}" alt="Logo" width="160" style="display: block; margin: auto; border: 0; outline: none; text-decoration: none;">
    </div>
    <body style="font-family: Arial, sans-serif; background-color: #f4f6f8; padding: 30px;">

    <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #fff; padding: 30px; border-radius: 10px; box-shadow: 0 0 10px rgba(0,0,0,0.05);">
        <tr>
            <td colspan="2" valign="top" style="padding: 0;">
                <table width="100%" cellpadding="0" cellspacing="0" style="font-size: 14px; table-layout: fixed; border-collapse: collapse;">
                    <tr>
                        <td style="text-align: center; border: none; padding: 0;">
                            <div style="font-size: 28px; font-weight: bold; color: #2c3e50;">Alerta de Aniversarios</div>
                            <div style="font-size: 15px; color: #7f8c8d; margin-top: 6px;">Trabajadores próximos a cumplir un nuevo año en la empresa.</div>
                        </td>
                    </tr>
                </table>

                <div style="padding: 20px 30px 10px 30px;">
    """

    df_rango = df.filter(pl.col("ALERTA_ANIVERSARIO") == "< 1 semana")
    if not df_rango.is_empty():
        columnas = ['NOMBRE_COMPLETO', 'CARGO', 'Fecha Ingreso']
        rows = df_rango.select(columnas).rows()

        html += f"""
            <h3 style="background-color:{color}; color: white; padding: 12px; border-radius: 6px; font-size: 16px; text-align: center; margin: 20px 0 15px 0;">
                🎊 Aniversario en menos de una semana
            </h3>
            <table border="1" cellpadding="6" cellspacing="0" style="border-collapse: collapse; font-size: 13px; width: 100%; margin-bottom: 30px;">
                <tr style="background-color: #2c3e50; color: white;">
                    {''.join(f"<th>{col}</th>" for col in columnas)}
                </tr>
        """
        for row in rows:
            html += "<tr>" + "".join(f"<td>{cell}</td>" for cell in row) + "</tr>"
        html += "</table>"
    else:
        html += """
            <div style="background-color:#ecf0f1; color:#7f8c8d; padding:12px; border-radius:6px; text-align:center; font-style: italic; margin-top: 10px;">
                No hay trabajadores próximos a cumplir aniversario esta semana.
            </div>
        """

    html += """
                </div>
            </td>
        </tr>
    </table>

    </body>
    </html>
    """

    return html

# Reporte de alertas para las personas estan a 2 meses de cumplir 2 años sin vacaciones
def generate_two_year_alert(df: pl.DataFrame, LOGO_AYA: str) -> str:
    df_alerta = df.filter(pl.col("VACACIONES_ACUMULADAS") > 55)

    if df_alerta.is_empty():
        # HTML vacío pero con estilo amigable y logo
        return f"""
        <html>
        <div style="text-align: center;">
            <img src="cid:{LOGO_AYA}" alt="Logo" width="160" style="display: block; margin: auto;">
        </div>
        <body style="font-family: Arial, sans-serif; background-color: #f4f6f8; padding: 30px;">
            <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #fff; padding: 30px; border-radius: 10px; box-shadow: 0 0 10px rgba(0,0,0,0.05);">
                <tr>
                    <td style="text-align: center;">
                        <div style="font-size: 26px; font-weight: bold; color: #2c3e50;">
                            Trabajadores a 2 meses de cumplir 2 años sin vacaciones
                        </div>
                        <div style="font-size: 14px; color: #7f8c8d; margin-top: 6px;">
                            Este informe muestra el historial de personas con más de 55 días acumulados.
                        </div>
                        <div style="margin-top: 30px; font-size: 15px; color: #16a085; font-weight: bold;">
                            No se encontraron trabajadores en esta condición.
                        </div>
                    </td>
                </tr>
            </table>
        </body>
        </html>
        """

    history_cols = [col for col in df.columns if col.endswith("_original")]
    columnas_fijas = ["NOMBRE_COMPLETO", "CARGO", "Fecha Ingreso", "VACACIONES_ACUMULADAS"]

    cabeceras = columnas_fijas + [
        col.replace("_original", "").replace("Vacaciones ", "") for col in history_cols
    ]

    # Construcción de tabla HTML
    tabla_html = "<table border='1' cellpadding='6' cellspacing='0' style='border-collapse: collapse; font-size: 13px; width: 100%;'>"
    tabla_html += "<tr style='background-color: #d35400; color: white;'>" + "".join(f"<th>{col}</th>" for col in cabeceras) + "</tr>"

    for row in df_alerta.iter_rows(named=True):
        ingreso_year = row["Fecha Ingreso"].year
        celdas = [
            row["NOMBRE_COMPLETO"],
            row["CARGO"],
            row["Fecha Ingreso"].strftime("%d-%m-%Y") if isinstance(row["Fecha Ingreso"], (datetime, date)) else "",
            round(row["VACACIONES_ACUMULADAS"], 2)
        ]

        for col in history_cols:
            # Extraer el año inicial del periodo de vacaciones
            match = re.search(r"(\d{4})-\d{4}", col)
            if match:
                start_year = int(match.group(1))
                # Solo mostrar si el año de vacaciones es igual o posterior al año de ingreso
                if start_year < ingreso_year:
                    celdas.append("Ausente")
                    continue

            valor = row.get(col)

            if valor is None or valor == "":
                celdas.append("Ausente")
            elif isinstance(valor, str) and "subsidio" in valor.lower():
                celdas.append("Subsidio")
            elif isinstance(valor, (datetime, date)):
                celdas.append(valor.strftime("%d-%m-%Y"))
            else:
                celdas.append(str(valor))  # Por si acaso hay algo inesperado

        tabla_html += "<tr>" + "".join(f"<td>{c}</td>" for c in celdas) + "</tr>"

    tabla_html += "</table>"

    html = f"""
    <html>
    <div style="text-align: center;">
        <img src="cid:{LOGO_AYA}" alt="Logo" width="160" style="display: block; margin: auto;">
    </div>
    <body style="font-family: Arial, sans-serif; background-color: #f4f6f8; padding: 30px;">
        <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #fff; padding: 30px; border-radius: 10px; box-shadow: 0 0 10px rgba(0,0,0,0.05);">
            <tr>
                <td style="text-align: center;">
                    <div style="font-size: 26px; font-weight: bold; color: #2c3e50;">
                        Trabajadores a 2 meses de cumplir 2 años sin vacaciones
                    </div>
                    <div style="font-size: 14px; color: #7f8c8d; margin-top: 6px;">
                        Este informe muestra el historial de personas con más de 55 días acumulados.
                    </div>
                </td>
            </tr>
            <tr>
                <td style="padding-top: 30px;">
                    {tabla_html}
                </td>
            </tr>
        </table>
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
        TWO_YEARS_WITHOUT_GOZO,
        LOGO_AYA,
        group_option
    ):
    initial_year = 2020
    today = datetime.today().date()
    this_year = today.year

    if group_option == 1:
        conglomerado_report = generate_consolidated_report(
            df, 
            initial_year, 
            this_year, 
            VACACION_GOZADA_ACTUAL_ESTADOS, 
            months,
            os.path.join(project_address, LOGO_AYA)
        )
        with open(os.path.join(project_address, CONSOLIDADO), 'w', encoding='utf-8') as f:
            f.write(conglomerado_report)

    elif group_option == 2:
        DNI = int(input("\n>> Ingresa DNI de personal: "))
        personal_report = generate_personal_report(
            df, 
            months, 
            initial_year, 
            this_year, 
            VACACION_GOZADA_ACTUAL_ESTADOS, 
            DNI, 
            os.path.join(project_address, LOGO_AYA)
        )
        with open(os.path.join(project_address, PERSONAL), 'w', encoding='utf-8') as f:
            f.write(personal_report)

    elif group_option == 3:
        vacacion_alert = generate_vacation_alert(
            df, 
            this_year, 
            os.path.join(project_address, LOGO_AYA)
        )
        with open(os.path.join(project_address, VACACION), 'w', encoding='utf-8') as f:
            f.write(vacacion_alert)

    elif group_option == 4:
        anniversary_alert = generate_anniversary_alert(
            df, 
            os.path.join(project_address, LOGO_AYA)
        )
        with open(os.path.join(project_address, ANIVERSARIO), 'w', encoding='utf-8') as f:
            f.write(anniversary_alert)

    elif group_option == 5:
        two_year_alert = generate_two_year_alert(
            df, 
            os.path.join(project_address, LOGO_AYA)
        )
        with open(os.path.join(project_address, TWO_YEARS_WITHOUT_GOZO), 'w', encoding='utf-8') as f:
            f.write(two_year_alert)
