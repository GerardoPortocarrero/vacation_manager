import polars as pl
from datetime import datetime

# Crear columna que me indique a cuanto tiempo esta de tener vacaciones
def create_alert_1(df, this_year, today):
    vacaciones_col = f"Vacaciones {this_year-1}-{this_year}"

    # Calcular días restantes para vacaciones
    df = df.with_columns([
        (pl.col(vacaciones_col) - pl.lit(today)).dt.total_days().alias("DIAS_PARA_VACACIONES")
    ])

    # Clasificar condición según VACACION_GOZADA_ACTUAL
    df = df.with_columns([
        (
            pl.when((pl.col("DIAS_PARA_VACACIONES") >= 0) & (pl.col("DIAS_PARA_VACACIONES") <= 7))
            .then(pl.lit("< 1 semana"))
            .when((pl.col("DIAS_PARA_VACACIONES") > 7) & (pl.col("DIAS_PARA_VACACIONES") <= 30))
            .then(pl.lit("< 1 mes"))
            .when((pl.col("DIAS_PARA_VACACIONES") > 30))
            .then(pl.lit("> 1 mes"))
            .otherwise(pl.lit("No aplica"))
        ).alias("ALERTA_VACACIONES")
    ])

    return df

# Crear columna que me indique a cuanto tiempo esta de cumplir aniversario
def create_alert_2(df, today):
    # Paso 1: Calcular el aniversario de este año
    df = df.with_columns([
        pl.datetime(
            year=pl.lit(today.year),
            month=pl.col("Fecha Ingreso").dt.month(),
            day=pl.col("Fecha Ingreso").dt.day()
        ).alias("ANIVERSARIO_TEMP")
    ])

    # Paso 2: Ajustar si el aniversario ya pasó (asignar año siguiente)
    df = df.with_columns([
        pl.when(pl.col("ANIVERSARIO_TEMP") < pl.lit(today))
        .then(
            pl.datetime(
                year=pl.lit(today.year + 1),
                month=pl.col("Fecha Ingreso").dt.month(),
                day=pl.col("Fecha Ingreso").dt.day()
            )
        )
        .otherwise(pl.col("ANIVERSARIO_TEMP"))
        .alias("PROXIMO_ANIVERSARIO")
    ])

    # Paso 3: Calcular los días que faltan
    df = df.with_columns([
        (pl.col("PROXIMO_ANIVERSARIO") - pl.lit(today)).dt.total_days().alias("DIAS_PARA_ANIVERSARIO")
    ])

    # Paso 4: Crear la alerta
    df = df.with_columns([
        pl.when((pl.col("DIAS_PARA_ANIVERSARIO") > 0) & (pl.col("DIAS_PARA_ANIVERSARIO") <= 7))
        .then(pl.lit("< 1 semana"))
        .otherwise(pl.lit("> 1 semana"))
        .alias("ALERTA_ANIVERSARIO")
    ])

    return df

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

    # "VACACIONES_ACUMULADAS" Dias de vacaciones acumuladas que tiene pendiente para gozar
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
            pl.when(pl.col("VACACION_GOZADA_ACTUAL").is_in([0, 2, 3]))  # gozando y no ha gozado
            .then(pl.col("VACACIONES_PROPORCIONALES"))
            .when(pl.col("VACACION_GOZADA_ACTUAL").is_in([1]))  # ya gozó
            .then(pl.col("VACACIONES_PROPORCIONALES")-30)
            .otherwise(0.0)
        ).round(2).alias("VACACIONES_ACUMULADAS")
    ])

    # (Opcional) eliminar columna intermedia si no quieres dejarla
    df = df.drop("VACACIONES_PROPORCIONALES")
    df = df.drop("ANIVERSARIO")
    
    return df

# Unir las columnas 'NOMBRES' y 'APELLIDOS'
def create_column_fullname(df):
    # Unir columnas y limpiar caracteres no deseados
    df = df.with_columns([
        (
            (pl.col("NOMBRES") + " " + pl.col("APELLIDOS"))
            .str.replace_all(r"[^a-zA-ZáéíóúÁÉÍÓÚñÑ\s]", "")  # Eliminar todo menos letras y espacios
            .str.strip_chars()
            .alias("NOMBRE_COMPLETO")
        )
    ])

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

    # Crear columna 'NOMBRE_COMPLETO'
    df = create_column_fullname(df)

    # Calcular las columnas faltantes
    df = create_relevant_columns(df, this_year, this_month, today)

    # Alerta 1: A un mes o una semana de entrar a vacaciones
    df = create_alert_1(df, this_year, today)

    # Alerta 2: A una semana de cumplir aniversario
    df = create_alert_2(df, today)

    return df