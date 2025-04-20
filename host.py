import os
import sys
import socket
import threading
import time
import random
import json
import math
import ssl  # Add SSL import
from collections import deque

try:
    from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
                               QLabel, QPushButton, QLineEdit, QListWidget, QWidget, 
                               QMessageBox, QFileDialog, QMenu, QAction, QCheckBox)  # Add QCheckBox
    from PyQt5.QtCore import Qt, QThread, pyqtSignal
except ImportError as e:
    print(f"Required libraries not found: {e}")
    print("Please install with: pip install PyQt5")
    sys.exit(1)

# Game constants - tune these for better performance
WORLD_SIZE = 3000  # Increased map size
FOOD_COUNT = 850   # Reduced from 1200 to 300 for better performance
TICK_RATE = 15     # Higher tick rate for smoother experience
SNAKE_RADIUS = 10  # Radius of the snake for collision detection

class Snake:
    def __init__(self, player_id, name, color):
        self.id = player_id
        self.name = name
        self.color = color
        self.segments = []
        self.direction = [1, 0]  # Initial direction: right
        self.speed = 4  # Keep the speed the same
        self.score = 0
        self.alive = True
        self.creation_time = time.time()  # Track when snake was created
        # Initialize snake with 5 segments at random position, with REDUCED spacing
        x = random.randint(100, WORLD_SIZE - 100)
        y = random.randint(100, WORLD_SIZE - 100)
        for i in range(5):
            # Reduce spacing from 5 to 3 units between initial segments for better turning
            self.segments.append([x - i * 3, y])

    def update(self):
        if not self.alive:
            return
            
        # Move head in current direction
        head = self.segments[0].copy()
        head[0] += self.direction[0] * self.speed
        head[1] += self.direction[1] * self.speed
        
        # Wrap around world boundaries (optimize with modulo)
        if head[0] < 0: head[0] += WORLD_SIZE
        elif head[0] >= WORLD_SIZE: head[0] -= WORLD_SIZE
        if head[1] < 0: head[1] += WORLD_SIZE
        elif head[1] >= WORLD_SIZE: head[1] -= WORLD_SIZE
        
        # Add new head
        self.segments.insert(0, head)
        
        # Remove tail if not growing - optimize segment count based on score
        max_length = min(5 + self.score // 10, 100)  # Cap maximum length for performance
        if len(self.segments) > max_length:
            self.segments.pop()

    def set_direction(self, dx, dy):
        # Debug output before direction change - REMOVE THIS
        # old_direction = self.direction.copy()
        
        # Prevent 180-degree turns
        dot_product = self.direction[0] * dx + self.direction[1] * dy
        if dot_product < 0:
            # Removed debug print
            return
        
        # Only update if there's a significant change
        diff_x = abs(dx - self.direction[0])
        diff_y = abs(dy - self.direction[1])
        
        if diff_x > 0.05 or diff_y > 0.05:  # Only update direction if it changed significantly
            # Normalize direction vector
            length = (dx**2 + dy**2)**0.5
            if length > 0:
                self.direction = [dx/length, dy/length]
                # Removed debug print

    def check_collision(self, other_snake):
        if not self.alive or not other_snake.alive:
            return False
            
        # Check if this snake's head collides with any segment of the other snake
        head = self.segments[0]
        
        # If checking against self, skip collision detection completely
        if other_snake.id == self.id:
            return False  # Never collide with own body
        
        # Quick check to see if other snake is nearby before detailed collision check
        if other_snake.segments:
            other_head = other_snake.segments[0]
            approx_dist = abs(head[0] - other_head[0]) + abs(head[1] - other_head[1])
            # If snake heads are very far apart, skip detailed collision check
            if approx_dist > 500:  # Far enough that collision is impossible
                return False
        
        # Only check every other segment for performance (starting with the head)
        check_step = 2
        for i in range(0, len(other_snake.segments), check_step):
            segment = other_snake.segments[i]
            distance = ((head[0] - segment[0])**2 + (head[1] - segment[1])**2)**0.5
            if distance < SNAKE_RADIUS * 1.2:
                return True
            
        return False

    def check_food_collision(self, foods):
        if not self.alive:
            return None
            
        head = self.segments[0]
        for i, food in enumerate(foods):
            distance = ((head[0] - food[0])**2 + (head[1] - food[1])**2)**0.5
            if distance < 15:  # Snake head + food radius
                return i
        return None

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "color": self.color,
            "segments": self.segments,
            "score": self.score,
            "alive": self.alive
        }

class GameState:
    def __init__(self):
        self.snakes = {}
        self.foods = []
        self.next_player_id = 1
        self.dead_players = {}  # Store dead players with death time: {player_id: death_time}
        self.respawn_delay = 5  # Respawn delay in seconds
        self.log_message_callback = lambda msg: None  # Default empty callback for logging
        self.player_name_to_id = {}  # Map player names to IDs for reconnection
        self.initialize_food()
    
    def initialize_food(self):
        self.foods = []
        for _ in range(FOOD_COUNT):
            x = random.randint(0, WORLD_SIZE)
            y = random.randint(0, WORLD_SIZE)
            self.foods.append([x, y])
    
    def add_snake(self, name, color):
        # Check if this player name has connected before
        if name in self.player_name_to_id:
            old_id = self.player_name_to_id[name]
            # Use the old ID if it's not currently active
            if old_id not in self.snakes:
                player_id = old_id
                # print(f"Reusing previous ID {player_id} for player {name}")
            else:

                player_id = self.next_player_id
                self.next_player_id += 1
                print(f"Player {name} already connected with ID {old_id}, assigning new ID {player_id}")
        else:
            # New player, assign a new ID
            player_id = self.next_player_id
            self.next_player_id += 1
            
        # Store this name-to-id mapping for future reconnections
        self.player_name_to_id[name] = player_id
        
        # Create snake in a VERY safe location, far from other snakes
        is_safe = False
        max_attempts = 20  # Increased attempts
        
        # Initialize with a random position
        x = random.randint(200, WORLD_SIZE - 200)
        y = random.randint(200, WORLD_SIZE - 200)
        
        new_snake = None
        
        while not is_safe and max_attempts > 0:
            # Create a new snake at this position
            new_snake = Snake(player_id, name, color)
            new_snake.segments = []
            for i in range(5):
                # Reduce spacing from 8 to 3 units for better turning
                new_snake.segments.append([x - i * 3, y])
            
            # Assume safe until proven otherwise
            is_safe = True
            
            # Check distance from ALL existing snakes
            for other_snake in self.snakes.values():
                min_distance = float('inf')
                
                # Check distance from new snake's head to all segments of other snakes
                for other_segment in other_snake.segments:
                    for new_segment in new_snake.segments:
                        dist = math.sqrt((other_segment[0] - new_segment[0])**2 + 
                                         (other_segment[1] - new_segment[1])**2)
                        min_distance = min(min_distance, dist)
                
                # If too close to any snake, try a new position
                if min_distance < 50:  # Much larger safe distance (was 20)
                    is_safe = False
                    x = random.randint(200, WORLD_SIZE - 200)
                    y = random.randint(200, WORLD_SIZE - 200)
                    max_attempts -= 1
                    break
        
        # If we couldn't find a safe position after many attempts,
        # place the snake very far away
        if not is_safe:
            new_snake = Snake(player_id, name, color)
            # Place in a corner far from the typical action
            x = random.randint(WORLD_SIZE - 500, WORLD_SIZE - 200)
            y = random.randint(WORLD_SIZE - 500, WORLD_SIZE - 200)
            new_snake.segments = []
            for i in range(5):
                # Reduce spacing from 8 to 3 units here as well
                new_snake.segments.append([x - i * 3, y])
        
        self.snakes[player_id] = new_snake
        print(f"Created snake: ID={player_id}, Name={name}, Alive={self.snakes[player_id].alive}")
        return player_id
    
    def add_snake_with_score(self, name, color, score, length=5):
        """Add a snake with an existing score and length (for reconnections)"""
        # Check if this player name has connected before
        if name in self.player_name_to_id:
            player_id = self.player_name_to_id[name]
            # print(f"Reusing previous ID {player_id} for reconnecting player {name}")
        else:
            # New player who somehow has a score (strange case)
            player_id = self.next_player_id
            self.next_player_id += 1
            
        # Update the name-to-id mapping
        self.player_name_to_id[name] = player_id
        
        # Create a new snake at a random position
        new_snake = Snake(player_id, name, color)
        
        # Set the previous score
        if score > 0:
            new_snake.score = score
            # print(f"Restored score {score} for player {name} with ID {player_id}")
            self.log_message_callback(f"Restored score {score} for reconnecting player {name}")
        
        # Adjust the snake length if needed (only if larger than default)
        if length > 5:
            # Get the head position and direction
            head = new_snake.segments[0].copy()
            direction = new_snake.direction
            
            # Clear existing segments
            new_snake.segments = []
            
            # Recreate segments with the specified length
            max_length = min(length, 100)  # Cap at 100 segments for performance
            for i in range(max_length):
                # Calculate position for this segment
                # Reduce spacing from 5 to 3 units for better turning
                segment_x = head[0] - direction[0] * i * 3
                segment_y = head[1] - direction[1] * i * 3
                
                # Apply world wrap if needed
                if segment_x < 0: segment_x += WORLD_SIZE
                elif segment_x >= WORLD_SIZE: segment_x -= WORLD_SIZE
                if segment_y < 0: segment_y += WORLD_SIZE
                elif segment_y >= WORLD_SIZE: segment_y -= WORLD_SIZE
                
                new_snake.segments.append([segment_x, segment_y])
                
            # print(f"Restored length {max_length} for player {name}")
            self.log_message_callback(f"Restored length {max_length} for reconnecting player {name}")
        
        # Add to snakes dictionary
        self.snakes[player_id] = new_snake
        return player_id

    def remove_snake(self, player_id):
        if player_id in self.snakes:
            del self.snakes[player_id]
    
    def update(self):
        # Create a copy of the snakes dictionary values to safely iterate
        snakes_list = list(self.snakes.values())
        current_time = time.time()
        
        # Only print dead player debug once per second
        if int(current_time) != getattr(self, 'last_debug_time', 0) and self.dead_players:
            for player_id, death_time in self.dead_players.items():
                elapsed = current_time - death_time
                print(f"Player {player_id} dead for {elapsed:.1f} seconds")
            self.last_debug_time = int(current_time)
        
        # Check for respawning dead players
        for player_id, death_time in list(self.dead_players.items()):
            if current_time - death_time >= self.respawn_delay:
                # Time to respawn this player
                if player_id in self.snakes:
                    # Get the old snake's info
                    name = self.snakes[player_id].name
                    color = self.snakes[player_id].color
                    old_score = self.snakes[player_id].score
                    
                    # Create a completely new snake
                    del self.snakes[player_id]
                    
                    # Create a brand new snake
                    new_snake = Snake(player_id, name, color)
                    new_snake.score = old_score // 2
                    self.snakes[player_id] = new_snake
                    
                    print(f"Player {player_id} respawned")
                
                # Remove from dead players list
                del self.dead_players[player_id]
        
        # Update all snakes
        for snake in snakes_list:
            snake.update()
            
            # Check for food collisions
            food_index = snake.check_food_collision(self.foods)
            if food_index is not None:
                # Snake ate food - score increases by 1 point (unchanged)
                snake.score += 1
                
                # Add a second segment to make growth rate 2x
                # The snake already keeps its tail when food is eaten (growth of 1)
                # Adding one more segment here makes the total growth rate 2 segments
                if len(snake.segments) > 0:
                    last_segment = snake.segments[-1].copy()
                    snake.segments.append(last_segment)
                
                # Replace the eaten food with a new one
                x = random.randint(0, WORLD_SIZE)
                y = random.randint(0, WORLD_SIZE)
                self.foods[food_index] = [x, y]
        
        # Check for snake collisions - use the same copy of the list
        current_time = time.time()
        for snake in snakes_list:
            # Skip collision check for very new snakes (5 second grace period)
            if current_time - snake.creation_time < 5:
                continue
            
            for other_snake in snakes_list:
                if snake.check_collision(other_snake):
                    if snake.alive:  # Only process death once
                        snake.alive = False
                        # Track death time for respawn
                        self.dead_players[snake.id] = current_time
                        print(f"Snake {snake.id} died, scheduled respawn")
                        
                        # Give points to the killer if it wasn't suicide
                        if snake.id != other_snake.id and other_snake.alive:
                            other_snake.score += 10
    
    def get_state_for_player(self, player_id):
        # Return the portion of the game state visible to this player
        visible_snakes = []
        for snake in self.snakes.values():
            visible_snakes.append(snake.to_dict())
            
        return {
            "player_id": player_id,
            "snakes": visible_snakes,
            "foods": self.foods,
            "world_size": WORLD_SIZE
        }

class ServerThread(QThread):
    log_signal = pyqtSignal(str)
    clients_updated = pyqtSignal(int)

    def __init__(self, host, port, max_clients=20, use_ssl=True):  # Add use_ssl parameter
        super().__init__()
        self.host = host
        self.port = port
        self.max_clients = max_clients
        self.server_socket = None
        self.clients = {}  # Map of client_socket -> player_id
        self.running = False
        self.game_state = GameState()
        self.client_input_queues = {}  # Map of player_id -> input queue
        self.use_ssl = use_ssl  # Store SSL setting
        self.ssl_context = None  # Will store the SSL context if SSL is enabled

    def run(self):
        try:
            # Create server socket
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            
            # Set up SSL if enabled
            if self.use_ssl:
                # Create SSL context
                self.ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
                
                # Check for existing certificate and key
                cert_path = "server.crt"
                key_path = "server.key"
                
                # If certificates don't exist, create self-signed ones
                if not (os.path.exists(cert_path) and os.path.exists(key_path)):
                    self.log_signal.emit("SSL certificate not found. Creating self-signed certificate...")
                    self.generate_self_signed_cert(cert_path, key_path)
                
                # Load the certificate and key
                try:
                    self.ssl_context.load_cert_chain(certfile=cert_path, keyfile=key_path)
                    self.log_signal.emit("SSL certificate loaded successfully")
                except Exception as e:
                    self.log_signal.emit(f"Error loading SSL certificate: {e}")
                    self.use_ssl = False  # Fall back to non-SSL mode
            
            # Modified to use '' to listen on all network interfaces
            self.server_socket.bind(('', self.port))
            self.server_socket.listen(self.max_clients)
            
            local_ip = self.get_local_ip()
            protocol = "https" if self.use_ssl else "http"
            self.log_signal.emit(f"Game server started on {local_ip}:{self.port} using {protocol}")
            self.running = True

            # Set up the game state's logging callback
            self.game_state.log_message_callback = lambda msg: self.log_signal.emit(msg)
            
            # Start the game loop thread
            game_thread = threading.Thread(target=self.game_loop)
            game_thread.daemon = True
            game_thread.start()

            while self.running:
                # Accept client connections with a timeout
                self.server_socket.settimeout(1.0)
                try:
                    client_socket, address = self.server_socket.accept()
                    
                    # Wrap socket with SSL if enabled
                    if self.use_ssl and self.ssl_context:
                        try:
                            client_socket = self.ssl_context.wrap_socket(
                                client_socket, server_side=True)
                            self.log_signal.emit(f"SSL handshake successful with {address}")
                        except ssl.SSLError as e:
                            self.log_signal.emit(f"SSL handshake failed with {address}: {e}")
                            client_socket.close()
                            continue
                    
                    # Check max clients limit
                    if len(self.clients) >= self.max_clients:
                        client_socket.send(json.dumps({"type": "error", "message": "Server is full"}).encode())
                        client_socket.close()
                        continue

                    # Start a thread to handle this client
                    client_thread = threading.Thread(
                        target=self.handle_client,
                        args=(client_socket, address)
                    )
                    client_thread.daemon = True
                    client_thread.start()

                except socket.timeout:
                    # This allows us to periodically check if server should stop
                    continue
                except Exception as e:
                    self.log_signal.emit(f"Error accepting client: {e}")

        except Exception as e:
            self.log_signal.emit(f"Server error: {e}")
        finally:
            self.stop()
    
    def generate_self_signed_cert(self, cert_path, key_path):
        """Generate a self-signed certificate for SSL connections"""
        try:
            # First try using Python's built-in SSL module to generate certificates
            # This avoids dependency on external OpenSSL command
            from cryptography import x509
            from cryptography.x509.oid import NameOID
            from cryptography.hazmat.primitives import hashes
            from cryptography.hazmat.primitives.asymmetric import rsa
            from cryptography.hazmat.primitives import serialization
            import datetime
            
            # Generate a private key
            private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048,
            )
            
            # Write private key to file
            with open(key_path, "wb") as f:
                f.write(private_key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.PKCS8,
                    encryption_algorithm=serialization.NoEncryption()
                ))
            
            # Generate a self-signed certificate
            subject = issuer = x509.Name([
                x509.NameAttribute(NameOID.COMMON_NAME, u"FunSnakes Game Server"),
            ])
            
            cert = x509.CertificateBuilder().subject_name(
                subject
            ).issuer_name(
                issuer
            ).public_key(
                private_key.public_key()
            ).serial_number(
                x509.random_serial_number()
            ).not_valid_before(
                datetime.datetime.utcnow()
            ).not_valid_after(
                # Certificate valid for 365 days
                datetime.datetime.utcnow() + datetime.timedelta(days=365)
            ).add_extension(
                x509.SubjectAlternativeName([
                    # Allow connections to localhost
                    x509.DNSName(u"localhost"),
                    # Allow connections to any IP
                    x509.DNSName(self.get_local_ip())
                ]),
                critical=False
            ).sign(private_key, hashes.SHA256())
            
            # Write certificate to file
            with open(cert_path, "wb") as f:
                f.write(cert.public_bytes(serialization.Encoding.PEM))
            
            self.log_signal.emit(f"Self-signed certificate generated at {cert_path}")
            
        except ImportError:
            # If cryptography module is not available, try using OpenSSL command
            self.log_signal.emit("Python cryptography module not found, trying OpenSSL command...")
            try:
                import subprocess
                import os
                
                # Generate private key
                key_cmd = [
                    "openssl", "genrsa",
                    "-out", key_path,
                    "2048"
                ]
                subprocess.run(key_cmd, check=True)
                
                # Generate self-signed certificate (valid for 365 days)
                cert_cmd = [
                    "openssl", "req",
                    "-new", "-x509",
                    "-key", key_path,
                    "-out", cert_path,
                    "-days", "365",
                    "-subj", "/CN=FunSnakes Game Server"
                ]
                subprocess.run(cert_cmd, check=True)
                
                self.log_signal.emit(f"Self-signed certificate generated at {cert_path}")
                
            except Exception as e:
                # If OpenSSL commands fail, create a very simple certificate
                self.log_signal.emit(f"Failed to generate certificate using OpenSSL: {e}")
                self.log_signal.emit("Falling back to simple certificate generation...")
                
                # Generate simple certificate and key
                import ssl
                import os
                
                # Create a temporary directory for the certificates
                cert_dir = os.path.dirname(cert_path)
                os.makedirs(cert_dir, exist_ok=True)
                
                # Generate a simple self-signed certificate
                try:
                    # Generate a fixed key using Python's built-in modules
                    from socket import gethostname
                    from OpenSSL import crypto
                    
                    # Create a key pair
                    k = crypto.PKey()
                    k.generate_key(crypto.TYPE_RSA, 2048)
                    
                    # Create a self-signed cert
                    cert = crypto.X509()
                    cert.get_subject().CN = gethostname()
                    cert.set_serial_number(1000)
                    cert.gmtime_adj_notBefore(0)
                    cert.gmtime_adj_notAfter(365*24*60*60)  # 1 year expiry
                    cert.set_issuer(cert.get_subject())
                    cert.set_pubkey(k)
                    cert.sign(k, 'sha256')
                    
                    # Save certificate
                    with open(cert_path, "wb") as f:
                        f.write(crypto.dump_certificate(crypto.FILETYPE_PEM, cert))
                        
                    # Save private key
                    with open(key_path, "wb") as f:
                        f.write(crypto.dump_privatekey(crypto.FILETYPE_PEM, k))
                        
                    self.log_signal.emit(f"Simple self-signed certificate generated at {cert_path}")
                except Exception as e:
                    self.log_signal.emit(f"Failed to generate simple certificate: {e}")
                    self.log_signal.emit("SSL will be disabled - please create certificates manually")
                    self.use_ssl = False
                    
        except Exception as e:
            self.log_signal.emit(f"Failed to generate certificate: {e}")
            self.log_signal.emit("Please create certificates manually and place them in the application directory")
            self.use_ssl = False

    def handle_client(self, client_socket, address):
        try:
            # Wait for the initial join message with player name and color
            data = client_socket.recv(1024).decode('utf-8')
            if not data:
                return
                
            try:
                message = json.loads(data)
                if message["type"] == "join":
                    player_name = message.get("name", f"Player{len(self.clients)+1}")
                    player_color = message.get("color", "#ff0000")
                    is_reconnect = message.get("reconnect", False)
                    last_score = int(message.get("last_score", 0))
                    last_length = int(message.get("last_length", 5))  # Default to 5 segments
                    
                    # Add more detailed logging
                    self.log_signal.emit(f"Player joining: {player_name}, reconnect={is_reconnect}, score={last_score}, length={last_length}")
                    
                    # Create a new snake for this player
                    if is_reconnect and last_score > 0:
                        # Use the new method for reconnecting players with a score
                        player_id = self.game_state.add_snake_with_score(
                            player_name, player_color, last_score, last_length)
                        self.log_signal.emit(f"Player {player_name} reconnected with score {last_score} and length {last_length}")
                    else:
                        # Normal new player
                        player_id = self.game_state.add_snake(player_name, player_color)
                        self.log_signal.emit(f"New player {player_name} joined from {address}")
                    
                    # Add client to our records
                    self.clients[client_socket] = player_id
                    self.client_input_queues[player_id] = deque()
                    
                    # Send acknowledgement with player_id
                    response = {
                        "type": "join_ack",
                        "player_id": player_id
                    }
                    client_socket.send(json.dumps(response).encode())
                    
                    self.clients_updated.emit(len(self.clients))
                    
                    # Enter message loop for this client
                    while self.running:
                        data = client_socket.recv(1024).decode('utf-8')
                        if not data:
                            break
                            
                        try:
                            message = json.loads(data)
                            if message["type"] == "input":
                                # Queue the player input for processing in the game loop
                                self.client_input_queues[player_id].append(message)
                            elif message["type"] == "chat":
                                # Handle chat message
                                if client_socket in self.clients:
                                    player_id = self.clients[client_socket]
                                    player_name = self.game_state.snakes[player_id].name
                                    chat_text = message.get("text", "")
                                    
                                    # Create a chat message to broadcast
                                    chat_message = {
                                        "type": "chat",
                                        "player_id": player_id,
                                        "player_name": player_name,
                                        "text": chat_text
                                    }
                                    
                                    # Log chat message
                                    self.log_signal.emit(f"Chat: {player_name}: {chat_text}")
                                    
                                    # Broadcast to all clients
                                    self.broadcast_message(chat_message)
                        except json.JSONDecodeError:
                            continue
            
            except (json.JSONDecodeError, KeyError) as e:
                self.log_signal.emit(f"Invalid join message from {address}: {e}")
                return
                
        except Exception as e:
            self.log_signal.emit(f"Error handling client {address}: {e}")
        finally:
            # Clean up when client disconnects
            if client_socket in self.clients:
                player_id = self.clients[client_socket]
                self.game_state.remove_snake(player_id)
                del self.clients[client_socket]
                if player_id in self.client_input_queues:
                    del self.client_input_queues[player_id]
                self.log_signal.emit(f"Player {player_id} disconnected from {address}")
                self.clients_updated.emit(len(self.clients))
            
            try:
                client_socket.close()
            except:
                pass
    
    def game_loop(self):
        """Main game loop that updates game state and sends updates to clients"""
        last_time = time.time()
        update_counter = 0
        
        while self.running:
            # Process inputs from all clients
            self.process_client_inputs()
            
            # Update game state
            self.game_state.update()
            
            # Send updates every other tick to reduce network traffic
            update_counter += 1
            if update_counter >= 3:  # Send every 3rd update instead of every update
                update_counter = 0
                self.broadcast_game_state()
            
            # Sleep to maintain tick rate
            current_time = time.time()
            sleep_time = max(0, TICK_RATE / 1000 - (current_time - last_time))
            time.sleep(sleep_time)
            last_time = current_time
    
    def process_client_inputs(self):
        """Process any pending input from clients"""
        # Create a copy of the dictionary items to prevent RuntimeError during iteration
        clients_copy = list(self.clients.items())
        
        for client_socket, player_id in clients_copy:
            # Skip if player was removed
            if player_id not in self.client_input_queues:
                continue
                
            # Process all pending inputs from this client
            input_queue = self.client_input_queues.get(player_id, deque())
            
            # For deque, check len instead of empty()
            while len(input_queue) > 0:  
                message = input_queue.popleft()  # Use popleft() instead of get()
                
                # Handle input message (movement direction)
                if message.get("type") == "input":
                    dx = message.get("dx", 0)
                    dy = message.get("dy", 0)
                    
                    # Apply to snake if player exists
                    if player_id in self.game_state.snakes:
                        # Only print direction changes occasionally to reduce spam
                        self.game_state.snakes[player_id].set_direction(dx, dy)
    
    def broadcast_game_state(self):
        """Send the current game state to all connected clients"""
        # Create a copy of the dictionary items to prevent RuntimeError
        clients_copy = list(self.clients.items())
        
        for client_socket, player_id in clients_copy:
            try:
                # Prepare custom state view for this player
                state = self.game_state.get_state_for_player(player_id)
                message = {
                    "type": "state_update",
                    "state": state
                }
                
                # Convert to JSON once
                json_message = json.dumps(message) + "\n"
                client_socket.send(json_message.encode())
            except Exception as e:
                # Will be cleaned up in the client handler thread
                self.log_signal.emit(f"Error sending to client: {e}")
    
    def broadcast_message(self, message):
        """Send a message to all connected clients"""
        # Create a copy of the clients for thread safety
        clients_copy = list(self.clients.keys())
        
        message_json = json.dumps(message) + "\n"
        for client_socket in clients_copy:
            try:
                client_socket.send(message_json.encode())
            except Exception as e:
                # Will be cleaned up in the client handler thread
                self.log_signal.emit(f"Error sending message: {e}")
    
    def get_local_ip(self):
        """Get the local IP address of the server"""
        try:
            # Create a socket to determine the IP address
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            # Doesn't need to be reachable, just to determine interface
            s.connect(('8.8.8.8', 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"  # Fallback to localhost if error

    def stop(self):
        """
        Stop the server and clean up resources
        """
        self.running = False
        
        # Close all client sockets
        for client_socket in list(self.clients.keys()):
            try:
                client_socket.close()
            except Exception as e:
                self.log_signal.emit(f"Error closing client socket: {e}")

        # Clear client records
        self.clients.clear()
        self.client_input_queues.clear()

        # Close server socket
        if self.server_socket:
            try:
                self.server_socket.close()
                self.log_signal.emit("Server socket closed")
            except Exception as e:
                self.log_signal.emit(f"Error closing server socket: {e}")

        # Update clients count
        self.clients_updated.emit(0)

class SnakeGameHostApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.server_thread = None
        self.initUI()

    def initUI(self):
        self.setWindowTitle('FunSnakes - Game Server')
        self.setGeometry(100, 100, 700, 500)

        main_widget = QWidget()
        main_layout = QVBoxLayout()
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

        # Server section with configuration
        server_layout = QHBoxLayout()
        
        # Get IP address to show in the UI
        self.host_ip_label = QLabel(f'Your IP: {self.get_local_ip()}')
        
        self.port_input = QLineEdit('5000')
        self.port_input.setPlaceholderText('Enter port number')
        
        # Max clients input
        self.max_clients_input = QLineEdit('20')
        self.max_clients_input.setPlaceholderText('Max Players')
        
        # Add SSL checkbox
        self.use_ssl_checkbox = QCheckBox('Enable SSL')
        self.use_ssl_checkbox.setChecked(True)
        
        start_server_btn = QPushButton('Start Server')
        stop_server_btn = QPushButton('Stop Server')
        start_server_btn.clicked.connect(self.start_server)
        stop_server_btn.clicked.connect(self.stop_server)
        
        server_layout.addWidget(self.host_ip_label)
        server_layout.addWidget(QLabel('Port:'))
        server_layout.addWidget(self.port_input)
        server_layout.addWidget(QLabel('Max Players:'))
        server_layout.addWidget(self.max_clients_input)
        server_layout.addWidget(self.use_ssl_checkbox)
        server_layout.addWidget(start_server_btn)
        server_layout.addWidget(stop_server_btn)
        main_layout.addLayout(server_layout)

        # Connected Players section
        self.clients_label = QLabel('Connected Players: 0')
        main_layout.addWidget(self.clients_label)

        # Game settings section
        game_layout = QHBoxLayout()
        game_layout.addWidget(QLabel('Game World Size:'))
        self.world_size_label = QLabel(f'{WORLD_SIZE}x{WORLD_SIZE}')
        game_layout.addWidget(self.world_size_label)
        game_layout.addWidget(QLabel('Food Items:'))
        self.food_count_label = QLabel(f'{FOOD_COUNT}')
        game_layout.addWidget(self.food_count_label)
        main_layout.addLayout(game_layout)

        # Log area
        self.log_list = QListWidget()
        main_layout.addWidget(QLabel('Server Logs:'))
        main_layout.addWidget(self.log_list)
        
        # Add refresh IP button
        refresh_ip_btn = QPushButton('Refresh IP')
        refresh_ip_btn.clicked.connect(self.refresh_ip)
        main_layout.addWidget(refresh_ip_btn)

    def get_local_ip(self):
        """Get the local IP address of the server"""
        try:
            # Create a socket to determine the IP address
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            # Doesn't need to be reachable, just to determine interface
            s.connect(('8.8.8.8', 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"  # Fallback to localhost if error
    
    def refresh_ip(self):
        """Refresh the displayed IP address"""
        ip = self.get_local_ip()
        self.host_ip_label.setText(f'Your IP: {ip}')
        self.log_message(f"IP refreshed: {ip}")

    def log_message(self, message):
        # Add a message to the log list
        self.log_list.addItem(message)
        self.log_list.scrollToBottom()

    def start_server(self):
        # Validate inputs
        try:
            port = int(self.port_input.text())
            if port <= 0 or port > 65535:
                raise ValueError("Invalid port number")
        except ValueError:
            QMessageBox.warning(self, "Input Error", "Please enter a valid port number (1-65535)")
            return

        try:
            max_clients = int(self.max_clients_input.text())
            if max_clients <= 0:
                raise ValueError("Invalid max players number")
        except ValueError:
            QMessageBox.warning(self, "Input Error", "Please enter a valid number of max players")
            return

        # Stop existing server if running
        if self.server_thread:
            self.stop_server()

        # Get SSL setting
        use_ssl = self.use_ssl_checkbox.isChecked()

        # Start new server thread - use empty string to bind to all interfaces
        self.server_thread = ServerThread('', port, max_clients, use_ssl)
        self.server_thread.log_signal.connect(self.log_message)
        self.server_thread.clients_updated.connect(self.update_clients_count)
        self.server_thread.start()
        self.log_message("Starting game server...")

    def stop_server(self):
        if self.server_thread:
            self.server_thread.stop()
            self.server_thread = None
            self.log_message("Game server stopped")

    def update_clients_count(self, count):
        self.clients_label.setText(f'Connected Players: {count}')

    def closeEvent(self, event):
        if self.server_thread:
            self.server_thread.stop()
        event.accept()

def main():
    app = QApplication(sys.argv)
    host_app = SnakeGameHostApp()
    host_app.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()