# Corrections — Dear Alexandre(1) et échanges antérieurs

## Cohérence des projets

| Point signalé | Traitement |
|---|---|
| Puissance globale 450 W contre 720 W dans le matériel | Synchronisation à partir de la ligne module ; rendement calculé à partir de la puissance et de la surface. |
| Image introuvable, accents et suffixes de copie | Résolution relative au JSON, prise en charge des anciens noms, images incluses et copie lors d'un enregistrement ailleurs. |
| Références de panneaux supprimés dans la variante 462 | Nettoyage des références orphelines sans déplacement des panneaux restants. |
| Numérotation discontinue | Renumérotation des identifiants affichés lorsque l'option continue est active ; les coordonnées utilisées par chaînes et chemins restent stables. |
| Ancienne confusion 517/516 | Vérification du contenu : la nouvelle variante 517 possède 517 panneaux (21 chaînes de 17 et 10 de 16). Référence 516 fournie séparément. |
| Modèle d'onduleur « ee » | Remplacement par DEYE SUN-125K-SG02HP3-EU-GM10 ; configuration trois hybrides de 125 kW, dix MPPT chacun. Pas de remplacement par un onduleur de chaîne 136 kW. |
| Schéma et affectations MPPT divergents | Reconstruction des connexions automatiques et des nombres de panneaux depuis les données de chaînes ; suppression des connexions chaînes/MPPT obsolètes, conservation des équipements personnalisés. |
| Dimensions de module et données électriques incertaines | Géométrie conservée ; confirmation des dimensions et saisie des caractéristiques dans le contrôle électrique. Les limites manquantes empêchent de présenter une validation complète. |
| Câbles incomplets, un seul conducteur | Calcul A/B, dénivelés, total de boucle, export et vérification de la validité des itinéraires enregistrés. Estimations explicitement identifiées. |

## Fonctions intégrées

- Import des consommations horaires ; simulation annuelle tenant compte des orientations individuelles et de la puissance AC des onduleurs.
- Import/téléchargement météo historique, distinction explicite avec le modèle à ciel clair ; correction du calcul solaire sur l'année réelle et les années bissextiles.
- Comparaison PV seul / un BESS / deux BESS ; puissance de charge commune de 250 kW, au lieu d'une addition automatique des puissances des armoires.
- Courbes annuelles et journalières, réseau nocturne et SOC ; export CSV des bilans.
- Valorisation de l'injection à 7/8 centimes, prix d'achat 0,25/0,32 €, coûts d'investissement, coût annuel net et retours simples/incrémentaux.
- Limitation de l'injection après autoconsommation et charge ; distinction contrat 507 kW/demande d'injection 300 kW ; indications EMS sans commande réelle.
- Exports SVG du schéma unifilaire de site en français/anglais pour les trois scénarios ; saisie et contrôle des données électriques manquantes.
- Sauvegarde des réglages, profils, résultats et itinéraires ; détection des résultats devenus obsolètes après modification des entrées.

## Interface

- Suppression du conteneur de défilement global.
- Une seule ligne de commandes, sélection d'espace de travail et menu More adaptatif.
- Paramètres longs répartis en pages ; panneau plein espace sur petite fenêtre et bascule vers le plan avec View.
- Ajustement du plan à la fenêtre et graphiques redimensionnables ; défilement conservé uniquement à l'intérieur des tableaux qui le nécessitent.

## Points explicitement non certifiés

Le logiciel ne remplace pas les fiches techniques manquantes ni le dimensionnement d'exécution. Les sections issues de la chute de tension, protections AC/DC/BESS, variante exacte des batteries, contraintes VF/incendie et autorisation réseau restent à valider. Le déplacement longitudinal envisagé sur la petite toiture de 3,70 m n'a pas été imposé : vous aviez indiqué réaliser cette implantation vous-mêmes.

La référence 516 livrée contient un calcul annuel à ciel clair : 626 669,74 kWh PV et 485 698,15 kWh de consommation. Ce ne sont pas des résultats de production mesurés ni une estimation corrigée par une météo téléchargée. Deux heures de consommation imputées restent identifiées dans le profil hérité.

## Mise à jour de l'interface demandée ensuite

- Home sans plan : historique local horodaté, ouverture directe, rubriques Tutoriel sans corps rédactionnel.
- Clic-glissé gauche pour déplacer le plan, en respectant les modes de dessin et le déplacement des objets.
- « Polygon » devient « Cable routing area » dans Installation area.
- Quatre groupes Panel, Layout, Block, Inverter ; dimensions et orientation regroupées dans Panel.
- Étiquettes des chaînes allégées et numéros détaillés pour la chaîne active.
- Aperçu avant tous les exports CSV, annulation sans enregistrement.
- Tableur : sélection de plages, recopie et suites par poignée, clic pour insérer une référence dans une formule, copie/colle, noms de variables anglais avec migration des sauvegardes françaises.

## Schéma électrique détaillé du projet actif

- Menu compact Site wiring dans l'onglet Electrical single-line diagram ; éditeur sur cinq pages, sans nouvelle commande sur la barre principale.
- Nomenclature chaînes, panneaux, onduleurs et MPPT tirée des affectations du projet ouvert ; longueurs A+B reprises uniquement si leur calcul est toujours valable. SVG vectoriel et CSV vérifiables avant export.
- Trois onduleurs hybrides DEYE 125 kVA ; premier MC-L522 relié par ses deux clusters aux ports BAT de INV1 et INV2. INV3 reste photovoltaïque. Deuxième armoire présentée comme connexion non définie tant qu'un schéma DEYE d'extension n'est pas disponible.
- Saisie et sauvegarde par chaîne des protections et sections DC, par onduleur des départs AC, par armoire des liaisons batterie et au TGBT du comptage et des protections. Liste des vérifications manquantes visible et reproduite dans le schéma ; un projet modifié exige un nouveau contrôle.

## Liste Fix logiciel.pdf et note technique VE (28 septembre)

- Onglets visibles avec sélecteur conservé, suppression du menu View, boutons de zoom compacts ; image importée via Home → Project.
- Historique Home réduit et guide en deux pages avec fonctions et équations rendues, note technique anglaise révisée accessible par bouton et incluse en PDF.
- Mesure effaçable par Ctrl + clic droit, badges de chaînes S1… et affichage de leurs trajets restreint aux vues spécialisées, volet Stringing/MPPT masqué par défaut sur petit écran.
- Ombres : paramètres en colonne gauche défilante, année réelle transmise au calcul solaire pour les simulations datées ; aperçu sans année toujours sur 2024.
- Schéma électrique d'exploration : génération ordonnée et liaisons orthogonales ; export d'ingénierie et points ouverts rédigés en anglais. Cabling distingue A et B avec légende.
- Energy / BESS : espace de résultats sans image de toiture, résumé annuel 0/1/2 BESS, commandes d'accès et principaux libellés traduits en anglais.
- Note d'origine contrôlée contre le code et étendue aux données météo horaires, à la température ambiante, au câblage A+B, aux contraintes BESS et aux coûts d'achat et d'injection.
