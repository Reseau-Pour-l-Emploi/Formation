# Parcours Formation | Tableau de bord RPE

Parcours guidé dans les données du tableau de bord du Réseau pour l'emploi : **« Envoyons-nous les bonnes personnes dans les bonnes formations (dispositif et métier) ? »**

Trois étapes : **Situer** (six repères), **Comprendre** (trois questions), **Agir** (pistes, simulation, récapitulatif exportable). Méthode exploratoire : une approche parmi d'autres, à compléter avec les partenaires.

> Les données livrées dans `data/` sont **fictives** (14 CLPE inventés). Elles servent de modèle de format.

## Contenu du dépôt

```
index.html               la page (autonome : polices, logos, bibliothèques PDF intégrés, aucun CDN)
modele-donnees.html      dessin d'enregistrement des fichiers de données
data/
  meta.json              version, date de mise à jour, période, bandeau
  ref/                   référentiels : territoires, territoires proches, métiers, problématiques, pistes, évaluations nationales
  faits/                 comptages par CLPE : sortants, publics, inscrits, métiers, offres, demande, problématiques
scripts/
  controle.py            contrôles avant publication (Python 3, bibliothèque standard)
.nojekyll                publication telle quelle par GitHub Pages
```

## Publier sur GitHub Pages

1. Déposer l'ensemble des fichiers à la racine du dépôt (y compris `.nojekyll`).
2. *Settings > Pages* : source « Deploy from a branch », branche principale, dossier `/ (root)`.
3. La page lit les fichiers de `data/` à chaque ouverture (sans cache).

## Adresse d'un territoire

L'étape et le territoire consultés figurent dans l'adresse, à partager ou à mettre en favori :

| Territoire | Exemple d'adresse |
|---|---|
| CLPE | `.../index.html#situer/CLPE00006` |
| Département | `.../index.html#comprendre/DEP-D01` |
| Région | `.../index.html#agir/REG-R01` |

Étapes : `situer`, `comprendre`, `agir`, `methode`. Un département ou une région additionne les comptages de ses CLPE ; il est comparé aux autres départements de sa région, ou aux autres régions (modifiable dans `ref/proches.csv`). Un code inconnu ouvre le dernier territoire consulté.

## Mettre à jour les données

**Actualisation mensuelle, sur 12 mois glissants.** Chaque source garde son propre dernier mois disponible (exemple en novembre 2026) :

| Source | Nature | Dernier mois | 12 mois retenus |
|---|---|---|---|
| Demandeurs d'emploi inscrits | stock | septembre 2026 | octobre 2025 à septembre 2026 |
| Offres d'emploi | flux | juillet 2026 | août 2025 à juillet 2026 |
| Entrées en formation | flux | juin 2026 | juillet 2025 à juin 2026 |
| Sortants de formation, accès à l'emploi à 6 mois | flux | cohorte de février 2026 | mars 2025 à février 2026 |

Ces périodes sont déclarées dans `data/meta.json` (rubrique `periodes`) : la page les affiche avec les limites d'interprétation (périodes décalées, stock et flux), et le script de contrôle vérifie qu'elles correspondent aux données.


1. Extraire les comptages du tableau de bord RPE au format décrit dans `modele-donnees.html` (CSV, séparateur `;`, UTF-8, comptages et jamais de taux).
2. Contrôler : `python3 scripts/controle.py data --seuil 5` (code retour 1 en cas d'erreur bloquante ; `--seuil` signale les effectifs sous le seuil de secret statistique).
3. Mettre à jour `data/meta.json` : `date_mise_a_jour`, `periode_12_mois`, les `periodes` de chaque source, et `donnees` à `reelles` avec un `badge` vide pour retirer la mention de maquette.
4. Commit sur la branche principale : GitHub Pages republie.

Aucune modification de `index.html` n'est nécessaire pour changer les territoires, les territoires proches, les métiers, les problématiques ou les textes et paramètres des pistes (`ref/leviers.csv`).

## Évaluations nationales

`data/ref/evaluations.csv` (une ligne par étude), `data/ref/evaluations_resultats.csv` (une ligne par résultat) et `data/ref/evaluations_definitions.csv` (définitions des termes employés) alimentent le bloc « Ce que disent les évaluations nationales » de l'étape Agir. Chaque résultat est rattaché à des pistes (`L1` à `L10`), à des questions (`q1` à `q3`) et à des métiers (codes ROME). Exemple fourni : Dares, Rapport d'études n° 63, janvier 2025. Les sources sont numérotées et renvoyées en note en bas du bloc. Ces fichiers sont facultatifs : sans eux, le bloc n'apparaît pas.

Le champ et les limites de chaque étude sont obligatoires : ces résultats nationaux ne tiennent pas compte du contexte propre à chaque territoire, et la page le rappelle à côté de chacun d'eux.

## Points d'attention

- **Ouverture en local** (double-clic sur `index.html`) : le navigateur bloque la lecture des fichiers `data/`. La page affiche alors les **données de démonstration intégrées** (copie des CSV fictifs) et l'indique en pied de page. Les fichiers de `data/` ne sont lus qu'une fois la page publiée.
- Même message en pied de page si un fichier de `data/` est absent ou illisible sur GitHub Pages : vérifier le nom et l'emplacement des fichiers.
- **Pistes ajoutées** par l'utilisateur : conservées le temps de la session du navigateur (onglet), jamais envoyées ni stockées sur le dépôt.
- **Exports** (PDF, CSV, copie) : générés dans le navigateur.
- Données : uniquement des agrégats par CLPE, aucune donnée individuelle. Appliquer le secret statistique avant publication, le dépôt pouvant être public.
