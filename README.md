# ChatRoom Application

A real-time chat application built with Python, PySide6, and Socket.IO.

## Features

- Real-time messaging
- Private chat rooms
- Remote control functionality
- System tray integration
- Dark theme support
- Auto-reconnect mechanism
- VNC integration

## Requirements

- Python 3.8+
- PySide6
- Socket.IO
- aiohttp
- python-dotenv

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/chatroom.git
cd chatroom
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the root directory with the following content:
```env
SERVER_IP=127.0.0.1
SERVER_PORT=1026
WS_PORT=1026
LOG_DIR=A:/temp/chatRoomLog
```

## Usage

1. Start the server:
```bash
python run_backend_server.py
```

2. Start the client:
```bash
python clientend/pyqt_chatroom.py
```

## Project Structure

```
chatroom/
├── backend/           # Server-side code
├── clientend/         # Client-side code
│   ├── modules/      # Client modules
│   ├── static/       # Static files
│   └── icons/        # Application icons
├── tests/            # Test files
└── docs/             # Documentation
```

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details. 