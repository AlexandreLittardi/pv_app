# Projet pv_layout_app
Application Tkinter de layout et stringing photovoltaïque. Python 3.12, Pillow.
Architecture : PVLayoutRibbonApp (app.py) hérite de mixins (dossier mixins/).

## Règles
- Avant toute exploration, lis CODEMAP.md (une seule fois par tâche).
- Pour un fichier marqué GROS FICHIER, ne lis que la plage de lignes utile.
- Ne lis jamais pv_projects/. Ne relis pas un fichier déjà lu.
- Modifie par petits diffs, sans refactor non demandé.
- Après modification du code : `python3 tools/gen_codemap.py`.
- Pour ajouter un onglet, suis .roo/rules/add-tab.md.
- Travaille sur une branche git, jamais sur main.
- Réponses courtes, sans recopier le code existant.
# Ajouter un onglet (Tkinter, ruban ttk.Notebook)

Onglets actuels (index dans le Notebook) : 0 Fichier, 1 Toit, 2 Layout, 3 Stringing,
4 Répartition MPPT, 5 Chemins, 6 Ombre Pylône, 7 Matériel, 8 Schéma Unifilaire.

## RÈGLE CRITIQUE
`_on_ribbon_tab_changed` (mixins/zone_tools.py, ~L257) compare l'onglet actif à des
NUMÉROS EN DUR (`idx == 3`, `idx == 6`...). Un nouvel onglet se place TOUJOURS À LA FIN
(prochain index libre : 9). Ne jamais insérer au milieu : cela décale tous les autres.

## Étapes
1. Créer `mixins/<nom>_tools.py` avec `class <Nom>ToolsMixin`.
   Reprendre l'en-tête d'imports (tkinter, ttk, HAS_PIL) de mixins/zone_tools.py.
   Logique de calcul dans des fonctions pures (sans `self`), dans un module séparé.
2. État : méthode `_init_<nom>_state(self)` appelée dans `PVLayoutRibbonApp.__init__`
   (app.py), AVANT `self._build_ribbon_ui()`. Nommer les attributs `<nom>_...`.
3. app.py : `from mixins.<nom>_tools import <Nom>ToolsMixin` et l'ajouter à l'héritage.
4. mixins/ui_builders.py, `_build_ribbon_ui` (~L70-108) : trois ajouts, à la suite des autres :
   - `self.tab_<nom> = ttk.Frame(self.ribbon_notebook, padding=5)`
   - `self.ribbon_notebook.add(self.tab_<nom>, text=" 🔧 Nom ")`
   - `self._build_tab_<nom>_tools()` (défini dans le nouveau mixin)
5. Barre d'outils de l'onglet : widgets packés en `side=tk.LEFT` dans `self.tab_<nom>`,
   `ttk.Menubutton` + `tk.Menu` pour les groupes d'actions, `ttk.Separator(orient=tk.VERTICAL)`
   entre groupes. Pour un Combobox, appeler `self._fix_combobox_popdown_position(combo)`.
6. Panneau latéral (optionnel) : `_build_side_panel_<nom>()` crée `self.side_panel_<nom>`
   (ttk.Frame, non packé), appelé depuis `_build_main_area` (mixins/zone_tools.py, ~L105-115).
7. mixins/zone_tools.py, `_on_ribbon_tab_changed` : ajouter un bloc dans le style des autres
   ```python
   if idx == 9:  # Onglet <Nom>
       self.side_panel_<nom>.pack(side=tk.RIGHT, fill=tk.Y)
       self._refresh_<nom>()
   else:
       self.side_panel_<nom>.pack_forget()
       # réinitialiser ici tout mode d'outil propre à l'onglet
   ```
   Le bloc final `self.draw_grid()` redessine le canvas à chaque changement d'onglet.
8. Sauvegarde (mixins/project_io.py), seulement si l'onglet a des données à conserver :
   - `save_project` : ajouter les clés dans le dict `data` (~L52-86). Types JSON uniquement
     (les tuples deviennent des listes, les clés de dict doivent être des chaînes).
   - `_load_project_file` : ajouter un bloc de lecture (~avant `self.draw_grid()` final, L297) avec
     `data.get("cle", valeur_par_defaut)` pour rester compatible avec les anciens JSON, puis
     rafraîchir l'interface. Toute exception est attrapée et affichée dans une boîte
     "Erreur lors du chargement du fichier JSON" : tester avec un ancien projet.
9. Dessin sur le canvas : passe par `draw_grid` (chercher la méthode, ne pas la lire en entier).
   Utiliser la même conversion coordonnées image ↔ canvas que les autres onglets.
10. Vérifier : `python -c "import app"`, lancer l'appli, ouvrir l'onglet, changer d'onglet
    et revenir, sauvegarder puis recharger un projet existant (pv_projects/), tests pytest sur
    les fonctions pures, puis `python3 tools/gen_codemap.py`.

## Interdits
- Ne pas ajouter de code dans shadow_tools.py, canvas_grid.py ni zone_tools.py (gros fichiers),
  sauf les 2 lignes d'intégration ci-dessus.
- Ne pas modifier l'ordre des onglets existants.
- Ne pas ajouter des dizaines d'attributs dans `__init__` : passer par `_init_<nom>_state`.

## Exemple de référence
L'onglet Schéma Unifilaire (mixins/diagram_tools.py) : état dans `__init__`, barre d'outils
`_build_tab_diagram_tools`, panneau `_build_side_panel_diagram`, `_refresh_diagram_list`,
sauvegarde `diagram_*` dans project_io.py. Lire via CODEMAP.md, par plages de lignes.
