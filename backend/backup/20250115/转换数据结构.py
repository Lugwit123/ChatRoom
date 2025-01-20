import os
os.chdir("D:/TD_Depot/Software/Lugwit_syncPlug/lugwit_insapp/trayapp/Lib/ChatRoom/backend")
from pydantic2ts import generate_typescript_defs

generate_typescript_defs("schemas", "apiTypes.ts")