# FunSnakes - Multiplayer Snake Game

A multiplayer snake game built with Python and PyQt5 where players can compete against each other over a network connection.

## Overview

FunSnakes is a real-time multiplayer snake game where players control snakes to collect food and grow larger while avoiding collisions with other snakes. The game features a client-server architecture allowing multiple players to join from different machines.

## Features

- **Real-time multiplayer gameplay** - Compete with multiple players simultaneously
- **Cross-platform support** (Windows, Linux, macOS)
- **Smooth snake movement** with mouse or arrow key controls
- **In-game chat** to communicate with other players
- **Leaderboard** showing top players by score
- **Automatic respawn** after death
- **Colorful snakes** with customizable colors
- **Optimized performance** for smooth gameplay even with many players

## Requirements

- Python 3.6+
- PyQt5

## Installation

1. Ensure you have Python installed on your system
2. Install the required dependencies:
   ```
   pip install PyQt5
   ```

## How to Play

### Starting the Server (Host)

1. Run the host.py script:
   ```
   python host.py
   ```
2. Configure the server settings (port number and max players)
3. Click "Start Server" to begin hosting the game
4. Share your IP address with other players who want to join

### Joining a Game (Client)

1. Run the client.py script:
   ```
   python client.py
   ```
2. Enter the server IP address and port
3. Choose your player name and color
4. Click "Join Game" to connect to the server

### Game Controls

- **Mouse Movement**: Move your mouse to control the direction of your snake
- **Arrow Keys**: Can also be used to change direction
- **T Key**: Focus the chat input
- **Enter**: Send chat messages

### Game Rules

1. Eat red food to grow your snake and gain points
2. Avoid collisions with other snakes
3. If you collide with another snake, you die and lose half your points
4. After death, you'll automatically respawn after a short delay
5. The player with the highest score leads the leaderboard

## Project Structure

- **host.py** - Server-side application that manages the game state and client connections
- **client.py** - Client-side application that connects to the server and renders the game

## Troubleshooting

- **Connection Issues**: Make sure the server is running and the correct IP/port are entered
- **Performance Problems**: Reduce the number of players or increase your system's resources
- **Display Issues**: Make sure PyQt5 is properly installed

## Credits

Created as a Computer Networks Mini Project.

## License

This project is available for educational purposes.
