from dataclasses import dataclass
import time, random
import pyautogui as pgui
import pyperclip


@dataclass
class HumanizeConfig:
    enabled: bool = True

    #Pausas gerais entre as ações
    min_wait: float = 1.2
    max_wait: float = 3.8

    #Ao clicar ou mover
    mouse_move_min: float = 0.35
    mouse_move_max: float = 1.15
    mouse_jitter_px: int = 4

    #Ao digitar
    type_min: float = 0.05
    type_max: float = 0.14

    #probabilidade de digitar (vs colar)
    prob_type: float = 0.30

    #pausas micro entre passos
    micro_min: float = 0.20
    micro_max: float = 0.55


class Humanizer:
    def __init__(self, cfg: HumanizeConfig | None = None):
        self.cfg = cfg or HumanizeConfig()
        pgui.FAILSAFE = False

        #ESPERAS
    def esperar(self, min_s: float | None = None, max_s: float | None = None):
        if not self.cfg.enabled:
            return
        a = self.cfg.min_wait if min_s is None else min_s
        b = self.cfg.max_wait if max_s is None else max_s
        time.sleep(random.uniform(a, b))

    def micro(self):
        self.esperar(self.cfg.micro_min, self.cfg.micro_max)

    #MOUSE
    def move_to(self, x: int, y: int, duration: float | None = None, jitter: int | None = None):
        if not self.cfg.enabled:
            pgui.moveTo(x, y, duration=0)
            return

        if duration is None:
            duration = random.uniform(self.cfg.mouse_move_min, self.cfg.mouse_move_max)
        if jitter is None:
            jitter = self.cfg.mouse_jitter_px
        jx = random.randint(-jitter, jitter)
        jy = random.randint(-jitter, jitter)
        pgui.moveTo(x + jx, y + jy, duration=duration)

    def click(self, x: int, y: int, clicks: int = 1, interval: float  | None = None, button: str = "left"):
        self.move_to(x, y)
        self.micro()
        if interval is None:
            interval = random.uniform(0.12, 0.35) if self.cfg.enabled else 0
        pgui.click(clicks=clicks, interval=interval, button=button)
        self.micro()

    #TECLADO
    def digitar(self, msg: str):
        for ch in msg:
            pgui.write(ch)
            time.sleep(random.uniform(self.cfg.type_min, self.cfg.type_max) if self.cfg.enabled else 0)

    def colar(self, msg: str):
        pyperclip.copy(msg)
        pgui.hotkey("ctrl", "v")

    def escrever(self, msg: str, force_type: bool | None = None):
        use_type = (random.random() < self.cfg.prob_type) if force_type is None else force_type
        if use_type:
            self.digitar(msg)
        else:
            self.colar(msg)
        self.micro()

    def enter(self, delay_min: float = 0.3, delay_max: float = 0.9):
        if self.cfg.enabled:
            time.sleep(random.uniform(delay_min, delay_max))
        pgui.press("enter")
        self.micro()

#Singleton
_default = Humanizer()

def esperar(min_s: float = 1.5, max_s: float = 4.0):
    _default.espera(min_s, max_s)

def escrever(msg:str):
    _default.escrever(msg)

def click(x: int, y: int, clicks: int = 1, button: str = "left"):
    _default.click(x, y, clicks=clicks, button=button)
