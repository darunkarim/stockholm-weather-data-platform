import requests
import pandas as pd
from io import StringIO


# ---------------------------------------------------------
# INSTÄLLNINGAR
# ---------------------------------------------------------

# SMHI-stationer som vi vill undersöka.
# Vi behåller station_id eftersom vi senare vill kunna
# jämföra stationerna och välja bästa station per period.
STATIONS = {
    "97200": "Stockholm-Bromma Flygplats",
    "98210": "Stockholm-Observatoriekullen",
    "98230": "Stockholm-Observatoriekullen A",
}

# SMHI parameter 5 = Nederbördsmängd
PARAMETER_ID = 5

# URL till SMHI:s historiska, kvalitetskontrollerade data.
BASE_URL = (
    "https://opendata-download-metobs.smhi.se/api/version/1.0/"
    "parameter/{parameter_id}/station/{station_id}/"
    "period/corrected-archive/data.csv"
)


# ---------------------------------------------------------
# HÄMTA OCH PARSA DATA FRÅN EN STATION
# ---------------------------------------------------------

def fetch_precipitation(station_id, station_name):
    """
    Hämtar historisk nederbördsdata från SMHI för en station.

    Returnerar en pandas DataFrame med:
        date
        precipitation_mm
        quality
        station_id
        station_name
    """

    url = BASE_URL.format(
        parameter_id=PARAMETER_ID,
        station_id=station_id
    )

    print("=" * 70)
    print(f"STATION: {station_id} - {station_name}")
    print("=" * 70)
    print()
    print("Hämtar:")
    print(url)

    # -----------------------------------------------------
    # Hämta filen från SMHI
    # -----------------------------------------------------

    response = requests.get(url, timeout=60)

    print(f"HTTP status: {response.status_code}")

    # Om SMHI svarar med exempelvis 404 eller 500
    # stoppas funktionen för den här stationen.
    response.raise_for_status()

    # -----------------------------------------------------
    # Leta efter den riktiga observations-headern
    # -----------------------------------------------------

    lines = response.text.splitlines()

    header_index = None

    for i, line in enumerate(lines):

        # Den riktiga observations-tabellen börjar
        # med denna header.
        if line.startswith(
            "Från Datum Tid (UTC);Till Datum Tid (UTC);"
            "Representativt dygn;Nederbördsmängd;Kvalitet"
        ):
            header_index = i
            break

    if header_index is None:
        raise ValueError(
            "Kunde inte hitta observations-headern i SMHI-svaret."
        )

    print(f"Observations-header hittad på rad: {header_index}")
    print()

    # -----------------------------------------------------
    # Läs endast observationsdelen
    # -----------------------------------------------------

    # Allt före headern är metadata och ska inte läsas
    # som observationer.
    observation_lines = lines[header_index:]

    # Skapa en textsträng som pandas kan läsa.
    observation_text = "\n".join(observation_lines)

    df = pd.read_csv(
        StringIO(observation_text),
        sep=";",
        dtype=str
    )

    # -----------------------------------------------------
    # Behåll endast de kolumner vi behöver
    # -----------------------------------------------------

    df = df[
        [
            "Från Datum Tid (UTC)",
            "Till Datum Tid (UTC)",
            "Representativt dygn",
            "Nederbördsmängd",
            "Kvalitet",
        ]
    ].copy()

    # -----------------------------------------------------
    # Rensa eventuella tomma/rubbade rader
    # -----------------------------------------------------

    df = df.dropna(
        subset=[
            "Representativt dygn",
            "Nederbördsmängd"
        ]
    )

    # -----------------------------------------------------
    # Konvertera datum
    # -----------------------------------------------------

    df["date"] = pd.to_datetime(
        df["Representativt dygn"],
        errors="coerce"
    )

    # Om någon rad inte innehåller ett riktigt datum
    # tar vi bort den.
    df = df.dropna(subset=["date"])

    # -----------------------------------------------------
    # Konvertera nederbörd till numeriskt värde
    # -----------------------------------------------------

    df["precipitation_mm"] = pd.to_numeric(
        df["Nederbördsmängd"],
        errors="coerce"
    )

    # Rader utan ett numeriskt nederbördsvärde tas bort.
    df = df.dropna(subset=["precipitation_mm"])

    # -----------------------------------------------------
    # Lägg till information om stationen
    # -----------------------------------------------------

    df["station_id"] = station_id
    df["station_name"] = station_name

    # -----------------------------------------------------
    # Byt namn på kvalitetskolumnen
    # -----------------------------------------------------

    df["quality"] = df["Kvalitet"]

    # -----------------------------------------------------
    # Välj slutliga kolumner
    # -----------------------------------------------------

    df = df[
        [
            "date",
            "precipitation_mm",
            "quality",
            "station_id",
            "station_name",
        ]
    ].copy()

    # Sortera kronologiskt.
    df = df.sort_values("date")

    # -----------------------------------------------------
    # RESULTAT
    # -----------------------------------------------------

    print("RESULTAT")
    print("-" * 40)

    print(f"Antal observationer: {len(df):,}")

    if len(df) > 0:

        print(
            f"Första observation:   "
            f"{df['date'].min().date()}"
        )

        print(
            f"Sista observation:    "
            f"{df['date'].max().date()}"
        )

        print()

        print("Kvalitet:")

        quality_counts = df["quality"].value_counts()

        for quality, count in quality_counts.items():
            print(f"  {quality}: {count:,}")

        print()

        print("Nederbörd:")
        print(
            f"  Medel: {df['precipitation_mm'].mean():.2f} mm"
        )
        print(
            f"  Min:   {df['precipitation_mm'].min():.2f} mm"
        )
        print(
            f"  Max:   {df['precipitation_mm'].max():.2f} mm"
        )

        print()

        # -------------------------------------------------
        # Kontrollera datumluckor
        # -------------------------------------------------

        expected_dates = pd.date_range(
            start=df["date"].min(),
            end=df["date"].max(),
            freq="D"
        )

        actual_dates = pd.DatetimeIndex(
            df["date"].unique()
        )

        missing_dates = expected_dates.difference(
            actual_dates
        )

        print("DATUMKONTROLL")
        print("-" * 40)

        print(
            f"Förväntade dygn: {len(expected_dates):,}"
        )

        print(
            f"Faktiska dygn:   {len(actual_dates):,}"
        )

        print(
            f"Saknade dygn:    {len(missing_dates):,}"
        )

        if len(missing_dates) > 0:

            print()
            print("Första saknade datum:")

            for date in missing_dates[:10]:
                print(f"  {date.date()}")

            if len(missing_dates) > 10:
                print(
                    f"  ... och {len(missing_dates) - 10:,} till"
                )

    print()

    return df


# ---------------------------------------------------------
# MAIN
# ---------------------------------------------------------

def main():

    print("=" * 70)
    print("STOCKHOLM WEATHER – HISTORISK NEDERBÖRD")
    print("=" * 70)
    print()

    all_data = []

    # Vi hämtar stationerna EN I TAGET.
    # Det är bättre för SMHI:s API än att skicka många
    # historiska förfrågningar samtidigt.
    for station_id, station_name in STATIONS.items():

        try:

            df = fetch_precipitation(
                station_id,
                station_name
            )

            all_data.append(df)

        except requests.exceptions.HTTPError as error:

            print()
            print(
                f"❌ Kunde inte hämta station "
                f"{station_id}"
            )
            print(error)
            print()

        except Exception as error:

            print()
            print(
                f"❌ Fel vid behandling av station "
                f"{station_id}"
            )
            print(error)
            print()

    # -----------------------------------------------------
    # KOMBINERA ALLA STATIONER
    # -----------------------------------------------------

    if not all_data:

        print("❌ Ingen data kunde hämtas.")
        return

    combined = pd.concat(
        all_data,
        ignore_index=True
    )

    combined = combined.sort_values(
        ["date", "station_id"]
    )

    # -----------------------------------------------------
    # SAMMANFATTNING
    # -----------------------------------------------------

    print("=" * 70)
    print("SAMMANFATTNING – ALLA STATIONER")
    print("=" * 70)

    print()
    print(
        f"Totalt antal observationer: "
        f"{len(combined):,}"
    )

    print()

    print("Observationer per station:")

    station_counts = (
        combined
        .groupby(
            ["station_id", "station_name"]
        )
        .size()
    )

    for (station_id, station_name), count in station_counts.items():

        print(
            f"  {station_id} - "
            f"{station_name}: "
            f"{count:,}"
        )

    print()

    # -----------------------------------------------------
    # SPARA RESULTATET
    # -----------------------------------------------------

    output_file = "data/raw/stockholm_precipitation.csv"

    combined.to_csv(
        output_file,
        index=False
    )

    print(
        f"Data sparad till: {output_file}"
    )

    print()

    print("Första 10 raderna:")
    print(
        combined.head(10).to_string(
            index=False
        )
    )

    print()

    print("=" * 70)
    print("NEDERBÖRDSANALYS KLAR")
    print("=" * 70)


# ---------------------------------------------------------
# STARTA PROGRAMMET
# ---------------------------------------------------------

if __name__ == "__main__":
    main()