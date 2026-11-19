"""Builds data/competitions/2026-competitions.json from the normative participant lists.

This catalog is the "cataloged" layer: identifiers, participants, format, dates and
trophy asset ids. It does NOT claim motor implementation or validated calendars
beyond what is explicitly provided. Competitions without complete local data are
marked with the appropriate pending status.
"""
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "competitions" / "2026-competitions.json"
BRA = json.loads((ROOT / "data" / "competitions" / "2026-brazil.json").read_text(encoding="utf-8"))

# map Brazilian club display name -> id (from 2026-brazil.json)
BRA_ID = {}
for c in BRA["clubs"]:
    BRA_ID.setdefault(c["name"], c["id"])
# disambiguate by state when needed
BRA_BY_STATE = {(c["name"], c["state"]): c["id"] for c in BRA["clubs"]}


def bra(name, state=None):
    if state and (name, state) in BRA_BY_STATE:
        return BRA_BY_STATE[(name, state)]
    if name in BRA_ID:
        return BRA_ID[name]
    # fallback slug
    return "br-" + name.lower().replace(" ", "-").replace(".", "") + ("-xx" if not state else "-" + state.lower())


def foreign(country, name):
    slug = name.lower().replace(" ", "-").replace(".", "").replace("'", "").replace("ó", "o").replace("ú", "u").replace("á", "a").replace("é", "e").replace("í", "i").replace("ñ", "n").replace("ü", "u")
    return f"{country.lower()}-{slug}"


clubs: dict[str, dict] = {}


def reg_club(cid, name, country, extra=None):
    if cid not in clubs:
        clubs[cid] = {"clubId": cid, "officialName": name, "countryId": country}
        if extra:
            clubs[cid].update(extra)
    return cid


def bra_club(name, state=None):
    cid = bra(name, state)
    reg_club(cid, name, "BRA", {"state": state} if state else None)
    return cid


COMP = []


def add(c):
    # ensure participant club entries exist as foreign/bra already registered by caller? We'll register lazily.
    COMP.append(c)


# ---------- Brazil ----------
serie_a_names = ["Flamengo","São Paulo","Palmeiras","Atlético-MG","Fluminense","Grêmio","Botafogo","Cruzeiro","Corinthians","Bahia","Mirassol","Vasco da Gama","Internacional","Athletico-PR","Coritiba","Red Bull Bragantino","Vitória","Remo","Chapecoense","Santos"]
# map display names to brazil ids using known
name_state = {
 "Flamengo":("Flamengo","RJ"),"São Paulo":("São Paulo","SP"),"Palmeiras":("Palmeiras","SP"),
 "Atlético-MG":("Atlético Mineiro","MG"),"Fluminense":("Fluminense","RJ"),"Grêmio":("Grêmio","RS"),
 "Botafogo":("Botafogo","RJ"),"Cruzeiro":("Cruzeiro","MG"),"Corinthians":("Corinthians","SP"),
 "Bahia":("Bahia","BA"),"Mirassol":("Mirassol","SP"),"Vasco da Gama":("Vasco da Gama","RJ"),
 "Internacional":("Internacional","RS"),"Athletico-PR":("Athletico Paranaense","PR"),
 "Coritiba":("Coritiba","PR"),"Red Bull Bragantino":("Red Bull Bragantino","SP"),
 "Vitória":("Vitória","BA"),"Remo":("Remo","PA"),"Chapecoense":("Chapecoense","SC"),"Santos":("Santos","SP"),
}
serie_a_ids = []
for n in serie_a_names:
    nm, st = name_state[n]
    cid = bra(nm, st)
    reg_club(cid, nm, "BRA", {"shortName": n})
    serie_a_ids.append(cid)

add({
  "competitionId": "BRA_SERIE_A",
  "officialName": "Campeonato Brasileiro Série A",
  "displayName": "Brasileirão Série A 2026",
  "countryId": "BRA",
  "confederationId": "CONMEBOL",
  "competitionType": "league",
  "seasonId": "2026",
  "seasonStartDate": "2026-01-28",
  "seasonEndDate": "2026-12-06",
  "calendarType": "annual",
  "participantCount": 20,
  "participantIds": serie_a_ids,
  "competitionFormat": "round_robin_double",
  "stages": ["regular_season"],
  "round1Fixtures": [
    ("São Paulo","Flamengo"),("Atlético-MG","Palmeiras"),("Fluminense","Grêmio"),
    ("Botafogo","Cruzeiro"),("Corinthians","Bahia"),("Mirassol","Vasco da Gama"),
    ("Internacional","Athletico-PR"),("Coritiba","Red Bull Bragantino"),
    ("Vitória","Remo"),("Chapecoense","Santos"),
  ],
  "promotionRules": [],
  "relegationRules": ["bottom_4_to_BRA_SERIE_B"],
  "continentalQualificationRules": ["libertadores_and_sudamericana_slots"],
  "trophyAssetId": "tr_nacional_BRA.png",
  "status": "participants_complete_calendar_partial",
})

serie_b_names = ["Ceará","São Bernardo","Vila Nova","CRB","Operário-PR","Atlético-GO","Botafogo-SP","Fortaleza","Cuiabá","Sport","Avaí","Juventude","Náutico","Criciúma","Athletic","Ponte Preta","Goiás","América-MG","Novorizontino","Londrina"]
# map to brazil ids by name (may be ambiguous; use state hint from name)
state_hint = {"Ceará":"CE","São Bernardo":"SP","Vila Nova":"GO","CRB":"AL","Operário-PR":"PR","Atlético-GO":"GO","Botafogo-SP":"SP","Fortaleza":"CE","Cuiabá":"MT","Sport":"PE","Avaí":"SC","Juventude":"RS","Náutico":"PE","Criciúma":"SC","Athletic":"MG","Ponte Preta":"SP","Goiás":"GO","América-MG":"MG","Novorizontino":"SP","Londrina":"PR"}
serie_b_ids = []
for n in serie_b_names:
    st = state_hint[n]
    # find matching brazil club name by state + contains
    matches = [c for c in BRA["clubs"] if c["state"]==st and (c["name"].lower().startswith(n.lower().split("-")[0].lower()) or n.lower().split("-")[0] in c["name"].lower())]
    if len(matches)==1:
        cid = matches[0]["id"]
    else:
        # try exact name match
        exact = [c for c in BRA["clubs"] if c["name"]==n and c["state"]==st]
        cid = exact[0]["id"] if exact else bra(n, st)
    reg_club(cid, n, "BRA", {"state": st})
    serie_b_ids.append(cid)

# Série C and D participants come from the verified local Brazil catalog
serie_c_clubs = [c for c in BRA["clubs"] if c["division"] == "C"]
serie_d_clubs = [c for c in BRA["clubs"] if c["division"] == "D"]
serie_c_ids = [c["id"] for c in serie_c_clubs]
serie_d_ids = [c["id"] for c in serie_d_clubs]
for c in serie_c_clubs + serie_d_clubs:
    reg_club(c["id"], c["name"], "BRA", {"state": c["state"]})

add({
  "competitionId": "BRA_SERIE_B",
  "officialName": "Campeonato Brasileiro Série B",
  "displayName": "Brasileirão Série B 2026",
  "countryId": "BRA",
  "confederationId": "CONMEBOL",
  "competitionType": "league",
  "seasonId": "2026",
  "seasonStartDate": "2026-03-21",
  "seasonEndDate": None,
  "calendarType": "annual",
  "participantCount": 20,
  "participantIds": serie_b_ids,
  "competitionFormat": "round_robin_double_with_playoffs",
  "stages": ["regular_season","playoffs_access"],
  "promotionRules": ["top2_direct","playoff_3vs6","playoff_4vs5","two_playoff_winners_promoted"],
  "relegationRules": ["bottom_4_relegated"],
  "trophyAssetId": "tr_bra_serie_b_2026.png",
  "status": "participants_complete_calendar_partial",
})

# Série C / D: counts only, participants pending (no verified local list)
add({
  "competitionId": "BRA_SERIE_C",
  "officialName": "Campeonato Brasileiro Série C",
  "displayName": "Brasileirão Série C 2026",
  "countryId": "BRA",
  "confederationId": "CONMEBOL",
  "competitionType": "league",
  "seasonId": "2026",
  "seasonStartDate": None,
  "seasonEndDate": None,
  "calendarType": "annual",
  "participantCount": 20,
  "participantIds": [],
  "competitionFormat": "official_2026_format_preserved",
  "stages": ["classification","decisive_groups","promotion","relegation"],
  "trophyAssetId": "tr_bra_serie_c_2026.png",
  "participantIds": serie_c_ids,
  "status": "participants_complete_calendar_pending",
})
add({
  "competitionId": "BRA_SERIE_D",
  "officialName": "Campeonato Brasileiro Série D",
  "displayName": "Brasileirão Série D 2026",
  "countryId": "BRA",
  "confederationId": "CONMEBOL",
  "competitionType": "league",
  "seasonId": "2026",
  "seasonStartDate": None,
  "seasonEndDate": None,
  "calendarType": "annual",
  "participantCount": 96,
  "participantIds": [],
  "competitionFormat": "16_groups_of_6",
  "stages": ["group_stage","knockout"],
  "trophyAssetId": "tr_bra_serie_d_2026.png",
  "participantIds": serie_d_ids,
  "status": "participants_complete_calendar_pending",
  "configNote": "Requires .cfg nTimes 64->96 and nGrupos 8->16 (trial-serie-d-96, experimental only)",
})

# Copa do Brasil
add({
  "competitionId": "BRA_COPA_DO_BRASIL",
  "officialName": "Copa do Brasil",
  "displayName": "Copa do Brasil 2026",
  "countryId": "BRA",
  "confederationId": "CONMEBOL",
  "competitionType": "cup",
  "seasonId": "2026",
  "seasonStartDate": "2026-02-18",
  "seasonEndDate": "2026-12-06",
  "calendarType": "annual",
  "participantCount": 126,
  "participantIds": [],
  "competitionFormat": "nine_phases_mixed_single_and_two_legs",
  "stages": ["phase_1","phase_2","phase_3","phase_4","phase_5","phase_6","phase_7","phase_8","final"],
  "trophyAssetId": "tr_copa_BRA.png",
  "status": "motor_implemented_participants_pending",
})

# Copa do Nordeste
nordeste = ["ABC","América-RN","ASA","Botafogo-PB","Ceará","Confiança","CRB","Ferroviário","Fluminense-PI","Fortaleza","Imperatriz","Itabaiana","Jacuipense","Juazeirense","Maranhão","Piauí","Retrô","Sousa","Sport","Vitória"]
nd_ids = []
for n in nordeste:
    # try brazil id by name
    exact = [c for c in BRA["clubs"] if c["name"]==n]
    cid = exact[0]["id"] if exact else bra(n, None)
    reg_club(cid, n, "BRA")
    nd_ids.append(cid)
add({
  "competitionId": "BRA_COPA_NORDESTE",
  "officialName": "Copa do Nordeste",
  "displayName": "Copa do Nordeste 2026",
  "countryId": "BRA",
  "confederationId": "CONMEBOL",
  "competitionType": "regional_cup",
  "seasonId": "2026",
  "seasonStartDate": "2026-03-25",
  "seasonEndDate": "2026-06-07",
  "calendarType": "annual",
  "participantCount": 20,
  "participantIds": nd_ids,
  "competitionFormat": "4_groups_of_5_cross_groups",
  "stages": ["group_stage_50_matches","knockout"],
  "trophyAssetId": "tr_copanordeste.png",
  "status": "participants_complete_calendar_partial",
})

# Copa Verde
copa_norte_a = ["Grêmio Sampaio","Guaporé","Independência","Nacional-AM","Paysandu","Trem"]
copa_norte_b = ["Águia de Marabá","Amazonas","Galvez","Monte Roraima","Porto Velho","Remo"]
copa_co_a = ["Araguaína","Capital-DF","Operário-MS","Primavera-MT","Rio Branco-ES","Vila Nova"]
copa_co_b = ["Anápolis","Atlético-GO","Cuiabá","Gama","Porto Vitória","Tocantinópolis"]
cv_ids = []
for grp in (copa_norte_a, copa_norte_b, copa_co_a, copa_co_b):
    for n in grp:
        exact = [c for c in BRA["clubs"] if c["name"]==n]
        cid = exact[0]["id"] if exact else bra(n, None)
        reg_club(cid, n, "BRA")
        cv_ids.append(cid)
add({
  "competitionId": "BRA_COPA_VERDE",
  "officialName": "Copa Verde",
  "displayName": "Copa Verde 2026",
  "countryId": "BRA",
  "confederationId": "CONMEBOL",
  "competitionType": "regional_cup",
  "seasonId": "2026",
  "seasonStartDate": "2026-03-24",
  "seasonEndDate": "2026-06-07",
  "calendarType": "annual",
  "participantCount": 24,
  "participantIds": cv_ids,
  "competitionFormat": "4_groups_of_6_regional_then_final",
  "stages": ["group_stage","regional_semifinals","regional_finals","copa_verde_final"],
  "trophyAssetId": "tr_copaverde.png",
  "status": "participants_complete_calendar_partial",
})

# Supercopa Rei
add({
  "competitionId": "BRA_SUPERCOPA_REI",
  "officialName": "Supercopa Rei",
  "displayName": "Supercopa Rei 2026",
  "countryId": "BRA",
  "confederationId": "CONMEBOL",
  "competitionType": "supercup",
  "seasonId": "2026",
  "seasonStartDate": "2026-02-01",
  "seasonEndDate": "2026-02-01",
  "calendarType": "annual",
  "participantCount": 2,
  "participantIds": [bra("Flamengo","RJ"), bra("Corinthians","SP")],
  "competitionFormat": "single_match",
  "stages": ["final"],
  "venue": "Arena BRB Mané Garrincha, Brasília",
  "thirdPlaceEnabled": False,
  "trophyAssetId": "tr_bra_supercopa_rei_2026.png",
  "status": "participants_complete_calendar_complete",
})

# ---------- CONMEBOL ----------
lib_groups = {
 "A": ["Flamengo","Estudiantes","Cusco","Independiente Medellín"],
 "B": ["Nacional-URU","Universitario","Coquimbo Unido","Deportes Tolima"],
 "C": ["Fluminense","Bolívar","Deportivo La Guaira","Independiente Rivadavia"],
 "D": ["Boca Juniors","Cruzeiro","Universidad Católica-CHI","Barcelona-EQU"],
 "E": ["Peñarol","Corinthians","Independiente Santa Fe","Platense"],
 "F": ["Palmeiras","Cerro Porteño","Junior Barranquilla","Sporting Cristal"],
 "G": ["LDU Quito","Lanús","Always Ready","Mirassol"],
 "H": ["Independiente del Valle","Libertad","Rosario Central","Universidad Central"],
}
lib_ids = []
for g, teams in lib_groups.items():
    for t in teams:
        cid = foreign("conmebol", t)
        reg_club(cid, t, None)
        lib_ids.append(cid)
add({
  "competitionId": "CONMEBOL_LIBERTADORES",
  "officialName": "CONMEBOL Libertadores",
  "displayName": "Copa Libertadores 2026",
  "countryId": None,
  "confederationId": "CONMEBOL",
  "competitionType": "continental_cup",
  "seasonId": "2026",
  "seasonStartDate": "2026-04-07",
  "seasonEndDate": "2026-11-28",
  "calendarType": "annual",
  "participantCount": 32,
  "participantIds": lib_ids,
  "competitionFormat": "group_stage_8_groups_of_4_then_knockout",
  "stages": ["preliminary","group_stage","round_of_16","quarterfinals","semifinals","final"],
  "groups": lib_groups,
  "finalVenue": "Montevidéu",
  "finalDate": "2026-11-28",
  "thirdPlaceEnabled": False,
  "trophyAssetId": "tr_libertadores.png",
  "status": "group_stage_participants_complete_calendar_complete",
})

sula_groups = {
 "A": ["América de Cali","Tigre","Macará","Alianza Atlético"],
 "B": ["Atlético-MG","Cienciano","Academia Puerto Cabello","Juventud"],
 "C": ["São Paulo","Millonarios","Boston River","O'Higgins"],
 "D": ["Santos","San Lorenzo","Deportivo Cuenca","Recoleta"],
 "E": ["Racing Club","Caracas","Independiente Petrolero","Botafogo"],
 "F": ["Grêmio","Palestino","Montevideo City Torque","Deportivo Riestra"],
 "G": ["Olimpia-PAR","Vasco","Audax Italiano","Barracas Central"],
 "H": ["River Plate","Red Bull Bragantino","Blooming","Carabobo"],
}
sula_ids = []
for g, teams in sula_groups.items():
    for t in teams:
        cid = foreign("conmebol", t)
        reg_club(cid, t, None)
        sula_ids.append(cid)
add({
  "competitionId": "CONMEBOL_SULAMERICANA",
  "officialName": "CONMEBOL Sudamericana",
  "displayName": "Copa Sudamericana 2026",
  "countryId": None,
  "confederationId": "CONMEBOL",
  "competitionType": "continental_cup",
  "seasonId": "2026",
  "seasonStartDate": "2026-04-07",
  "seasonEndDate": "2026-11-21",
  "calendarType": "annual",
  "participantCount": 32,
  "participantIds": sula_ids,
  "competitionFormat": "group_stage_8_groups_of_4_then_knockout",
  "stages": ["preliminary","group_stage","playoff_round_of_16","round_of_16","quarterfinals","semifinals","final"],
  "groups": sula_groups,
  "finalVenue": "Barranquilla",
  "finalDate": "2026-11-21",
  "thirdPlaceEnabled": False,
  "trophyAssetId": "tr_sulamericana.png",
  "status": "group_stage_participants_complete_calendar_complete",
})

add({
  "competitionId": "CONMEBOL_RECOPA",
  "officialName": "CONMEBOL Recopa",
  "displayName": "Recopa Sudamericana 2026",
  "countryId": None,
  "confederationId": "CONMEBOL",
  "competitionType": "supercup",
  "seasonId": "2026",
  "seasonStartDate": "2026-02-19",
  "seasonEndDate": "2026-02-26",
  "calendarType": "annual",
  "participantCount": 2,
  "participantIds": [foreign("conmebol","Flamengo"), foreign("conmebol","Lanús")],
  "competitionFormat": "two_legs",
  "stages": ["first_leg","second_leg"],
  "legs": 2,
  "firstLegVenue": "Lanús (home)",
  "secondLegVenue": "Flamengo (home)",
  "thirdPlaceEnabled": False,
  "trophyAssetId": "tr_conmebol_recopa_2026.png",
  "status": "participants_complete_calendar_complete",
})

# ---------- UEFA Champions League ----------
ucl = ["LASK","Sabah","Club Brugge","Slavia Praha","Arsenal","Aston Villa","Liverpool","Manchester City","Manchester United","Lens","Lille","Paris Saint-Germain","Bayern München","Borussia Dortmund","RB Leipzig","Stuttgart","AEK Athens","Como","Inter","Napoli","Roma","Feyenoord","PSV","Bodø/Glimt","Viking","Porto","Sporting CP","Slovan Bratislava","Atlético de Madrid","Barcelona","Real Betis","Real Madrid","Villarreal","Fenerbahçe","Galatasaray","Shakhtar Donetsk"]
ucl_ids = [foreign("uefa", t) for t in ucl]
for t in ucl:
    reg_club(foreign("uefa", t), t, None)
add({
  "competitionId": "UEFA_CHAMPIONS_LEAGUE",
  "officialName": "UEFA Champions League",
  "displayName": "UEFA Champions League 2026/27",
  "countryId": None,
  "confederationId": "UEFA",
  "competitionType": "continental_cup",
  "seasonId": "2026/27",
  "seasonStartDate": "2026-09-08",
  "seasonEndDate": "2027-06-05",
  "calendarType": "interannual",
  "participantCount": 36,
  "participantIds": ucl_ids,
  "competitionFormat": "league_phase_36_single_table",
  "stages": ["league_phase","playoff","round_of_16","quarterfinals","semifinals","final"],
  "finalVenue": "Madri",
  "finalDate": "2027-06-05",
  "thirdPlaceEnabled": False,
  "trophyAssetId": "tr_ligacampeoes.png",
  "status": "participants_complete_calendar_complete",
  "admissionNote": "UEFA list published 2026-11-04, subject to admission conditions",
})

add({
  "competitionId": "UEFA_EUROPA_LEAGUE",
  "officialName": "UEFA Europa League",
  "displayName": "UEFA Europa League 2026/27",
  "countryId": None,
  "confederationId": "UEFA",
  "competitionType": "continental_cup",
  "seasonId": "2026/27",
  "seasonStartDate": None,
  "seasonEndDate": None,
  "calendarType": "interannual",
  "participantCount": 36,
  "participantIds": [],
  "competitionFormat": "league_phase_36",
  "stages": ["league_phase","knockout"],
  "trophyAssetId": "tr_ligaeuropa.png",
  "status": "architecture_ready_participants_pending",
})
add({
  "competitionId": "UEFA_CONFERENCE_LEAGUE",
  "officialName": "UEFA Conference League",
  "displayName": "UEFA Conference League 2026/27",
  "countryId": None,
  "confederationId": "UEFA",
  "competitionType": "continental_cup",
  "seasonId": "2026/27",
  "seasonStartDate": None,
  "seasonEndDate": None,
  "calendarType": "interannual",
  "participantCount": 36,
  "participantIds": [],
  "competitionFormat": "league_phase_36",
  "stages": ["league_phase","knockout"],
  "trophyAssetId": "tr_conference.png",
  "status": "architecture_ready_participants_pending",
})
add({
  "competitionId": "UEFA_SUPER_CUP",
  "officialName": "UEFA Super Cup",
  "displayName": "UEFA Super Cup 2026",
  "countryId": None,
  "confederationId": "UEFA",
  "competitionType": "supercup",
  "seasonId": "2026",
  "seasonStartDate": "2026-08-12",
  "seasonEndDate": "2026-08-12",
  "calendarType": "annual",
  "participantCount": 2,
  "participantIds": [foreign("uefa","Paris Saint-Germain"), foreign("uefa","Aston Villa")],
  "competitionFormat": "single_match_neutral",
  "stages": ["final"],
  "venue": "Stadion Salzburg, Salzburgo",
  "thirdPlaceEnabled": False,
  "trophyAssetId": "tr_uefa_supercup_2026.png",
  "status": "participants_complete_calendar_complete",
})

# ---------- CONCACAF ----------
concacaf = ["Vancouver FC","Mount Pleasant","O&M FC","Defence Force","Alajuelense","Real España","Xelajú","Olimpia de Honduras","Cartaginés","Sporting San Miguelito","Forge FC","Atlético Ottawa","Seattle Sounders","LA Galaxy","Club América","Monterrey","Toluca","Cruz Azul","Tigres UANL","Pumas UNAM","Inter Miami","Philadelphia Union","San Diego FC","FC Cincinnati","Vancouver Whitecaps","Los Angeles FC","Nashville SC"]
cc_ids = [foreign("concacaf", t) for t in concacaf]
for t in concacaf:
    reg_club(foreign("concacaf", t), t, None)
add({
  "competitionId": "CONCACAF_CHAMPIONS_CUP",
  "officialName": "Concacaf Champions Cup",
  "displayName": "Concacaf Champions Cup 2026",
  "countryId": None,
  "confederationId": "CONCACAF",
  "competitionType": "continental_cup",
  "seasonId": "2026",
  "seasonStartDate": "2026-02-01",
  "seasonEndDate": "2026-05-30",
  "calendarType": "annual",
  "participantCount": 27,
  "participantIds": cc_ids,
  "competitionFormat": "5_knockout_rounds_22_start_r1_5_bye_to_r16",
  "stages": ["round_1","round_of_16","quarterfinals","semifinals","final"],
  "finalDate": "2026-05-30",
  "thirdPlaceEnabled": False,
  "trophyAssetId": "tr_ligaconcacaf.png",
  "status": "participants_complete_calendar_partial",
})

# ---------- FIFA Intercontinental ----------
add({
  "competitionId": "FIFA_INTERCONTINENTAL_CUP",
  "officialName": "FIFA Intercontinental Cup",
  "displayName": "FIFA Intercontinental Cup 2026",
  "countryId": None,
  "confederationId": "FIFA",
  "competitionType": "intercontinental",
  "seasonId": "2026",
  "seasonStartDate": "2026-12-09",
  "seasonEndDate": "2026-12-16",
  "calendarType": "annual",
  "participantCount": None,
  "participantIds": [],
  "competitionFormat": "intercontinental_with_intermediate_trophies",
  "stages": ["derby_of_the_americas","challenger_cup","final"],
  "intermediateTrophies": ["tr_fifa_derby_americas_2026.png","tr_fifa_challenger_cup_2026.png"],
  "qualifiedSlots": {"UEFA": "Paris Saint-Germain","CONCACAF": "Toluca","CAF": "Mamelodi Sundowns","CONMEBOL": "WINNER(CONMEBOL_LIBERTADORES,2026)"},
  "thirdPlaceEnabled": False,
  "trophyAssetId": "tr_fifa_intercontinental_2026.png",
  "status": "structure_complete_participants_partial",
})

# ---------- CAF Super Cup ----------
add({
  "competitionId": "CAF_SUPER_CUP",
  "officialName": "CAF Super Cup",
  "displayName": "CAF Super Cup 2026",
  "countryId": None,
  "confederationId": "CAF",
  "competitionType": "supercup",
  "seasonId": "2026",
  "seasonStartDate": "2026-11-08",
  "seasonEndDate": "2026-11-08",
  "calendarType": "annual",
  "participantCount": 2,
  "participantIds": [foreign("caf","Mamelodi Sundowns"), foreign("caf","USM Alger")],
  "competitionFormat": "single_match",
  "stages": ["final"],
  "venue": "Loftus Versfeld, Pretória",
  "thirdPlaceEnabled": False,
  "trophyAssetId": "tr_caf_supercup_2026.png",
  "status": "participants_complete_calendar_complete",
})

# ---------- AFC / CAF / OFC architecture placeholders ----------
for cid, name, conf in [("AFC_CHAMPIONS_LEAGUE_ELITE","AFC Champions League Elite","AFC"),
                        ("AFC_CHAMPIONS_LEAGUE_TWO","AFC Champions League Two","AFC"),
                        ("AFC_CHALLENGE_LEAGUE","AFC Challenge League","AFC"),
                        ("CAF_CHAMPIONS_LEAGUE","CAF Champions League","CAF"),
                        ("CAF_CONFEDERATION_CUP","CAF Confederation Cup","CAF"),
                        ("OFC_CHAMPIONS_LEAGUE","OFC Champions League","OFC"),
                        ("OFC_PRO_LEAGUE","OFC Pro League","OFC")]:
    add({
      "competitionId": cid,
      "officialName": name,
      "displayName": f"{name} 2026/27",
      "countryId": None,
      "confederationId": conf,
      "competitionType": "continental_cup",
      "seasonId": "2026/27",
      "seasonStartDate": None,
      "seasonEndDate": None,
      "calendarType": "interannual",
      "participantCount": None,
      "participantIds": [],
      "competitionFormat": "see_regulation",
      "stages": [],
      "trophyAssetId": None,
      "status": "architecture_ready_participants_pending",
    })

# ---------- National supercups ----------
supercups = [
 ("ARG_TROFEO_CAMPEONES","Argentina","Trofeo de Campeones LPF","tr_arg_trofeo_campeones_2026.png","2026-12-19"),
 ("COL_SUPERLIGA","Colombia","Superliga BetPlay DIMAYOR","tr_col_superliga_2026.png",None),
 ("ESP_SUPERCOPA","Spain","Supercopa de España","tr_esp_supercopa_2026.png",None),
 ("ITA_SUPERCOPPA","Italy","Supercoppa Italiana","tr_ita_supercoppa_2026.png","2026-12-22"),
 ("ENG_COMMUNITY_SHIELD","England","FA Community Shield","tr_eng_community_shield_2026.png","2026-08-16"),
 ("GER_FRANZ_BECKENBAUER_SUPERCUP","Germany","Franz Beckenbauer Supercup","tr_ger_supercup_2026.png","2026-08-22"),
 ("FRA_TROPHEE_CHAMPIONS","France","Trophée des Champions","tr_fra_trophee_champions.png",None),
 ("POR_SUPERTACA","Portugal","Supertaça Cândido de Oliveira","tr_por_supertaca_2026.png","2026-08-01"),
 ("NED_JOHAN_CRUIJFF_SCHAAL","Netherlands","Johan Cruijff Schaal","tr_ned_johan_cruyff_schaal_2026.png","2026-08-02"),
 ("BEL_SUPERCUP","Belgium","Belgian Super Cup","tr_bel_supercup_2026.png",None),
 ("TUR_SUPER_KUPA","Turkey","Turkcell Süper Kupa","tr_tur_super_kupa_2026.png",None),
]
for cid, country, name, trophy, date in supercups:
    add({
      "competitionId": cid,
      "officialName": name,
      "displayName": f"{name} 2026",
      "countryId": country.upper()[:3],
      "confederationId": "UEFA",
      "competitionType": "supercup",
      "seasonId": "2026",
      "seasonStartDate": date,
      "seasonEndDate": date,
      "calendarType": "annual",
      "participantCount": None,
      "participantIds": [],
      "competitionFormat": "see_regulation",
      "stages": [],
      "thirdPlaceEnabled": False,
      "trophyAssetId": trophy,
      "status": "architecture_ready_participants_pending",
    })

# ---------- Women / youth ----------
add({
  "competitionId": "CONMEBOL_LIBERTADORES_U20",
  "officialName": "CONMEBOL Libertadores Sub-20",
  "displayName": "Libertadores Sub-20 2026",
  "countryId": None,
  "confederationId": "CONMEBOL",
  "competitionType": "youth_continental_cup",
  "seasonId": "2026",
  "seasonStartDate": "2026-03-01",
  "seasonEndDate": "2026-03-22",
  "calendarType": "annual",
  "participantCount": 12,
  "participantIds": [],
  "competitionFormat": "3_groups_of_4_semifinal_third_place_final",
  "stages": ["group_stage","semifinals","third_place","final"],
  "thirdPlaceEnabled": True,
  "trophyAssetId": "tr_conmebol_libertadores_u20_2026.png",
  "status": "participants_partial",
})
add({
  "competitionId": "CONMEBOL_LIBERTADORES_WOMEN",
  "officialName": "CONMEBOL Libertadores Feminina",
  "displayName": "Libertadores Feminina 2026",
  "countryId": None,
  "confederationId": "CONMEBOL",
  "competitionType": "women_continental_cup",
  "seasonId": "2026",
  "seasonStartDate": "2026-10-15",
  "seasonEndDate": "2026-10-31",
  "calendarType": "annual",
  "participantCount": 16,
  "participantIds": [],
  "competitionFormat": "4_groups_of_4_quarters_semis_third_place_final",
  "stages": ["group_stage","quarterfinals","semifinals","third_place","final"],
  "thirdPlaceEnabled": True,
  "trophyAssetId": "tr_conmebol_libertadores_women_2026.png",
  "status": "participants_pending",
})
add({
  "competitionId": "FIFA_WOMENS_CHAMPIONS_CUP",
  "officialName": "FIFA Women's Champions Cup",
  "displayName": "FIFA Women's Champions Cup 2026",
  "countryId": None,
  "confederationId": "FIFA",
  "competitionType": "women_intercontinental",
  "seasonId": "2026",
  "seasonStartDate": "2026-01-28",
  "seasonEndDate": "2026-02-01",
  "calendarType": "annual",
  "participantCount": 6,
  "participantIds": [],
  "competitionFormat": "intercontinental_with_third_place",
  "stages": ["preliminary","semifinals","third_place","final"],
  "thirdPlaceEnabled": True,
  "thirdPlaceDate": "2026-02-01",
  "trophyAssetId": "tr_fifa_womens_champions_cup_2026.png",
  "status": "participants_partial",
})

# write output
doc = {
  "schemaVersion": 1,
  "season": "2026",
  "generatedBy": "tools/build_competitions_catalog.py",
  "scope": "Cataloged competitions with provided participant lists; motor implementation is separate.",
  "competitionCount": len(COMP),
  "clubCount": len(clubs),
  "competitions": COMP,
  "clubs": list(clubs.values()),
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")
print("competitions:", len(COMP), "clubs:", len(clubs))
print("written:", OUT)
