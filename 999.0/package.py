# -*- coding: utf-8 -*-

name = "ChatRoom"
version = "999.0"
description = "Lugwit ChatRoom: FastAPI/WebSocket backend + React frontend + PySide6 client"
authors = ["Lugwit Team"]

requires = [
    "python-3.12+<3.13",
    "Lugwit_Module",
    "l_notepad",
    "lugwit_auth",
]

build_command = False
cachable = True
relocatable = True


def commands():
    env.PYTHONPATH.prepend("{root}/src")
    # Use Windows-friendly path separators because downstream .bat scripts
    # frequently concatenate with backslashes.
    env.CHATROOM_ROOT = "{root}\\src\\ChatRoom"

    alias("chatroom_backend", 'cmd /c "{root}/src/ChatRoom/run_backend_server.bat"')
    alias(
        "chatroom_backend_api",
        'cmd /c "{root}/src/ChatRoom/run_backend_server_api.bat"',
    )
    alias("chatroom_frontend", 'cmd /c "{root}/src/ChatRoom/start_frontend.bat"')
    alias("chatroom_client", 'cmd /c "{root}/src/ChatRoom/run_client.bat"')

