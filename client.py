import sys
import os
import json
import requests
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout,
                             QLabel, QLineEdit, QPushButton, QCheckBox,
                             QMessageBox, QWidget, QListWidget, QListWidgetItem, QTextEdit, QScrollArea)

TOKEN_FILE = 'token.json'  # File to store token if "Remember Me" is checked

class LoginWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle('Discord Login')
        self.setGeometry(300, 200, 300, 300)

        layout = QVBoxLayout()

        # Email input field
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Enter Email")
        layout.addWidget(QLabel("Email:"))
        layout.addWidget(self.email_input)

        # Password input field
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Enter Password")
        self.password_input.setEchoMode(QLineEdit.Password)
        layout.addWidget(QLabel("Password:"))
        layout.addWidget(self.password_input)

        # Remember me checkbox
        self.remember_checkbox = QCheckBox("Remember Me")
        layout.addWidget(self.remember_checkbox)

        # Login button
        self.login_button = QPushButton('Login')
        self.login_button.clicked.connect(self.login)
        layout.addWidget(self.login_button)

        # Container for layout
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        # Load saved token if exists
        self.load_saved_token()

    def load_saved_token(self):
        if os.path.exists(TOKEN_FILE):
            with open(TOKEN_FILE, 'r') as file:
                data = json.load(file)
                token = data.get('token', '')
                if token:
                    print("Logged in with saved token.")
                    self.open_main_window(token)

    def save_token(self, token):
        if self.remember_checkbox.isChecked():
            with open(TOKEN_FILE, 'w') as file:
                json.dump({'token': token}, file)
        elif os.path.exists(TOKEN_FILE):
            os.remove(TOKEN_FILE)

    def login(self):
        email = self.email_input.text().strip()
        password = self.password_input.text().strip()

        if not email or not password:
            QMessageBox.warning(self, "Error", "Email and password cannot be empty!")
            return

        print("Attempting to log in...")
        token, error = self.retrieve_token(email, password)

        if error:
            QMessageBox.warning(self, "Error", error)
            return

        print(f"Token retrieved: {token}")
        self.save_token(token)  # Save token if "Remember Me" is checked
        self.open_main_window(token)

    def retrieve_token(self, email, password):
        # Login URL
        url = "https://discord.com/api/v9/auth/login"
        payload = {
            "email": email,
            "password": password,
        }
        headers = {
            "Content-Type": "application/json",
        }

        # Send login request
        response = requests.post(url, json=payload, headers=headers)

        print("Response:", response.text)  # Debugging

        if response.status_code == 200:
            data = response.json()
            return data.get('token'), None  # Return token or None if not found
        elif response.status_code == 401:
            return None, "Invalid email or password."
        elif response.status_code == 403:
            return None, "Two-factor authentication required."
        else:
            return None, f"Failed to log in: {response.json().get('message', 'Unknown error')}"

    def open_main_window(self, token):
        self.main_window = MainWindow(token)
        self.main_window.show()
        self.close()


class MainWindow(QMainWindow):
    def __init__(self, token):
        super().__init__()
        self.token = token
        self.current_channel_id = None  # Variable to hold the current channel ID
        self.setWindowTitle('Discord Client')
        self.setGeometry(300, 200, 800, 600)

        self.layout = QHBoxLayout()

        # Sidebar for channels
        self.channel_list = QListWidget()
        self.channel_list.clicked.connect(self.on_channel_click)
        self.layout.addWidget(self.channel_list)

        # Main content area
        self.main_content = QWidget()
        self.main_content.setLayout(QVBoxLayout())
        self.layout.addWidget(self.main_content)

        # Message display area with scroll capability
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.message_area = QWidget()
        self.message_area_layout = QVBoxLayout(self.message_area)
        self.scroll_area.setWidget(self.message_area)
        self.main_content.layout().addWidget(self.scroll_area)

        # Input for new messages
        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText("Type a message...")
        self.main_content.layout().addWidget(self.message_input)

        # Send button
        self.send_button = QPushButton("Send")
        self.send_button.clicked.connect(self.send_message)
        self.main_content.layout().addWidget(self.send_button)

        # Input for friend requests
        self.friend_input = QLineEdit()
        self.friend_input.setPlaceholderText("Type friend's username...")
        self.main_content.layout().addWidget(self.friend_input)

        # Send friend request button
        self.send_friend_request_button = QPushButton("Send Friend Request")
        self.send_friend_request_button.clicked.connect(self.send_friend_request)
        self.main_content.layout().addWidget(self.send_friend_request_button)

        # Set the layout for the main window
        container = QWidget()
        container.setLayout(self.layout)
        self.setCentralWidget(container)

        self.fetch_user_info()

    def fetch_user_info(self):
        # Fetching user info
        response = requests.get("https://discord.com/api/v9/users/@me", headers={'Authorization': self.token})
        if response.status_code == 200:
            user_data = response.json()
            print(f"Logged in as: {user_data['username']}#{user_data['discriminator']}")
            self.load_guilds()
            self.load_friends()
        else:
            print(f"Failed to fetch user info: {response.status_code} {response.text}")

    def load_guilds(self):
        # Fetching user's guilds (servers)
        response = requests.get("https://discord.com/api/v9/users/@me/guilds", headers={'Authorization': self.token})
        if response.status_code == 200:
            guilds = response.json()
            for guild in guilds:
                item = QListWidgetItem(guild['name'])
                item.setData(1, guild['id'])  # Store the guild ID in the item
                self.channel_list.addItem(item)
            print("Guilds loaded.")
        else:
            print(f"Failed to fetch guilds: {response.status_code} {response.text}")

    def load_friends(self):
        # Fetching user's friends
        response = requests.get("https://discord.com/api/v9/users/@me/relationships", headers={'Authorization': self.token})
        if response.status_code == 200:
            friends = response.json()
            for friend in friends:
                if friend['type'] == 1:  # Type 1 means friend
                    msg_label = QLabel(f"Friend: {friend['user']['username']}#{friend['user']['discriminator']}")
                    self.message_area_layout.addWidget(msg_label)
            print("Friends loaded.")
        else:
            print(f"Failed to fetch friends: {response.status_code} {response.text}")

    def on_channel_click(self, item):
        guild_id = item.data(1)
        print(f"Clicked on guild: {guild_id}")
        self.load_channels(guild_id)

    def load_channels(self, guild_id):
        # Clear previous messages
        for i in reversed(range(self.message_area_layout.count())):
            widget = self.message_area_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)

        # Fetch channels for the selected guild
        response = requests.get(f"https://discord.com/api/v9/guilds/{guild_id}/channels", headers={'Authorization': self.token})
        if response.status_code == 200:
            channels = response.json()
            self.message_area_layout.addWidget(QLabel(f"Channels in Guild {guild_id}:"))
            for channel in channels:
                if channel['type'] == 0:  # Text channel
                    channel_item = QPushButton(channel['name'])
                    channel_item.clicked.connect(lambda _, channel_id=channel['id']: self.join_channel(channel_id))
                    self.message_area_layout.addWidget(channel_item)
                elif channel['type'] == 2:  # Voice channel
                    vc_item = QPushButton(channel['name'])
                    vc_item.clicked.connect(lambda _, channel_id=channel['id']: self.join_voice_channel(channel_id))
                    self.message_area_layout.addWidget(vc_item)
        else:
            print(f"Failed to fetch channels: {response.status_code} {response.text}")

    def join_channel(self, channel_id):
        print(f"Joining channel: {channel_id}")
        self.current_channel_id = channel_id  # Set the current channel ID
        self.fetch_channel_messages(channel_id)

    def fetch_channel_messages(self, channel_id):
        # Clear previous messages
        for i in reversed(range(self.message_area_layout.count())):
            widget = self.message_area_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)

        # Fetch messages for the selected channel
        response = requests.get(f"https://discord.com/api/v9/channels/{channel_id}/messages", headers={'Authorization': self.token})
        if response.status_code == 200:
            messages = response.json()
            for message in messages:
                msg_label = QLabel(f"{message['author']['username']}: {message['content']}")
                self.message_area_layout.addWidget(msg_label)
        else:
            print(f"Failed to fetch messages: {response.status_code} {response.text}")

    def send_message(self):
        message_content = self.message_input.text().strip()
        if not message_content:
            QMessageBox.warning(self, "Error", "Message cannot be empty!")
            return

        if not self.current_channel_id:  # Ensure a channel is selected
            QMessageBox.warning(self, "Error", "No channel selected!")
            return

        payload = {
            "content": message_content,
            "tts": False
        }

        response = requests.post(f"https://discord.com/api/v9/channels/{self.current_channel_id}/messages", json=payload,
                                 headers={'Authorization': self.token})
        if response.status_code == 200:
            self.message_input.clear()  # Clear input field after sending
            self.fetch_channel_messages(self.current_channel_id)  # Refresh messages
        else:
            print(f"Failed to send message: {response.status_code} {response.text}")

    def send_friend_request(self):
        friend_username = self.friend_input.text().strip()
        if not friend_username:
            QMessageBox.warning(self, "Error", "Friend's username cannot be empty!")
            return

        # Here, you should split username and discriminator if needed
        payload = {
            "username": friend_username,
            "type": 1  # 1 means friend request
        }

        response = requests.post("https://discord.com/api/v9/users/@me/relationships", json=payload,
                                 headers={'Authorization': self.token})
        if response.status_code == 200:
            QMessageBox.information(self, "Success", "Friend request sent successfully!")
            self.friend_input.clear()  # Clear input after sending
        else:
            print(f"Failed to send friend request: {response.status_code} {response.text}")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = LoginWindow()
    window.show()
    sys.exit(app.exec_())
