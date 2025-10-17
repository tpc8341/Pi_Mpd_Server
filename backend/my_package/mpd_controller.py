# First, ensure you have the python-mpd2 library installed:
# pip install python-mpd2
import os,sys
from mpd import MPDClient
from mpd import ConnectionError as MPDConnectionError
from mpd import CommandError as MPDCommandError

class MPDClientController:
    """
    A class to control the Music Player Daemon (MPD) using python-mpd2.

    This class provides a simple interface for common MPD commands like playing,
    pausing, changing tracks, and managing volume.

    Attributes:
        host (str): The hostname or IP address of the MPD server.
        port (int): The port number for the MPD server.
        client (MPDClient): The MPDClient instance used for communication.
        is_connected (bool): A flag to track the connection status.
    """

    def __init__(self, host='localhost', port=6600):
        """
        Initializes the MPDClientController with the server host and port.

        Args:
            host (str): The host of the MPD server. Defaults to 'localhost'.
            port (int): The port of the MPD server. Defaults to 6600.
        """
        self.host = host
        self.port = port
        self.client = MPDClient(use_unicode=True)
        self.is_connected = False

    def __enter__(self):
        """Allows the class to be used as a context manager."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Ensures the client is disconnected when exiting the context."""
        self.disconnect()

    def connect(self):
        """
        Connects to the MPD server.

        Handles connection errors and updates the connection status.
        """
        if self.is_connected:
            print("Already connected.")
            return

        print(f"Attempting to connect to MPD at {self.host}:{self.port}...")
        try:
            self.client.connect(self.host, self.port)
            self.is_connected = True
            print("Successfully connected to MPD.")
        except MPDConnectionError as e:
            print(f"Error: Could not connect to MPD. {e}")
            sys.exit(1)
        except Exception as e:
            print(f"An unexpected error occurred during connection: {e}")
            sys.exit(1)

    def disconnect(self):
        """
        Disconnects from the MPD server.
        """
        if self.is_connected:
            self.client.close()
            self.client.disconnect()
            self.is_connected = False
            print("Disconnected from MPD.")
        else:
            print("Not connected.")

    def _check_connection(self):
        """
        Private method to check if the client is connected before
        executing a command.
        """
        if not self.is_connected:
            print("Error: Not connected to MPD. Please connect first.")
            return False
        return True
    def get_status(self):
        """
        Retrieves the current status of the MPD server.

        Returns:
            dict: A dictionary containing the player status, or None if not connected.
        """
        if not self._check_connection():
            return None
        
        try:
            status = self.client.status()
            print("--- Player Status ---")
            for key, value in status.items():
                print(f"{key.capitalize()}: {value}")
            return status
        except MPDCommandError as e:
            print(f"Command Error: {e}")
            return None
        
    def play(self):
        """
        Starts playback of the current playlist.
        """
        if not self._check_connection():
            return
        
        try:
            self.client.play()
            print("Playback started.")
        except MPDCommandError as e:
            print(f"Command Error: {e}")

    def pause(self):
        """
        Pauses or unpauses playback.
        """
        if not self._check_connection():
            return

        try:
            self.client.pause()
            print("Playback paused/unpaused.")
        except MPDCommandError as e:
            print(f"Command Error: {e}")

    def stop(self):
        """
        Stops playback.
        """
        if not self._check_connection():
            return
        
        try:
            self.client.stop()
            print("Playback stopped.")
        except MPDCommandError as e:
            print(f"Command Error: {e}")

    def next(self):
        """
        Skips to the next song in the playlist.
        """
        if not self._check_connection():
            return

        try:
            self.client.next()
            print("Skipped to the next song.")
        except MPDCommandError as e:
            print(f"Command Error: {e}")
    
    def prev(self):
        """
        Goes back to the previous song in the playlist.
        """
        if not self._check_connection():
            return

        try:
            self.client.previous()
            print("Skipped to the previous song.")
        except MPDCommandError as e:
            print(f"Command Error: {e}")

    def setvolume(self, volume):
        """
        Sets the volume of the MPD player.

        Args:
            volume (int): The volume level, from 0 to 100.
        """
        if not self._check_connection():
            return

        try:
            volume = int(volume)
            if 0 <= volume <= 100:
                self.client.setvol(volume)
                print(f"Volume set to {volume}.")
            else:
                print("Error: Volume must be an integer between 0 and 100.")
        except (ValueError, MPDCommandError) as e:
            print(f"Error setting volume: {e}")
    def update(self):
        """
        Updates the MPD server's music database. This is necessary for MPD
        to discover new files or changes in the music directory.
        """
        if not self._check_connection():
            return
        
        print("Starting MPD database update...")
        try:
            self.client.update()
            print("MPD database update command sent. The update will run in the background.")
        except MPDCommandError as e:
            print(f"Command Error: {e}")

    def queue_add_song(self, path):
        """
        Adds a song to the current playlist.

        Args:
            path (str): The path to the song (relative to the MPD music directory).
        """
        if not self._check_connection():
            return

        try:
            self.client.add(path)
            print(f"Added '{path}' to the playlist.")
        except MPDCommandError as e:
            print(f"Error adding song: {e}")


    def queue_add_folder(self, music_folder):
        """
        Adds all music files from a specified folder to the MPD playlist.

        Args:
            music_folder (str): The path to the folder containing music files,
                                relative to the MPD server's music_directory.
        """
        if not self._check_connection():
            return

        # We then tell MPD to add the entire folder. This correctly handles
        # symbolic links and recursive folder structures from MPD's perspective.
        try:
            self.client.add(music_folder)
            print(f"Added all files from '{music_folder}' to the playlist.")
        except MPDCommandError as e:
            # The most likely reason for an error here is that the folder path
            # is not accessible or not in MPD's music_directory.
            print(f"Error adding folder: {e}")
            print(f"Please ensure '{music_folder}' is a directory within MPD's configured music_directory.")
            return
        

    def get_current_song(self):
        """
        Retrieves the details of the currently playing song.

        Returns:
            dict: A dictionary with the song details, or None if no song is playing.
        """
        if not self._check_connection():
            return None
        
        try:
            current_song = self.client.currentsong()
            if current_song:
                print("--- Current Song ---")
                for key, value in current_song.items():
                    print(f"{key.capitalize()}: {value}")
            else:
                print("No song is currently playing.")
            return current_song
        except MPDCommandError as e:
            print(f"Command Error: {e}")
            return None

    def get_playlist(self):
        """
        Retrieves the current playlist.

        Returns:
            list: A list of dictionaries, where each dictionary represents a song.
        """
        if not self._check_connection():
            return []
        
        try:
            playlist = self.client.playlistinfo()
            print("--- Current Playlist ---")
            for i, song in enumerate(playlist):
                print(f"{i+1}. {song.get('artist', 'Unknown')} - {song.get('title', song.get('file', 'Unknown'))}")
            return playlist
        except MPDCommandError as e:
            print(f"Command Error: {e}")
            return []

    def get_playlistid(self):
        """
        Retrieves the current playlist.

        Returns:
            list: A list of dictionaries, where each dictionary represents a song.
        """
        if not self._check_connection():
            return []
        
        try:
            playlistid = self.client.playlistid()
            print("--- Current Playlist ---")
            for i, song in enumerate(playlistid):
                print(f"{i+1}. {song.get('artist', 'Unknown')} - {song.get('title', song.get('file', 'Unknown'))}")
            return playlistid
        except MPDCommandError as e:
            print(f"Command Error: {e}")
            return []
#TTT
    def get_playlists_list(self):
        """
        Retrieves the current playlists_list.

        Returns:
            list: A list of dictionaries, where each dictionary represents a playlist.
        """
        if not self._check_connection():
            print("Mpd not connected")
            return []
        
        try:
            playlists_List = self.client.listplaylists()
            print("--- Current playlists_List ---")
            return playlists_List
        except MPDCommandError as e:
            print(f"Command Error: {e}")
            return []

    def queue_clear(self):
        """
        Clears the current playlist on the MPD server.
        """
        if not self._check_connection():
            return
        
        print("Clearing the current playlist...")
        try:
            self.client.clear()
            print("Playlist has been cleared.")
        except MPDCommandError as e:
            print(f"Command Error: {e}")

    # --- ADD THE NEW METHOD HERE ---
    def queue_load_radiostreams(self, streams_dict):
        """
        Clears the current playlist and loads a dictionary of radio streams.

        Args:
            streams_dict (dict): A dictionary where keys are stream names
                                 and values are the stream URLs.
        """
        if not self._check_connection():
            return
        
        print("Clearing the current playlist and loading radio streams...")
        try:
            # 1. Clear the existing queue
            self.client.clear()
            
            # 2. Iterate through the dictionary's values (the URLs) and add them
            for url in streams_dict.values():
                self.client.add(url)
            
            print(f"Successfully loaded {len(streams_dict)} radio streams to the playlist.")
        except MPDCommandError as e:
            print(f"Command Error while loading radio streams: {e}")

    def queue_saveto_playlist(self, pi_plname):
        """
        Saves the current playlist on the MPD server.

        Args:
            playlist_name (str): The name to save the playlist as.
        """
        if not self._check_connection():
            return
        
        print(f"Saving current playlist as '{pi_plname}'...")
        try:
            self.client.save(pi_plname)
            print(f"Playlist saved as '{pi_plname}'")
        except MPDCommandError as e:
            print(f"Command Error: {e}")

    def queue_loadfrom_playlist(self, pi_plname):
        """
        Load pi_plname to Queue.

        Args:
            pi_plname (str): The name of the playlist to load to Queue.
        """
        if not self._check_connection():
            return
        
        try:
            # Corrected line: Pass the string directly
            self.client.load(pi_plname)
            print(f"Playlist '{pi_plname}' loading")      
        except MPDCommandError as e:
            print(f"Command Error: {e}")

