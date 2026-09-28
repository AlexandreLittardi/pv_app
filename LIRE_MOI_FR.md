# Application PV — version corrigée du 28 septembre 2026

## Installation et lancement

Décompresser entièrement l'archive, puis ouvrir le dossier `pv_app`.
Python 3.10 ou plus récent avec Tkinter est nécessaire. Sous Windows, installer Python avec Tcl/Tk et l'ajouter au PATH.

```console
python -m pip install -r requirements.txt
python main.py
```

Sous Windows, `LANCER_WINDOWS.bat` démarre l'application après installation des dépendances. Le paquet contient le code source, pas un nouvel exécutable Windows compilé. Sous Linux, installer le paquet Tkinter de la distribution si nécessaire.

## Ouvrir un projet

Dans Home → Project, ouvrir un fichier du dossier `pv_projects` :

- `Usine_Frimo_517.json` : nouvelle implantation fournie, réellement 517 panneaux. Elle n'a pas été réduite artificiellement à 516.
- `Usine_Frimo_462.json` et `Usine_Frimo_562.json` : autres variantes fournies, normalisées.
- `Volfrigo_516_autoconsumo.json` : référence antérieure à 516 panneaux, avec profil annuel de consommation et résultats recalculés pour les trois options de stockage.

Les images de toiture sont incluses. Conserver le JSON et son image ensemble lors d'un transfert. L'enregistrement dans un nouveau dossier y copie l'image.

## Interface compacte

Le sélecteur à gauche choisit l'espace de travail. La barre reste sur une ligne ; les actions excédentaires se trouvent dans More. « Fields and selectors… » donne accès aux champs masqués, répartis sur plusieurs pages au besoin.

View → Show / hide panel permet de basculer entre panneau et plan sur petit écran. View → Fit roof to window ajuste le plan à la fenêtre. Un zoom manuel désactive cet ajustement automatique jusqu'à sa réactivation. La barre de défilement globale a été supprimée ; les tableaux conservent leur défilement local pour rendre toutes leurs colonnes accessibles.

## Énergie, stockage et économie

Choisir Energy / BESS :

1. Data → Import consumption Excel : importer les consommations horaires au format de la version précédente (date, jour, 24 heures).
2. Facultatif : télécharger la météo historique ou importer son JSON. Sans météo, le calcul reste une estimation à ciel clair, et ne devient pas une prévision météorologique réelle. Le téléchargement nécessite Internet. Un profil météo d'irradiation dans un seul plan est refusé si les panneaux ont plusieurs orientations incompatibles.
3. Settings : facteur AC et réglages du stockage. Par défaut : 522,496 kWh nominaux par armoire, SOC 10–90 %, rendement aller-retour 90 %, charge totale 250 kW et décharge totale 150 kW. Ces plafonds sont partagés, y compris avec deux armoires.
4. Calculate 3 options : calcul horaire sans batterie, avec une batterie et avec deux batteries. Priorité : consommation directe, charge sur surplus PV, puis export ; limitation du surplus au-delà du plafond d'export. Pas de charge depuis le réseau ni de vente d'énergie déchargée des batteries dans ce modèle.
5. Results : comparaison annuelle/mensuelle, graphique annuel, détail de chaque journée, économie et exports CSV.

Les courbes distinguent production, consommation, prélèvement et injection ; le détail journalier montre notamment le prélèvement nocturne et le SOC. Le modèle part du SOC minimal, sans énergie initiale gratuite. Les résultats liés à une ancienne géométrie, un ancien profil ou d'anciens réglages demandent un recalcul.

Economics / export / EMS permet de comparer achat à 0,25 ou 0,32 €/kWh (ou une autre valeur), vente à 0,07 et 0,08 €/kWh, investissement PV de 250 000 € et 50 000 € par BESS. Ces valeurs sont modifiables.

- Coût annuel net = achats résiduels au réseau − revenus des injections.
- Économie annuelle = coût énergétique sans installation − coût annuel net.
- Retour simple = investissement / économie annuelle.
- Le bénéfice supplémentaire du stockage déduit les revenus d'injection perdus.

Les coûts fixes du contrat, taxes, maintenance, financement, dégradation et remplacements ne sont pas chiffrés. Le calcul EMS est une simulation ; il ne pilote aucun équipement réel. La puissance contractuelle de 507 kW reste distincte de la demande d'injection de 300 kW, non considérée comme une autorisation acquise.

## Câbles et schémas

Cabling recalcule les chemins des deux extrémités de chaque chaîne jusqu'à son onduleur. L'inventaire et le CSV distinguent conducteur A, conducteur B et total A+B. Les altitudes de toiture sont prises en compte. Un chemin non relevé est signalé comme estimation. Modifier la géométrie ou les chemins invalide les itinéraires stockés.

Le calcul de chute de tension exploite la boucle complète. La section obtenue ne valide pas à elle seule l'intensité admissible, le mode de pose, le regroupement, les températures ni les protections. A/B désigne les deux extrémités : la polarité physique doit être vérifiée au câblage.

Dans **Electrical single-line diagram → Site wiring → Detailed wiring editor…**, choisir 0, 1 ou 2 armoires, puis compléter les pages Site, PV strings, Inverters AC et BESS / grid. L'éditeur donne la répartition réelle de chaque chaîne sur l'onduleur et le MPPT, les parcours A+B encore valides et les champs de câble, fusible, sectionneur et parafoudre. Renseigner la tension composée pour obtenir le courant AC nominal calculé des onduleurs, puis les départs AC, protections générales, comptage et commande d'injection. **Refresh checks** affiche toutes les données encore absentes. **Save settings and project** conserve les choix dans le JSON ; **Drawing / exports** montre le SVG courant et propose le SVG ou le bordereau CSV avec aperçu. Le menu Site wiring permet aussi un export SVG direct depuis les réglages déjà enregistrés.

Le schéma détaillé représente trois hybrides DEYE 125 kVA. Pour **un MC-L522**, il raccorde ses deux clusters respectivement aux ports BAT de INV1 et INV2 ; INV3 reste dédié au PV. Le document DEYE reçu montre aussi un onduleur de chaîne 136 kW, remplacé ici par le troisième hybride demandé. Avec **deux MC-L522**, la connexion du second reste visiblement à définir : demander au fabricant un schéma d'extension validé avant d'affecter des ports BAT en doublon. Le dessin exporté inclut le bordereau des 31 chaînes du projet 516 et la liste exhaustive des points à vérifier. Un changement des chaînes, des positions, des itinéraires ou du raccordement réseau signale la nécessité d'une nouvelle vérification des réglages.

Les liaisons chaînes → MPPT sont reconstruites à partir des affectations du projet. Le contrôle électrique existant permet de renseigner les caractéristiques réelles du module et de l'onduleur, puis vérifie Voc à froid, Vmp STC, courants MPPT et puissance PV par onduleur.

Les caractéristiques absentes ne sont pas inventées. Les dimensions de module existantes sont conservées en attendant confirmation de la référence exacte. L'ancien export de site préliminaire reste dans le code à titre de compatibilité ; le menu utilise maintenant le schéma détaillé avec raccordement BAT DC. Les vérifications VF/incendie, protections finales, Vmp à chaud, gains bifaciaux, limites par entrée, conformité réseau et dimensionnement d'exécution nécessitent les données du matériel et une validation d'ingénierie.

## Vérifications réalisées

- 16 tests automatiques : cohérence des projets, numérotation, liaisons, portabilité des images, stockage/limitation, économie, exports SVG, caractéristiques manquantes, topologie DC/BAT détaillée, année solaire et rendu des équations.
- Ouverture des quatre projets et essais des dix espaces de travail à 640×480, 800×600, 1024×768 et 1366×768 sous Tk/Linux.
- Enregistrement/réouverture dans un autre dossier, routage des deux conducteurs et accès aux commandes masquées.
- Recalcul des 8 760 heures du projet 516 et contrôle visuel des fenêtres de résultats à 640×480.

Les tests d'interface n'ont pas été exécutés sous Windows natif. Commandes reproductibles :

```console
python -m unittest discover -s tests -v
python tools/test_gui.py
```

Le second test nécessite un affichage graphique (ou Xvfb sous Linux).

## Accueil, navigation et tableur (mise à jour)

Home affiche les quinze derniers projets ouverts, leur chemin et date de dernière ouverture. Double cliquer sur un projet ou utiliser « Open selected » pour le rouvrir. L'historique reste disponible entre deux lancements sur le même poste. Les pages du guide expliquent les espaces de travail et les formules calculées ; voir la mise à jour plus bas.

Sur le plan, un clic gauche glissé déplace la vue dans tous les onglets où il est visible ; les modes de dessin et de déplacement d'objets gardent leurs gestes dédiés. Sur un petit écran, View permet d'alterner entre le panneau et le plan.

Installation area nomme la surface délimitée « Cable routing area », distincte des zones de pose et des tracés de câbles. Layout and blocks regroupe les commandes en quatre menus : Panel, Layout, Block et Inverter. Panel configure dimensions, inclinaison et azimut. L'orientation s'applique aux panneaux sélectionnés, ou devient le défaut en l'absence de sélection.

Dans Stringing, une étiquette marque le début de chaque chaîne ; les numéros détaillés s'affichent pour la chaîne active. Les trajets colorés et l'arborescence restent utilisables pour suivre les chaînes.

Chaque export CSV montre un aperçu avant sauvegarde. « Save CSV… » choisit le fichier final ; « Cancel » n'en crée aucun. Cela concerne les chaînes, MPPT, câbles, tableur, ombres, économie et énergie horaire.

Dans Spreadsheet, glisser sélectionne une plage et la poignée bleue en bas à droite la prolonge. Deux nombres de départ créent une suite ; les formules recopiées ajustent leurs références relatives. Ctrl+C/Ctrl+V copie/colle une plage. En éditant une formule, cliquer une autre cellule insère son adresse au curseur. Les variables proposées sont en anglais. Les formules françaises des anciens projets sont converties lors de l'ouverture et enregistrées en anglais, sans modifier les textes ordinaires.

## Mise à jour du guide et de l'interface

Home affiche un historique raccourci et deux pages de guide en anglais : **How it works** et **Formulas**. Les équations sont rendues mathématiquement ; la note technique complète et corrigée s'ouvre depuis **Open full technical note (PDF)**, et figure aussi dans `docs/technical_note_updated.pdf`. Installer les dépendances actualisées, notamment Matplotlib, avec `python -m pip install -r requirements.txt`.

La rangée d'onglets redevient visible ; le sélecteur de pages reste accessible sur les écrans étroits. Le menu View a été remplacé par un petit bouton Panel. Chaque barre de plan utilise des boutons discrets −, remise à zéro et + ; **Fit roof to window** se trouve dans Home → Project. L'image de toiture s'importe dans le même menu. Dans Installation area, Ctrl + clic droit supprime une mesure à proximité d'une extrémité ou de son étiquette. Les badges S1, S2, etc. n'apparaissent que dans les vues utiles et se placent hors des numéros des modules.

Les panneaux latéraux de Stringing et MPPT assignment sont initialement masqués sur une fenêtre étroite ; le bouton Panel les ouvre. Dans Shadow, les paramètres sont empilés dans une barre à gauche avec défilement interne. Cabling distingue visuellement les deux conducteurs A et B. Energy / BESS dispose d'une page de résultats propres en anglais, sans toile de toiture, avec les valeurs annuelles des trois options et leurs commandes de calcul et graphiques. Dans le schéma d'exploration, les liaisons générées suivent des tronçons orthogonaux ; le schéma d'ingénierie exporté par Site wiring reste le document de câblage détaillé.

La note d'Alexandre a été confrontée au code : les simulations datées utilisent l'année réelle (365/366 jours), tandis que l'aperçu Shadow sans année reste calculé sur 2024. Le bilan annuel météo utilise l'irradiance et la température ambiante horaires importées, et le ciel clair est une autre source. Le dimensionnement DC repose sur les deux trajets A+B ; la simulation horaire ajoute les limites de puissance et de SOC, les pertes, l'injection et le coût net. Les équations ne valident pas l'ampacité, les protections ni une conformité réseau.
