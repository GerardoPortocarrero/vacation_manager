import polars as pl
from datetime import datetime

# Crear las columnas necesarias
def create_relevant_columns(df, this_year, this_month, today):
    # "DIAS_ACUMULADOS"
    df = df.with_columns([
        (pl.lit(today) - pl.col("Fecha Ingreso")).dt.total_days().alias("DIAS_ACUMULADOS")
    ])

    # "VACACIONES_GOZADAS"
    vaca_cols = [col for col in df.columns if col.startswith("Vacaciones ")]

        # Crear una columna VACACIONES_GOZADAS que cuenta 30 días por cada año de vacaciones cumplido
    vacaciones_gozadas = sum([
        pl.when(
            pl.col(col).is_not_null() &
            (pl.col(col) <= pl.lit(today)) &
            (pl.col(col) >= pl.col("Fecha Ingreso"))
        ).then(30).otherwise(0)
        for col in vaca_cols
    ])

    df = df.with_columns([
        vacaciones_gozadas.alias("VACACIONES_GOZADAS")
    ])

    # "VACACION_GOZADA_ACTUAL" 3 estados (No vacaciono, esta vacacionando, por vacacionar)
        # Construir nombre dinámico de columna

    vaca_col = f"Vacaciones {this_year-1}-{this_year}"

        # Crear columna booleana VACACION_GOZADA_ACTUAL
    df = df.with_columns([
        pl.when(
            pl.col(vaca_col).is_not_null() &
            (pl.col(vaca_col).dt.year() == this_year) &
            (pl.col(vaca_col).dt.month() == this_month)
        ).then(2)
        
        .when(
            pl.col(vaca_col).is_not_null() &
            (pl.col(vaca_col) <= pl.lit(today)) &
            (pl.col(vaca_col).dt.year() == this_year)
        ).then(1)        

        .when(
            pl.col(vaca_col).is_not_null() &
            (pl.col(vaca_col) > pl.lit(today)) &
            (pl.col(vaca_col).dt.year() == this_year)
        ).then(3)

        .otherwise(0)
        .alias("VACACION_GOZADA_ACTUAL")
    ])

    # "VACACIONES_PENDIENTES" Dias de vacaciones acumuladas que tiene pendiente para gozar
        # Crear columna de aniversario
    df = df.with_columns([
        pl.datetime(this_year-1, pl.col("Fecha Ingreso").dt.month(), pl.col("Fecha Ingreso").dt.day())
        .alias("ANIVERSARIO")
    ])

        # Calcular días desde aniversario hasta hoy
    df = df.with_columns([
        ((pl.lit(today) - pl.col("ANIVERSARIO")).dt.total_days() / 365 * 30).alias("VACACIONES_PROPORCIONALES")
    ])

        # Calcular vacaciones pendientes
    df = df.with_columns([
        (
            pl.when(pl.col("VACACION_GOZADA_ACTUAL").is_in([0, 3]))  # no ha gozado
            .then(pl.col("VACACIONES_PROPORCIONALES"))
            .when(pl.col("VACACION_GOZADA_ACTUAL").is_in([1, 2]))  # ya gozó
            .then(pl.col("VACACIONES_PROPORCIONALES")-30)
            .otherwise(0.0)
        ).round(2).alias("VACACIONES_PENDIENTES")
    ])

    # for x in df.select(['NOMBRES', 'VACACIONES_GOZADAS', 'VACACION_GOZADA_ACTUAL', 'VACACIONES_PENDIENTES']).iter_rows():
    #     print(x[0], x[1], x[2], x[3])
    
    return df

# Establecer los tipos de datos correctos en las columnas
def set_data_types(df, initial_year, this_year, date_format):
    # Setear fecha de ingreso
    df = df.with_columns([
        pl.col('Fecha Ingreso').str.strptime(pl.Datetime, format=date_format)
    ])

    # Setear registro historico
    for year in range(initial_year, this_year):
        df = df.with_columns([
            pl.col(f'Vacaciones {year}-{year+1}').str.strptime(pl.Datetime, format=date_format, strict=False)
        ])

    return df
    
# Funcion principal
def main(df):
    # Configuraciones
    initial_year = 2020
    today = datetime.today().date()
    this_year = today.year
    this_month = today.month
    
    date_format = "%Y-%m-%d %H:%M:%S"

    # Setear los tipos de datos
    df = set_data_types(df, initial_year, this_year, date_format)

    # Calcular las columnas faltantes
    df = create_relevant_columns(df, this_year, this_month, today)

    return df