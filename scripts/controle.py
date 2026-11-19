#!/usr/bin/env python3
"""Contrôles avant publication des fichiers du dossier data/.

Usage : python3 scripts/controle.py [dossier_data] [--seuil 5]
Code retour 1 si une erreur bloquante est trouvée (à corriger avant le commit).
"""
import csv, json, os, re, sys

DATA = 'data'
SEUIL = 0
args = sys.argv[1:]
if '--seuil' in args:
    i = args.index('--seuil'); SEUIL = int(args[i + 1]); del args[i:i + 2]
if args:
    DATA = args[0]

COLS = {
    'ref/territoires.csv': ['code_clpe', 'libelle_clpe', 'code_departement', 'libelle_departement', 'code_region', 'libelle_region'],
    'ref/proches.csv': ['code_clpe', 'code_clpe_proche', 'rang', 'indice_proximite'],
    'ref/metiers.csv': ['code_rome', 'libelle_metier', 'domaine', 'niveau_tension', 'lien_formation_metier', 'pre_qualifiant', 'millesime'],
    'ref/problematiques.csv': ['code_problematique', 'libelle', 'indicateur', 'objectif', 'unite'],
    'ref/leviers.csv': ['code_levier', 'libelle', 'description', 'facilite', 'niveau_actuel_defaut', 'effet_max', 'estimation', 'partenaires'],
    'faits/sortants_mois.csv': ['code_clpe', 'mois_sortie', 'dispositif', 'nb_sortants', 'nb_acces_1m', 'nb_acces_3m', 'nb_acces_6m', 'nb_presence_6m', 'nb_publics_prioritaires', 'somme_delais_jours'],
    'faits/sortants_public.csv': ['code_clpe', 'dispositif', 'public', 'nb_sortants', 'nb_acces_6m', 'nb_presence_6m'],
    'faits/inscrits_public.csv': ['code_clpe', 'public', 'nb_inscrits', 'nb_acces_6m'],
    'faits/formation_metier.csv': ['code_clpe', 'code_rome', 'nb_entrees', 'nb_sortants', 'nb_acces_6m'],
    'faits/offres_metier.csv': ['code_clpe', 'code_rome', 'nb_offres'],
    'faits/demande_offres_mois.csv': ['code_clpe', 'mois', 'nb_defm_abc', 'nb_offres'],
    'faits/problematiques.csv': ['code_clpe', 'code_problematique', 'volume', 'numerateur'],
}
DISP = {'AFC', 'CPF', 'PRF', 'AIF', 'POEI', 'AFPR'}
PUB = {'BRSA', 'BOE', 'SEN50', 'JEU26', 'NIVBAC', 'AUTRES'}
LEV = {'L%d' % i for i in range(1, 11)}
ERR, WARN = [], []
def err(m): ERR.append(m)
def warn(m): WARN.append(m)

def read(name):
    p = os.path.join(DATA, name)
    if not os.path.exists(p):
        err('%s : fichier absent' % name); return []
    with open(p, encoding='utf-8-sig', newline='') as f:
        r = csv.DictReader(f, delimiter=';')
        h = [c.strip() for c in (r.fieldnames or [])]
        manque = [c for c in COLS[name] if c not in h]
        if manque: err('%s : colonnes manquantes %s' % (name, ', '.join(manque)))
        return [{k.strip(): (v or '').strip() for k, v in row.items() if k} for row in r]

def ent(name, i, row, col, vide=False):
    v = row.get(col, '')
    if v == '':
        if not vide: err('%s ligne %d : %s vide' % (name, i + 2, col))
        return None
    if not re.fullmatch(r'\d+', v):
        err('%s ligne %d : %s doit être un entier positif (%r)' % (name, i + 2, col, v)); return None
    n = int(v)
    if SEUIL and 0 < n < SEUIL and col.startswith('nb_'):
        warn('%s ligne %d : %s = %d, sous le seuil de secret statistique (%d)' % (name, i + 2, col, n, SEUIL))
    return n

T = {name: read(name) for name in COLS}
clpe = {r['code_clpe'] for r in T['ref/territoires.csv']}
rome = {r['code_rome'] for r in T['ref/metiers.csv']}
prob = {r['code_problematique'] for r in T['ref/problematiques.csv']}
if len(clpe) != len(T['ref/territoires.csv']): err('ref/territoires.csv : codes CLPE en double')

unites = clpe | {'DEP-' + r['code_departement'] for r in T['ref/territoires.csv']} | {'REG-' + r['code_region'] for r in T['ref/territoires.csv']}
for i, r in enumerate(T['ref/proches.csv']):
    for c in ('code_clpe', 'code_clpe_proche'):
        if r[c] not in unites: err('ref/proches.csv ligne %d : %s inconnu (%s)' % (i + 2, c, r[c]))
    if r['code_clpe'][:4] != r['code_clpe_proche'][:4] and (r['code_clpe'][:4] in ('DEP-', 'REG-') or r['code_clpe_proche'][:4] in ('DEP-', 'REG-')):
        err('ref/proches.csv ligne %d : les deux territoires doivent être du même niveau (CLPE, DEP- ou REG-)' % (i + 2))
    if r['code_clpe'] == r['code_clpe_proche']: err('ref/proches.csv ligne %d : un CLPE ne peut pas être son propre territoire proche' % (i + 2))
sans = clpe - {r['code_clpe'] for r in T['ref/proches.csv']}
if sans: err('ref/proches.csv : CLPE sans territoire proche : %s' % ', '.join(sorted(sans)))
for i, r in enumerate(T['ref/metiers.csv']):
    if r['niveau_tension'] not in ('', 'TRES_FORTE', 'FORTE', 'MODEREE'): err('ref/metiers.csv ligne %d : niveau_tension inconnu (%s)' % (i + 2, r['niveau_tension']))
    if r['lien_formation_metier'] not in ('', 'FORT', 'MOYEN', 'FAIBLE'): err('ref/metiers.csv ligne %d : lien_formation_metier inconnu' % (i + 2))
    if r['pre_qualifiant'] not in ('OUI', 'NON'): err('ref/metiers.csv ligne %d : pre_qualifiant doit valoir OUI ou NON' % (i + 2))
for i, r in enumerate(T['ref/problematiques.csv']):
    if r['objectif'] not in ('PERSONNES', 'ENTREPRISES'): err('ref/problematiques.csv ligne %d : objectif doit valoir PERSONNES ou ENTREPRISES' % (i + 2))
for i, r in enumerate(T['ref/leviers.csv']):
    if r['code_levier'] not in LEV: warn('ref/leviers.csv ligne %d : code %s inconnu de la page, ignoré' % (i + 2, r['code_levier']))
    if r['facilite'] and r['facilite'] not in '12345': err('ref/leviers.csv ligne %d : facilite entre 1 et 5' % (i + 2))
    if r['niveau_actuel_defaut'] and r['niveau_actuel_defaut'] not in '01234': err('ref/leviers.csv ligne %d : niveau_actuel_defaut entre 0 et 4' % (i + 2))

def faits(name, cle, extra):
    vus = set()
    for i, r in enumerate(T[name]):
        if r.get('code_clpe') not in clpe: err('%s ligne %d : code_clpe inconnu (%s)' % (name, i + 2, r.get('code_clpe')))
        k = tuple(r.get(c) for c in cle)
        if k in vus: err('%s ligne %d : doublon sur %s' % (name, i + 2, ', '.join(cle)))
        vus.add(k)
        extra(i, r)

MOIS = re.compile(r'\d{4}-(0[1-9]|1[0-2])$')
def sm(i, r):
    n = 'faits/sortants_mois.csv'
    if not MOIS.match(r['mois_sortie']): err('%s ligne %d : mois_sortie au format AAAA-MM' % (n, i + 2))
    if r['dispositif'] not in DISP: err('%s ligne %d : dispositif inconnu (%s)' % (n, i + 2, r['dispositif']))
    s = ent(n, i, r, 'nb_sortants')
    for c in ('nb_acces_1m', 'nb_acces_3m', 'nb_acces_6m', 'nb_presence_6m', 'nb_publics_prioritaires', 'somme_delais_jours'):
        v = ent(n, i, r, c, vide=True)
        if v is not None and s is not None and c != 'somme_delais_jours' and v > s: err('%s ligne %d : %s > nb_sortants' % (n, i + 2, c))
    a1, a3, a6 = (int(r[c]) if r[c].isdigit() else None for c in ('nb_acces_1m', 'nb_acces_3m', 'nb_acces_6m'))
    if a1 is not None and a3 is not None and a1 > a3: warn('%s ligne %d : accès à 1 mois > accès à 3 mois' % (n, i + 2))
    if a3 is not None and a6 is not None and a3 > a6: warn('%s ligne %d : accès à 3 mois > accès à 6 mois' % (n, i + 2))
    if r['dispositif'] == 'CPF' and r['nb_publics_prioritaires'] != '': warn('%s ligne %d : publics prioritaires renseignés pour le CPF (non suivis)' % (n, i + 2))
faits('faits/sortants_mois.csv', ['code_clpe', 'mois_sortie', 'dispositif'], sm)
def sp(i, r):
    n = 'faits/sortants_public.csv'
    if r['dispositif'] not in DISP: err('%s ligne %d : dispositif inconnu' % (n, i + 2))
    if r['public'] not in PUB: err('%s ligne %d : public inconnu (%s)' % (n, i + 2, r['public']))
    s = ent(n, i, r, 'nb_sortants')
    for c in ('nb_acces_6m', 'nb_presence_6m'):
        v = ent(n, i, r, c)
        if v is not None and s is not None and v > s: err('%s ligne %d : %s > nb_sortants' % (n, i + 2, c))
faits('faits/sortants_public.csv', ['code_clpe', 'dispositif', 'public'], sp)
def ip(i, r):
    n = 'faits/inscrits_public.csv'
    if r['public'] not in PUB: err('%s ligne %d : public inconnu' % (n, i + 2))
    s = ent(n, i, r, 'nb_inscrits'); v = ent(n, i, r, 'nb_acces_6m')
    if s is not None and v is not None and v > s: err('%s ligne %d : nb_acces_6m > nb_inscrits' % (n, i + 2))
faits('faits/inscrits_public.csv', ['code_clpe', 'public'], ip)
def fm(i, r):
    n = 'faits/formation_metier.csv'
    if r['code_rome'] not in rome: err('%s ligne %d : code_rome absent de ref/metiers.csv (%s)' % (n, i + 2, r['code_rome']))
    ent(n, i, r, 'nb_entrees'); s = ent(n, i, r, 'nb_sortants'); v = ent(n, i, r, 'nb_acces_6m')
    if s is not None and v is not None and v > s: err('%s ligne %d : nb_acces_6m > nb_sortants' % (n, i + 2))
faits('faits/formation_metier.csv', ['code_clpe', 'code_rome'], fm)
def om(i, r):
    if r['code_rome'] not in rome: err('faits/offres_metier.csv ligne %d : code_rome inconnu (%s)' % (i + 2, r['code_rome']))
    ent('faits/offres_metier.csv', i, r, 'nb_offres')
faits('faits/offres_metier.csv', ['code_clpe', 'code_rome'], om)
def do(i, r):
    if not MOIS.match(r['mois']): err('faits/demande_offres_mois.csv ligne %d : mois au format AAAA-MM' % (i + 2))
    ent('faits/demande_offres_mois.csv', i, r, 'nb_defm_abc', vide=True); ent('faits/demande_offres_mois.csv', i, r, 'nb_offres', vide=True)
faits('faits/demande_offres_mois.csv', ['code_clpe', 'mois'], do)
def pr(i, r):
    n = 'faits/problematiques.csv'
    if r['code_problematique'] not in prob: err('%s ligne %d : code_problematique inconnu (%s)' % (n, i + 2, r['code_problematique']))
    v = ent(n, i, r, 'volume'); m = ent(n, i, r, 'numerateur')
    if v is not None and m is not None and m > v: err('%s ligne %d : numerateur > volume' % (n, i + 2))
faits('faits/problematiques.csv', ['code_clpe', 'code_problematique'], pr)

# coherences entre fichiers
mois = sorted({r['mois_sortie'] for r in T['faits/sortants_mois.csv']})
m6 = sorted({r['mois_sortie'] for r in T['faits/sortants_mois.csv'] if r['nb_acces_6m'] != ''})
if len(m6) < 24: err('faits/sortants_mois.csv : 24 mois avec accès à 6 mois attendus, %d trouvés' % len(m6))
if len(mois) != 27: warn('faits/sortants_mois.csv : 27 mois attendus (24 mesurés à 6 mois + 3 récents), %d trouvés' % len(mois))
md = sorted({r['mois'] for r in T['faits/demande_offres_mois.csv'] if r['nb_defm_abc'] != ''})
mo = sorted({r['mois'] for r in T['faits/demande_offres_mois.csv'] if r['nb_offres'] != ''})
if len(md) < 24: err('faits/demande_offres_mois.csv : 24 mois de demande d\'emploi attendus, %d trouvés' % len(md))
if len(mo) < 24: err('faits/demande_offres_mois.csv : 24 mois d\'offres attendus, %d trouvés' % len(mo))
win = set(m6[-12:])
for c in sorted(clpe):
    a = sum(int(r['nb_sortants']) for r in T['faits/sortants_mois.csv'] if r['code_clpe'] == c and r['mois_sortie'] in win and r['nb_sortants'].isdigit())
    b = sum(int(r['nb_sortants']) for r in T['faits/sortants_public.csv'] if r['code_clpe'] == c and r['nb_sortants'].isdigit())
    d = sum(int(r['nb_sortants']) for r in T['faits/formation_metier.csv'] if r['code_clpe'] == c and r['nb_sortants'].isdigit())
    for lib, x in (('sortants_public', b), ('formation_metier', d)):
        if a and abs(x - a) / a > .02: warn('%s : %d sortants sur 12 mois dans sortants_mois, %d dans %s (écart > 2 %%)' % (c, a, x, lib))

try:
    meta = json.load(open(os.path.join(DATA, 'meta.json'), encoding='utf-8'))
    p = meta.get('periode_12_mois', {})
    if m6 and (p.get('debut'), p.get('fin')) != (m6[-12], m6[-1]): warn('meta.json : periode_12_mois %s - %s, les données donnent %s - %s' % (p.get('debut'), p.get('fin'), m6[-12], m6[-1]))
    PER = {x.get('code'): x for x in meta.get('periodes', [])}
    if not PER: warn('meta.json : rubrique "periodes" absente (les périodes ne seront pas affichées)')
    attendu = {'sortants': m6[-12:], 'sortants_recents': [m for m in mois if m > (m6[-1] if m6 else '')], 'demande': md[-12:], 'offres': mo[-12:], 'acces_de': m6[-12:]}
    for code, ms in attendu.items():
        x = PER.get(code)
        if x is None:
            if PER: warn('meta.json : période "%s" absente' % code)
            continue
        if ms and (x.get('debut'), x.get('fin')) != (ms[0], ms[-1]): warn('meta.json : période "%s" %s - %s, les données donnent %s - %s' % (code, x.get('debut'), x.get('fin'), ms[0], ms[-1]))
    for code, x in PER.items():
        if x.get('nature') not in ('stock', 'flux'): err('meta.json : période "%s", nature doit valoir stock ou flux' % code)
        for k in ('debut', 'fin'):
            if not MOIS.match(str(x.get(k, ''))): err('meta.json : période "%s", %s au format AAAA-MM' % (code, k))
except Exception as e:
    err('meta.json : illisible (%s)' % e)

for m in WARN[:200]: print('ATTENTION', m)
if len(WARN) > 200: print('... %d avertissements au total' % len(WARN))
for m in ERR[:200]: print('ERREUR', m)
print('%d erreur(s), %d avertissement(s)' % (len(ERR), len(WARN)))
sys.exit(1 if ERR else 0)
