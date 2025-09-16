from MainClass import *


canal = "terra"
mailing = Tools.mailing(canal=canal)



print(mailing["Telefone"].count())