import sys
import ctypes
import wx
from main import FenetrePrincipale

def run_as_admin():
    """Demande les droits d'administrateur si nécessaire."""
    if ctypes.windll.shell32.IsUserAnAdmin():
        # Exécution avec les droits administrateurs
        app = wx.App(False)
        fenetre = FenetrePrincipale(None)
        fenetre.Show()
        app.MainLoop()
    else:
        # Relance le script en mode administrateur
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, __file__, None, 1
        )
        sys.exit()

if __name__ == "__main__":
    run_as_admin()
