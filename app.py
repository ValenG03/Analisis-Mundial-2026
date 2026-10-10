# -*- coding: utf-8 -*-
"""
MUNDIAL 2026 · ANÁLISIS CUANTITATIVO
Dashboard interactivo en Streamlit sobre la Copa del Mundo FIFA 2026 (Canadá · México · EE.UU.)
Datos: Al Jazeera, FOX Sports, FIFA, Transfermarkt (vía Visual Capitalist), AP, ESPN, Foot Africa.
"""

import math
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import quote

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import streamlit as st

# ──────────────────────────────────────────────────────────────────────────────
# CONFIG
# ──────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Mundial 2026 · Análisis Cuantitativo",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="collapsed",
)

EUR_USD = 1.16  # tipo de cambio de referencia para pasar valores de mercado (€) a dólares

# Paleta inspirada en la identidad del Mundial 2026: base negra/blanca + acentos vibrantes por sede
C = {
    "bg": "#06060B",
    "ink": "#F4F4F8",
    "muted": "#9A9AB0",
    "magenta": "#FF2E93",
    "lime": "#C6FF00",
    "cyan": "#00E5FF",
    "orange": "#FF7A00",
    "violet": "#8B5CF6",
    "red": "#FF3B3B",
    "mint": "#2EFFB4",
    "gold": "#FFD60A",
}
NEON = [C["magenta"], C["lime"], C["cyan"], C["orange"], C["violet"], C["red"], C["mint"], C["gold"]]
CONF_COLORS = {
    "UEFA": C["cyan"],
    "CONMEBOL": C["gold"],
    "CONCACAF": C["magenta"],
    "CAF": C["lime"],
    "AFC": C["orange"],
    "OFC": C["violet"],
}

# ──────────────────────────────────────────────────────────────────────────────
# DATOS
# ──────────────────────────────────────────────────────────────────────────────
# Estadísticas por selección (FOX Sports, tabla final del torneo) + valor de plantel (Transfermarkt, €M)
# cols: nombre, bandera, conf, PJ, GF, goles de cabeza, GF 1T, GF 2T, GC, asist, amarillas, rojas, valor €M
TEAMS_RAW = [
    ("Inglaterra", "🏴󠁧󠁢󠁥󠁮󠁧󠁿", "UEFA", 8, 20, 5, 9, 10, 12, 14, 8, 1, 1360.0),
    ("Irak", "🇮🇶", "AFC", 3, 1, 1, 1, 0, 12, 1, 4, 1, 21.2),
    ("Túnez", "🇹🇳", "CAF", 3, 2, 2, 1, 1, 12, 2, 1, 0, 70.0),
    ("Noruega", "🇳🇴", "UEFA", 6, 13, 2, 6, 7, 11, 10, 3, 0, 589.9),
    ("Uzbekistán", "🇺🇿", "AFC", 3, 2, 1, 1, 1, 11, 1, 4, 0, 85.3),
    ("Francia", "🇫🇷", "UEFA", 8, 20, 1, 5, 15, 10, 18, 6, 0, 1520.0),
    ("Nueva Zelanda", "🇳🇿", "OFC", 3, 4, 1, 2, 2, 10, 3, 4, 0, 34.5),
    ("Qatar", "🇶🇦", "AFC", 3, 2, 0, 1, 1, 10, 1, 4, 2, 19.9),
    ("Suecia", "🇸🇪", "UEFA", 4, 7, 0, 2, 5, 10, 6, 5, 0, 406.1),
    ("Argelia", "🇩🇿", "CAF", 4, 5, 1, 1, 4, 9, 3, 3, 0, 256.9),
    ("Austria", "🇦🇹", "UEFA", 4, 6, 1, 2, 4, 9, 4, 5, 0, 245.2),
    ("Curazao", "🇨🇼", "CONCACAF", 3, 1, 0, 1, 0, 9, 0, 7, 0, 25.8),
    ("Senegal", "🇸🇳", "CAF", 4, 10, 0, 2, 8, 9, 9, 3, 0, 478.1),
    ("Argentina", "🇦🇷", "CONMEBOL", 8, 19, 4, 6, 9, 8, 12, 14, 1, 807.5),
    ("Bosnia y Herzegovina", "🇧🇦", "UEFA", 4, 5, 1, 3, 2, 8, 3, 7, 1, 146.4),
    ("Haití", "🇭🇹", "CONCACAF", 3, 2, 0, 2, 0, 8, 1, 7, 0, 55.9),
    ("Jordania", "🇯🇴", "AFC", 3, 3, 0, 1, 2, 8, 3, 4, 0, 20.3),
    ("Estados Unidos", "🇺🇸", "CONCACAF", 5, 11, 1, 8, 3, 8, 4, 7, 1, 385.6),
    ("Bélgica", "🇧🇪", "UEFA", 6, 14, 4, 4, 9, 7, 9, 6, 1, 547.5),
    ("Croacia", "🇭🇷", "UEFA", 4, 6, 1, 3, 3, 7, 6, 4, 0, 387.3),
    ("Egipto", "🇪🇬", "CAF", 5, 8, 4, 4, 4, 7, 7, 12, 0, 116.5),
    ("Canadá", "🇨🇦", "CONCACAF", 5, 9, 0, 3, 6, 6, 3, 11, 0, 198.7),
    ("Chequia", "🇨🇿", "UEFA", 3, 2, 1, 1, 1, 6, 2, 1, 0, 188.2),
    ("Marruecos", "🇲🇦", "CAF", 6, 10, 1, 4, 6, 6, 9, 7, 0, 447.7),
    ("Paraguay", "🇵🇾", "CONMEBOL", 5, 3, 1, 2, 1, 6, 3, 9, 1, 153.7),
    ("Suiza", "🇨🇭", "UEFA", 6, 10, 0, 2, 8, 6, 6, 7, 1, 332.5),
    ("Cabo Verde", "🇨🇻", "CAF", 4, 4, 0, 1, 2, 5, 2, 5, 0, 49.3),
    ("RD Congo", "🇨🇩", "CAF", 4, 5, 1, 2, 3, 5, 3, 6, 0, 143.9),
    ("Alemania", "🇩🇪", "UEFA", 4, 11, 2, 4, 7, 5, 10, 3, 0, 947.0),
    ("Japón", "🇯🇵", "AFC", 4, 8, 2, 3, 5, 5, 7, 4, 0, 270.9),
    ("Países Bajos", "🇳🇱", "UEFA", 4, 11, 2, 4, 7, 5, 10, 3, 0, 754.2),
    ("Arabia Saudita", "🇸🇦", "AFC", 3, 1, 0, 1, 0, 5, 0, 6, 0, 40.7),
    ("Turquía", "🇹🇷", "UEFA", 3, 3, 0, 2, 1, 5, 2, 2, 0, 473.7),
    ("Brasil", "🇧🇷", "CONMEBOL", 5, 10, 2, 6, 4, 4, 8, 8, 0, 928.2),
    ("Ecuador", "🇪🇨", "CONMEBOL", 4, 2, 0, 1, 1, 4, 2, 8, 1, 368.7),
    ("Costa de Marfil", "🇨🇮", "CAF", 4, 5, 0, 2, 3, 4, 4, 4, 0, 522.1),
    ("Panamá", "🇵🇦", "CONCACAF", 3, 0, 0, 0, 0, 4, 0, 5, 0, 34.6),
    ("Escocia", "🏴󠁧󠁢󠁳󠁣󠁴󠁿", "UEFA", 3, 1, 0, 1, 0, 4, 0, 5, 0, 170.3),
    ("Sudáfrica", "🇿🇦", "CAF", 4, 2, 0, 0, 2, 4, 1, 5, 2, 49.3),
    ("Uruguay", "🇺🇾", "CONMEBOL", 3, 3, 1, 2, 1, 4, 1, 5, 1, 359.3),
    ("Australia", "🇦🇺", "AFC", 4, 3, 0, 1, 2, 3, 1, 5, 0, 77.5),
    ("Ghana", "🇬🇭", "CAF", 4, 2, 0, 0, 2, 3, 2, 6, 0, 234.5),
    ("Irán", "🇮🇷", "AFC", 3, 3, 1, 2, 1, 3, 1, 6, 0, 32.1),
    ("México", "🇲🇽", "CONCACAF", 5, 10, 1, 4, 6, 3, 7, 4, 1, 191.9),
    ("Portugal", "🇵🇹", "UEFA", 5, 8, 2, 4, 4, 3, 4, 7, 0, 1010.0),
    ("Corea del Sur", "🇰🇷", "AFC", 3, 2, 0, 0, 2, 3, 2, 4, 0, 139.1),
    ("Colombia", "🇨🇴", "CONMEBOL", 5, 5, 1, 2, 3, 1, 5, 8, 0, 302.4),
    ("España", "🇪🇸", "UEFA", 8, 14, 1, 7, 6, 1, 10, 6, 0, 1220.0),
]
STAGE_BY_GP = {3: "Fase de grupos", 4: "16avos", 5: "Octavos", 6: "Cuartos", 8: "Semifinal"}
STAGE_ORDER = ["Fase de grupos", "16avos", "Octavos", "Cuartos", "4° puesto", "3° puesto", "Subcampeón", "Campeón"]
FINAL_PLACES = {"España": "Campeón", "Argentina": "Subcampeón", "Inglaterra": "3° puesto", "Francia": "4° puesto"}

TOTAL_GOALS = 308
TOTAL_MATCHES = 104
TOTAL_PLAYERS = 1039
ATTENDANCE_102 = 6_665_825  # acumulado FIFA tras 102 partidos
AVG_ATT = 65_351

# Top 10 goleadores (goles, asistencias)
SCORERS = [
    ("Kylian Mbappé", "Francia", "🇫🇷", 10, 4),
    ("Lionel Messi", "Argentina", "🇦🇷", 8, 4),
    ("Jude Bellingham", "Inglaterra", "🏴󠁧󠁢󠁥󠁮󠁧󠁿", 7, 1),
    ("Erling Haaland", "Noruega", "🇳🇴", 7, 0),
    ("Ousmane Dembélé", "Francia", "🇫🇷", 6, 2),
    ("Harry Kane", "Inglaterra", "🏴󠁧󠁢󠁥󠁮󠁧󠁿", 6, 2),
    ("Mikel Oyarzabal", "España", "🇪🇸", 5, 1),
    ("Ismaïla Sarr", "Senegal", "🇸🇳", 4, 1),
    ("Julián Quiñones", "México", "🇲🇽", 4, 1),
    ("Vinícius Júnior", "Brasil", "🇧🇷", 4, 1),
]
# Top 10 asistidores
ASSISTERS = [
    ("Michael Olise", "Francia", "🇫🇷", 7),
    ("Martin Ødegaard", "Noruega", "🇳🇴", 4),
    ("Kylian Mbappé", "Francia", "🇫🇷", 4),
    ("Brahim Díaz", "Marruecos", "🇲🇦", 4),
    ("Lionel Messi", "Argentina", "🇦🇷", 4),
    ("Bruno Guimarães", "Brasil", "🇧🇷", 4),
    ("Roberto Alvarado", "México", "🇲🇽", 3),
    ("Anthony Gordon", "Inglaterra", "🏴󠁧󠁢󠁥󠁮󠁧󠁿", 3),
    ("Florian Wirtz", "Alemania", "🇩🇪", 3),
    ("Andreas Schjelderup", "Noruega", "🇳🇴", 3),
]
SAVES = [
    ("Orlando Gill", "Paraguay", 28), ("Eloy Room", "Curazao", 21), ("Emiliano Martínez", "Argentina", 20),
    ("Gregor Kobel", "Suiza", 20), ("Diogo Costa", "Portugal", 20), ("Jordan Pickford", "Inglaterra", 19),
    ("Yassine Bounou", "Marruecos", 19), ("Vozinha", "Cabo Verde", 18), ("Zion Suzuki", "Japón", 17),
    ("Mohammed Al Owais", "Arabia Saudita", 17),
]
CLEAN_SHEETS = [
    ("Unai Simón", "España", 7), ("Camilo Vargas", "Colombia", 4), ("Mike Maignan", "Francia", 4),
    ("Raúl Rangel", "México", 4), ("Matt Freese", "Estados Unidos", 2), ("Yahia Fofana", "Costa de Marfil", 2),
    ("Patrick Beach", "Australia", 2), ("Vozinha", "Cabo Verde", 2), ("Alisson", "Brasil", 2),
    ("Maxime Crépeau", "Canadá", 2),
]
# Top 5 vallas menos vencidas (criterio: GC ↑, luego más partidos jugados, luego vallas invictas)
BEST_DEFENSE = [
    ("España", "🇪🇸", "Unai Simón", 1, 8, "Guante de Oro · 7 vallas invictas · récord de 650' sin recibir goles"),
    ("Colombia", "🇨🇴", "Camilo Vargas", 1, 5, "4 vallas invictas en 5 partidos (80%) · eliminado por penales sin recibir goles"),
    ("México", "🇲🇽", "Raúl Rangel", 3, 5, "4 vallas invictas, primer arquero mexicano con 4 seguidas en un Mundial"),
    ("Portugal", "🇵🇹", "Diogo Costa", 3, 5, "20 atajadas, entre las más altas del torneo"),
    ("Australia", "🇦🇺", "Patrick Beach", 3, 4, "2 vallas invictas en 4 partidos"),
]

# Estadios / sedes
STADIUMS = pd.DataFrame([
    # key, estadio (nombre comercial), nombre FIFA, ciudad, país, lat, lon, capacidad aprox., partidos, título Wikipedia, población metro (M), dato
    ("MET", "MetLife Stadium", "New York New Jersey Stadium", "Nueva York / Nueva Jersey", "EE.UU.", 40.8135, -74.0745, 82500, 8, "MetLife_Stadium", 19.5, "Sede de la final. Área metropolitana más poblada de EE.UU."),
    ("ATT", "AT&T Stadium", "Dallas Stadium", "Dallas (Arlington)", "EE.UU.", 32.7473, -97.0945, 80000, 9, "AT&T_Stadium", 8.1, "El estadio con más partidos del Mundial (9), incluida una semifinal."),
    ("ARR", "Arrowhead Stadium", "Kansas City Stadium", "Kansas City", "EE.UU.", 39.0489, -94.4839, 73000, 6, "Arrowhead_Stadium", 2.2, "Famoso por su récord de ruido. Base de Argentina e Inglaterra."),
    ("NRG", "NRG Stadium", "Houston Stadium", "Houston", "EE.UU.", 29.6847, -95.4107, 72000, 7, "NRG_Stadium", 7.5, "Techo retráctil y aire acondicionado contra el calor texano."),
    ("MBS", "Mercedes-Benz Stadium", "Atlanta Stadium", "Atlanta", "EE.UU.", 33.7554, -84.4008, 71000, 8, "Mercedes-Benz_Stadium", 6.3, "Techo tipo diafragma de cámara. Sede de una semifinal."),
    ("SOF", "SoFi Stadium", "Los Angeles Stadium", "Los Ángeles (Inglewood)", "EE.UU.", 33.9535, -118.3392, 70000, 8, "SoFi_Stadium", 12.9, "Uno de los estadios más caros jamás construidos. Debut de EE.UU."),
    ("LFF", "Lincoln Financial Field", "Philadelphia Stadium", "Filadelfia", "EE.UU.", 39.9008, -75.1675, 69000, 6, "Lincoln_Financial_Field", 6.2, "Partido clave el 4 de julio, en los 250 años de EE.UU."),
    ("LUM", "Lumen Field", "Seattle Stadium", "Seattle", "EE.UU.", 47.5952, -122.3316, 69000, 6, "Lumen_Field", 4.1, "Una de las hinchadas más ruidosas del deporte estadounidense."),
    ("LEV", "Levi's Stadium", "San Francisco Bay Area Stadium", "San Francisco (Santa Clara)", "EE.UU.", 37.4030, -121.9700, 68500, 6, "Levi's_Stadium", 7.7, "En el corazón de Silicon Valley."),
    ("GIL", "Gillette Stadium", "Boston Stadium", "Boston (Foxborough)", "EE.UU.", 42.0909, -71.2643, 65000, 7, "Gillette_Stadium", 4.9, "Ya fue sede en el Mundial 1994."),
    ("HRS", "Hard Rock Stadium", "Miami Stadium", "Miami", "EE.UU.", 25.9580, -80.2389, 65000, 7, "Hard_Rock_Stadium", 6.1, "Sede del partido por el 3° puesto (Inglaterra 6-4 Francia)."),
    ("AZT", "Estadio Azteca", "Mexico City Stadium", "Ciudad de México", "México", 19.3029, -99.1505, 83000, 5, "Estadio_Azteca", 22.0, "Partido inaugural. Primer estadio en tres Mundiales (1970, 1986, 2026)."),
    ("AKR", "Estadio Akron", "Estadio Guadalajara", "Guadalajara (Zapopan)", "México", 20.6817, -103.4627, 48000, 4, "Estadio_Akron", 5.3, "Diseño de volcán con cubierta verde. Allí España venció a Uruguay."),
    ("BBV", "Estadio BBVA", "Estadio Monterrey", "Monterrey (Guadalupe)", "México", 25.6690, -100.2445, 53500, 4, "Estadio_BBVA", 5.3, "Vista al Cerro de la Silla, ícono de la ciudad."),
    ("BMO", "BMO Field", "Toronto Stadium", "Toronto", "Canadá", 43.6332, -79.4186, 45000, 6, "BMO_Field", 6.7, "Ampliado para el torneo. Debut mundialista de Canadá en casa."),
    ("BCP", "BC Place", "BC Place Vancouver", "Vancouver", "Canadá", 49.2768, -123.1120, 54000, 7, "BC_Place", 2.7, "Allí Canadá logró su primer triunfo en un Mundial (6-0 a Qatar)."),
], columns=["key", "estadio", "nombre_fifa", "ciudad", "pais", "lat", "lon", "capacidad", "partidos", "wiki", "pob_metro_m", "dato"])

# Recorridos (partido a partido) de las tres selecciones
ROUTES = {
    "España": {
        "color": C["red"], "flag": "🇪🇸",
        "legs": [
            ("Grupo H · F1", "Cabo Verde", "0-0", "MBS"),
            ("Grupo H · F2", "Arabia Saudita", "4-0", "MBS"),
            ("Grupo H · F3", "Uruguay", "1-0", "AKR"),
            ("16avos", "Austria", "3-0", "SOF"),
            ("Octavos", "Portugal", "1-0", "ATT"),
            ("Cuartos", "Bélgica", "2-1", "SOF"),
            ("Semifinal", "Francia", "2-0", "ATT"),
            ("FINAL", "Argentina", "1-0 (t.s.)", "MET"),
        ],
    },
    "Argentina": {
        "color": C["cyan"], "flag": "🇦🇷",
        "legs": [
            ("Grupo J · F1", "Argelia", "3-0", "ARR"),
            ("Grupo J · F2", "Austria", "2-0", "ATT"),
            ("Grupo J · F3", "Jordania", "3-1", "ATT"),
            ("16avos", "Cabo Verde", "3-2 (t.s.)", "HRS"),
            ("Octavos", "Egipto", "3-2", "MBS"),
            ("Cuartos", "Suiza", "3-1 (t.s.)", "ARR"),
            ("Semifinal", "Inglaterra", "2-1", "MBS"),
            ("FINAL", "España", "0-1 (t.s.)", "MET"),
        ],
    },
    "Inglaterra": {
        "color": C["lime"], "flag": "🏴󠁧󠁢󠁥󠁮󠁧󠁿",
        "legs": [
            ("Grupo L · F1", "Croacia", "4-2", "ATT"),
            ("Grupo L · F2", "Ghana", "0-0", "GIL"),
            ("Grupo L · F3", "Panamá", "2-0", "MET"),
            ("16avos", "RD Congo", "2-1", "MBS"),
            ("Octavos", "México", "3-2", "AZT"),
            ("Cuartos", "Noruega", "2-1 (t.s.)", "HRS"),
            ("Semifinal", "Argentina", "1-2", "MBS"),
            ("3° puesto", "Francia", "6-4", "HRS"),
        ],
    },
}

MASCOTS = [
    ("MAPLE", "Alce", "🫎", "Canadá", "🇨🇦", "Arquero", C["red"],
     "Su nombre homenajea a la hoja de arce, símbolo nacional canadiense. Juega bajo los tres palos, como los arqueros de los primeros Mundiales de Canadá."),
    ("ZAYU", "Jaguar", "🐆", "México", "🇲🇽", "Delantero", C["mint"],
     "Rinde tributo a la fauna y las tradiciones de México. Es el goleador del trío."),
    ("CLUTCH", "Águila calva", "🦅", "Estados Unidos", "🇺🇸", "Mediocampista · N.º 10", C["cyan"],
     "'Clutch' es el jugador que aparece en el momento decisivo. Lleva la 10, como Pulisic o Donovan."),
]


@st.cache_data
def teams_df() -> pd.DataFrame:
    df = pd.DataFrame(TEAMS_RAW, columns=[
        "seleccion", "bandera", "conf", "pj", "gf", "gf_cabeza", "gf_1t", "gf_2t",
        "gc", "asist", "amarillas", "rojas", "valor_eur",
    ])
    df["valor_usd"] = (df["valor_eur"] * EUR_USD).round(1)
    df["dif"] = df["gf"] - df["gc"]
    df["gf_pp"] = (df["gf"] / df["pj"]).round(2)
    df["gc_pp"] = (df["gc"] / df["pj"]).round(2)
    df["etapa"] = df.apply(lambda r: FINAL_PLACES.get(r["seleccion"], STAGE_BY_GP[r["pj"]]), axis=1)
    df["usd_por_gol"] = (df["valor_usd"] / df["gf"].replace(0, float("nan"))).round(1)
    df["label"] = df["bandera"] + " " + df["seleccion"]
    return df


def haversine_km(a, b):
    lat1, lon1, lat2, lon2 = map(math.radians, [a[0], a[1], b[0], b[1]])
    h = math.sin((lat2 - lat1) / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2
    return 2 * 6371 * math.asin(math.sqrt(h))


@st.cache_data
def routes_df() -> pd.DataFrame:
    s = STADIUMS.set_index("key")
    rows = []
    for team, info in ROUTES.items():
        prev = None
        total = 0.0
        for i, (stage, rival, score, key) in enumerate(info["legs"], start=1):
            st_row = s.loc[key]
            km = 0.0 if prev is None or prev == key else haversine_km(
                (s.loc[prev, "lat"], s.loc[prev, "lon"]), (st_row["lat"], st_row["lon"]))
            total += km
            rows.append({
                "equipo": team, "n": i, "etapa": stage, "rival": rival, "resultado": score,
                "estadio": st_row["estadio"], "ciudad": st_row["ciudad"],
                "lat": st_row["lat"], "lon": st_row["lon"],
                "km_tramo": round(km), "km_acum": round(total),
            })
            prev = key
    return pd.DataFrame(rows)


@st.cache_data(ttl=60 * 60 * 24, show_spinner=False)
def wiki_thumb(title: str):
    """Foto de referencia del estadio vía la API REST de Wikipedia (imágenes de Wikimedia Commons)."""
    try:
        r = requests.get(
            f"https://en.wikipedia.org/api/rest_v1/page/summary/{quote(title, safe='')}",
            headers={"User-Agent": "Mundial2026Dashboard/1.0 (Streamlit educational project)"},
            timeout=8,
        )
        if r.ok:
            data = r.json()
            img = data.get("originalimage") or data.get("thumbnail")
            if img and img.get("source"):
                src = img["source"]
                thumb = (data.get("thumbnail") or {}).get("source")
                return thumb.replace("/320px-", "/640px-") if thumb and "/320px-" in thumb else src
    except Exception:
        pass
    return None


@st.cache_data(ttl=60 * 60 * 24, show_spinner=False)
def all_thumbs(titles: tuple) -> dict:
    with ThreadPoolExecutor(max_workers=8) as ex:
        return dict(zip(titles, ex.map(wiki_thumb, titles)))


# ──────────────────────────────────────────────────────────────────────────────
# ESTILO
# ──────────────────────────────────────────────────────────────────────────────
CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Anton&family=Space+Grotesk:wght@400;500;700&display=swap');

@property --n { syntax: '<integer>'; initial-value: 0; inherits: false; }
@property --ang { syntax: '<angle>'; initial-value: 0deg; inherits: false; }

:root {
  --bg: #06060B; --ink: #F4F4F8; --muted: #9A9AB0;
  --mg: #FF2E93; --lm: #C6FF00; --cy: #00E5FF; --or: #FF7A00; --vi: #8B5CF6; --rd: #FF3B3B; --mt: #2EFFB4; --gd: #FFD60A;
  --card: rgba(255,255,255,0.04); --line: rgba(255,255,255,0.09);
}

html, body, [class*="css"], .stApp, .stMarkdown, p, li, label, span, div { font-family: 'Space Grotesk', sans-serif; }
.stApp {
  background:
    radial-gradient(1200px 600px at 10% -10%, rgba(255,46,147,0.16), transparent 60%),
    radial-gradient(900px 500px at 100% 10%, rgba(0,229,255,0.14), transparent 60%),
    radial-gradient(900px 700px at 50% 110%, rgba(198,255,0,0.10), transparent 60%),
    #06060B;
  background-attachment: fixed;
  color: var(--ink);
}
.stApp::before {
  content: ""; position: fixed; inset: 0; pointer-events: none; z-index: 0;
  background-image: linear-gradient(rgba(255,255,255,0.025) 1px, transparent 1px),
                    linear-gradient(90deg, rgba(255,255,255,0.025) 1px, transparent 1px);
  background-size: 48px 48px;
  mask-image: radial-gradient(ellipse at center, black 30%, transparent 80%);
}
[data-testid="stHeader"] { background: transparent; }
.block-container { padding-top: 2.2rem; max-width: 1320px; }

/* ── Emblema neón (esquina superior derecha) ── */
.neon-badge {
  position: fixed; top: 64px; right: 26px; z-index: 9999;
  width: 104px; height: 104px; border-radius: 50%;
  display: grid; place-items: center;
  animation: float 4s ease-in-out infinite;
}
.neon-badge::before {
  content: ""; position: absolute; inset: -6px; border-radius: 50%;
  background: conic-gradient(from var(--ang), var(--mg), var(--or), var(--gd), var(--lm), var(--mt), var(--cy), var(--vi), var(--mg));
  animation: spin 4s linear infinite;
  filter: blur(10px); opacity: .85;
}
.neon-badge::after {
  content: ""; position: absolute; inset: -2px; border-radius: 50%;
  background: conic-gradient(from var(--ang), var(--mg), var(--or), var(--gd), var(--lm), var(--mt), var(--cy), var(--vi), var(--mg));
  animation: spin 4s linear infinite;
}
.neon-core {
  position: relative; z-index: 2; width: 92px; height: 92px; border-radius: 50%;
  background: radial-gradient(circle at 30% 25%, #1b1b2a, #050508 70%);
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  box-shadow: inset 0 0 18px rgba(255,255,255,.08);
}
.neon-core .n26 {
  font-family: 'Anton', sans-serif; font-size: 40px; line-height: .9; letter-spacing: 1px;
  background: linear-gradient(90deg, var(--mg), var(--gd), var(--lm), var(--cy), var(--vi), var(--mg));
  background-size: 300% 100%; -webkit-background-clip: text; background-clip: text; color: transparent;
  animation: slide 5s linear infinite;
  filter: drop-shadow(0 0 6px rgba(255,255,255,.35));
}
.neon-core .wc { font-size: 8.5px; letter-spacing: 2.4px; color: #fff; margin-top: 3px; font-weight: 700; }
.neon-core .hosts { font-size: 7px; letter-spacing: 1.6px; color: var(--muted); margin-top: 1px; }
.spark { position: absolute; width: 5px; height: 5px; border-radius: 50%; z-index: 3; filter: blur(.4px); animation: twinkle 2.4s ease-in-out infinite; }
.spark.s1 { top: -4px; left: 48px; background: var(--gd); box-shadow: 0 0 10px var(--gd); }
.spark.s2 { bottom: 6px; left: -2px; background: var(--cy); box-shadow: 0 0 10px var(--cy); animation-delay: .6s; }
.spark.s3 { top: 22px; right: -4px; background: var(--mg); box-shadow: 0 0 10px var(--mg); animation-delay: 1.2s; }
.spark.s4 { bottom: -3px; right: 30px; background: var(--lm); box-shadow: 0 0 10px var(--lm); animation-delay: 1.8s; }

@keyframes spin { to { --ang: 360deg; } }
@keyframes slide { to { background-position: 300% 0; } }
@keyframes float { 0%,100% { transform: translateY(0) } 50% { transform: translateY(-6px) } }
@keyframes twinkle { 0%,100% { opacity: .2; transform: scale(.6) } 50% { opacity: 1; transform: scale(1.4) } }
@keyframes rise { from { opacity: 0; transform: translateY(24px) } to { opacity: 1; transform: none } }
@keyframes count { from { --n: 0 } to { --n: var(--to) } }
@keyframes marquee { from { transform: translateX(0) } to { transform: translateX(-50%) } }
@keyframes grow { from { transform: scaleY(0) } to { transform: scaleY(1) } }
@keyframes pulse { 0%,100% { box-shadow: 0 0 0 0 rgba(255,214,10,.45) } 50% { box-shadow: 0 0 0 14px rgba(255,214,10,0) } }

/* ── Hero ── */
.hero { position: relative; padding: 10px 140px 6px 0; animation: rise .8s ease both; }
.kicker { font-size: 13px; letter-spacing: 4px; color: var(--muted); text-transform: uppercase; }
.kicker b { color: var(--lm); font-weight: 700; }
.title {
  font-family: 'Anton', sans-serif; font-size: clamp(44px, 7.2vw, 104px); line-height: .92; margin: 8px 0 10px;
  text-transform: uppercase; letter-spacing: .5px;
}
.title .grad {
  background: linear-gradient(90deg, var(--mg), var(--or), var(--gd), var(--lm), var(--cy), var(--vi), var(--mg));
  background-size: 300% 100%; -webkit-background-clip: text; background-clip: text; color: transparent;
  animation: slide 8s linear infinite;
}
.subtitle { color: var(--muted); font-size: 17px; max-width: 760px; }
.chips { display: flex; gap: 8px; flex-wrap: wrap; margin-top: 16px; }
.chip { border: 1px solid var(--line); background: var(--card); padding: 6px 12px; border-radius: 999px; font-size: 13px; }

/* ── Ticker ── */
.ticker { margin: 22px 0 8px; border-top: 1px solid var(--line); border-bottom: 1px solid var(--line); overflow: hidden; white-space: nowrap; }
.ticker-track { display: inline-block; padding: 10px 0; animation: marquee 38s linear infinite; }
.ticker-track span { margin: 0 28px; font-size: 14px; letter-spacing: .5px; }
.ticker-track span b { color: var(--gd); }
.ticker:hover .ticker-track { animation-play-state: paused; }

/* ── KPIs ── */
.kpis { display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 14px; margin: 18px 0 6px; }
.kpi {
  position: relative; padding: 18px 18px 16px; border-radius: 18px; background: var(--card); border: 1px solid var(--line);
  overflow: hidden; transition: transform .25s ease, border-color .25s ease, box-shadow .25s ease; animation: rise .7s ease both;
}
.kpi::after { content: ""; position: absolute; left: 0; right: 0; bottom: 0; height: 3px; background: var(--accent); box-shadow: 0 0 14px var(--accent); }
.kpi:hover { transform: translateY(-5px); border-color: var(--accent); box-shadow: 0 10px 40px -12px var(--accent); }
.kpi .lbl { font-size: 12px; letter-spacing: 1.6px; text-transform: uppercase; color: var(--muted); }
.kpi .val { font-family: 'Anton', sans-serif; font-size: 42px; line-height: 1.05; margin-top: 6px; color: #fff; }
.kpi .val.count { animation: count 2.2s cubic-bezier(.2,.8,.2,1) forwards; counter-reset: n var(--n); }
.kpi .val.count::after { content: counter(n); }
.kpi .sub { font-size: 12.5px; color: var(--muted); margin-top: 2px; }

/* ── Secciones ── */
.sec { margin: 34px 0 10px; animation: rise .7s ease both; }
.sec h2 { font-family: 'Anton', sans-serif; font-size: 34px; letter-spacing: .6px; text-transform: uppercase; margin: 0; }
.sec .bar { width: 120px; height: 4px; border-radius: 4px; margin-top: 8px; background: linear-gradient(90deg, var(--mg), var(--gd), var(--cy)); background-size: 200% 100%; animation: slide 4s linear infinite; }
.sec p { color: var(--muted); margin-top: 10px; max-width: 820px; }
.note { color: var(--muted); font-size: 12.5px; margin-top: 6px; }

/* ── Tarjetas genéricas ── */
.grid { display: grid; gap: 16px; }
.g2 { grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); }
.g3 { grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); }
.g5 { grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); }
.card {
  position: relative; padding: 20px; border-radius: 20px; background: var(--card); border: 1px solid var(--line);
  transition: transform .25s ease, box-shadow .25s ease, border-color .25s ease; animation: rise .7s ease both; overflow: hidden;
}
.card:hover { transform: translateY(-4px); border-color: var(--accent, var(--cy)); box-shadow: 0 16px 50px -20px var(--accent, var(--cy)); }
.card h3 { margin: 0 0 6px; font-size: 20px; }
.card .meta { color: var(--muted); font-size: 13px; }
.tag { display: inline-block; font-size: 11px; letter-spacing: 1.5px; text-transform: uppercase; padding: 4px 10px; border-radius: 999px; border: 1px solid var(--accent, var(--cy)); color: var(--accent, var(--cy)); }

/* ── Partido ── */
.match { --accent: var(--gd); }
.match .teams { display: grid; grid-template-columns: 1fr auto 1fr; align-items: center; gap: 10px; margin: 18px 0 14px; text-align: center; }
.match .tm { font-size: 18px; font-weight: 700; }
.match .tm .fl { font-size: 46px; display: block; line-height: 1.1; }
.match .score { font-family: 'Anton', sans-serif; font-size: 64px; letter-spacing: 2px; background: linear-gradient(180deg, #fff, var(--accent)); -webkit-background-clip: text; background-clip: text; color: transparent; }
.match .row { display: flex; justify-content: space-between; border-top: 1px dashed var(--line); padding: 8px 0; font-size: 14px; }
.match .row span:first-child { color: var(--muted); }

/* ── Podio ── */
.podium { display: flex; align-items: flex-end; justify-content: center; gap: 14px; height: 300px; margin: 10px 0 0; }
.step { width: 30%; max-width: 210px; text-align: center; }
.step .who { font-size: 15px; font-weight: 700; margin-bottom: 8px; }
.step .who .fl { font-size: 44px; display: block; }
.step .blk {
  border-radius: 16px 16px 4px 4px; transform-origin: bottom; animation: grow 1.1s cubic-bezier(.2,.8,.2,1) both;
  display: flex; align-items: flex-start; justify-content: center; padding-top: 12px;
  font-family: 'Anton', sans-serif; font-size: 40px; color: #06060B;
}
.step.p1 .blk { height: 170px; background: linear-gradient(180deg, var(--gd), #b89400); animation-delay: .5s; box-shadow: 0 0 40px -6px var(--gd); }
.step.p2 .blk { height: 120px; background: linear-gradient(180deg, #e8e8f0, #8d8da0); animation-delay: .25s; }
.step.p3 .blk { height: 90px; background: linear-gradient(180deg, var(--or), #a34d00); }
.step.p1 .who .fl { animation: pulse 2.4s infinite; border-radius: 50%; display: inline-block; }

/* ── Estadios ── */
.stad { position: relative; border-radius: 20px; overflow: hidden; border: 1px solid var(--line); background: #0d0d16; aspect-ratio: 4/3; animation: rise .7s ease both; }
.stad img { width: 100%; height: 100%; object-fit: cover; transition: transform .6s ease, filter .6s ease; filter: saturate(1.1) brightness(.78); }
.stad:hover img { transform: scale(1.08); filter: saturate(1.3) brightness(.95); }
.stad .ph { width: 100%; height: 100%; background: linear-gradient(135deg, var(--accent), #0d0d16 70%); }
.stad .ov { position: absolute; inset: auto 0 0 0; padding: 14px 16px; background: linear-gradient(0deg, rgba(0,0,0,.92), transparent); }
.stad .ov h4 { margin: 0; font-size: 17px; }
.stad .ov .m { font-size: 12.5px; color: #cfcfe0; }
.stad .badge { position: absolute; top: 12px; right: 12px; background: rgba(0,0,0,.6); border: 1px solid var(--accent); color: var(--accent); font-size: 11px; padding: 4px 9px; border-radius: 999px; letter-spacing: 1px; backdrop-filter: blur(6px); }
.stad .cty { position: absolute; top: 12px; left: 12px; font-size: 22px; }

/* ── Mascotas ── */
.masc { text-align: center; padding: 26px 20px; }
.masc .emo { font-size: 84px; display: inline-block; animation: float 3.4s ease-in-out infinite; filter: drop-shadow(0 0 22px var(--accent)); }
.masc h3 { font-family: 'Anton', sans-serif; font-size: 38px; letter-spacing: 3px; margin: 6px 0 2px; color: var(--accent); text-shadow: 0 0 18px var(--accent); }

/* ── Arqueros ── */
.gk .rank { font-family: 'Anton', sans-serif; font-size: 54px; line-height: 1; color: transparent; -webkit-text-stroke: 1.5px var(--accent); }
.gk .ga { font-family: 'Anton', sans-serif; font-size: 30px; color: var(--accent); }

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] { gap: 6px; flex-wrap: wrap; border-bottom: 1px solid var(--line); }
.stTabs [data-baseweb="tab"] { background: var(--card); border: 1px solid var(--line); border-radius: 999px; padding: 8px 16px; height: auto; transition: all .2s ease; }
.stTabs [data-baseweb="tab"]:hover { border-color: var(--cy); color: var(--cy); }
.stTabs [aria-selected="true"] { background: linear-gradient(90deg, rgba(255,46,147,.25), rgba(0,229,255,.25)); border-color: var(--mg); }
.stTabs [data-baseweb="tab-highlight"], .stTabs [data-baseweb="tab-border"] { display: none; }

[data-testid="stMetric"] { background: var(--card); border: 1px solid var(--line); border-radius: 16px; padding: 14px; }
.foot { color: var(--muted); font-size: 12.5px; text-align: center; margin: 50px 0 20px; line-height: 1.7; }
a { color: var(--cy) !important; }

@media (max-width: 760px) {
  .neon-badge { width: 74px; height: 74px; top: 58px; right: 12px; }
  .neon-core { width: 66px; height: 66px; }
  .neon-core .n26 { font-size: 28px; }
  .neon-core .wc { font-size: 6px; letter-spacing: 1.4px; }
  .neon-core .hosts { display: none; }
  .hero { padding-right: 84px; }
  .match .score { font-size: 46px; }
}
</style>
"""

BADGE = (
    '<div class="neon-badge" title="Mundial 2026 · Canadá · México · EE.UU.">'
    '<i class="spark s1"></i><i class="spark s2"></i><i class="spark s3"></i><i class="spark s4"></i>'
    '<div class="neon-core"><div class="n26">26</div><div class="wc">WORLD CUP</div>'
    '<div class="hosts">CAN · MEX · USA</div></div></div>'
)


def html(s: str):
    st.markdown(s, unsafe_allow_html=True)


def section(title: str, text: str = ""):
    html(f'<div class="sec"><h2>{title}</h2><div class="bar"></div>{f"<p>{text}</p>" if text else ""}</div>')


def kpi(label, value, sub="", accent=C["cyan"], count=False, delay=0.0):
    val = f'<div class="val count" style="--to:{int(value)}"></div>' if count else f'<div class="val">{value}</div>'
    return (f'<div class="kpi" style="--accent:{accent};animation-delay:{delay}s">'
            f'<div class="lbl">{label}</div>{val}<div class="sub">{sub}</div></div>')


def style_fig(fig, height=430, legend=True):
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Space Grotesk, sans-serif", color=C["ink"], size=13),
        height=height,
        margin=dict(l=10, r=10, t=50, b=10),
        hoverlabel=dict(bgcolor="#11111b", bordercolor=C["cyan"], font=dict(family="Space Grotesk", color="#fff")),
        showlegend=legend,
        legend=dict(bgcolor="rgba(0,0,0,0)", orientation="h", y=1.08, x=0),
        title_font=dict(family="Anton, sans-serif", size=20),
        transition=dict(duration=600, easing="cubic-in-out"),
    )
    fig.update_xaxes(gridcolor="rgba(255,255,255,0.06)", zerolinecolor="rgba(255,255,255,0.12)")
    fig.update_yaxes(gridcolor="rgba(255,255,255,0.06)", zerolinecolor="rgba(255,255,255,0.12)")
    return fig


def show(fig, key=None):
    st.plotly_chart(fig, width="stretch", config={"displaylogo": False, "displayModeBar": False}, key=key)


# ──────────────────────────────────────────────────────────────────────────────
# PÁGINA
# ──────────────────────────────────────────────────────────────────────────────
html(CSS)
html(BADGE)

df = teams_df()
rdf = routes_df()
sum_gf = int(df["gf"].sum())
own_goals = TOTAL_GOALS - sum_gf

html(
    '<div class="hero">'
    '<div class="kicker">FIFA World Cup <b>2026</b> · Análisis cuantitativo</div>'
    '<div class="title">El Mundial<br><span class="grad">más grande de la historia</span></div>'
    '<div class="subtitle">48 selecciones, 3 países anfitriones, 16 estadios y 104 partidos en 39 días. '
    'Un recorrido por los números que dejó Norteamérica 2026: goles, figuras, arqueros, dinero y kilómetros.</div>'
    '<div class="chips"><span class="chip">🗓️ 11 jun – 19 jul 2026</span><span class="chip">🇨🇦 🇲🇽 🇺🇸 Sede tripartita</span>'
    '<span class="chip">🏆 Campeón: 🇪🇸 España</span><span class="chip">⚽ 308 goles</span></div>'
    '</div>'
)

ticker_items = [
    "🏆 <b>España</b> campeona por 2ª vez: 1-0 a Argentina en tiempo suplementario",
    "⚽ <b>Ferran Torres</b> marcó el gol del título en el minuto 106",
    "👟 <b>Mbappé</b>: Bota de Oro con 10 goles y máximo goleador histórico de los Mundiales (22)",
    "🎯 <b>Olise</b>: 7 asistencias, récord para una sola edición desde 1966",
    "🧤 <b>Unai Simón</b>: 1 gol recibido en 8 partidos",
    "🏟️ <b>6,66 M</b> de espectadores en 102 partidos, récord absoluto",
    "🇨🇻 <b>Cabo Verde</b>: debutante que pasó de grupo con tres empates",
    "🇳🇴 <b>Noruega</b> llegó por primera vez a cuartos",
    "🔥 <b>Inglaterra 6-4 Francia</b>: el partido por el 3° puesto más loco",
]
track = "".join(f"<span>{t}</span>" for t in ticker_items)
html(f'<div class="ticker"><div class="ticker-track">{track}{track}</div></div>')

html(
    '<div class="kpis">'
    + kpi("Partidos", TOTAL_MATCHES, "Récord: 64 en Qatar 2022", C["magenta"], True, 0)
    + kpi("Goles", TOTAL_GOALS, f"{TOTAL_GOALS / TOTAL_MATCHES:.2f} por partido", C["lime"], True, .08)
    + kpi("Selecciones", 48, "Primer Mundial de 48", C["cyan"], True, .16)
    + kpi("Estadios", 16, "11 EE.UU. · 3 MEX · 2 CAN", C["orange"], True, .24)
    + kpi("Jugadores", TOTAL_PLAYERS, "usados en el torneo", C["violet"], True, .32)
    + kpi("Público", "6,67 M", f"Promedio {AVG_ATT:,} · 99,7% ocupación".replace(",", "."), C["gold"], False, .40)
    + '</div>'
)

tabs = st.tabs([
    "🏆 Resumen", "🏟️ Sedes y estadios", "✈️ Rutas aéreas", "🎬 Inaugural y final",
    "🧸 Mascotas", "⭐ Jugadores", "📊 Selecciones", "💰 Valor de planteles", "🧤 Arqueros", "🧪 Más datos",
])

# ───────────────────────────── 1. RESUMEN ─────────────────────────────
with tabs[0]:
    section("El podio", "Por primera vez los cuatro semifinalistas eran excampeones del mundo.")
    html(
        '<div class="podium">'
        '<div class="step p2"><div class="who"><span class="fl">🇦🇷</span>Argentina</div><div class="blk">2</div></div>'
        '<div class="step p1"><div class="who"><span class="fl">🇪🇸</span>España</div><div class="blk">1</div></div>'
        '<div class="step p3"><div class="who"><span class="fl">🏴󠁧󠁢󠁥󠁮󠁧󠁿</span>Inglaterra</div><div class="blk">3</div></div>'
        '</div><div class="note" style="text-align:center">4° puesto: 🇫🇷 Francia (perdió 6-4 con Inglaterra en Miami)</div>'
    )

    section("Premios individuales")
    awards = [
        ("Balón de Oro", "Rodri", "🇪🇸 España", "Capitán y cerebro del campeón invicto. Plata: Messi · Bronce: Mbappé.", C["gold"]),
        ("Bota de Oro", "Kylian Mbappé", "🇫🇷 Francia", "10 goles en 8 partidos. Primero en ganarla en dos Mundiales seguidos.", C["lime"]),
        ("Guante de Oro", "Unai Simón", "🇪🇸 España", "7 vallas invictas y un solo gol recibido (ante Bélgica).", C["cyan"]),
        ("Mejor Jugador Joven", "Pau Cubarsí", "🇪🇸 España", "19 años. Jugó todos los minutos de la campaña campeona.", C["magenta"]),
    ]
    html('<div class="grid g5">' + "".join(
        f'<div class="card" style="--accent:{a};animation-delay:{i*.08}s"><span class="tag">{t}</span>'
        f'<h3 style="margin-top:12px">{n}</h3><div class="meta">{c}</div><p style="font-size:14px;margin:10px 0 0">{d}</p></div>'
        for i, (t, n, c, d, a) in enumerate(awards)) + '</div>')
    html('<div class="note">Premio Fair Play: 🇳🇱 Países Bajos.</div>')

    section("¿Hasta dónde llegó cada confederación?", "Selecciones por instancia máxima alcanzada.")
    stage_conf = df.groupby(["conf", "etapa"]).size().reset_index(name="selecciones")
    stage_conf["etapa"] = pd.Categorical(stage_conf["etapa"], STAGE_ORDER, ordered=True)
    stage_conf = stage_conf.sort_values("etapa")
    fig = px.bar(stage_conf, x="etapa", y="selecciones", color="conf", color_discrete_map=CONF_COLORS,
                 category_orders={"etapa": STAGE_ORDER}, text_auto=True)
    fig.update_traces(marker_line_width=0)
    fig.update_layout(barmode="stack", xaxis_title=None, yaxis_title="Selecciones", legend_title=None)
    show(style_fig(fig, 420), "stage_conf")

# ───────────────────────────── 2. SEDES ─────────────────────────────
with tabs[1]:
    section("Tres países, dieciséis ciudades",
            "El primer Mundial organizado por tres naciones. EE.UU. tuvo la mayoría de las sedes y todos los partidos desde cuartos de final.")
    c1, c2 = st.columns([1.5, 1])
    with c1:
        fig = go.Figure()
        for pais, col in [("EE.UU.", C["cyan"]), ("México", C["mint"]), ("Canadá", C["red"])]:
            d = STADIUMS[STADIUMS["pais"] == pais]
            fig.add_trace(go.Scattergeo(
                lon=d["lon"], lat=d["lat"], name=pais, mode="markers+text",
                text=d["ciudad"].str.split(" ").str[0], textposition="top center",
                textfont=dict(color="#fff", size=11),
                marker=dict(size=d["capacidad"] / 3200, color=col, opacity=.85,
                            line=dict(width=2, color="rgba(255,255,255,.7)")),
                customdata=d[["estadio", "ciudad", "capacidad", "partidos"]],
                hovertemplate="<b>%{customdata[0]}</b><br>%{customdata[1]}<br>Capacidad ≈ %{customdata[2]:,}<br>Partidos: %{customdata[3]}<extra></extra>",
            ))
        fig.update_geos(scope="north america", projection_type="natural earth", showland=True, landcolor="#12121c",
                        showocean=True, oceancolor="#06060B", showcountries=True, countrycolor="rgba(255,255,255,.25)",
                        showlakes=False, bgcolor="rgba(0,0,0,0)", lataxis_range=[14, 55], lonaxis_range=[-130, -62],
                        showsubunits=True, subunitcolor="rgba(255,255,255,.08)")
        fig.update_layout(title="Mapa de sedes (tamaño = capacidad)")
        show(style_fig(fig, 470), "host_map")
    with c2:
        by_country = STADIUMS.groupby("pais").agg(estadios=("key", "count"), partidos=("partidos", "sum")).reset_index()
        fig = go.Figure(go.Pie(
            labels=by_country["pais"], values=by_country["partidos"], hole=.62,
            marker=dict(colors=[C["red"], C["cyan"], C["mint"]], line=dict(color="#06060B", width=3)),
            textinfo="label+value", pull=[0.04, 0, 0.04],
            hovertemplate="%{label}: %{value} partidos<extra></extra>",
        ))
        fig.update_layout(title="Partidos por país",
                          annotations=[dict(text="104<br>partidos", showarrow=False, font=dict(size=20, family="Anton"))])
        show(style_fig(fig, 470, legend=False), "host_pie")

    section("Los 16 estadios", "Pasá el mouse sobre cada foto. Imágenes de referencia de Wikimedia Commons.")
    thumbs = all_thumbs(tuple(STADIUMS["wiki"]))
    flag = {"EE.UU.": "🇺🇸", "México": "🇲🇽", "Canadá": "🇨🇦"}
    accent = {"EE.UU.": C["cyan"], "México": C["mint"], "Canadá": C["red"]}
    order = STADIUMS.sort_values("partidos", ascending=False)
    cards = []
    for i, r in enumerate(order.itertuples()):
        src = thumbs.get(r.wiki)
        media = f'<img src="{src}" alt="{r.estadio}" loading="lazy">' if src else '<div class="ph"></div>'
        cards.append(
            f'<div class="stad" style="--accent:{accent[r.pais]};animation-delay:{(i % 8) * .05}s">{media}'
            f'<span class="cty">{flag[r.pais]}</span><span class="badge">{r.partidos} PARTIDOS</span>'
            f'<div class="ov"><h4>{r.estadio}</h4><div class="m">{r.ciudad} · ≈{r.capacidad:,} lugares</div></div></div>'.replace(",", ".")
        )
    html('<div class="grid g3">' + "".join(cards) + '</div>')

    section("Ciudades sede: datos básicos")
    city_tbl = STADIUMS[["ciudad", "pais", "estadio", "nombre_fifa", "capacidad", "partidos", "pob_metro_m", "dato"]].sort_values(
        "partidos", ascending=False)
    st.dataframe(
        city_tbl, hide_index=True, width="stretch",
        column_config={
            "ciudad": "Ciudad", "pais": "País", "estadio": "Estadio", "nombre_fifa": "Nombre FIFA en el torneo",
            "capacidad": st.column_config.NumberColumn("Capacidad aprox.", format="%d"),
            "partidos": st.column_config.ProgressColumn("Partidos", min_value=0, max_value=9, format="%d"),
            "pob_metro_m": st.column_config.NumberColumn("Población metro (M, aprox.)", format="%.1f"),
            "dato": st.column_config.TextColumn("Dato curioso", width="large"),
        },
    )
    html('<div class="note">Durante el torneo la FIFA usó nombres neutros (sin patrocinadores). Capacidades y poblaciones son aproximadas.</div>')

# ───────────────────────────── 3. RUTAS ─────────────────────────────
with tabs[2]:
    section("Kilómetros de campeonato",
            "El recorrido aéreo de España, Argentina e Inglaterra de estadio en estadio. "
            "Cada línea es un traslado entre sedes de partido (distancia en círculo máximo).")
    c1, c2 = st.columns([1, 2.2])
    with c1:
        teams_sel = st.multiselect("Selecciones", list(ROUTES.keys()), default=list(ROUTES.keys()))
        step = st.slider("Avanzar el torneo partido a partido", 1, 8, 8,
                         help="Mové el control para ver cómo se fue armando cada ruta.")
        anim = st.toggle("Mostrar números de partido", value=True)
        km = rdf[rdf["n"] <= step].groupby("equipo")["km_tramo"].sum()
        for t in teams_sel:
            st.metric(f'{ROUTES[t]["flag"]} {t}', f"{int(km.get(t, 0)):,} km".replace(",", "."),
                      f'{int((rdf[(rdf.equipo == t) & (rdf.n <= step)].km_tramo > 0).sum())} vuelos')
    with c2:
        fig = go.Figure()
        for t in teams_sel:
            d = rdf[(rdf["equipo"] == t) & (rdf["n"] <= step)]
            col = ROUTES[t]["color"]
            fig.add_trace(go.Scattergeo(
                lon=d["lon"], lat=d["lat"], mode="lines", name=t,
                line=dict(width=7, color=col), opacity=.18, hoverinfo="skip", showlegend=False))
            fig.add_trace(go.Scattergeo(
                lon=d["lon"], lat=d["lat"], mode="lines+markers+text" if anim else "lines+markers", name=f'{ROUTES[t]["flag"]} {t}',
                line=dict(width=2.5, color=col), marker=dict(size=11, color=col, line=dict(width=2, color="#06060B")),
                text=d["n"].astype(str), textposition="top right", textfont=dict(color=col, size=12),
                customdata=d[["etapa", "rival", "resultado", "estadio", "ciudad", "km_tramo"]],
                hovertemplate="<b>%{customdata[0]}</b> vs %{customdata[1]} · %{customdata[2]}<br>"
                              "%{customdata[3]} · %{customdata[4]}<br>Tramo: %{customdata[5]:,} km<extra>" + t + "</extra>",
            ))
        fig.update_geos(scope="north america", projection_type="natural earth", showland=True, landcolor="#12121c",
                        showocean=True, oceancolor="#06060B", showcountries=True, countrycolor="rgba(255,255,255,.25)",
                        bgcolor="rgba(0,0,0,0)", lataxis_range=[15, 50], lonaxis_range=[-125, -65],
                        showsubunits=True, subunitcolor="rgba(255,255,255,.08)")
        show(style_fig(fig, 560), "routes_map")

    tot = rdf.groupby("equipo")["km_tramo"].sum().reset_index().sort_values("km_tramo")
    fig = px.bar(tot, x="km_tramo", y="equipo", orientation="h", text="km_tramo",
                 color="equipo", color_discrete_map={k: v["color"] for k, v in ROUTES.items()})
    fig.update_traces(texttemplate="%{text:,} km", textposition="outside", marker_line_width=0)
    fig.update_layout(title="Distancia total recorrida entre sedes", xaxis_title="km", yaxis_title=None)
    show(style_fig(fig, 280, legend=False), "km_bar")

    pick = st.radio("Itinerario detallado", list(ROUTES.keys()), horizontal=True)
    st.dataframe(
        rdf[rdf["equipo"] == pick][["n", "etapa", "rival", "resultado", "estadio", "ciudad", "km_tramo", "km_acum"]],
        hide_index=True, width="stretch",
        column_config={"n": "#", "etapa": "Instancia", "rival": "Rival", "resultado": "Resultado", "estadio": "Estadio",
                       "ciudad": "Ciudad", "km_tramo": st.column_config.NumberColumn("Vuelo (km)", format="%d"),
                       "km_acum": st.column_config.ProgressColumn("Acumulado (km)", min_value=0,
                                                                  max_value=int(rdf.km_acum.max()), format="%d")},
    )
    html('<div class="note">No incluye los viajes entre campamentos base y estadios. Resultados desde la óptica de cada selección.</div>')

# ───────────────────────────── 4. INAUGURAL Y FINAL ─────────────────────────────
with tabs[3]:
    section("Los dos partidos que abrieron y cerraron la historia")

    def match_card(tag, home, hf, away, af, score, rows, accent):
        rws = "".join(f'<div class="row"><span>{k}</span><span>{v}</span></div>' for k, v in rows)
        return (f'<div class="card match" style="--accent:{accent}"><span class="tag">{tag}</span>'
                f'<div class="teams"><div class="tm"><span class="fl">{hf}</span>{home}</div>'
                f'<div class="score">{score}</div><div class="tm"><span class="fl">{af}</span>{away}</div></div>{rws}</div>')

    html('<div class="grid g2">'
         + match_card("Partido inaugural · 11 jun 2026", "México", "🇲🇽", "Sudáfrica", "🇿🇦", "2-0", [
             ("Estadio", "Estadio Azteca · Ciudad de México"),
             ("Asistencia", "80.824 espectadores"),
             ("Goles", "Julián Quiñones 9' · Raúl Jiménez 67'"),
             ("Expulsados", "Sithole y Zwane (RSA) · Montes (MEX)"),
             ("Dato", "Primera inauguración con 3 rojas · revancha del debut de 2010"),
         ], C["mint"])
         + match_card("Final · 19 jul 2026", "España", "🇪🇸", "Argentina", "🇦🇷", "1-0", [
             ("Estadio", "MetLife Stadium · Nueva York/Nueva Jersey"),
             ("Asistencia", "80.663 espectadores"),
             ("Gol", "Ferran Torres 106' (tiempo suplementario)"),
             ("Expulsado", "Enzo Fernández (ARG) · doble amarilla 90+3'"),
             ("Dato", "Dibu Martínez hizo 11 atajadas · 2° título de España"),
         ], C["gold"])
         + '</div>')

    section("Asistencia: inauguración vs final")
    att = pd.DataFrame({"partido": ["Inaugural · Azteca", "Final · MetLife", "Promedio del torneo"],
                        "asistencia": [80824, 80663, AVG_ATT]})
    fig = px.bar(att, x="partido", y="asistencia", text="asistencia", color="partido",
                 color_discrete_sequence=[C["mint"], C["gold"], C["violet"]])
    fig.update_traces(texttemplate="%{text:,}", textposition="outside", marker_line_width=0)
    fig.update_layout(yaxis_title="Espectadores", xaxis_title=None, yaxis_range=[0, 95000])
    show(style_fig(fig, 360, legend=False), "att_bar")

    section("Bonus: el partido más loco", "Por el 3° puesto en Miami: Inglaterra 6-4 Francia. Saka hizo un hat-trick y Mbappé llegó a 22 goles en Mundiales, récord histórico.")

# ───────────────────────────── 5. MASCOTAS ─────────────────────────────
with tabs[4]:
    section("Maple, Zayu y Clutch", "Por primera vez un Mundial tuvo tres mascotas oficiales, una por país anfitrión.")
    html('<div class="grid g3">' + "".join(
        f'<div class="card masc" style="--accent:{acc};animation-delay:{i*.12}s"><div class="emo">{emo}</div>'
        f'<h3>{name}</h3><div class="meta">{animal} · {flag_} {pais}</div>'
        f'<div style="margin:12px 0"><span class="tag">{pos}</span></div><p style="font-size:14px">{desc}</p></div>'
        for i, (name, animal, emo, pais, flag_, pos, acc, desc) in enumerate(MASCOTS)) + '</div>')
    st.link_button("🖼️ Ver imágenes oficiales de las mascotas (FIFA)",
                   "https://www.fifa.com/en/tournaments/mens/worldcup/canadamexicousa2026", width="stretch")
    html('<div class="note">Las ilustraciones oficiales son propiedad de FIFA; acá se muestran íconos de referencia del animal de cada mascota.</div>')

# ───────────────────────────── 6. JUGADORES ─────────────────────────────
with tabs[5]:
    section("Top 10 goleadores", "Mbappé ganó la Bota de Oro y superó a Klose y a Messi como máximo goleador histórico de los Mundiales.")
    sc = pd.DataFrame(SCORERS, columns=["jugador", "pais", "flag", "goles", "asist"])
    sc["label"] = sc["flag"] + " " + sc["jugador"]
    c1, c2 = st.columns([1.4, 1])
    with c1:
        d = sc.iloc[::-1]
        fig = go.Figure(go.Bar(
            x=d["goles"], y=d["label"], orientation="h", text=d["goles"], textposition="outside",
            marker=dict(color=d["goles"], colorscale=[[0, C["violet"]], [.5, C["magenta"]], [1, C["gold"]]],
                        line=dict(width=0)),
            hovertemplate="%{y}: %{x} goles<extra></extra>"))
        fig.update_layout(title="Goles", xaxis_title=None, yaxis_title=None)
        show(style_fig(fig, 470, legend=False), "scorers")
    with c2:
        fig = px.scatter(sc, x="asist", y="goles", size=sc["goles"] + sc["asist"], color="pais", text="jugador",
                         color_discrete_sequence=NEON, size_max=46)
        fig.update_traces(textposition="top center", textfont=dict(size=10), marker=dict(line=dict(width=0)))
        fig.update_layout(title="Goles vs asistencias", xaxis_title="Asistencias", yaxis_title="Goles", showlegend=False)
        show(style_fig(fig, 470, legend=False), "ga_scatter")

    section("Top 10 asistidores", "Michael Olise rompió el récord de asistencias en una sola edición (desde que hay registros, 1966).")
    asd = pd.DataFrame(ASSISTERS, columns=["jugador", "pais", "flag", "asist"])
    asd["label"] = asd["flag"] + " " + asd["jugador"]
    d = asd.iloc[::-1]
    fig = go.Figure(go.Bar(
        x=d["asist"], y=d["label"], orientation="h", text=d["asist"], textposition="outside",
        marker=dict(color=d["asist"], colorscale=[[0, C["cyan"]], [1, C["lime"]]], line=dict(width=0)),
        hovertemplate="%{y}: %{x} asistencias<extra></extra>"))
    fig.update_layout(xaxis_title=None, yaxis_title=None)
    show(style_fig(fig, 440, legend=False), "assists")

    section("Las figuras")
    stars = [
        ("Rodri", "🇪🇸", "Balón de Oro", "Dirigió el mediocampo de un campeón que recibió un solo gol.", C["gold"]),
        ("Lionel Messi", "🇦🇷", "Balón de Plata", "8 goles y 4 asistencias a los 39 años; llegó a 12 asistencias en Mundiales.", C["cyan"]),
        ("Kylian Mbappé", "🇫🇷", "Bota de Oro", "10 goles, primer jugador con 10 en una edición desde Gerd Müller (1970).", C["lime"]),
        ("Jude Bellingham", "🏴󠁧󠁢󠁥󠁮󠁧󠁿", "7 goles", "Primer inglés en marcar 7 en un Mundial; doblete ante Noruega y México.", C["magenta"]),
        ("Michael Olise", "🇫🇷", "7 asistencias", "Récord en una sola Copa: superó las 6 de Pelé en 1970.", C["orange"]),
        ("Erling Haaland", "🇳🇴", "7 goles", "Llevó a Noruega a sus primeros cuartos de final; doblete a Brasil.", C["violet"]),
    ]
    html('<div class="grid g3">' + "".join(
        f'<div class="card" style="--accent:{a};animation-delay:{i*.06}s"><span class="tag">{t}</span>'
        f'<h3 style="margin-top:12px">{f} {n}</h3><p style="font-size:14px;margin:6px 0 0;color:#cfcfe0">{d_}</p></div>'
        for i, (n, f, t, d_, a) in enumerate(stars)) + '</div>')

# ───────────────────────────── 7. SELECCIONES ─────────────────────────────
with tabs[6]:
    section("Goles por selección",
            f"Las 48 selecciones sumaron {sum_gf} goles (incluye los 14 goles en contra, acreditados al rival). Qatar y Egipto fueron los que más se hicieron en contra: 2 cada uno.")
    c1, c2, c3 = st.columns([2, 1, 1])
    confs = c1.multiselect("Confederación", list(CONF_COLORS.keys()), default=list(CONF_COLORS.keys()))
    metric = c2.selectbox("Métrica", ["Goles a favor", "Goles en contra", "Diferencia de gol", "Goles por partido"])
    asc = c3.toggle("Orden ascendente", value=False)
    mcol = {"Goles a favor": "gf", "Goles en contra": "gc", "Diferencia de gol": "dif", "Goles por partido": "gf_pp"}[metric]
    d = df[df["conf"].isin(confs)].sort_values(mcol, ascending=asc)
    fig = px.bar(d, x="label", y=mcol, color="conf", color_discrete_map=CONF_COLORS, text=mcol,
                 hover_data={"label": False, "pj": True, "etapa": True})
    fig.update_traces(textposition="outside", marker_line_width=0, cliponaxis=False)
    fig.update_layout(xaxis_title=None, yaxis_title=metric, legend_title=None, xaxis_tickangle=-55)
    show(style_fig(fig, 520), "goals_team")

    section("Ataque vs defensa", "Cada burbuja es una selección (tamaño = partidos jugados). Arriba a la izquierda: mucho gol y poco recibido.")
    fig = px.scatter(df, x="gc_pp", y="gf_pp", size="pj", color="conf", color_discrete_map=CONF_COLORS,
                     hover_name="label", text=df["seleccion"].where(df["pj"] >= 5, ""),
                     hover_data={"gf": True, "gc": True, "etapa": True, "gf_pp": False, "gc_pp": False, "pj": True, "conf": False},
                     size_max=34)
    fig.add_hline(y=df["gf_pp"].mean(), line_dash="dot", line_color="rgba(255,255,255,.35)")
    fig.add_vline(x=df["gc_pp"].mean(), line_dash="dot", line_color="rgba(255,255,255,.35)")
    fig.update_traces(textposition="top center", textfont=dict(size=10), marker=dict(line=dict(width=1, color="#06060B")))
    fig.update_layout(xaxis_title="Goles recibidos por partido", yaxis_title="Goles convertidos por partido", legend_title=None)
    show(style_fig(fig, 520), "att_def")

    c1, c2 = st.columns(2)
    with c1:
        section("¿Cuándo llegaron los goles?")
        halves = pd.DataFrame({"tiempo": ["1er tiempo", "2do tiempo + alargue"],
                               "goles": [int(df["gf_1t"].sum()), int(df["gf"].sum() - df["gf_1t"].sum())]})
        fig = go.Figure(go.Pie(labels=halves["tiempo"], values=halves["goles"], hole=.6,
                               marker=dict(colors=[C["cyan"], C["magenta"]], line=dict(color="#06060B", width=3)),
                               textinfo="percent+value"))
        show(style_fig(fig, 340), "halves")
    with c2:
        section("¿Cómo se hicieron?")
        heads = int(df["gf_cabeza"].sum())
        fig = go.Figure(go.Pie(labels=["Con el pie", "De cabeza"], values=[sum_gf - heads, heads], hole=.6,
                               marker=dict(colors=[C["lime"], C["orange"]], line=dict(color="#06060B", width=3)),
                               textinfo="percent+value"))
        show(style_fig(fig, 340), "heads")

    section("Estadística descriptiva", "Medidas resumen por selección (n = 48).")
    desc = df[["gf", "gc", "dif", "gf_pp", "gc_pp", "asist", "amarillas", "valor_usd"]].describe().T
    desc = desc.rename(index={"gf": "Goles a favor", "gc": "Goles en contra", "dif": "Diferencia de gol",
                              "gf_pp": "Goles/partido", "gc_pp": "Recibidos/partido", "asist": "Asistencias",
                              "amarillas": "Amarillas", "valor_usd": "Valor plantel (US$ M)"})
    desc = desc.rename(columns={"count": "n", "mean": "Media", "std": "Desvío", "min": "Mín", "25%": "Q1",
                                "50%": "Mediana", "75%": "Q3", "max": "Máx"})
    st.dataframe(desc.round(2), width="stretch")
    corr = df[["gf", "valor_usd"]].corr().iloc[0, 1]
    corr_gc = df[["gc_pp", "valor_usd"]].corr().iloc[0, 1]
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Goles por partido (torneo)", f"{TOTAL_GOALS / TOTAL_MATCHES:.2f}")
    m2.metric("Mediana goles por selección", f"{df['gf'].median():.1f}")
    m3.metric("Correlación valor ↔ goles", f"{corr:.2f}")
    m4.metric("Correlación valor ↔ recibidos/partido", f"{corr_gc:.2f}")

    fig = px.box(df, x="conf", y="gf", color="conf", color_discrete_map=CONF_COLORS, points="all", hover_name="label")
    fig.update_layout(title="Distribución de goles por confederación", xaxis_title=None, yaxis_title="Goles a favor")
    show(style_fig(fig, 420, legend=False), "box_conf")

# ───────────────────────────── 8. VALOR ─────────────────────────────
with tabs[7]:
    section("¿Cuánto valía cada plantel?",
            f"Valor de mercado de los 48 planteles en millones de dólares (Transfermarkt, convertido de euros a US$ {EUR_USD:.2f} por €).")
    total_usd = df["valor_usd"].sum()
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Valor total del Mundial", f"US$ {total_usd / 1000:,.1f} mil M")
    top = df.loc[df["valor_usd"].idxmax()]
    low = df.loc[df["valor_usd"].idxmin()]
    m2.metric("Más caro", f"{top['bandera']} {top['seleccion']}", f"US$ {top['valor_usd']:,.0f} M")
    m3.metric("Más barato", f"{low['bandera']} {low['seleccion']}", f"US$ {low['valor_usd']:,.0f} M", delta_color="off")
    m4.metric("Brecha más caro / más barato", f"{top['valor_usd'] / low['valor_usd']:.0f}x")

    c1, c2 = st.columns([1, 1])
    order_val = c1.radio("Orden", ["Más caro → más barato", "Más barato → más caro"], horizontal=True)
    n_top = c2.slider("Cantidad de selecciones", 5, 48, 48)
    d = df.sort_values("valor_usd", ascending=(order_val != "Más caro → más barato")).head(n_top)
    d = d.iloc[::-1]
    fig = go.Figure(go.Bar(
        x=d["valor_usd"], y=d["label"], orientation="h", text=d["valor_usd"],
        marker=dict(color=[CONF_COLORS[c] for c in d["conf"]], line=dict(width=0)),
        customdata=d[["etapa", "valor_eur"]],
        hovertemplate="<b>%{y}</b><br>US$ %{x:,.1f} M (€ %{customdata[1]:,.1f} M)<br>Llegó a: %{customdata[0]}<extra></extra>"))
    fig.update_traces(texttemplate="US$ %{text:,.0f} M", textposition="outside", cliponaxis=False)
    fig.update_layout(xaxis_title="Millones de US$", yaxis_title=None)
    show(style_fig(fig, max(380, 24 * len(d) + 80), legend=False), "value_bar")
    html('<div class="note">Colores por confederación: ' + " · ".join(
        f'<span style="color:{v}">■ {k}</span>' for k, v in CONF_COLORS.items()) + '</div>')

    c1, c2 = st.columns(2)
    with c1:
        section("Mapa de valor por confederación")
        fig = px.treemap(df, path=[px.Constant("Mundial 2026"), "conf", "label"], values="valor_usd",
                         color="conf", color_discrete_map={**CONF_COLORS, "(?)": "#222"})
        fig.update_traces(hovertemplate="<b>%{label}</b><br>US$ %{value:,.0f} M<extra></extra>",
                          marker=dict(line=dict(color="#06060B", width=2)), root_color="#0d0d16")
        show(style_fig(fig, 480, legend=False), "treemap")
    with c2:
        section("¿La plata hace goles?")
        fig = px.scatter(df, x="valor_usd", y="gf", color="conf", color_discrete_map=CONF_COLORS, size="pj",
                         hover_name="label", log_x=True, size_max=30,
                         text=df["seleccion"].where(df["valor_usd"] > 900, ""))
        fig.update_traces(textposition="top center", textfont=dict(size=10))
        fig.update_layout(xaxis_title="Valor del plantel (US$ M, escala log)", yaxis_title="Goles a favor", legend_title=None)
        show(style_fig(fig, 480), "money_goals")

    section("Eficiencia: dólares por gol", "Cuántos millones de valor de plantel 'costó' cada gol. Las selecciones sin goles quedan fuera.")
    eff = df.dropna(subset=["usd_por_gol"]).sort_values("usd_por_gol")
    pick = st.radio("Ver", ["Las 10 más eficientes", "Las 10 menos eficientes"], horizontal=True)
    e = eff.head(10) if pick.startswith("Las 10 más") else eff.tail(10)
    fig = px.bar(e, x="label", y="usd_por_gol", color="conf", color_discrete_map=CONF_COLORS, text="usd_por_gol")
    fig.update_traces(texttemplate="US$ %{text:.0f} M", textposition="outside", marker_line_width=0, cliponaxis=False)
    fig.update_layout(xaxis_title=None, yaxis_title="US$ M por gol", legend_title=None)
    show(style_fig(fig, 420), "eff")
    html('<div class="note">España, el campeón, fue el 3° plantel más caro. Francia, el más caro, terminó 4°.</div>')

# ───────────────────────────── 9. ARQUEROS ─────────────────────────────
with tabs[8]:
    section("Top 5: las vallas menos vencidas",
            "Criterio: menos goles recibidos; en caso de empate, más partidos jugados y luego más vallas invictas.")
    cols = [C["gold"], C["cyan"], C["mint"], C["magenta"], C["orange"]]
    html('<div class="grid g5">' + "".join(
        f'<div class="card gk" style="--accent:{cols[i]};animation-delay:{i*.08}s"><div class="rank">0{i+1}</div>'
        f'<h3 style="margin-top:6px">{fl} {team}</h3><div class="meta">🧤 {gk}</div>'
        f'<div style="margin-top:12px"><span class="ga">{ga}</span> <span class="meta">goles en {pj} PJ</span></div>'
        f'<p style="font-size:13px;color:#cfcfe0;margin:8px 0 0">{note}</p></div>'
        for i, (team, fl, gk, ga, pj, note) in enumerate(BEST_DEFENSE)) + '</div>')
    html('<div class="note">Con 3 goles recibidos también quedaron Ghana (4 PJ), Irán y Corea del Sur (3 PJ).</div>')

    bd = pd.DataFrame(BEST_DEFENSE, columns=["sel", "flag", "arquero", "gc", "pj", "nota"])
    bd["gc_pp"] = bd["gc"] / bd["pj"]
    bd["label"] = bd["flag"] + " " + bd["sel"] + " · " + bd["arquero"]
    fig = go.Figure()
    fig.add_trace(go.Bar(x=bd["label"], y=bd["pj"], name="Partidos jugados", marker_color="rgba(255,255,255,.12)"))
    fig.add_trace(go.Bar(x=bd["label"], y=bd["gc"], name="Goles recibidos", marker_color=cols, text=bd["gc"], textposition="outside"))
    fig.update_layout(barmode="overlay", yaxis_title=None, xaxis_title=None)
    show(style_fig(fig, 380), "best_def")

    c1, c2 = st.columns(2)
    with c1:
        section("Vallas invictas")
        cs = pd.DataFrame(CLEAN_SHEETS, columns=["arquero", "pais", "vi"]).iloc[::-1]
        fig = go.Figure(go.Bar(x=cs["vi"], y=cs["arquero"] + " (" + cs["pais"] + ")", orientation="h", text=cs["vi"],
                               textposition="outside",
                               marker=dict(color=cs["vi"], colorscale=[[0, C["violet"]], [1, C["mint"]]])))
        show(style_fig(fig, 430, legend=False), "cs")
    with c2:
        section("Más atajadas")
        sv = pd.DataFrame(SAVES, columns=["arquero", "pais", "atajadas"]).iloc[::-1]
        fig = go.Figure(go.Bar(x=sv["atajadas"], y=sv["arquero"] + " (" + sv["pais"] + ")", orientation="h",
                               text=sv["atajadas"], textposition="outside",
                               marker=dict(color=sv["atajadas"], colorscale=[[0, C["orange"]], [1, C["magenta"]]])))
        show(style_fig(fig, 430, legend=False), "saves")
    html('<div class="note">Orlando Gill (Paraguay) atajó dos penales en la tanda que eliminó a Alemania.</div>')

# ───────────────────────────── 10. MÁS DATOS ─────────────────────────────
with tabs[9]:
    section("Disciplina", "Tarjetas amarillas y rojas por selección.")
    disc = df.sort_values(["amarillas", "rojas"], ascending=False).head(15)
    fig = go.Figure()
    fig.add_trace(go.Bar(x=disc["label"], y=disc["amarillas"], name="Amarillas", marker_color=C["gold"]))
    fig.add_trace(go.Bar(x=disc["label"], y=disc["rojas"], name="Rojas", marker_color=C["red"]))
    fig.update_layout(barmode="group", xaxis_tickangle=-45, xaxis_title=None, yaxis_title="Tarjetas")
    show(style_fig(fig, 430), "cards")

    c1, c2 = st.columns(2)
    with c1:
        section("Récord de público")
        hist = pd.DataFrame({"mundial": ["EE.UU. 1994", "Rusia 2018 + Qatar 2022", "2026 (102 partidos)"],
                             "publico": [3_587_538, 6_436_020, ATTENDANCE_102]})
        fig = px.bar(hist, x="mundial", y="publico", text="publico", color="mundial",
                     color_discrete_sequence=[C["violet"], C["cyan"], C["lime"]])
        fig.update_traces(texttemplate="%{text:,}", textposition="outside", marker_line_width=0, cliponaxis=False)
        fig.update_layout(xaxis_title=None, yaxis_title="Espectadores")
        show(style_fig(fig, 400, legend=False), "att_hist")
    with c2:
        section("Capacidad vs partidos por estadio")
        fig = px.scatter(STADIUMS, x="capacidad", y="partidos", size="capacidad", color="pais", hover_name="estadio",
                         color_discrete_map={"EE.UU.": C["cyan"], "México": C["mint"], "Canadá": C["red"]}, size_max=30,
                         text="ciudad")
        fig.update_traces(textposition="top center", textfont=dict(size=9))
        fig.update_layout(xaxis_title="Capacidad aprox.", yaxis_title="Partidos", legend_title=None)
        show(style_fig(fig, 400), "cap_matches")

    section("Asistencias de equipo vs goles", "Francia fue la selección más 'asociada': 18 asistencias en 20 goles.")
    fig = px.scatter(df, x="asist", y="gf", color="conf", color_discrete_map=CONF_COLORS, hover_name="label",
                     text=df["seleccion"].where(df["gf"] >= 10, ""), size="pj", size_max=26)
    fig.add_trace(go.Scatter(x=[0, 20], y=[0, 20], mode="lines", line=dict(dash="dot", color="rgba(255,255,255,.3)"),
                             name="1 asistencia por gol"))
    fig.update_traces(textposition="top center", selector=dict(mode="markers+text"))
    fig.update_layout(xaxis_title="Asistencias", yaxis_title="Goles", legend_title=None)
    show(style_fig(fig, 460), "assist_goals")

    section("Explorador completo")
    q = st.text_input("Buscar selección", placeholder="Ej: Argentina")
    view = df if not q else df[df["seleccion"].str.contains(q, case=False)]
    st.dataframe(
        view[["label", "conf", "etapa", "pj", "gf", "gc", "dif", "asist", "amarillas", "rojas", "valor_usd"]]
        .sort_values("gf", ascending=False),
        hide_index=True, width="stretch",
        column_config={
            "label": "Selección", "conf": "Conf.", "etapa": "Llegó a", "pj": "PJ", "gf": "GF", "gc": "GC", "dif": "DIF",
            "asist": "Asist.", "amarillas": "🟨", "rojas": "🟥",
            "valor_usd": st.column_config.ProgressColumn("Valor (US$ M)", min_value=0,
                                                         max_value=float(df.valor_usd.max()), format="%.0f"),
        },
    )
    st.download_button("⬇️ Descargar datos (CSV)", df.drop(columns=["label"]).to_csv(index=False).encode("utf-8"),
                       "mundial2026_selecciones.csv", "text/csv", width="stretch")

html(
    '<div class="foot">Fuentes: FIFA · Al Jazeera · FOX Sports (estadísticas por equipo) · Transfermarkt vía Visual Capitalist '
    '(valores de mercado) · AP · ESPN · NBC Sports · Foot Africa · Wikimedia Commons (fotos de estadios).<br>'
    f'Valores en dólares convertidos a un tipo de cambio de referencia de US$ {EUR_USD:.2f} por euro. '
    'Proyecto independiente, sin afiliación con la FIFA.</div>'
)
