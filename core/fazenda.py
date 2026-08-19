from dataclasses import dataclass
import math
import os
import random

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QPen, QPixmap, QTransform


@dataclass
class Animal:
    tipo: str
    imagem: QPixmap
    x: float
    y: float
    vx: float
    limites: tuple
    tamanho: int
    origem_x: float
    tempo: float = 0.0

    def atualizar(self, dt):
        self.tempo += dt
        if self.tempo > 3.3:
            velocidade = max(abs(self.vx), 0.025)
            self.vx = -velocidade if self.x > self.origem_x else velocidade
        self.x += self.vx * dt
        esquerda, direita, topo, base = self.limites
        if self.tempo <= 3.3 and (self.x < esquerda or self.x > direita):
            self.vx *= -1
            self.x = max(esquerda, min(direita, self.x))


@dataclass
class Elemento:
    x: float
    y: float
    vx: float
    vy: float = 0.0
    tempo: float = 0.0


class CenaFazenda:
    ACOES = ("galinha", "ovelha", "cavalo", "passaro", "peixe")

    def __init__(self, caminho_assets, config):
        self.config = config
        self.largura = self.altura = 0
        self.animais, self.passaros, self.peixes = [], [], []
        self.nuvens = [Elemento(-.10,.12,.012), Elemento(.42,.20,.008)]
        self.proxima_interacao = 0
        self.total_interacoes = 0
        self.tempo_ocioso = 0.0
        self.tempo_total = 0.0
        self.surpresa_tempo = 0.0
        self.contadores = {"galinha":0, "ovelha":0, "cavalo":0}
        self.fundo = QPixmap(os.path.join(caminho_assets, "fazenda-fundo-v2.png"))
        self.fundo_escalado = QPixmap()
        self.passaro_sprite = QPixmap(os.path.join(caminho_assets, "passaro-v2.png"))
        self.peixe_sprite = QPixmap(os.path.join(caminho_assets, "peixe-v2.png"))
        self.sprites = {
            "galinha": QPixmap(os.path.join(caminho_assets, "galinha-v3.png")),
            "ovelha": QPixmap(os.path.join(caminho_assets, "ovelha.png")),
            "cavalo": QPixmap(os.path.join(caminho_assets, "cavalo.png")),
        }

    def redimensionar(self, largura, altura):
        if (largura, altura) == (self.largura, self.altura):
            return
        self.largura, self.altura = largura, altura
        self.fundo_escalado = self.fundo.scaled(largura, altura, Qt.AspectRatioMode.IgnoreAspectRatio, Qt.TransformationMode.SmoothTransformation)

    def atualizar(self, dt):
        self.tempo_total += dt
        self.tempo_ocioso += dt
        self.surpresa_tempo = max(0.0, self.surpresa_tempo-dt)
        duracao = self.config["duracao_animais"]
        for animal in self.animais:
            animal.atualizar(dt)
        self.animais = [a for a in self.animais if a.tempo < duracao]
        for passaro in self.passaros:
            passaro.tempo += dt; passaro.x += passaro.vx*dt; passaro.y += passaro.vy*dt
        self.passaros = [p for p in self.passaros if p.tempo < duracao]
        for peixe in self.peixes:
            peixe.tempo += dt; peixe.x += peixe.vx*dt
            if peixe.x < .70 or peixe.x > .91:
                peixe.vx *= -1; peixe.x=max(.70,min(.91,peixe.x))
        self.peixes = [p for p in self.peixes if p.tempo < duracao]
        for nuvem in self.nuvens:
            nuvem.x += nuvem.vx*dt
            if nuvem.x > 1.10: nuvem.x = -.18

    def desenhar(self, p):
        p.drawPixmap(0,0,self.fundo_escalado)
        self._desenhar_nuvens(p)
        self._desenhar_peixes(p)
        for animal in sorted(self.animais,key=lambda a:a.y):
            sprite=animal.imagem.scaled(animal.tamanho,animal.tamanho,Qt.AspectRatioMode.KeepAspectRatio,Qt.TransformationMode.SmoothTransformation)
            if animal.vx < 0: sprite=sprite.transformed(QTransform().scale(-1,1))
            p.drawPixmap(int(animal.x*self.largura-sprite.width()/2),int(animal.y*self.altura-sprite.height()/2),sprite)
        self._desenhar_passaros(p)
        self._desenhar_atracao(p)
        self._desenhar_surpresa(p)

    def _registrar(self, acao):
        self.tempo_ocioso = 0.0
        self.total_interacoes += 1
        if self.total_interacoes % self.config["surpresa_a_cada"] == 0:
            self.surpresa_tempo = 3.0
        return acao

    def soltar(self, tipo):
        limites={"galinha":self.config["maximo_galinhas"],"ovelha":self.config["maximo_ovelhas"],"cavalo":self.config["maximo_cavalos"]}
        ativos=[a for a in self.animais if a.tipo==tipo]
        if len(ativos)>=limites[tipo]: self.animais.remove(ativos[0])
        faixa=self.contadores[tipo]%limites[tipo]; self.contadores[tipo]+=1
        if tipo=="galinha":
            y=.62+faixa*.035; animal=Animal(tipo,self.sprites[tipo],.14,y,.055+faixa*.006,(.14,.40,y-.01,y+.02),105,.14)
        elif tipo=="ovelha":
            y=.455+(faixa//3)*.028; animal=Animal(tipo,self.sprites[tipo],.43+(faixa%3)*.045,y,.025 if faixa%2==0 else -.025,(.37,.59,.445,.515),108,.43+(faixa%3)*.045)
        else:
            y=.48+faixa*.055; animal=Animal(tipo,self.sprites[tipo],.76,y,-.038-faixa*.004,(.60,.77,y,y+.03),155,.76)
        self.animais.append(animal)
        return self._registrar(tipo)

    def soltar_passaro(self):
        if len(self.passaros)>=self.config["maximo_passaros"]: self.passaros.pop(0)
        i=len(self.passaros); self.passaros.append(Elemento(.25,.22+i*.025,.09+i*.008,(-1 if i%2 else 1)*.008))
        return self._registrar("passaro")

    def soltar_peixe(self):
        if len(self.peixes)>=self.config["maximo_peixes"]: self.peixes.pop(0)
        i=len(self.peixes); self.peixes.append(Elemento(.73+i*.025,.75+(i%3)*.035,.025+(i%2)*.008))
        return self._registrar("peixe")

    def interagir_proximo(self):
        acao=self.ACOES[self.proxima_interacao%len(self.ACOES)]; self.proxima_interacao+=1
        return self.executar(acao)

    def executar(self, acao):
        if acao in self.sprites: return self.soltar(acao)
        if acao=="passaro": return self.soltar_passaro()
        return self.soltar_peixe()

    def interagir_em(self,x,y):
        nx,ny=x/max(1,self.largura),y/max(1,self.altura)
        if nx<.25 and .40<ny<.78: return self.soltar("galinha")
        if .30<nx<.66 and .38<ny<.62: return self.soltar("ovelha")
        if nx>.67 and .20<ny<.62: return self.soltar("cavalo")
        if .12<nx<.40 and .05<ny<.53: return self.soltar_passaro()
        if nx>.64 and ny>.62: return self.soltar_peixe()
        return self.interagir_proximo()

    def _desenhar_nuvens(self,p):
        p.setPen(Qt.PenStyle.NoPen); p.setBrush(QColor(255,255,255,185))
        for n in self.nuvens:
            x,y=n.x*self.largura,n.y*self.altura
            p.drawEllipse(QRectF(x,y+18,125,48)); p.drawEllipse(QRectF(x+30,y,90,68)); p.drawEllipse(QRectF(x+78,y+15,115,50))

    def _desenhar_passaros(self,p):
        for b in self.passaros:
            s=self.passaro_sprite.scaled(74,74,Qt.AspectRatioMode.KeepAspectRatio,Qt.TransformationMode.SmoothTransformation)
            p.drawPixmap(int(b.x*self.largura-s.width()/2),int(b.y*self.altura-s.height()/2),s)

    def _desenhar_peixes(self,p):
        for peixe in self.peixes:
            s=self.peixe_sprite.scaled(62,62,Qt.AspectRatioMode.KeepAspectRatio,Qt.TransformationMode.SmoothTransformation)
            if peixe.vx<0: s=s.transformed(QTransform().scale(-1,1))
            p.drawPixmap(int(peixe.x*self.largura-s.width()/2),int(peixe.y*self.altura-s.height()/2),s)

    def _desenhar_atracao(self,p):
        if self.tempo_ocioso < self.config["tempo_modo_atracao"]: return
        pontos=((.16,.58),(.48,.48),(.76,.39),(.25,.25),(.80,.76))
        x,y=pontos[int((self.tempo_ocioso-self.config["tempo_modo_atracao"])//2)%len(pontos)]
        raio=35+10*math.sin(self.tempo_total*4)
        p.setPen(QPen(QColor(255,245,120,210),7)); p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawEllipse(QRectF(x*self.largura-raio,y*self.altura-raio,raio*2,raio*2))

    def _desenhar_surpresa(self,p):
        if self.surpresa_tempo <= 0:
            return
        cores = ("#E94B4B", "#F28C28", "#F2D34F", "#55B85A", "#4A90D9", "#8A5BC4")
        base = QRectF(self.largura*.43, self.altura*.035, self.largura*.25, self.altura*.27)
        for i, cor in enumerate(cores):
            margem = i * 7
            area = base.adjusted(margem, margem, -margem, -margem)
            tinta = QColor(cor)
            tinta.setAlpha(175)
            p.setPen(QPen(tinta, 8, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            p.drawArc(area, 0, 180*16)
