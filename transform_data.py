import polars as pl
import re
from datetime import timedelta
from datetime import datetime, date

# Crear columna que me indique a cuanto tiempo esta de tener vacaciones
def create_vacation_alert(df, this_year, today):
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
def create_anniversary_alert(df, today):
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
    vaca_cols = [col for col in df.columns if col.startswith("Vacaciones ") and not col.endswith("_original")]

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
            (pl.lit(today) >= pl.col(vaca_col)) &
            (pl.lit(today) <= (pl.col(vaca_col) + timedelta(days=30)))
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
        
        # Paso 1: Calcular aniversario
    df = df.with_columns([
        pl.datetime(
            pl.when(pl.col("Fecha Ingreso").dt.year() < this_year)
            .then(this_year - 1)
            .otherwise(this_year),
            pl.col("Fecha Ingreso").dt.month(),
            pl.col("Fecha Ingreso").dt.day()
        ).alias("ANIVERSARIO")
    ])

        # Paso 2: Calcular proporcionales desde aniversario hasta hoy
    df = df.with_columns([
        ((pl.lit(today) - pl.col("ANIVERSARIO")).dt.total_days() / 365 * 30)
        .round(2)
        .alias("VACACIONES_PROPORCIONALES")
    ])

        # Paso 3: Identificar columnas de vacaciones originales (texto, con subsidio)
    vac_columns = [col for col in df.columns if col.startswith("Vacaciones ") and col.endswith("_original")]
    vac_column_map = {
        col: int(re.search(r"(\d{4})-\d{4}", col).group(1))
        for col in vac_columns
    }

        # Paso 4: Función para sumar acumuladas
    def calcular_acumuladas(row):
        ingreso_year = row["Fecha Ingreso"].year
        vac_estado = row.get("VACACION_GOZADA_ACTUAL", None)
        proporcionales = row.get("VACACIONES_PROPORCIONALES", 0.0)

        suma = 0.0

        for col, start_year in vac_column_map.items():
            if ingreso_year <= start_year < this_year - 1:
                valor = row.get(col)
                if valor is None:
                    suma += 30.0
                elif isinstance(valor, str) and "subsidio" in valor.lower():
                    continue  # subsidio → no suma
                elif isinstance(valor, (datetime, date)):
                    suma += 30.0
                else:
                    continue

        # Último periodo
        if vac_estado in [0, 2, 3]:
            suma += proporcionales
        elif vac_estado == 1 and proporcionales > 30:
            suma += proporcionales - 30

        return round(suma, 2)

        # Paso 5: Aplicar en Polars
    df = df.with_columns([
        pl.struct(["Fecha Ingreso", "VACACION_GOZADA_ACTUAL", "VACACIONES_PROPORCIONALES"] + list(vac_column_map.keys()))
        .map_elements(calcular_acumuladas)
        .alias("VACACIONES_ACUMULADAS")
    ])

        # Paso 6: Limpieza
    df = df.drop(["ANIVERSARIO", "VACACIONES_PROPORCIONALES"])
    
    return df

# Unir las columnas 'NOMBRES' y 'APELLIDOS'
def create_column_fullname(df):
    # Unir columnas y limpiar caracteres no deseados
    df = df.with_columns([
        (
            (pl.col("APELLIDOS") + " " + pl.col("NOMBRES"))
            .str.replace_all(r"[^a-zA-ZáéíóúÁÉÍÓÚñÑ\s]", "")  # Eliminar todo menos letras y espacios
            .str.strip_chars()
            .alias("NOMBRE_COMPLETO")
        )
    ])

    df = df.sort("NOMBRE_COMPLETO")

    return df

# Establecer los tipos de datos correctos en las columnas
def set_data_types(df, initial_year, this_year, date_format):
    # Convertir 'Fecha Ingreso' a datetime
    df = df.with_columns([
        pl.col("Fecha Ingreso").str.strptime(pl.Datetime, format=date_format)
    ])

    # Convertir cada columna de vacaciones y guardar su valor original
    for year in range(initial_year, this_year):
        col = f"Vacaciones {year}-{year+1}"
        df = df.with_columns([
            pl.col(col).alias(f"{col}_original"),  # respaldo original
            pl.col(col).str.strptime(pl.Datetime, format=date_format, strict=False)
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
    df = create_vacation_alert(df, this_year, today)

    # Alerta 2: A una semana de cumplir aniversario
    df = create_anniversary_alert(df, today)

    return df