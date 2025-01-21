import os
import shutil
import wx
import sys

def resource_path(relative_path):
    """Obtenir le chemin absolu vers les ressources, même si elles sont intégrées dans un .exe."""
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)

# Déterminer le chemin du dossier de logs dans AppData
appdata_path = os.path.join(os.getenv('LOCALAPPDATA'), "NoTemp")
if not os.path.exists(appdata_path):
    os.makedirs(appdata_path)

log_folder = os.path.join(appdata_path, "log")
if not os.path.exists(log_folder):
    os.makedirs(log_folder)

# Fonction pour obtenir la taille d'un fichier ou d'un dossier
def obtenir_taille(chemin):
    taille_totale = 0
    try:
        if os.path.isfile(chemin):
            taille_totale = os.path.getsize(chemin)
        else:
            for chemin_dossier, dossiers, fichiers in os.walk(chemin):
                for fichier in fichiers:
                    fp = os.path.join(chemin_dossier, fichier)
                    taille_totale += os.path.getsize(fp)
    except (PermissionError, FileNotFoundError):
        pass
    return taille_totale

# Fonction pour analyser les fichiers temporaires
def analyser_temp():
    dossiers_temp = [
        os.getenv('TEMP'),
        os.path.expanduser('~\\AppData\\Local\\Temp'),
        os.path.expanduser('C:\\Windows\\Temp')
    ]
    fichiers_temp = []
    taille_totale = 0

    # Écriture des résultats dans un fichier log dans AppData
    fichier_log = os.path.join(log_folder, "temp_files_log.txt")
    with open(fichier_log, "w", encoding="utf-8") as log:
        log.write("Fichiers temporaires trouvés :\n")
        for dossier_temp in dossiers_temp:
            if os.path.exists(dossier_temp):
                for root, _, fichiers in os.walk(dossier_temp):
                    for fichier in fichiers:
                        chemin_fichier = os.path.join(root, fichier)
                        fichiers_temp.append(chemin_fichier)
                        taille_totale += obtenir_taille(chemin_fichier)
                        log.write(f"{chemin_fichier}\n")
        log.write(f"\nTaille totale : {taille_totale / (1024 * 1024):.2f} MB\n")

    return fichiers_temp, taille_totale

def supprimer_temp(fichiers_temp):
    fichiers_supprimes = 0
    fichiers_echoues = []

    fichier_log = os.path.join(log_folder, "delete_report.txt")
    
    with open(fichier_log, "w", encoding="utf-8") as log:
        for fichier in fichiers_temp:
            try:
                if os.path.isfile(fichier):
                    os.remove(fichier)
                    fichiers_supprimes += 1
                elif os.path.isdir(fichier):
                    shutil.rmtree(fichier)
                    fichiers_supprimes += 1
            except Exception as e:
                fichiers_echoues.append((fichier, str(e)))

        log.write(f"Fichiers supprimés : {fichiers_supprimes}\n")
        if fichiers_echoues:
            log.write("Échecs de suppression :\n")
            for fichier, erreur in fichiers_echoues:
                log.write(f"{fichier} : {erreur}\n")

    # Vérification si le fichier a bien été créé
    if os.path.exists(fichier_log):
        print(f"Le rapport de suppression a été généré : {fichier_log}")
    else:
        print("Erreur : Le rapport de suppression n'a pas été créé.")

    return fichiers_supprimes, len(fichiers_echoues)

# Classe de la fenêtre principale wxPython
class FenetrePrincipale(wx.Frame):
    def __init__(self, *args, **kwargs):
        super(FenetrePrincipale, self).__init__(*args, **kwargs)

        self.fichiers_temp = []

        self.SetTitle("NoTemp - Nettoyeur de fichiers temporaires")
        self.SetSize((800, 500))
        self.Center()

        # Charger l'icône
        icon_path = resource_path("icon.ico")
        self.SetIcon(wx.Icon(icon_path, wx.BITMAP_TYPE_ICO))

        # MenuBar
        menubar = wx.MenuBar()

        menu_fichier = wx.Menu()
        rapport_menu = wx.Menu()

        # Ajouter les éléments de menu et stocker leurs IDs
        id_analyser = wx.NewIdRef()
        id_supprimer = wx.NewIdRef()

        rapport_menu.Append(id_analyser, "Analyser", "Ouvrir le rapport d'analyse")
        rapport_menu.Append(id_supprimer, "Supprimer", "Ouvrir le rapport de suppression")
        menu_fichier.AppendSubMenu(rapport_menu, "Rapport")

        menu_fichier.Append(wx.ID_EXIT, "Fermer")

        menu_help = wx.Menu()
        menu_help.Append(wx.ID_ABOUT, "À propos")

        menubar.Append(menu_fichier, "Fichier")
        menubar.Append(menu_help, "?")
        self.SetMenuBar(menubar)

        # Gestion des événements du menu en utilisant les IDs stockés
        self.Bind(wx.EVT_MENU, self.ouvrir_rapport_analyse, id=id_analyser)
        self.Bind(wx.EVT_MENU, self.ouvrir_rapport_suppression, id=id_supprimer)
        self.Bind(wx.EVT_MENU, self.on_close, id=wx.ID_EXIT)
        self.Bind(wx.EVT_MENU, self.afficher_a_propos, id=wx.ID_ABOUT)

        # Panneau principal
        panneau = wx.Panel(self)

        vbox = wx.BoxSizer(wx.VERTICAL)

        self.affichage_fichiers = wx.TextCtrl(panneau, style=wx.TE_MULTILINE | wx.TE_READONLY, size=(750, 300))
        vbox.Add(self.affichage_fichiers, flag=wx.ALL, border=10)

        self.label_resultat = wx.StaticText(panneau, label="Cliquez sur 'Analyser' pour commencer.")
        vbox.Add(self.label_resultat, flag=wx.ALL, border=10)

        hbox = wx.BoxSizer(wx.HORIZONTAL)
        bouton_analyser = wx.Button(panneau, label="Analyser")
        bouton_analyser.Bind(wx.EVT_BUTTON, self.sur_analyser)
        hbox.Add(bouton_analyser, flag=wx.RIGHT, border=10)

        bouton_nettoyer = wx.Button(panneau, label="Nettoyer")
        bouton_nettoyer.Bind(wx.EVT_BUTTON, self.sur_nettoyer)
        hbox.Add(bouton_nettoyer, flag=wx.LEFT, border=10)

        vbox.Add(hbox, flag=wx.ALIGN_CENTER | wx.ALL, border=10)
        panneau.SetSizer(vbox)

    def sur_analyser(self, event):
        self.fichiers_temp, taille_totale = analyser_temp()
        taille_mb = taille_totale / (1024 * 1024)
        self.label_resultat.SetLabel(f"Fichiers trouvés : {len(self.fichiers_temp)}\nTaille totale : {taille_mb:.2f} Mo")

        self.affichage_fichiers.Clear()
        for fichier in self.fichiers_temp:
            self.affichage_fichiers.AppendText(fichier + "\n")

    def sur_nettoyer(self, event):
        if not self.fichiers_temp:
            wx.MessageBox("Aucun fichier temporaire à supprimer.", "Nettoyage", wx.OK | wx.ICON_INFORMATION)
            return

        confirmation = wx.MessageBox("Êtes-vous sûr de vouloir supprimer ces fichiers ?", "Confirmation", wx.YES_NO | wx.ICON_QUESTION)

        if confirmation == wx.YES:
            fichiers_supprimes, fichiers_echoues = supprimer_temp(self.fichiers_temp)
            wx.MessageBox(
                f"Nettoyage terminé ! {fichiers_supprimes} fichiers supprimés.\n"
                f"{fichiers_echoues} fichiers n'ont pas pu être supprimés. Consultez 'log/delete_report.txt' pour plus de détails.",
                "Nettoyage",
                wx.OK | wx.ICON_INFORMATION
            )
            self.label_resultat.SetLabel("Nettoyage terminé. Relancez l'analyse pour vérifier.")

    def ouvrir_rapport_analyse(self, event):
        fichier_analyse = os.path.join(log_folder, "temp_files_log.txt")
        if os.path.exists(fichier_analyse):
            os.startfile(fichier_analyse)
        else:
            wx.MessageBox("Le fichier de rapport d'analyse est introuvable.", "Erreur", wx.OK | wx.ICON_ERROR)

    def ouvrir_rapport_suppression(self, event):
        fichier_suppression = os.path.join(log_folder, "delete_report.txt")
        if os.path.exists(fichier_suppression):
            os.startfile(fichier_suppression)
        else:
            wx.MessageBox("Le fichier de rapport de suppression est introuvable.", "Erreur", wx.OK | wx.ICON_ERROR)

    def afficher_a_propos(self, event):
        wx.MessageBox("NoTemp - Version 1.0\nDéveloppé par GR Computer.", "À propos", wx.OK | wx.ICON_INFORMATION)

    def on_close(self, event):
        self.Close()

if __name__ == "__main__":
    app = wx.App(False)
    fenetre = FenetrePrincipale(None)
    fenetre.Show()
    app.MainLoop()
