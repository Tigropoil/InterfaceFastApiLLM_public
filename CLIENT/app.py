import clientAPI_LLM as capi
import json
import sys
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QLineEdit, QLabel, QFileDialog, QComboBox, QTextEdit, QCheckBox
)
from PyQt6.QtCore import QTimer

def remplir_combobox_model(addr):
    response = capi.get_list_model(addr)
    models = [item['model'] for item in response]
    return models

def remplir_combobox_PDF(addr):
    return capi.get_indexed_pdf(addr)

class Fenetre(QWidget):
    def __init__(self):
        super().__init__()
        self.ip = ""
        self.port = ""
        self.addr = ""
        self.initUI()
    
    def initUI(self):
        layout = QVBoxLayout()
        
        # Adresse IP et Port
        ip_layout = QHBoxLayout()
        self.ip_input = QLineEdit(self)
        self.ip_input.setPlaceholderText("Adresse IP")
        self.port_input = QLineEdit(self)
        self.port_input.setPlaceholderText("Port")
        self.validate_button = QPushButton("Valider")
        ip_layout.addWidget(QLabel("IP :"))
        ip_layout.addWidget(self.ip_input)
        ip_layout.addWidget(QLabel("Port :"))
        ip_layout.addWidget(self.port_input)
        ip_layout.addWidget(self.validate_button)
        layout.addLayout(ip_layout)
        
        self.validate_button.clicked.connect(self.validate_ip_port)
        
        # Désactiver les autres widgets jusqu'à validation
        self.disable_widgets = []
        
        # Première ComboBox (initialement vide)
        self.combo1 = QComboBox()
        self.disable_widgets.append(self.combo1)
        layout.addWidget(self.combo1)



        # Chatbot
        chat_layout = QVBoxLayout()
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_input = QLineEdit()
        self.chat_button = QPushButton("Envoyer")
        self.disable_widgets.extend([self.chat_input, self.chat_button])
        chat_layout.addWidget(QLabel("Chatbot :"))
        chat_layout.addWidget(self.chat_display)
        chat_layout.addWidget(self.chat_input)
        chat_layout.addWidget(self.chat_button)
        layout.addLayout(chat_layout)
        
        self.setLayout(layout)
        self.setWindowTitle("UI API pour LLMs")
        self.resize(500, 400)
        
        # Désactiver les autres widgets initialement
        self.set_widgets_enabled(False)
        
        # Connexions des boutons
        self.chat_button.clicked.connect(self.send_message)
        
    def validate_ip_port(self):
        self.ip = self.ip_input.text().strip()
        self.port = self.port_input.text().strip()
        if self.ip and self.port:
            self.addr = "http://"+self.ip+":"+self.port
            print(f"Adresse IP: {self.ip}, Port: {self.port}")  # Stocker les valeurs
            self.set_widgets_enabled(True)  # Activer les autres widgets
            self.validate_button.setEnabled(False)  # Désactiver le bouton de validation
            
            # Mettre à jour la combo box avec des données
            self.combo1.clear()
            self.combo1.addItems(remplir_combobox_model(self.addr))

    def set_widgets_enabled(self, enabled):
        """ Active ou désactive tous les widgets sauf la partie IP/Port """
        for widget in self.disable_widgets:
            widget.setEnabled(enabled)

    def send_message(self):
        """ Gère l'envoi du message utilisateur et affiche 'Bot : Typing...' """
        message = self.chat_input.text().strip()
        if message:
            self.chat_display.append(f"Vous : {message}")  # Afficher immédiatement le message utilisateur
            self.chat_input.clear()  # Nettoyer l'input utilisateur
            self.chat_display.append(" ")
            self.chat_display.append("Bot : Typing...")  # Afficher immédiatement "Bot : Typing..."
            # Lancer la récupération de la réponse après un court instant
            QTimer.singleShot(100, lambda: self.bot_response(message))  # 100ms pour fluidifier l'affichage

    def bot_response(self, message):
        """ Gère la récupération et l'affichage de la réponse après avoir retiré 'Bot : Typing...' """
        selected_model = self.combo1.currentText()
        
        # Récupérer la réponse depuis l'API
        reponse_json = capi.query(self.addr, selected_model, message)
        reponse = reponse_json['response']['text']
        
        # Supprimer "Bot : Typing..." avant d'afficher la vraie réponse
        texte = self.chat_display.toPlainText().split("\n")
        if texte and texte[-1] == "Bot : Typing...":
            texte.pop()  # Supprimer la ligne "Bot : Typing..."
        
        # Mettre à jour l'affichage avec la réponse
        self.chat_display.setPlainText("\n".join(texte))
        try:
            self.chat_display.append(f"Bot : {reponse}")
        except Exception as e:
            self.chat_display.append(f"Erreur : {str(e)}")
        self.chat_display.append(" ")

            
        

if __name__ == "__main__":
    app = QApplication(sys.argv)
    fenetre = Fenetre()
    fenetre.show()
    sys.exit(app.exec())

