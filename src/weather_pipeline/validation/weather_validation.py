import pandas as pd


def validate_weather_data(df):
    # Vi använder en lista för att samla alla validation-resultat
    errors = []

    # ---------------------------------------------------------
    # 1. Kontrollera null-värden
    # ---------------------------------------------------------

    # Dessa kolumner måste alltid ha ett värde
    required_columns = [
        "from_utc",
        "to_utc",
        "reference_date",
        "temperature_c",
        "quality",
    ]

    # Går igenom varje obligatorisk kolumn
    for column in required_columns:

        # Räknar hur många null-värden kolumnen innehåller
        null_count = df[column].isna().sum()

        # Om vi hittar null-värden sparar vi ett fel
        if null_count > 0:
            errors.append(
                f"{column} contains {null_count} null values"
            )

    # ---------------------------------------------------------
    # 2. Kontrollera dubbletter
    # ---------------------------------------------------------

    # Kontrollerar om samma observation förekommer flera gånger
    duplicate_count = df.duplicated().sum()

    if duplicate_count > 0:
        errors.append(
            f"Found {duplicate_count} duplicate rows"
        )

    # ---------------------------------------------------------
    # 3. Kontrollera temperaturens datatyp
    # ---------------------------------------------------------

    # Temperatur ska vara numerisk
    if not pd.api.types.is_numeric_dtype(df["temperature_c"]):
        errors.append(
            "temperature_c is not numeric"
        )

    # ---------------------------------------------------------
    # 4. Kontrollera orimliga temperaturer
    # ---------------------------------------------------------

    # Stockholm kan ha ganska kalla och varma temperaturer,
    # men värden utanför detta intervall är mycket misstänkta.
    invalid_temperature = df[
        (df["temperature_c"] < -50)
        | (df["temperature_c"] > 50)
    ]

    if len(invalid_temperature) > 0:
        errors.append(
            f"Found {len(invalid_temperature)} "
            "temperatures outside -50 to 50 C"
        )

    # ---------------------------------------------------------
    # Resultat
    # ---------------------------------------------------------

    # Om listan är tom har vi inte hittat några fel
    if len(errors) == 0:
        return True, []

    # Annars returnerar vi False tillsammans med felen
    return False, errors