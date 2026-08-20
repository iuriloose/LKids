import json
import os

import pygame
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QIcon, QPainter
from PySide6.QtWidgets import QApplication, QWidget

from core.fazenda import CenaFazenda


class LKids(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("LKids 1.0.1")
        self.setWindowIcon(QIcon(os.path.join(os.path.dirname(__file__), "assets", "app-icon.ico")))
        self.saida_permitida = False
        self.base = os.path.dirname(__file__)
        self.config = self._carregar_config()
        self.cena_fazenda = CenaFazenda(os.path.join(self.base, "assets"), self.config)

        pygame.init()
        pygame.joystick.init()
        self.sons = self._carregar_sons()
        self.controle = None
        if pygame.joystick.get_count() > 0:
            self.controle = pygame.joystick.Joystick(0)
            self.controle.init()

        self.ultimo_movimento_controle = 0
        self.timer_controle = QTimer(self)
        self.timer_controle.timeout.connect(self.verificar_controle)
        self.timer_controle.start(20)

        self.timer_animacao = QTimer(self)
        self.timer_animacao.timeout.connect(self.atualizar_animacao)
        self.timer_animacao.start(16)
        self.showFullScreen()

    def _carregar_config(self):
        caminho = os.path.join(self.base, "configuracao.json")
        with open(caminho, encoding="utf-8") as arquivo:
            return json.load(arquivo)

    def _carregar_sons(self):
        sons = {}
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()
            pasta = os.path.join(self.base, "assets", "sons")
            for nome in ("galinha", "ovelha", "cavalo", "passaro", "peixe"):
                extensao = ".mp3" if nome == "galinha" else ".wav"
                som = pygame.mixer.Sound(os.path.join(pasta, nome + extensao))
                som.set_volume(self.config["volume"])
                sons[nome] = som
        except pygame.error:
            pass
        return sons

    def reagir(self, acao):
        if acao in self.sons:
            self.sons[acao].play(maxtime=1800, fade_ms=40)
        self.update()

    def paintEvent(self, evento):
        pintura = QPainter(self)
        pintura.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.cena_fazenda.redimensionar(self.width(), self.height())
        self.cena_fazenda.desenhar(pintura)

    def mousePressEvent(self, evento):
        self.reagir(self.cena_fazenda.interagir_em(
            evento.position().x(), evento.position().y()
        ))

    def keyPressEvent(self, evento):
        if (
            evento.key() == Qt.Key.Key_Q
            and evento.modifiers() & Qt.KeyboardModifier.ControlModifier
            and evento.modifiers() & Qt.KeyboardModifier.ShiftModifier
        ):
            self.saida_permitida = True
            self.close()
            return

        if evento.key() in (Qt.Key.Key_Left, Qt.Key.Key_Right, Qt.Key.Key_Up, Qt.Key.Key_Down):
            acao = self.cena_fazenda.executar("cavalo")
        elif evento.key() in (Qt.Key.Key_Space, Qt.Key.Key_Return, Qt.Key.Key_Enter):
            acao = self.cena_fazenda.executar("galinha")
        else:
            acao = self.cena_fazenda.executar(
                self.cena_fazenda.ACOES[abs(evento.key()) % len(self.cena_fazenda.ACOES)]
            )
        self.reagir(acao)

    def verificar_controle(self):
        if self.controle is None:
            return
        pygame.event.pump()
        agora = pygame.time.get_ticks()
        for evento in pygame.event.get():
            if evento.type == pygame.JOYBUTTONDOWN:
                tipo = self.cena_fazenda.ACOES[evento.button % len(self.cena_fazenda.ACOES)]
                self.reagir(self.cena_fazenda.executar(tipo))
            elif evento.type == pygame.JOYHATMOTION and evento.value != (0, 0):
                self.reagir(self.cena_fazenda.executar("cavalo"))
            elif evento.type == pygame.JOYAXISMOTION and abs(evento.value) > 0.25:
                if agora - self.ultimo_movimento_controle >= 500:
                    tipo = "passaro" if evento.axis < 2 else "peixe"
                    self.reagir(self.cena_fazenda.executar(tipo))
                    self.ultimo_movimento_controle = agora

    def atualizar_animacao(self):
        self.cena_fazenda.redimensionar(self.width(), self.height())
        self.cena_fazenda.atualizar(0.016)
        self.update()

    def closeEvent(self, evento):
        evento.accept() if self.saida_permitida else evento.ignore()


app = QApplication([])
window = LKids()
app.exec()
pygame.quit()
