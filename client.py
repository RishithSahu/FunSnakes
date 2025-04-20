import socket
import sys
import json
import math
import threading
import time
import random
import ssl  # Add SSL import

try:
    from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
                               QLabel, QPushButton, QLineEdit, QListWidget, QWidget, 
                               QMessageBox, QFileDialog, QMenu, QAction, QCheckBox, QShortcut)  # Add QShortcut
    from PyQt5.QtCore import Qt, QThread, pyqtSignal, QRectF, QRect, QTimer
    from PyQt5.QtGui import QPainter, QColor, QBrush, QPen, QFont, QKeySequence
except ImportError as e:
    print(f"Required libraries not found: {e}")
    print("Please install with: pip install PyQt5")
    sys.exit(1)

# Game constants
WORLD_SIZE = 3000  # Size of the game world
VIEWPORT_SIZE = 800  # Size of the viewport
FOOD_RADIUS = 5
SNAKE_RADIUS = 10

class GameView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(VIEWPORT_SIZE, VIEWPORT_SIZE)
        self.setFocusPolicy(Qt.StrongFocus)
        self.game_state = None
        self.player_id = None
        self.mouse_pos = [0, 0]
        self.viewport_offset = [0, 0]
        self.death_time = 0  # Time when player died
        self.respawn_delay = 5  # Respawn delay in seconds
        self.is_dead = False  # Death state flag
        self.death_message = "You died!"  # Message to show when player dies
        self.allow_focus_change = True  # This flag will track if we want to allow focus changes
    
    def update_game_state(self, game_state):
        self.game_state = game_state
        self.player_id = game_state.get("player_id")
        
        # Check if player's snake exists and is alive
        player_alive = False
        player_exists = False
        
        for snake in game_state.get("snakes", []):
            if snake["id"] == self.player_id:
                player_exists = True
                if snake["alive"]:
                    player_alive = True
                    # Only reset death state when snake is fully alive and exists
                    self.is_dead = False
                    self.death_time = 0
                    print(f"Player is alive with segments: {len(snake['segments'])}")
                elif not self.is_dead:  # Just died
                    self.is_dead = True
                    self.death_time = time.time()
                    self.death_message = f"You died! Respawning in {self.respawn_delay} seconds..."
                    print(f"Player died at {self.death_time}")
                    
                break
        
        # If player doesn't exist in the snake list but we have a player_id,
        # they might be in the process of respawning
        if self.player_id and not player_exists and not self.is_dead:
            self.is_dead = True
            self.death_time = time.time()
            self.death_message = f"Respawning in {self.respawn_delay} seconds..."
            print("Player not found in snake list, waiting for respawn")
        
        # Update respawn countdown if dead
        if self.is_dead and self.death_time > 0:
            remaining = max(0, self.respawn_delay - (time.time() - self.death_time))
            if remaining > 0:
                self.death_message = f"You died! Respawning in {int(remaining)} seconds..."
            else:
                self.death_message = "Respawning..."
        
        # Update viewport position to follow player's snake
        if self.player_id and not self.is_dead:
            for snake in game_state.get("snakes", []):
                if snake["id"] == self.player_id and snake["alive"]:
                    head = snake["segments"][0]
                    self.viewport_offset = [
                        head[0] - VIEWPORT_SIZE // 2,
                        head[1] - VIEWPORT_SIZE // 2
                    ]
        
        self.update()
    
    def paintEvent(self, event):
        if not self.game_state:
            return
            
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw background
        painter.fillRect(0, 0, VIEWPORT_SIZE, VIEWPORT_SIZE, QColor(20, 20, 20))
        
        # Draw grid (reduced from every 100px to every 200px)
        painter.setPen(QPen(QColor(40, 40, 40), 1))
        grid_spacing = 200  # Increased from 100 to 200
        
        # Calculate grid offset based on viewport position
        offset_x = -self.viewport_offset[0] % grid_spacing
        offset_y = -self.viewport_offset[1] % grid_spacing
        
        # Draw vertical grid lines
        for x in range(int(offset_x), VIEWPORT_SIZE, grid_spacing):
            painter.drawLine(x, 0, x, VIEWPORT_SIZE)
            
        # Draw horizontal grid lines
        for y in range(int(offset_y), VIEWPORT_SIZE, grid_spacing):
            painter.drawLine(0, y, VIEWPORT_SIZE, y)
        
        # Draw food with visibility culling (only draw food within viewport)
        viewport_x = self.viewport_offset[0]
        viewport_y = self.viewport_offset[1]
        for food in self.game_state.get("foods", []):
            # Skip if completely outside viewport (with margin)
            if (food[0] < viewport_x - FOOD_RADIUS or 
                food[0] > viewport_x + VIEWPORT_SIZE + FOOD_RADIUS or
                food[1] < viewport_y - FOOD_RADIUS or 
                food[1] > viewport_y + VIEWPORT_SIZE + FOOD_RADIUS):
                continue
                
            screen_x = food[0] - viewport_x
            screen_y = food[1] - viewport_y
            
            painter.setBrush(QBrush(QColor(255, 0, 0)))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(QRectF(screen_x - FOOD_RADIUS, screen_y - FOOD_RADIUS, 
                                      FOOD_RADIUS * 2, FOOD_RADIUS * 2))
        
        # Draw snakes
        for snake in self.game_state.get("snakes", []):
            if not snake["alive"]:
                continue
                
            # Set snake color
            color = QColor(snake["color"])
            
            # Highlight player's snake
            is_player = snake["id"] == self.player_id
            
            for i, segment in enumerate(snake["segments"]):
                screen_x = segment[0] - self.viewport_offset[0]
                screen_y = segment[1] - self.viewport_offset[1]
                
                # Only draw if on or near screen
                if -SNAKE_RADIUS*2 <= screen_x <= VIEWPORT_SIZE + SNAKE_RADIUS*2 and \
                   -SNAKE_RADIUS*2 <= screen_y <= VIEWPORT_SIZE + SNAKE_RADIUS*2:
                    
                    # Head is slightly larger and has an outline if player's snake
                    if i == 0:
                        radius = SNAKE_RADIUS * 1.2
                        if is_player:
                            painter.setPen(QPen(QColor(255, 255, 255), 2))
                        else:
                            painter.setPen(Qt.NoPen)
                    else:
                        radius = SNAKE_RADIUS
                        painter.setPen(Qt.NoPen)
                    
                    painter.setBrush(QBrush(color))
                    painter.drawEllipse(QRectF(screen_x - radius, screen_y - radius, 
                                              radius * 2, radius * 2))
            
            # Draw snake name above head
            if snake["segments"]:
                head = snake["segments"][0]
                screen_x = head[0] - self.viewport_offset[0]
                screen_y = head[1] - self.viewport_offset[1] - 30  # Above head
                
                if 0 <= screen_x <= VIEWPORT_SIZE and 0 <= screen_y <= VIEWPORT_SIZE:
                    painter.setFont(QFont("Arial", 10))
                    painter.setPen(QColor(255, 255, 255))
                    # Convert float coordinates to integers
                    painter.drawText(int(screen_x) - 50, int(screen_y), 100, 20, 
                                    Qt.AlignCenter, f"{snake['name']} ({snake['score']})")
        
        # Draw leaderboard
        self.draw_leaderboard(painter)
        
        # Draw death screen overlay if dead
        if self.is_dead:
            # Semi-transparent overlay
            painter.setOpacity(0.7)
            painter.fillRect(0, 0, VIEWPORT_SIZE, VIEWPORT_SIZE, QColor(0, 0, 0))
            
            # Death message
            painter.setOpacity(1.0)
            painter.setFont(QFont("Arial", 24, QFont.Bold))
            painter.setPen(QColor(255, 0, 0))
            
            # Draw death message centered - use QRect
            painter.drawText(QRect(0, 0, VIEWPORT_SIZE, VIEWPORT_SIZE), 
                           Qt.AlignCenter, self.death_message)
            
            # Additional instructions - use QRect
            painter.setFont(QFont("Arial", 14))
            painter.setPen(QColor(200, 200, 200))
            painter.drawText(QRect(0, int(VIEWPORT_SIZE/2 + 40), VIEWPORT_SIZE, 40),
                           Qt.AlignCenter, "Wait for automatic respawn")
    
    def draw_leaderboard(self, painter):
        if not self.game_state:
            return
            
        # Sort snakes by score
        snakes = sorted(self.game_state.get("snakes", []), 
                       key=lambda s: s["score"], reverse=True)
        
        # Draw box
        painter.setOpacity(0.8)
        painter.fillRect(VIEWPORT_SIZE - 200, 10, 190, 30 + 20 * min(len(snakes), 5), 
                         QColor(0, 0, 0))
        painter.setOpacity(1.0)
        painter.setPen(QColor(255, 255, 255))
        painter.setFont(QFont("Arial", 12, QFont.Bold))
        painter.drawText(VIEWPORT_SIZE - 200, 10, 190, 30, Qt.AlignCenter, "Leaderboard")
        
        # Draw entries
        painter.setFont(QFont("Arial", 10))
        for i, snake in enumerate(snakes[:5]):
            y = 40 + i * 20
            text = f"{i+1}. {snake['name']}: {snake['score']}"
            
            # Highlight player's entry
            if snake["id"] == self.player_id:
                painter.setPen(QColor(255, 255, 0))
            else:
                painter.setPen(QColor(255, 255, 255))
                
            painter.drawText(VIEWPORT_SIZE - 190, y, 180, 20, Qt.AlignLeft, text)
    
    def mouseMoveEvent(self, event):
        self.mouse_pos = [event.x(), event.y()]
    
    def get_direction_vector(self):
        """Get direction vector from mouse position relative to snake head"""
        # Don't change direction if player is dead
        if self.is_dead or not self.game_state or not self.player_id:
            return [0, 0]
            
        # Find player snake
        player_snake = None
        for snake in self.game_state.get("snakes", []):
            if snake["id"] == self.player_id:
                player_snake = snake
                break
        
        if not player_snake or not player_snake["alive"] or not player_snake["segments"]:
            return [0, 0]
            
        # Get head position
        head = player_snake["segments"][0]
        
        # Calculate direction vector from head to mouse (in world coordinates)
        mouse_world_x = self.mouse_pos[0] + self.viewport_offset[0]
        mouse_world_y = self.mouse_pos[1] + self.viewport_offset[1]
        
        dx = mouse_world_x - head[0]
        dy = mouse_world_y - head[1]
        
        # Normalize
        length = math.sqrt(dx*dx + dy*dy)
        if length > 0:
            return [dx/length, dy/length]
        else:
            return [0, 0]

    def keyPressEvent(self, event):
        """Handle keyboard input for movement"""
        # Don't accept input if player is dead
        if self.is_dead:
            return
        
        # Default speed vector
        speed = 1.0
        
        dx, dy = 0, 0
        
        # Set direction based on arrow key
        if event.key() == Qt.Key_Up:
            dx, dy = 0, -speed
        elif event.key() == Qt.Key_Down:
            dx, dy = 0, speed
        elif event.key() == Qt.Key_Left:
            dx, dy = -speed, 0
        elif event.key() == Qt.Key_Right:
            dx, dy = speed, 0
        
        # If a direction key was pressed
        if dx != 0 or dy != 0:
            # Get main window instance
            main_window = self.window()
            if hasattr(main_window, 'send_direction'):
                main_window.send_direction(dx, dy)
                print(f"Key pressed: {dx}, {dy}")

    def focusOutEvent(self, event):
        # Only keep focus if we're not allowing focus change
        if not self.allow_focus_change:
            self.setFocus()
        super().focusOutEvent(event)

    def release_focus(self):
        """Temporarily allow focus to change to other widgets"""
        self.allow_focus_change = True

class ClientThread(QThread):
    log_signal = pyqtSignal(str)
    connection_status_signal = pyqtSignal(bool)
    game_state_signal = pyqtSignal(dict)
    chat_message_signal = pyqtSignal(str, str, str)  # player_id, player_name, message
    
    def __init__(self, host, port, player_name, color, timeout=10, use_ssl=True):  # Add use_ssl param
        super().__init__()
        self.host = host
        self.port = port
        self.timeout = timeout
        self.player_name = player_name
        self.color = color
        self.client_socket = None
        self.running = True
        self.direction = [0, 0]  # Current direction vector
        self.last_input_time = 0
        self.use_ssl = use_ssl  # Store SSL setting
    
    def run(self):
        try:
            # Create socket with timeout
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.settimeout(self.timeout)
            
            # Increase socket buffer sizes
            self.client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 65536)
            self.client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 65536)
            
            # Connect to the remote server using the provided hostname/IP
            self.log_signal.emit(f"Attempting to connect to {self.host}:{self.port}")
            
            # Try to resolve the hostname to an IP address
            try:
                server_ip = socket.gethostbyname(self.host)
                self.log_signal.emit(f"Resolved {self.host} to IP: {server_ip}")
            except socket.gaierror:
                server_ip = self.host  # Use as-is if not resolvable
                self.log_signal.emit(f"Could not resolve hostname, using direct IP: {self.host}")

            # Connect to the server
            self.client_socket.connect((server_ip, self.port))
            
            # Wrap socket with SSL if enabled
            if self.use_ssl:
                try:
                    ssl_context = ssl.create_default_context()
                    ssl_context.check_hostname = False  # Disable hostname verification for self-signed certs
                    ssl_context.verify_mode = ssl.CERT_NONE  # Accept self-signed certificates
                    
                    self.client_socket = ssl_context.wrap_socket(
                        self.client_socket, server_hostname=self.host)
                    
                    # Get certificate info
                    cert = self.client_socket.getpeercert(binary_form=True)
                    if cert:
                        self.log_signal.emit("SSL handshake successful")
                    else:
                        self.log_signal.emit("Warning: Server certificate not verified")
                        
                except ssl.SSLError as e:
                    self.log_signal.emit(f"SSL handshake failed: {e}")
                    self.log_signal.emit("Attempting to connect without SSL...")
                    # Reconnect without SSL
                    self.client_socket.close()
                    self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    self.client_socket.settimeout(self.timeout)
                    self.client_socket.connect((server_ip, self.port))
            
            self.log_signal.emit(f"Connected to {self.host}:{self.port}")
            self.connection_status_signal.emit(True)
            
            # Send join message
            join_message = {
                "type": "join",
                "name": self.player_name,
                "color": self.color
            }
            self.send_message(join_message)
            
            # Start input sending thread
            input_thread = threading.Thread(target=self.send_input_loop)
            input_thread.daemon = True
            input_thread.start()
            
            # Main message receiving loop
            while self.running:
                try:
                    data = self.client_socket.recv(16384)  # Larger buffer for game state
                    if not data:
                        break
                    
                    # Process received data
                    self.process_message(data.decode('utf-8'))
                except socket.timeout:
                    continue
                except Exception as e:
                    self.log_signal.emit(f"Error receiving data: {str(e)}")
                    break
        
        except socket.timeout:
            self.log_signal.emit(f"Connection to {self.host}:{self.port} timed out")
            self.connection_status_signal.emit(False)
        except ConnectionRefusedError:
            self.log_signal.emit(f"Connection refused by {self.host}:{self.port}. Make sure the server is running.")
            self.connection_status_signal.emit(False)
        except Exception as e:
            self.log_signal.emit(f"Client error: {str(e)}")
            self.connection_status_signal.emit(False)
        finally:
            self.cleanup()
    
    def send_input_loop(self):
        """Thread that sends direction input to the server"""
        while self.running:
            # Send direction input at regular intervals
            current_time = time.time()
            if current_time - self.last_input_time >= 0.15:  # Increased to 150ms
                self.last_input_time = current_time
                self.send_direction()
            time.sleep(0.05)  # Increased sleep time
    
    def send_direction(self):
        """Send current direction to the server"""
        if not self.running or not self.client_socket:
            return
            
        # Only send if there's a direction to send and it's changed
        if self.direction[0] != 0 or self.direction[1] != 0:
            input_message = {
                "type": "input",
                "dx": self.direction[0],
                "dy": self.direction[1]
            }
            self.send_message(input_message)
    
    def set_direction(self, dx, dy):
        """Set the current direction vector"""
        self.direction = [dx, dy]
        
    def process_message(self, data):
        """Process incoming messages from the server"""
        try:
            messages = data.split('\n')
            for message_str in messages:
                if not message_str:
                    continue
                    
                message = json.loads(message_str)
                message_type = message.get("type")
                
                if message_type == "join_ack":
                    # Received acknowledgement of our join request
                    player_id = message.get("player_id")
                    self.log_signal.emit(f"Joined game as player {player_id}")
                
                elif message_type == "state_update":
                    # Received game state update
                    game_state = message.get("state")
                    if game_state:
                        self.game_state_signal.emit(game_state)
                
                elif message_type == "chat":
                    # Handle chat message
                    player_id = str(message.get("player_id", ""))
                    player_name = message.get("player_name", "Unknown")
                    text = message.get("text", "")
                    self.chat_message_signal.emit(player_id, player_name, text)
                
                elif message_type == "error":
                    # Handle error messages
                    self.log_signal.emit(f"Error from server: {message.get('message')}")
        
        except json.JSONDecodeError as e:
            self.log_signal.emit(f"Error parsing message: {str(e)}")
        except Exception as e:
            self.log_signal.emit(f"Error processing message: {str(e)}")
    
    def send_message(self, message):
        """Send a message to the server"""
        if not self.client_socket:
            return
            
        try:
            # Ensure we end with a newline for message framing
            message_str = json.dumps(message) + "\n"
            self.client_socket.sendall(message_str.encode('utf-8'))
        except Exception as e:
            self.log_signal.emit(f"Error sending message: {str(e)}")
    
    def cleanup(self):
        # Cleanup method
        try:
            if self.client_socket:
                self.client_socket.close()
        except Exception as e:
            self.log_signal.emit(f"Cleanup error: {str(e)}")

        self.log_signal.emit("Disconnected from server")
        self.connection_status_signal.emit(False)

    def stop(self):
        self.running = False
        self.cleanup()

class SnakeGameClientApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.client_thread = None
        self.initUI()
        
        # Timer for direction updates - slower updates to reduce network traffic
        self.direction_timer = QTimer()
        self.direction_timer.timeout.connect(self.update_direction)
        self.direction_timer.start(100)  # Increase to 100ms interval
        
        # Add chat focus shortcut (T key is commonly used for chat in games)
        self.chat_shortcut = QShortcut(QKeySequence('T'), self)
        self.chat_shortcut.activated.connect(self.focus_chat_input)

    def focus_chat_input(self):
        """Focus the chat input field when T key is pressed"""
        # Tell the game view to allow focus change
        self.game_view.allow_focus_change = True
        
        # Focus the chat input
        self.chat_input.setFocus()
        
        # After a short delay, tell game view to start keeping focus again
        QTimer.singleShot(100, self.restore_game_focus)

    def restore_game_focus(self):
        """Restore game view's focus capturing behavior"""
        # Only restore focus capturing if we're not actively using the chat
        if not self.chat_input.hasFocus():
            self.game_view.allow_focus_change = False
            self.game_view.setFocus()
    
    def initUI(self):
        self.setWindowTitle('FunSnakes - Multiplayer Snake Game')
        self.setGeometry(100, 100, VIEWPORT_SIZE + 200, VIEWPORT_SIZE + 100)

        main_widget = QWidget()
        main_layout = QVBoxLayout()
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)
        
        # Top section with connection controls
        connection_layout = QHBoxLayout()
        
        # Server IP input
        self.host_input = QLineEdit('')
        self.host_input.setPlaceholderText('Enter server IP address')
        
        # Port input
        self.port_input = QLineEdit('5000')
        self.port_input.setPlaceholderText('Port')
        
        # Player name input
        self.name_input = QLineEdit('Player')
        self.name_input.setPlaceholderText('Your Name')
        
        # Color selection
        self.color_input = QLineEdit('#' + ''.join([random.choice('0123456789ABCDEF') for _ in range(6)]))
        self.color_input.setPlaceholderText('Color (hex)')
        
        # Add SSL checkbox
        self.use_ssl_checkbox = QCheckBox('Enable SSL')
        self.use_ssl_checkbox.setChecked(True)
        
        # Connect button
        connect_btn = QPushButton('Join Game')
        connect_btn.clicked.connect(self.join_game)
        
        connection_layout.addWidget(QLabel('Server:'))
        connection_layout.addWidget(self.host_input)
        connection_layout.addWidget(QLabel('Port:'))
        connection_layout.addWidget(self.port_input)
        connection_layout.addWidget(QLabel('Name:'))
        connection_layout.addWidget(self.name_input)
        connection_layout.addWidget(QLabel('Color:'))
        connection_layout.addWidget(self.color_input)
        connection_layout.addWidget(self.use_ssl_checkbox)
        connection_layout.addWidget(connect_btn)
        
        main_layout.addLayout(connection_layout)

        # Main game area
        game_layout = QHBoxLayout()
        
        # Game view
        self.game_view = GameView()
        game_layout.addWidget(self.game_view)
        
        # Right sidebar
        sidebar_layout = QVBoxLayout()
        
        # Connection status
        self.connection_status_label = QLabel('Status: Disconnected')
        sidebar_layout.addWidget(self.connection_status_label)
        
        # Instructions
        instructions_label = QLabel(
            "How to play:\n"
            "1. Move your mouse to control direction\n"
            "2. Eat red food to grow\n"
            "3. Avoid hitting other snakes\n"
            "4. Try to get others to hit you\n\n"
            "Controls:\n"
            "- Move mouse to change direction\n"
            "- Arrow keys also work for movement\n"
            "- Press T to focus chat"
        )
        instructions_label.setWordWrap(True)
        sidebar_layout.addWidget(instructions_label)
        
        # Chat section (replaces saved servers)
        sidebar_layout.addWidget(QLabel('Chat:'))
        
        # Chat display area
        self.chat_display = QListWidget()
        self.chat_display.setWordWrap(True)
        sidebar_layout.addWidget(self.chat_display)
        
        # Chat input area
        chat_input_layout = QHBoxLayout()
        self.chat_input = QLineEdit()
        self.chat_input.setPlaceholderText('Type your message here...')
        self.chat_input.returnPressed.connect(self.send_chat_message)
        
        # Connect mouse events to allow focusing the chat box
        self.chat_input.mousePressEvent = self.chat_input_clicked
        
        chat_input_layout.addWidget(self.chat_input)
        
        send_button = QPushButton('Send')
        send_button.clicked.connect(self.send_chat_message)
        chat_input_layout.addWidget(send_button)
        
        sidebar_layout.addLayout(chat_input_layout)
        
        # Log area
        self.log_list = QListWidget()
        sidebar_layout.addWidget(QLabel('Log:'))
        sidebar_layout.addWidget(self.log_list)
        
        game_layout.addLayout(sidebar_layout)
        main_layout.addLayout(game_layout)

    def chat_input_clicked(self, event):
        """Handle mouse clicks on the chat input field"""
        # Tell the game view to release focus
        self.game_view.allow_focus_change = True
        
        # Focus the chat input
        self.chat_input.setFocus()
        
        # Call the original mousePressEvent
        QLineEdit.mousePressEvent(self.chat_input, event)

    def update_direction(self):
        """Update direction based on game view and send to client thread"""
        if self.client_thread and self.client_thread.isRunning():
            # Don't send direction if player is dead
            if not self.game_view.is_dead:
                direction = self.game_view.get_direction_vector()
                self.client_thread.set_direction(direction[0], direction[1])
    
    def join_game(self):
        # Stop any existing client thread
        if self.client_thread:
            self.client_thread.stop()

        # Validate inputs
        host = self.host_input.text().strip()
        if not host:
            QMessageBox.warning(self, "Input Error", "Please enter a server IP address")
            return
        
        try:
            port = int(self.port_input.text())
            if port <= 0 or port > 65535:
                raise ValueError("Invalid port number")
        except ValueError:
            QMessageBox.warning(self, "Input Error", "Please enter a valid port number (1-65535)")
            return
            
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Input Error", "Please enter your name")
            return
            
        color = self.color_input.text().strip()
        if not color.startswith('#') or len(color) != 7:
            QMessageBox.warning(self, "Input Error", "Please enter a valid color (e.g., #FF5500)")
            return
        
        # Get SSL setting
        use_ssl = self.use_ssl_checkbox.isChecked()
        
        # Start client thread
        try:
            self.client_thread = ClientThread(host, port, name, color, use_ssl=use_ssl)
            self.client_thread.log_signal.connect(self.log_message)
            self.client_thread.connection_status_signal.connect(self.update_connection_status)
            self.client_thread.game_state_signal.connect(self.game_view.update_game_state)
            self.client_thread.chat_message_signal.connect(self.add_chat_message)  # Connect chat signal
            self.client_thread.start()
        except Exception as e:
            QMessageBox.critical(self, "Connection Error", f"Could not connect to {host}:{port}\n{str(e)}")

    def log_message(self, message):
        self.log_list.addItem(message)
        self.log_list.scrollToBottom()

    def update_connection_status(self, connected):
        status = 'Connected' if connected else 'Disconnected'
        self.connection_status_label.setText(f'Status: {status}')
        
        # Update window title with player name when connected
        if connected:
            player_name = self.name_input.text().strip()
            self.setWindowTitle(f'FunSnakes - {player_name}')
        else:
            self.setWindowTitle('FunSnakes - Multiplayer Snake Game')

    def closeEvent(self, event):
        if self.client_thread:
            self.client_thread.stop()
        event.accept()
    
    def send_direction(self, dx, dy):
        """Send direction from keyboard input"""
        if self.client_thread and self.client_thread.isRunning():
            self.client_thread.set_direction(dx, dy)
            print(f"Sending key direction: {dx}, {dy}")

    def send_chat_message(self):
        """Send a chat message to other players"""
        if not self.client_thread or not self.client_thread.isRunning():
            self.log_message("Cannot send message: Not connected to a server")
            return
            
        message_text = self.chat_input.text().strip()
        if not message_text:
            return
            
        # Prepare chat message
        chat_message = {
            "type": "chat",
            "text": message_text
        }
        
        # Send message to server
        self.client_thread.send_message(chat_message)
        
        # Clear input field
        self.chat_input.clear()
        
        # Return focus to game after sending message
        self.game_view.allow_focus_change = False
        self.game_view.setFocus()

    def add_chat_message(self, player_id, player_name, message):
        """Display a chat message in the chat window"""
        is_self = (self.client_thread and 
                  self.game_view.player_id is not None and 
                  str(self.game_view.player_id) == player_id)
        
        if is_self:
            # Format your own messages differently
            formatted_message = f"You: {message}"
            self.chat_display.addItem(formatted_message)
            item = self.chat_display.item(self.chat_display.count() - 1)
            item.setForeground(Qt.blue)
        else:
            # Format messages from others
            formatted_message = f"{player_name}: {message}"
            self.chat_display.addItem(formatted_message)
        
        # Scroll to the latest message
        self.chat_display.scrollToBottom()

def main():
    app = QApplication(sys.argv)
    client_app = SnakeGameClientApp()
    client_app.show()
    sys.exit(app.exec_())
    
if __name__ == '__main__':
    main()