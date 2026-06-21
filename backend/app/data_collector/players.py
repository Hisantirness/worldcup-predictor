"""Player rosters and per-player stat distribution."""
import hashlib

TEAM_ROSTERS: dict[str, list[dict]] = {}

_PLAYER_POOLS: dict[str, list[tuple[str, str, float, float, float, float]]] = {
    "Argentina": [
        ("L. Messi", "FWD", 4.5, 0.3, 0.2, 3.0),
        ("J. Álvarez", "FWD", 3.0, 0.5, 0.4, 1.5),
        ("L. Martínez", "FWD", 2.5, 0.8, 0.6, 1.0),
        ("A. Di María", "MID", 2.0, 0.4, 0.3, 1.5),
        ("R. De Paul", "MID", 1.5, 1.5, 1.2, 2.5),
        ("E. Fernández", "MID", 1.0, 1.2, 1.0, 2.0),
        ("L. Paredes", "MID", 0.5, 2.0, 1.8, 3.0),
        ("N. Molina", "DEF", 0.5, 1.0, 0.8, 2.0),
        ("C. Romero", "DEF", 0.3, 1.8, 1.5, 3.5),
        ("N. Otamendi", "DEF", 0.3, 1.5, 1.3, 3.0),
        ("M. Acuña", "DEF", 0.8, 1.2, 1.0, 2.0),
        ("E. Martínez", "GK", 0.0, 0.1, 0.0, 0.5),
    ],
    "Brazil": [
        ("Vinicius Jr.", "FWD", 4.0, 0.4, 0.3, 1.5),
        ("Raphinha", "FWD", 3.5, 0.5, 0.4, 1.0),
        ("Rodrygo", "FWD", 3.0, 0.3, 0.2, 0.5),
        ("Neymar", "MID", 2.5, 0.6, 0.5, 1.0),
        ("Casemiro", "MID", 1.0, 2.0, 1.5, 3.0),
        ("Paquetá", "MID", 1.5, 1.2, 1.0, 2.0),
        ("B. Guimarães", "MID", 0.8, 1.5, 1.2, 2.5),
        ("Danilo", "DEF", 0.5, 1.0, 0.8, 1.5),
        ("Marquinhos", "DEF", 0.3, 1.2, 1.0, 2.5),
        ("Thiago Silva", "DEF", 0.2, 1.0, 0.8, 2.0),
        ("Alex Sandro", "DEF", 0.5, 1.2, 1.0, 1.5),
        ("Alisson", "GK", 0.0, 0.1, 0.0, 0.5),
    ],
    "France": [
        ("K. Mbappé", "FWD", 5.0, 0.3, 0.2, 1.0),
        ("A. Griezmann", "FWD", 2.5, 0.8, 0.6, 2.0),
        ("O. Dembélé", "FWD", 3.0, 0.4, 0.3, 0.5),
        ("M. Thuram", "FWD", 2.0, 0.5, 0.4, 1.0),
        ("A. Tchouaméni", "MID", 1.0, 1.8, 1.5, 3.0),
        ("E. Camavinga", "MID", 1.2, 1.5, 1.2, 2.5),
        ("Y. Fofana", "MID", 0.8, 1.5, 1.3, 2.5),
        ("J. Koundé", "DEF", 0.3, 1.2, 1.0, 2.5),
        ("D. Upamecano", "DEF", 0.2, 1.5, 1.3, 3.0),
        ("L. Hernández", "DEF", 0.5, 1.0, 0.8, 2.0),
        ("T. Hernández", "DEF", 0.8, 1.0, 0.8, 1.5),
        ("H. Lloris", "GK", 0.0, 0.0, 0.0, 0.5),
    ],
    "England": [
        ("H. Kane", "FWD", 4.0, 0.3, 0.2, 1.0),
        ("B. Saka", "FWD", 3.0, 0.5, 0.4, 1.5),
        ("P. Foden", "MID", 2.5, 0.5, 0.4, 1.0),
        ("J. Bellingham", "MID", 2.0, 1.0, 0.8, 2.5),
        ("D. Rice", "MID", 0.8, 1.5, 1.2, 3.0),
        ("M. Mount", "MID", 1.5, 0.8, 0.6, 1.5),
        ("K. Walker", "DEF", 0.3, 0.8, 0.6, 1.5),
        ("J. Stones", "DEF", 0.2, 1.0, 0.8, 2.0),
        ("H. Maguire", "DEF", 0.5, 1.5, 1.2, 3.0),
        ("L. Shaw", "DEF", 0.5, 1.0, 0.8, 2.0),
        ("T. Alexander-Arnold", "DEF", 1.0, 0.8, 0.6, 1.5),
        ("J. Pickford", "GK", 0.0, 0.1, 0.0, 0.5),
    ],
    "Spain": [
        ("A. Morata", "FWD", 2.5, 0.8, 0.6, 1.0),
        ("N. Williams", "FWD", 3.0, 0.3, 0.2, 0.5),
        ("L. Yamal", "FWD", 2.5, 0.4, 0.3, 0.5),
        ("Pedri", "MID", 1.0, 0.8, 0.6, 2.0),
        ("Rodri", "MID", 0.8, 1.5, 1.2, 3.0),
        ("F. Ruiz", "MID", 1.2, 1.2, 1.0, 2.0),
        ("D. Olmo", "MID", 1.5, 0.6, 0.5, 1.0),
        ("D. Carvajal", "DEF", 0.5, 1.2, 1.0, 2.0),
        ("Nacho", "DEF", 0.3, 1.2, 1.0, 2.5),
        ("A. Laporte", "DEF", 0.2, 1.0, 0.8, 2.0),
        ("J. Alba", "DEF", 0.5, 0.8, 0.6, 1.5),
        ("Unai Simón", "GK", 0.0, 0.1, 0.0, 0.5),
    ],
    "Germany": [
        ("N. Füllkrug", "FWD", 3.0, 0.6, 0.5, 1.0),
        ("L. Sané", "FWD", 3.5, 0.3, 0.2, 0.5),
        ("J. Musiala", "MID", 2.5, 0.5, 0.4, 1.0),
        ("İ. Gündoğan", "MID", 1.5, 1.0, 0.8, 2.0),
        ("J. Kimmich", "MID", 1.0, 1.5, 1.2, 2.5),
        ("K. Havertz", "MID", 2.0, 0.5, 0.4, 1.5),
        ("A. Rüdiger", "DEF", 0.3, 2.0, 1.5, 3.5),
        ("N. Süle", "DEF", 0.2, 1.5, 1.2, 2.5),
        ("D. Raum", "DEF", 0.5, 1.0, 0.8, 1.5),
        ("M. Schlotterbeck", "DEF", 0.3, 1.2, 1.0, 2.0),
        ("B. Henrichs", "DEF", 0.5, 1.0, 0.8, 1.5),
        ("M. ter Stegen", "GK", 0.0, 0.0, 0.0, 0.5),
    ],
    "Portugal": [
        ("C. Ronaldo", "FWD", 4.0, 0.3, 0.2, 0.5),
        ("J. Félix", "FWD", 2.0, 0.5, 0.4, 1.0),
        ("Diogo Jota", "FWD", 2.5, 0.6, 0.5, 1.5),
        ("Bruno Fernandes", "MID", 2.5, 1.0, 0.8, 2.0),
        ("Bernardo Silva", "MID", 1.0, 0.8, 0.6, 1.5),
        ("R. Neves", "MID", 0.8, 1.5, 1.2, 2.5),
        ("Vitinha", "MID", 1.2, 1.0, 0.8, 2.0),
        ("R. Dias", "DEF", 0.2, 1.0, 0.8, 2.0),
        ("Pepe", "DEF", 0.3, 2.0, 1.5, 3.5),
        ("J. Cancelo", "DEF", 0.8, 1.0, 0.8, 1.5),
        ("N. Mendes", "DEF", 0.5, 0.8, 0.6, 1.5),
        ("Diogo Costa", "GK", 0.0, 0.0, 0.0, 0.5),
    ],
    "Netherlands": [
        ("M. Depay", "FWD", 3.0, 0.5, 0.4, 1.0),
        ("C. Gakpo", "FWD", 2.5, 0.5, 0.4, 1.0),
        ("D. Dumfries", "MID", 1.5, 0.8, 0.6, 1.5),
        ("F. de Jong", "MID", 1.0, 1.0, 0.8, 2.0),
        ("T. Koopmeiners", "MID", 1.2, 1.2, 1.0, 2.5),
        ("X. Simons", "MID", 1.5, 0.5, 0.4, 1.0),
        ("V. van Dijk", "DEF", 0.5, 0.8, 0.6, 2.0),
        ("M. de Ligt", "DEF", 0.3, 1.2, 1.0, 2.5),
        ("N. Aké", "DEF", 0.3, 1.0, 0.8, 2.0),
        ("J. Timber", "DEF", 0.3, 1.0, 0.8, 1.5),
        ("D. Blind", "DEF", 0.3, 0.8, 0.6, 1.0),
        ("J. Flekken", "GK", 0.0, 0.1, 0.0, 0.5),
    ],
}

# Generate remaining teams with synthetic but realistic players
_SURNAMES_BY_COUNTRY = {
    "Mexico": ["Jiménez", "Lozano", "Vega", "Álvarez", "Herrera", "Guardado", "Gallardo", "Moreno", "Araujo", "Montes", "Ochoa"],
    "South Korea": ["Son", "Hwang", "Lee", "Kim", "Park", "Jung", "Choi", "Yoon", "Kang", "Seo", "Jo"],
    "Japan": ["Mitoma", "Kubo", "Minamino", "Kamada", "Endō", "Tanaka", "Tomiyasu", "Itakura", "Sugawara", "Nagatomo", "Gonda"],
    "USA": ["Pulisic", "McKennie", "Reyna", "Musah", "Adams", "Aaronson", "Dest", "Ream", "Robinson", "Richards", "Turner"],
    "Uruguay": ["Suárez", "Núñez", "Pellistri", "Valverde", "Bentancur", "Ugarte", "Araújo", "Giménez", "Cáceres", "Olivera", "Rochet"],
    "Croatia": ["Modrić", "Kovačić", "Brozović", "Pašalić", "Vlašić", "Majer", "Gvardiol", "Stanišić", "Juranović", "Sosa", "Livaković"],
    "Morocco": ["En-Nesyri", "Boufal", "Ziyech", "Amrabat", "Ounahi", "El Khannous", "Hakimi", "Saïss", "Aguerd", "Mazraoui", "Bounou"],
    "Senegal": ["Mané", "Diatta", "Sarr", "Kouyaté", "Mendy", "Ndiaye", "Diallo", "Koulibaly", "BalloTouré", "Jakobs", "ÉdouardMendy"],
    "Switzerland": ["Embolo", "Shaqiri", "Vargas", "Xhaka", "Freuler", "Aebischer", "Rodríguez", "Akanji", "Elvedi", "Widmer", "Sommer"],
    "Canada": ["David", "Davies", "Larin", "Eustáquio", "Kone", "Osorio", "Johnston", "Miller", "Cornelius", "Adekugbe", "Borjan"],
    "South Africa": ["Mokoena", "Foster", "Zwane", "Modiba", "Monare", "Maart", "Mvala", "Xulu", "De Reuck", "Hlanti", "Williams"],
    "Czechia": ["Schick", "Hložek", "Černý", "Souček", "Darida", "Barák", "Coufal", "Zima", "Brabec", "Bořil", "Vaclík"],
    "Qatar": ["Afif", "Ali", "Muntari", "Al-Haydos", "Boudiaf", "Hatem", "Miguel", "Salman", "Khoukhi", "Hassan", "Barsham"],
    "Bosnia": ["Džeko", "Demirović", "Menalo", "Pjanić", "Krunić", "Gojak", "Ahmedhodžić", "Sančanin", "Todorović", "Kolašinac", "Šehić"],
    "Paraguay": ["Almirón", "Ávalos", "González", "Villamayor", "Giménez", "Rojas", "Alderete", "Balbuena", "Gómez", "Alonso", "Fernández"],
    "Haiti": ["Pierrot", "Nazon", "Duke", "Alcénat", "Mortel", "Levert", "Jérôme", "Désiré", "Mercéus", "Simon", "Placide"],
    "Scotland": ["Adams", "Dykes", "McTominay", "McGinn", "Gilmour", "McGregor", "Robertson", "Porteous", "Cooper", "Patterson", "Gunn"],
    "Turkey": ["Ünal", "Yılmaz", "Kahveci", "Çalhanoğlu", "Özcan", "Kökcü", "Çelik", "Demiral", "Kabak", "Müldür", "Çakır"],
    "Australia": ["Maclaren", "Goodwin", "Boyle", "Mooy", "Irvine", "Cacace", "Souttar", "Rowles", "Atkinson", "McGowan", "Ryan"],
    "Ivory Coast": ["Haller", "Bamba", "Kessié", "Zaha", "Fofana", "Gradel", "Aurier", "Diallo", "Kossounou", "Traorè", "Sangaré"],
    "Ecuador": ["Valencia", "Estrada", "Plata", "Caicedo", "Mena", "Gruezo", "Hincapié", "Torres", "Preciado", "Estupiñán", "Galíndez"],
    "Germany (sec)": [],
}

# For teams not in _PLAYER_POOLS, generate from surnames
_FIRST_NAMES = ["A.", "B.", "C.", "D.", "E.", "F.", "G.", "H.", "J.", "K.", "L.", "M."]

_POSITIONS_CYCLE = ["FWD", "FWD", "MID", "MID", "MID", "MID", "DEF", "DEF", "DEF", "DEF", "GK"]


def _seed_float(key: str) -> float:
    h = hashlib.md5(key.encode()).digest()
    return int.from_bytes(h[:4], "little") / (2 ** 32)


def _get_fallback_roster(team: str) -> list[tuple[str, str, float, float, float, float]]:
    sur = _SURNAMES_BY_COUNTRY.get(team, [])
    while len(sur) < 11:
        sur.append(sur[len(sur) % max(len(sur), 1)])
    roster = []
    for i, surname in enumerate(sur[:11]):
        s = _seed_float(f"{team}:{surname}")
        pos = _POSITIONS_CYCLE[i % len(_POSITIONS_CYCLE)]
        shoot = 0.5 + 2.5 * s
        foul = 0.3 + 1.5 * ((s * 7) % 1)
        tackle = 0.2 + 1.2 * ((s * 11) % 1)
        foul_suffered = 0.3 + 1.5 * ((s * 13) % 1)
        roster.append((f"{_FIRST_NAMES[i]} {surname}", pos, round(shoot, 1), round(foul, 1), round(tackle, 1), round(foul_suffered, 1)))
    return roster


def get_team_roster(team: str) -> list[dict]:
    """Get a team's player roster with base tendency ratings."""
    if team in TEAM_ROSTERS:
        return TEAM_ROSTERS[team]

    roster_raw = _PLAYER_POOLS.get(team, _get_fallback_roster(team))
    roster = []
    for name, pos, shoot, foul, tackle, foul_suffered in roster_raw:
        roster.append({
            "name": name,
            "position": pos,
            "shooting_tendency": shoot,
            "fouling_tendency": foul,
            "tackling_tendency": tackle,
            "foul_suffered_tendency": foul_suffered,
        })
    TEAM_ROSTERS[team] = roster
    return roster


def distribute_stats(team: str, total_shots: int, total_sot: int, total_fouls: int,
                     total_yc: int, total_corners: int, total_offsides: int,
                     total_saves: int, total_tackles_approx: int | None = None) -> list[dict]:
    """Distribute team-level stats across the roster based on player tendencies."""
    roster = get_team_roster(team)
    non_gk = [p for p in roster if p["position"] != "GK"]
    gk = [p for p in roster if p["position"] == "GK"]

    total_shoot = sum(p["shooting_tendency"] for p in non_gk) or 1
    total_foul = sum(p["fouling_tendency"] for p in non_gk) or 1
    total_tackle = sum(p["tackling_tendency"] for p in non_gk) or 1
    total_foul_suff = sum(p["foul_suffered_tendency"] for p in non_gk) or 1

    results = []
    for p in roster:
        if p["position"] == "GK":
            results.append({**p, "shots": 0, "sot": 0, "fouls": 0, "yc": 0,
                          "corners": 0, "offsides": 0, "saves": total_saves,
                          "tackles": 0, "fouls_suffered": 0})
        else:
            share = p["shooting_tendency"] / total_shoot
            foul_share = p["fouling_tendency"] / total_foul
            tack_share = p["tackling_tendency"] / total_tackle
            foul_suff_share = p["foul_suffered_tendency"] / total_foul_suff

            shots = round(total_shots * share * (0.85 + 0.3 * (_seed_float(f"{team}:{p['name']}:shots") % 1)))
            sot = min(shots, round(total_sot * share * (0.8 + 0.4 * (_seed_float(f"{team}:{p['name']}:sot") % 1))))
            fouls = round(total_fouls * foul_share * (0.8 + 0.4 * (_seed_float(f"{team}:{p['name']}:foul") % 1)))
            yc = 1 if _seed_float(f"{team}:{p['name']}:yc") < (total_yc / total_fouls * foul_share * 3) else 0
            yc = min(yc + (1 if total_yc >= 3 and _seed_float(f"{team}:{p['name']}:yc2") < 0.2 else 0), 2)
            corners = round(total_corners * share * (0.5 + 0.3 * (_seed_float(f"{team}:{p['name']}:cor") % 1)))
            offsides = round(total_offsides * share * (0.6 + 0.4 * (_seed_float(f"{team}:{p['name']}:off") % 1)))
            tackles = round((total_tackles_approx or fouls * 1.5) * tack_share * (0.7 + 0.6 * (_seed_float(f"{team}:{p['name']}:tack") % 1)))
            fouls_suffered = round(fouls * foul_suff_share / (foul_share + 0.01) * (0.6 + 0.8 * (_seed_float(f"{team}:{p['name']}:fs") % 1)))

            results.append({**p, "shots": shots, "sot": sot, "fouls": fouls, "yc": yc,
                          "corners": corners, "offsides": offsides, "saves": 0,
                          "tackles": tackles, "fouls_suffered": fouls_suffered})
    return results
