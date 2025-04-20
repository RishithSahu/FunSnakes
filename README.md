# FunSnakes - Multiplayer Snake Game Documentation

## Table of Contents

1. [Introduction](#1-introduction)
2. [Technology Stack and Implementation](#2-technology-stack-and-implementation)
3. [Installation and Setup](#3-installation-and-setup)
4. [Technical Architecture](#4-technical-architecture)
5. [Game Mechanics](#5-game-mechanics)
6. [Security Features](#6-security-features)
7. [User Guide](#7-user-guide)
8. [Implementation Details](#8-implementation-details)
9. [Troubleshooting](#9-troubleshooting)
10. [Future Enhancements](#10-future-enhancements)

## 1. Introduction

FunSnakes is a real-time multiplayer snake game built with Python and PyQt5. The game allows multiple players to connect to a central server and compete against each other in a shared virtual space. Players control snakes that grow by consuming food and can eliminate other players by causing them to collide with their body.

### 1.1 Project Overview

FunSnakes was developed as a Computer Networks mini-project to demonstrate client-server architecture, network programming concepts, and real-time data synchronization across multiple clients. The application leverages socket programming, multi-threading, and modern UI frameworks to create an engaging multiplayer experience.

### 1.2 Key Features

- Real-time multiplayer gameplay with support for multiple simultaneous players
- Client-server architecture with secure SSL communication
- Cross-platform compatibility (Windows, Linux, macOS)
- In-game chat functionality for player communication
- Dynamic leaderboard to track top players
- Automatic player respawn after elimination
- Intuitive mouse and keyboard controls
- Customizable player names and snake colors

## 2. Technology Stack and Implementation

### 2.1 Technology Overview

FunSnakes leverages several technologies to create a seamless multiplayer gaming experience:

| Component             | Technology Used                                                                                                     |
| --------------------- | ------------------------------------------------------------------------------------------------------------------- |
| Programming Language  | Python 3.6+                                                                                                         |
| User Interface        | PyQt5 Framework |
| Network Communication | Socket API, TCP/IP                                                                                                  |
| Security              | SSL/TLS Encryption                                                                                                  |
| Data Exchange Format  | JSON                                                                                                                |
| Concurrency           | Multi-threading                                                                                                     |
| Graphics Rendering    | PyQt5 Graphics Framework                                                                                            |

### 2.2 Networking Concepts Explained

#### Client-Server Architecture

At its core, FunSnakes uses a client-server model, which can be understood as similar to how a restaurant works:

- The **server** is like the kitchen that prepares food (game state) and manages all orders
- The **clients** are like customers who send requests (player inputs) and receive food (game updates)
- The **waiters** are like the network connections that carry information back and forth

In technical terms, one computer runs the server application (host.py) which maintains the authoritative game state. Multiple players run the client application (client.py) which connects to this server. This architecture ensures all players see a consistent game world.

#### TCP/IP Communication

FunSnakes uses TCP/IP (Transmission Control Protocol/Internet Protocol) for all network communication. Think of TCP/IP as the postal service of the internet:

- **IP** is like the addressing system that ensures data packets reach the correct computer
- **TCP** is like certified mail that guarantees delivery and correct ordering of messages

This reliability is crucial for a game where missed inputs or state updates would create a poor player experience. When a player changes direction, that command must reach the server without fail.

#### Sockets

Sockets are the endpoints of network communication, similar to telephone handsets in a call. In FunSnakes:

- The server creates a listening socket (like an open phone line waiting for calls)
- Each client creates its own socket to connect to the server
- When a client connects, the server creates a dedicated socket for that client

This allows the server to communicate individually with each player while still managing the overall game.

#### Network Packets and JSON

All game information is exchanged using JSON (JavaScript Object Notation) formatted text messages. This is like sending structured letters where:

- The envelope (network packet) delivers the message
- The letter inside (JSON data) has a standard format that both sender and receiver understand
- Each message contains specific information like snake positions, food locations, or chat messages

JSON was chosen because it's human-readable, widely supported, and efficiently represents structured data.

### 2.3 Multi-threading Explained

FunSnakes uses multiple threads to perform different tasks simultaneously, similar to how a restaurant might have separate staff for taking orders, cooking, and serving:

- The **main thread** handles the user interface, keeping it responsive
- A **game loop thread** continuously updates the game state at fixed intervals
- **Client handler threads** process each player's inputs and messages
- **Network threads** handle sending and receiving data

This separation allows the game to remain responsive even when network operations might take time.

### 2.4 User Interface Technology

The game uses PyQt5, a powerful UI framework that:

- Provides a window-based interface for both server and client applications
- Renders the game world with smooth graphics
- Handles user inputs from mouse and keyboard
- Displays the chat system, scores, and other game information

PyQt5's event-driven architecture makes it ideal for games, as it can respond immediately to player actions.

### 2.5 Security Implementation

To protect player communications, FunSnakes implements SSL/TLS encryption, which is like putting your letters in locked security envelopes:

- Each message is encrypted before being sent over the network
- Only the intended recipient can decrypt and read the message
- This prevents eavesdropping on game data or chat messages

The game uses self-signed certificates (generated automatically if needed) to establish secure connections between clients and the server.

### 2.6 PyQt5 Framework Deep Dive

PyQt5 is a set of Python bindings for the Qt application framework, which forms the backbone of FunSnakes' user interface and graphics rendering system.

#### 2.6.1 Overview of PyQt5

PyQt5 provides Python developers access to all the functionality of the Qt framework, a powerful C++ based application development platform. Key aspects include:

- **Cross-platform compatibility**: Consistent look and feel across Windows, macOS, and Linux
- **Comprehensive widget set**: Pre-built UI components that maintain native appearance on each OS
- **Signal-slot mechanism**: Event-driven programming model for responsive UI interactions
- **Graphics View Framework**: Powerful scene graph system for rendering game elements
- **Threading support**: Integration with Python's threading capabilities
- **Multimedia capabilities**: Support for audio and video playback

#### 2.6.2 PyQt5 Architecture in FunSnakes

In FunSnakes, PyQt5 operates on multiple architectural levels:

1. **Application Framework**: Provides the main event loop and application lifecycle management

   ```python
   app = QApplication(sys.argv)  # Creates the application instance
   window = MainWindow()         # Creates the main window
   app.exec_()                   # Starts the event loop
   ```

2. **Widget Hierarchy**: Creates the visual structure of the application

   - Main windows contain the game canvas, chat panel, and controls
   - Layouts manage positioning and resizing of UI elements
   - Custom widgets handle specialized game rendering

3. **Rendering System**: Manages the visual representation of game elements

   - QGraphicsScene holds all game objects (snakes, food items)
   - QGraphicsView provides the viewport into the game world
   - Custom QGraphicsItems represent individual game elements

4. **Input Handling**: Captures and processes user interactions
   - Mouse movement tracking for snake direction control
   - Keyboard event handling for alternative controls and chat
   - Custom event filters for specialized input processing

#### 2.6.3 PyQt5 Rendering Pipeline

The game's rendering system utilizes PyQt5's Graphics View Framework in the following pipeline:

1. **Scene Creation**: The server maintains the game state, while the client represents this as a QGraphicsScene
2. **Object Representation**: Each snake segment, food item, and UI element is a QGraphicsItem
3. **View Setup**: QGraphicsView provides the viewport into the virtual game world
4. **Transformation**: Matrix transformations handle zooming, panning, and coordinate mapping
5. **Rendering**: The scene is rendered to the screen with automatic double-buffering

```python
# Example of the rendering setup
self.scene = QGraphicsScene(self)
self.view = QGraphicsView(self.scene)
self.view.setRenderHint(QPainter.Antialiasing)
self.view.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
```

#### 2.6.4 Signal-Slot Communication

PyQt5's signal-slot mechanism facilitates communication between game components:

- **Network signals**: Triggered when data is received from the server
- **Game state signals**: Connect game events to UI updates
- **Timer signals**: Drive the game loop and animation updates
- **Input signals**: Connect user actions to game functions

This event-driven architecture allows the game to remain responsive while processing network traffic and rendering complex scenes.

#### 2.6.5 Styling and Theming

FunSnakes leverages PyQt5's styling capabilities to create a consistent visual experience:

- **QSS (Qt Style Sheets)**: CSS-like syntax for styling UI elements
- **Color palettes**: Consistent color themes across the application
- **Custom drawing**: Specialized rendering for game elements like snakes and food

The combination of these technologies enables FunSnakes to provide a smooth, responsive, and visually appealing multiplayer experience across multiple platforms.

## 3. Installation and Setup

### 3.1 System Requirements

- Python 3.6 or higher
- PyQt5 library
- Minimum 2GB RAM
- Network connection for multiplayer functionality

### 3.2 Installation Steps

1. Ensure Python 3.6+ is installed on your system

   ```bash
   python --version
   ```

2. Install the PyQt5 library using pip

   ```bash
   pip install PyQt5
   ```

3. Download or clone the FunSnakes repository

   ```bash
   git clone https://github.com/username/FunSnakes.git
   cd FunSnakes
   ```

4. No further installation is required - the game can be run directly from the source files

### 3.3 Project Structure

The project contains the following key files:

- **host.py**: Server application for hosting game sessions
- **client.py**: Client application for players to join games
- **server.crt** and **server.key**: SSL certificate files (auto-generated if not present)
- **README.md**: Basic project information and quick start guide

## 4. Technical Architecture

### 4.1 Client-Server Model

FunSnakes implements a classic client-server architecture:

- **Server (host.py)**: Centralized game server that:

  - Manages the game state including snake positions, food locations, scores
  - Processes player inputs and updates game state accordingly
  - Broadcasts game state updates to all connected clients
  - Handles player connections/disconnections
  - Facilitates chat message distribution

- **Client (client.py)**: Player application that:
  - Connects to server and renders the game state
  - Captures player input and sends to server
  - Receives state updates and renders the game world
  - Provides user interface for game controls and chat

### 4.2 Network Communication

All communication between clients and server uses TCP sockets to ensure reliable data delivery:

- **Connection Protocol**: Initial handshake with SSL/TLS encryption (when enabled)
- **Message Format**: JSON-encoded data structures with newline terminators
- **State Synchronization**: Server broadcasts game state updates regularly (typically 5 updates per second)
- **Input Handling**: Clients send direction inputs at controlled intervals to prevent network overload

### 4.3 Game State Management

The server maintains the authoritative game state including:

- Snake positions, directions, and sizes
- Food item locations
- Player scores and status (alive/dead)
- World boundaries and game constants

This state is updated on a fixed tick rate (typically 15 ticks per second) and broadcast to all connected clients.

### 4.4 Threading Model

Both client and server applications utilize multiple threads:

- **Server Threads**:

  - Main thread: UI and user interaction
  - Server socket thread: Accepts new client connections
  - Game loop thread: Updates game state on regular intervals
  - Client handler threads: One per connected client for message processing

- **Client Threads**:
  - Main thread: UI rendering and user interaction
  - Network thread: Receives server updates and sends player inputs
  - Input sending thread: Throttles direction updates to the server

## 5. Game Mechanics

### 5.1 Core Gameplay

FunSnakes follows the classic snake game mechanics with multiplayer additions:

1. Each player controls a snake that moves continuously in the current direction
2. Players can change their snake's direction using mouse or arrow keys
3. Consuming food items increases the snake's length and score
4. Colliding with another snake results in elimination
5. After elimination, players automatically respawn after a short delay
6. The world wraps around at boundaries (snakes that go off one edge appear at the opposite edge)

### 5.2 Scoring System

- +1 point for each food item consumed
- +10 points for eliminating another player
- Upon death, a player loses half their score when respawning

### 5.3 Game World

- **World Size**: 3000x3000 game units
- **Food Items**: 1050 food items distributed randomly across the world
- **Snake Starting Size**: 5 segments
- **Snake Movement Speed**: 7 units per update
- **Respawn Time**: 5 seconds after elimination

### 5.4 Collision Detection

The game implements circle-based collision detection:

- Snake segments are treated as circles with radius of 10 units
- Food items are circles with radius of 5 units
- A collision occurs when the distance between two circles is less than the sum of their radii
- New players have a 5-second grace period where collisions are ignored

## 6. Security Features

### 6.1 SSL/TLS Encryption

FunSnakes implements optional SSL/TLS encryption for secure communication:

- Self-signed certificates are auto-generated if not present
- Players can connect using encrypted or unencrypted connections
- SSL implementation helps prevent eavesdropping on game data and chat messages

### 6.2 Certificate Generation

When SSL is enabled and certificates are not found, the server can generate them using:

1. Python's cryptography module (preferred method)
2. OpenSSL command-line tools (fallback method)
3. Simple certificate generation using built-in modules (secondary fallback)

### 6.3 Connection Security

- Server verifies client connections with proper handshaking
- Clients can verify server identity (though self-signed certificates generate warnings)
- Clients can fall back to unencrypted connections if SSL handshake fails

## 7. User Guide

### 7.1 Starting a Game Server

1. Run the host.py script:

   ```bash
   python host.py
   ```

2. Configure server settings:

   - Port number (default: 5000)
   - Maximum number of players (default: 20)
   - Enable/disable SSL encryption (checked by default)

3. Click "Start Server" to begin hosting

4. Share your IP address (displayed in the UI) with players who want to join

5. Monitor connected players and server logs in the UI

### 7.2 Joining a Game

1. Run the client.py script:

   ```bash
   python client.py
   ```

2. Enter connection details:

   - Server IP address or hostname
   - Port number (default: 5000)
   - Your player name
   - Snake color (hex format, e.g., #FF5500)
   - Enable/disable SSL (should match server setting)

3. Click "Join Game" to connect to the server

4. Once connected, you'll spawn in the game world with your snake

### 7.3 Game Controls

- **Mouse Movement**: Move your mouse to direct your snake toward the cursor
- **Arrow Keys**: Alternative way to control direction (up, down, left, right)
- **T Key**: Focus on the chat input box
- **Enter Key**: Send a chat message when the chat input is focused

### 7.4 In-Game Communication

Players can communicate through the in-game chat system:

1. Press 'T' to focus on the chat input field
2. Type your message
3. Press Enter or click "Send" to send your message
4. Messages are broadcast to all connected players
5. Your own messages appear in blue, others' messages in white

## 8. Troubleshooting

### 8.1 Common Issues and Solutions

#### Cannot Connect to Server

**Problem**: Client cannot connect to the game server
**Solutions**:

- Verify the server is running and the IP address/port is correct
- Check if firewalls are blocking the connection
- Try connecting without SSL if SSL handshake fails
- Verify that server and client are using the same port

#### Game Lag or Performance Issues

**Problem**: Game feels sluggish or unresponsive
**Solutions**:

- Reduce the number of connected players
- Check your network connection quality
- Close other bandwidth-intensive applications
- Try connecting to a server geographically closer to you

#### SSL Certificate Errors

**Problem**: SSL handshake fails or certificates cannot be generated
**Solutions**:

- Try connecting without SSL encryption
- Manually create certificates using OpenSSL:
  ```bash
  openssl req -x509 -newkey rsa:2048 -keyout server.key -out server.crt -days 365 -nodes
  ```
- Place the certificate files in the same directory as the host.py script

#### Snake Movement Issues

**Problem**: Snake doesn't respond to controls or moves erratically
**Solutions**:

- Ensure you're focusing on the game window (click on it)
- Try using arrow keys if mouse control isn't working
- Check for high network latency that might cause delayed responses
- Restart the client application

### 8.2 Logs and Diagnostics

Both server and client applications maintain logs that can help diagnose issues:

- **Server Logs**: Displayed in the log area of the host application

  - Track player connections/disconnections
  - View errors and warnings
  - Monitor player respawns

- **Client Logs**: Displayed in the log area of the client application
  - Connection status and attempts
  - SSL handshake information
  - Error messages from the server

## 9. Future Enhancements

### 9.1 Planned Features

The following enhancements could be implemented in future versions:

1. **Power-ups and Special Abilities**

   - Speed boosts
   - Temporary shields
   - Special attacks

2. **Game Modes**

   - Team-based gameplay
   - Capture the flag
   - Battle royale with shrinking play area

3. **Enhanced User Interface**

   - Customizable viewport size
   - Graphical themes and backgrounds
   - Sound effects and music

4. **Account System**
   - Persistent player profiles
   - Stat tracking
   - Achievements

### 9.2 Technical Improvements

Potential technical improvements include:

1. **Network Optimizations**

   - Delta compression for state updates
   - Predictive client-side movement
   - Regional server deployment

2. **Security Enhancements**

   - Proper certificate validation
   - User authentication
   - Anti-cheat measures

3. **Performance Improvements**
   - Hardware acceleration for rendering
   - More efficient collision detection algorithms
   - Dynamic detail level based on client performance
