# main.py
# This script creates a FastAPI application to expose API endpoints
# for controlling the Music Player Daemon (MPD).
import os
import json # Added for JSON handling
from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.responses import HTMLResponse
from fastapi.responses import JSONResponse
from typing import Optional, List # Added List
from sqlalchemy.orm import Session
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta
from pathlib import Path
from my_package.mpd_controller import MPDClientController
from my_package.database import get_db, SessionLocal 
from my_package.models import User, UserPlaylist, Bulletin # Added UserPlaylist
# Updated imports to include PlaylistPayload
from my_package.schemas import UserCreate, UserResponse, Token, UserPlaylistCreate, UserPlaylistResponse, PlaylistPayload, PlaylistsListResponse, UserPasswordChange, Settings, BulletinCreate, Bulletin as BulletinSchema
from my_package.auth import get_password_hash, verify_password, create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES, get_current_user
import uvicorn
from contextlib import asynccontextmanager
from my_package.database import Base, engine
import subprocess
import asyncio
# ----------------------------------------------
music_Basefolder = "/home/ubuntu/Music/"
music_Type = [] # Will be populated at startup
#-----------------------------------------------
pi_ALLFILES = [] 
pi_Playlist_List = []  # Only one pi_Playlist_List for Pi_Server
pi_playlist_files = []
pi_IndexMax = 1
pi_Index = 0
pi_Playing = None
pi_Playmode = None
pi_RadioNo = None
pi_Volume = 1
pi_Mute = False
pi_Playrate = 1
pi_Duration = 0
cron_Status =  False
cron_Hour = '00'
cron_Min = '00'
cron_pi_Index = 1
pc_ALLFILES = []
pc_Playlist_List = [] # Each user will have his own pc_Playlist_List
pc_Playlist_files = []
pc_Indexmax = 1

# Initialize the MPD client controller globally
mpd_player = MPDClientController()

MPD_PLAYMODE = ["repeat", "random", "single", "consume"]


# Generate filespath base from music_Basefolder
def genFilelist(subfolder):
    global pc_Indexmax
    global music_Basefolder 
    songs = []; 
    for path, subdirs, files in os.walk(music_Basefolder + subfolder, followlinks=True):
       # for name in files:
        path = path[(len(music_Basefolder)-1):]
        path = path+"/"
        path = path[1:]
        files = [path + file for file in files]
        songs = songs + files; 
    songs = [ f for f in songs if f[-4:] == '.mp3' or f[-4:] =='.MP3' or f[-5:] == '.flac' or f[-5:] == '.FLAC']
    songs.sort()
    return songs

# --- FastAPI App  Setup ---
# --- Application Lifespan Event Handler ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    global music_Type
    global pi_ALLFILES  
    global pc_ALLFILES
    """
    Handles application startup and shutdown events.
    This replaces the deprecated @app.on_event("startup") and @app.on_event("shutdown").
    """
    print("Application startup...")

    # --- START: Dynamically find music types ---
    print(f"Scanning for music types in: {music_Basefolder}")
    base_path = Path(music_Basefolder)
    if base_path.is_dir():
        # Find all subdirectories and use their names for music_Type
        subfolders = [item.name for item in base_path.iterdir() if item.is_dir()]
        music_Type.extend(sorted(subfolders)) # Use extend and sort for consistency
        print(f"✅ Found music types: {music_Type}")
    else:
        print(f"⚠️  Warning: Music base folder not found at '{music_Basefolder}'")
    # --- END: Dynamically find music types ---

    # Create database tables
    Base.metadata.create_all(bind=engine)
    # Connect to the MPD server before the application starts
    mpd_player.connect()

    if not mpd_player.is_connected:
        raise HTTPException(status_code=503, detail="MPD is not connected")
    
    # Update the music database and create a playlist for each music type
    print("Updating MPD database and creating playlists...")
    mpd_player.update()
    
    # Use a loop to handle all found music types
    for folder_name in music_Type:
        print(f"  -> Processing and creating playlist for: '{folder_name}'")
        mpd_player.queue_clear()
        mpd_player.queue_add_folder(folder_name)
        mpd_player.queue_saveto_playlist(folder_name)
    
    # Clear the queue one last time after processing all folders
    mpd_player.queue_clear()
    print("✅ Playlist creation complete.")


    #When fastapi starts,  it generate pc_ALLFILES
    #pc_ALLFILES = genFilelist("") 
    #print(f"--- Found {len(pc_ALLFILES)} songs for PC ALLFILEs.")
    #podcast_BBC= genFilelist("播客/BBC")   
    #print(f"--- Found {len(podcast_BBC)} songs for BBC Podcast.")
    #podcast_Daily= genFilelist("播客/Daily")
    #print(f"--- Found {len(podcast_Daily)} songs for Daily Podcast.")
    ## Update or create the "ALLFILES" playlist for every registered user
    #print("Updating 'ALLFILES' playlist for all users...")
    #db = SessionLocal()
    #try:
    #    # Get all users from the database
    #    users = db.query(User).all()
    #    # Convert the file list to a JSON string for storage
    #    playlist_data_json = json.dumps(pc_ALLFILES)

    #    for user in users:
    #        # Check if an "ALLFILES" playlist already exists for the user
    #        existing_playlist = db.query(UserPlaylist).filter(
    #            UserPlaylist.user_id == user.id,
    #            UserPlaylist.playlist_name == "所有歌曲(自動產生)"
    #        ).first()

    #        if existing_playlist:
    #            # If it exists, overwrite its data
    #            print(f"Overwriting '所有歌曲(自動產生)' for user '{user.username}'.")
    #            existing_playlist.playlist_data = playlist_data_json
    #        else:
    #            # If it does not exist, create a new playlist entry
    #            print(f"Creating 'ALLFILES' for user '{user.username}'.")
    #            new_playlist = UserPlaylist(
    #                user_id=user.id,
    #                playlist_name="所有歌曲(自動產生)",
    #                playlist_data=playlist_data_json
    #            )
    #            db.add(new_playlist)

    #    # Commit the changes (updates and new entries) to the database
    #    db.commit()
    #    print("'ALLFILES' playlist update process completed.")

    #except Exception as e:
    #    print(f"An error occurred while updating 'ALLFILES' playlists: {e}")
    #    db.rollback() # Rollback the transaction in case of an error
    #finally:
    #    # Ensure the database session is closed
    #    db.close()

    try:
        # The `yield` statement indicates that the application is ready to serve requests
        yield
    finally:
        # Disconnect from the MPD server after the application shuts down
        print("Application shutdown...")
        mpd_player.disconnect()
  
# Initialize FastAPI application
# Configure CORS (Cross-Origin Resource Sharing)
# This allows the frontend (running on a different origin) to make requests to the backend.
origins = [
    "http://localhost:3000",  # The default address for a Vite dev server
    "http://127.0.0.1:3000",
    "*"
]
app = FastAPI(lifespan=lifespan,
    title="MPD Player API",
    description="A Player with Music Player Daemon (MPD).",
    version="1.0.0"
)

# Path to your built Nuxt.js application
NUXT_DIST_PATH = Path("../frontend/.output/public")  # Adjust path as needed

# Check if Nuxt build exists
if not NUXT_DIST_PATH.exists():
    raise Exception(f"Nuxt build not found at {NUXT_DIST_PATH}. Run 'npm run build' in your Nuxt project first.")

# Mount static files - ORDER MATTERS!
# 1. Mount your backend static files first with a specific prefix
app.mount("/static", StaticFiles(directory="static"), name="backend_static")  # Your backend static files
# 2. Mount Nuxt assets and the entire public directory
app.mount("/_nuxt", StaticFiles(directory=NUXT_DIST_PATH / "_nuxt"), name="nuxt_assets")
# 3. Mount music files
app.mount("/music", StaticFiles(directory="/home/ubuntu/Music"), name="music_files")
# 4. Mount image files
app.mount("/images", StaticFiles(directory=NUXT_DIST_PATH / "images"), name="nuxt_images")
# 5. Mount the entire Nuxt public directory to serve all static files including _payload.json
app.mount("/app", StaticFiles(directory=NUXT_DIST_PATH, html=True), name="nuxt_app")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Allows specified origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods (GET, POST, etc.)
    allow_headers=["*"],  # Allows all headers
)


# --- API Endpoints ---
# Serve the main index.html file for the root path
@app.get("/favicon.ico")
async def favicon():
    return FileResponse(os.path.join("static", "favicon.ico"))

@app.get("/")
async def root():
    """
    Serve the root route
    """
    index_file = NUXT_DIST_PATH / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    else:
        return HTMLResponse("<h1>Welcome! Nuxt app not found.</h1>")

# Handle _payload.json requests specifically
@app.get("/_payload.json")
async def serve_payload():
    """
    Serve the main _payload.json file
    """
    payload_file = NUXT_DIST_PATH / "_payload.json"
    if payload_file.exists():
        return FileResponse(payload_file, media_type="application/json")
    else:
        # Return empty payload if file doesn't exist
        return JSONResponse({})

# Handle dynamic _payload.json requests with query parameters
@app.get("/{path:path}/_payload.json")
async def serve_dynamic_payload(path: str):
    """
    Serve dynamic _payload.json files for specific routes
    """
    # Try to find the specific payload file
    payload_file = NUXT_DIST_PATH / path / "_payload.json"
    if payload_file.exists():
        return FileResponse(payload_file, media_type="application/json")
    
    # Fallback to main payload
    main_payload = NUXT_DIST_PATH / "_payload.json"
    if main_payload.exists():
        return FileResponse(main_payload, media_type="application/json")
    
    # Return empty payload if no file exists
    return JSONResponse({})

# API routes - make sure all your API routes are defined BEFORE the catch-all route
@app.post('/')
async def index_post():
    global pc_PLAYLIST_ALL
    global pi_PLAYLIST_ALL
    global pi_Index
    global pi_Playing
    global pi_Playmode
    global pi_RadioNo
    global pi_Volume
    global pi_Mute
    global pi_Playrate
    global pi_Duration
    global cron_Status
    global cron_Hour
    global cron_Min
    global cron_pi_Index
    return JSONResponse({
        "pi_Index" : pi_Index,
        "pi_Playing" : pi_Playing,
        "pi_Playmopde" : pi_Playmode,
        "pi_Volume" : pi_Volume,
        "pi_Mute" : pi_Mute,
        "pi_Playrate" : pi_Playrate,
        "pi_Duration" : pi_Duration,
        "pi_cronStatus" : cron_Status,
        "pi_cronTimeHour" : cron_Hour,
        "pi_cronTimeMin" : cron_Min,
        "pi_cronIndexPi" : cron_pi_Index
         })

@app.get("/status")
async def get_pi_status():
    """
    Returns the current status of the MPD player.
    """
    if not mpd_player.is_connected:
        raise HTTPException(status_code=503, detail="MPD is not connected")
    
    status = mpd_player.get_status()
    if status is None:
        raise HTTPException(status_code=500, detail="Failed to retrieve status")
    
    return status

@app.get("/pi_queue_files/")
async def pi_queue_files():
    """
    Get playlist in Queue
    """
    if not mpd_player.is_connected:
        raise HTTPException(status_code=503, detail="MPD is not connected")
    try:
            
        playlist = mpd_player.get_playlist()
        return playlist
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving playplaylist: {e}") 

@app.get("/pi_gen_playlist/{foldername}")
async def pi_gen_playlist(folder_name:str):
    """
    Generate a  playlist and save to  Queue
    """
    if not mpd_player.is_connected:
        raise HTTPException(status_code=503, detail="MPD is not connected")
    try:
            
        playlist = mpd_player.queue_add_folder(folder_name)
        return playlist
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving playplaylist: {e}") 
    
#TTTok
@app.get("/pi_load_playlist_to_queue/{pi_plname}")
async def pi_load_playlist_to_queue(pi_plname:str):
    """
    Find if pi_plname in playlists list, and load to Queue
    """
    if not mpd_player.is_connected:
        raise HTTPException(status_code=503, detail="MPD is not connected")
    try:
            
        mpd_player.queue_loadfrom_playlist(pi_plname)
        return {"message": "Loading '{pi_plname}'."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading playlist: {e}")
    
#TTT
@app.get("/pi_queue_save_to_playlist/{pi_plname}")
async def pi_queue_save_to_playlist(pi_plname:str):
    """
    Save current Queue to mpd playlist
    """
    if not mpd_player.is_connected:
        raise HTTPException(status_code=503, detail="MPD is not connected")
    try:
            
        mpd_player.queue_saveto_playlist(pi_plname)
        return {"message": "Playlist saved."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving playplaylist: {e}")
#    
@app.get("/pi_get_playlists_list")
async def pi_get_playlists_list():
    """
    Get  playlists list.
    """
    try:
        pi_playlists_list = mpd_player.get_playlists_list()
        return pi_playlists_list 
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting playlists list: {e}")    

@app.delete("/pi_delete_playlist_list/{pi_plname}")
async def pi_delete_playlist_list(pi_plname: str):
    """
    Deletes a specific playlist from MPD.
    - pi_plname: The name of the playlist to delete.
    """
    if not mpd_player.is_connected:
        raise HTTPException(status_code=503, detail="MPD is not connected")
    
    try:
        # The underlying python-mpd2 command to remove a playlist is 'rm'
        mpd_player.client.rm(pi_plname)
        return {"message": f"Playlist '{pi_plname}' deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting playlist: {e}")

@app.post("/pi_play")
async def pi_play():
    """
    Starts or resumes music playback.
    """
    if not mpd_player.is_connected:
        raise HTTPException(status_code=503, detail="MPD is not connected")
    
    try:
        mpd_player.play()
        return {"message": "Playback started."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error playing music: {e}")
    
@app.post("/pi_playid/{song_id}")
async def pi_playid(song_id: str):
    """
    Selects a song from the playlist and starts playing it.
    The song_id is the position in the playlist (0-indexed).
    """
    if not mpd_player.is_connected:
        raise HTTPException(status_code=503, detail="MPD is not connected")
    
    try:
        mpd_player.client.playid(song_id)
        return {"message": f"Playing song with id {song_id}."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error selecting and playing song: {e}")

@app.post("/pi_pause")
async def pi_pause():
    """
    Pauses or unpauses music playback.
    """
    if not mpd_player.is_connected:
        raise HTTPException(status_code=503, detail="MPD is not connected")
    
    try:
        mpd_player.pause()
        return {"message": "Playback paused/unpaused."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error pausing music: {e}")

@app.post("/pi_stop")
async def pi_stop():
    """
    Stops music playback.
    """
    if not mpd_player.is_connected:
        raise HTTPException(status_code=503, detail="MPD is not connected")
    
    try:
        mpd_player.stop()
        return {"message": "Playback stopped."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error stopping music: {e}")

@app.post("/pi_next")
async def pi_next():
    """
    Skips to the next song in the playlist.
    """
    if not mpd_player.is_connected:
        raise HTTPException(status_code=503, detail="MPD is not connected")
    
    try:
        mpd_player.next()
        return {"message": "Skipped to the next song."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error skipping to next song: {e}")

@app.post("/pi_prev")
async def pi_prev():
    """
    Goes back to the previous song in the playlist.
    """
    if not mpd_player.is_connected:
        raise HTTPException(status_code=503, detail="MPD is not connected")
    
    try:
        mpd_player.prev()
        return {"message": "Skipped to the previous song."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error skipping to previous song: {e}")

@app.put("/pi_setvol/{volume}")
async def pi_setvol(volume: int):
    """
    Sets the volume of the MPD player.
    """
    if not mpd_player.is_connected:
        raise HTTPException(status_code=503, detail="MPD is not connected")
    
    if not 0 <= volume <= 100:
        raise HTTPException(status_code=400, detail="Volume must be an integer between 0 and 100.")
    
    try:
        mpd_player.setvolume(volume)
        return {"message": f"Volume set to {volume}."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error setting volume: {e}")

@app.put("/pi_playmode")
async def pi_playmode(repeat: Optional[bool] = None, random: Optional[bool] = None, single: Optional[bool] = None):
    """
    Sets the play mode of the MPD player (repeat, shuffle, single).
    """
    if not mpd_player.is_connected:
        raise HTTPException(status_code=503, detail="MPD is not connected")
    
    try:
        if repeat is not None:
            mpd_player.client.repeat(1 if repeat else 0)
        if random is not None:
            mpd_player.client.random(1 if random else 0)
        if single is not None:
            mpd_player.client.single(1 if single else 0)
        
        return {"message": "Play mode updated."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error setting play mode: {e}")

# Pcplayer API 
@app.get("/pc_get_playlist_List", response_model=PlaylistsListResponse)
async def pc_get_playlists_list(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieves a list of all playlist names for the current user.
    """
    # Query the database for playlist names belonging to the current user
    playlist_names_tuples = db.query(UserPlaylist.playlist_name).filter(UserPlaylist.user_id == current_user.id).all()
    
    # The query returns a list of tuples, e.g., [('playlist1',), ('playlist2',)].
    # We need to flatten it into a simple list of strings.
    playlist_names = [name for (name,) in playlist_names_tuples]
    
    return {"names": playlist_names}

@app.get("/pc_get_playlist_files/{pc_plname}")
async def pc_get_playlist_files(
    pc_plname :str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)

):
    """
    Retrieves a specific playlist for the current user.
    """
    user_playlist = db.query(UserPlaylist).filter(
        UserPlaylist.user_id == current_user.id,
        UserPlaylist.playlist_name == pc_plname
    ).first()

    if user_playlist:
        # The data is stored as a JSON string, so we need to parse it back into a list
        return json.loads(user_playlist.playlist_data)
    
    # If no playlist is found, return an empty list
    return []

@app.post("/pc_save_playlists_to_list/{pc_plname}")
async def pc_save_playlist_to_list(
    pc_plname: str, # Captures the playlist name from the URL path
    payload: PlaylistPayload, # Uses the Pydantic model for the request body
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Saves or updates a playlist for the currently authenticated user.
    - pc_plname: The name of the playlist to save.
    - payload: The request body containing the list of songs.
    """
    # Check if a playlist with this name already exists for this user
    user_playlist = db.query(UserPlaylist).filter(
        UserPlaylist.user_id == current_user.id,
        UserPlaylist.playlist_name == pc_plname
    ).first()

    # Convert the list of songs into a JSON string for storage
    playlist_data_json = json.dumps(payload.songs)

    if user_playlist:
        # If it exists, update the playlist data
        user_playlist.playlist_data = playlist_data_json
        db.commit()
        db.refresh(user_playlist)
        return {"message": f"Playlist '{pc_plname}' updated successfully"}
    else:
        # If it does not exist, create a new playlist entry
        new_playlist = UserPlaylist(
            user_id=current_user.id,
            playlist_name=pc_plname,
            playlist_data=playlist_data_json
        )
        db.add(new_playlist)
        db.commit()
        db.refresh(new_playlist)
        return {"message": f"Playlist '{pc_plname}' created successfully"}

@app.delete("/pc_delete_playlist_list/{pc_plname}")
async def pc_delete_playlist_list(
    pc_plname: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Deletes a specific playlist for the current user.
    - pc_plname: The name of the playlist to delete.
    """
    # Query the database for the specific playlist belonging to the current user
    playlist_to_delete = db.query(UserPlaylist).filter(
        UserPlaylist.user_id == current_user.id,
        UserPlaylist.playlist_name == pc_plname
    ).first()

    # If the playlist doesn't exist, raise a 404 Not Found error
    if not playlist_to_delete:
        raise HTTPException(status_code=404, detail=f"Playlist '{pc_plname}' not found")

    # Delete the playlist from the database session
    db.delete(playlist_to_delete)
    # Commit the transaction to make the deletion permanent
    db.commit()

    return {"message": f"Playlist '{pc_plname}' deleted successfully"}


@app.get("/pc_get_allfiles")
async def pc_get_allfiles():
    #global pc_ALLFILES
    #print("/pc_get_allfiles:"+ str(pc_ALLFILES))
    files = [""]
    return files

@app.get("/pc_gen_fileslist/{foldername}")
async def pc_gen_fileslist(
    foldername :str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):  
    folderpath = foldername.replace(" ", "/")
    fileslist = genFilelist(folderpath)
    return fileslist
#------------------------------------------------------------------------------
# User Management
@app.post("/register", response_model=UserResponse)
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    # Define your designated registration code
    # For better security, load this from an environment variable
    DESIGNATED_CODE = "Happy"

    # Check if the provided code matches
    if user.code != DESIGNATED_CODE:
        raise HTTPException(status_code=400, detail="Invalid registration code")
    
    # Capitalize the username before checking and saving
    username_capitalized = user.username.upper()
    
    # Check if the capitalized username is already registered
    db_user = db.query(User).filter(User.username == username_capitalized).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    # Proceed with user creation using the capitalized username
    hashed_password = get_password_hash(user.password)
    default_settings = {
        "show_lyrics": True,
        "show_radio_card": True,
        "sleeping_time": 20,
        "spare_setting1": True,
        "spare_setting2": True
    }
    db_user = User(
        username=username_capitalized,
        hashed_password=hashed_password,
        settings=json.dumps(default_settings)
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    # Create an empty playlist "我的收藏" for the new user
    # The playlist_data is an empty JSON array string.
    new_playlist = UserPlaylist(
        user_id=db_user.id,
        playlist_name="我的收藏",
        playlist_data=json.dumps([])
    )
    db.add(new_playlist)
    db.commit()

    settings_dict = json.loads(db_user.settings) if db_user.settings else None
    return UserResponse(
        id=db_user.id,
        username=db_user.username,
        settings=settings_dict
    )

@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # Capitalize the username to match the stored format
    username_capitalized = form_data.username.upper()
    user = db.query(User).filter(User.username == username_capitalized).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/users/me/", response_model=UserResponse)
async def read_users_me(current_user: User = Depends(get_current_user)):
    settings_dict = json.loads(current_user.settings) if current_user.settings else None
    user_data = UserResponse(
        id=current_user.id,
        username=current_user.username,
        settings=settings_dict
    )
    return user_data

from my_package.schemas import Settings

@app.put("/users/me/settings")
async def update_user_settings(
    settings: Settings,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    current_user.settings = json.dumps(settings.dict())
    db.commit()
    db.refresh(current_user)
    return {"message": "Settings updated successfully"}

@app.put("/users/password")
async def change_password(
    password_data: UserPasswordChange,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Changes the password for the currently authenticated user.
    """
    # Verify the current password
    if not verify_password(password_data.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )
    
    # Validate new password (you can add more validation here)
    if len(password_data.new_password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be at least 6 characters long"
        )
    
    # Hash the new password and update the user
    new_hashed_password = get_password_hash(password_data.new_password)
    current_user.hashed_password = new_hashed_password
    
    # Save the changes to the database
    db.commit()
    db.refresh(current_user)
    
    return {"message": "Password changed successfully"}


from fastapi import UploadFile, File, Form
from PIL import Image
import io

@app.post("/upload_user_picture")
async def upload_user_picture(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """
    Uploads a new profile picture for the current user.
    """
    # Define the path to save the image
    save_path = Path(f"../frontend/public/images/user_picture/{current_user.username}.jpg")
    
    # Ensure the directory exists
    save_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        # Read the image file
        image_data = await file.read()
        
        # Open the image with Pillow
        with Image.open(io.BytesIO(image_data)) as img:
            # Convert to RGB if it has an alpha channel (like PNGs)
            if img.mode in ('RGBA', 'P'):
                img = img.convert('RGB')
            
            # Save the image as JPEG
            img.save(save_path, 'jpeg')

        return {"message": "Picture uploaded successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error uploading picture: {e}")


@app.get("/api/wallpaper-images")
async def get_wallpaper_images():
    """
    Returns a list of wallpaper image filenames.
    """
    #image_dir = Path("../frontend/public/images/home_picture/")
    image_dir = NUXT_DIST_PATH / "images" / "home_picture"   
    if not image_dir.is_dir():
        raise HTTPException(status_code=404, detail="Wallpaper image directory not found")
    
    images = [f"/images/home_picture/{p.name}" for p in image_dir.iterdir() if p.is_file()]
    return images


@app.post("/download_podcast")
async def download_podcast(current_user: User = Depends(get_current_user)):
    """
    Triggers the podcast download script asynchronously.
    """
    try:
        python_executable = os.path.join(os.path.dirname(__file__), ".venv/bin/python")
        script_path = os.path.join(os.path.dirname(__file__), "podcast_download.py")

        # Run the script as a background process
        await asyncio.create_subprocess_exec(python_executable, script_path)
        
        return {"message": "Podcast download started in the background."}
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail=f"Python executable not found at {python_executable}. Please check the path.")
    except Exception as e:
        # Handle other potential errors, such as issues with creating the subprocess
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")


@app.post("/bulletins/")
async def create_bulletin(
    title: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Create a new bulletin post with a file upload.
    """
    # Ensure the target directory exists
    upload_dir = Path("static/tpc")
    upload_dir.mkdir(parents=True, exist_ok=True)

    # Save the uploaded file
    file_path = upload_dir / file.filename
    with open(file_path, "wb") as buffer:
        buffer.write(await file.read())

    # Create a new bulletin record in the database
    db_bulletin = Bulletin(
        title=title,
        filename=file.filename,
        filepath=str(file_path)
    )
    db.add(db_bulletin)
    db.commit()
    db.refresh(db_bulletin)
    return db_bulletin

@app.get("/bulletins/", response_model=List[BulletinSchema])
def read_bulletins(db: Session = Depends(get_db)):
    """
    Retrieve all bulletin posts.
    """
    bulletins = db.query(Bulletin).all()
    return bulletins

@app.get("/bulletins/{filename}")
async def read_bulletin_file(filename: str):
    """
    Serve an uploaded bulletin file.
    """
    file_path = Path("static/tpc") / filename
    if not file_path.is_file():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(file_path)


# IMPORTANT: This catch-all route MUST be the LAST route defined
# It handles all SPA routes that don't match API endpoints or static files
@app.get("/{full_path:path}")
async def catch_all(full_path: str):
    """
    Catch-all route to serve index.html for all SPA routes
    This ensures that client-side routing works properly
    """
    # Skip API routes and static assets
    if full_path.startswith(("api/", "_nuxt/", "music/", "static/", "app/")):
        raise HTTPException(status_code=404, detail="Not found")
    
    # Skip _payload.json requests (they should be handled by specific routes above)
    if full_path.endswith("_payload.json"):
        raise HTTPException(status_code=404, detail="Payload not found")
    
    # Skip files with extensions (likely static files)
    if "." in full_path.split("/")[-1] and not full_path.endswith(".html"):
        raise HTTPException(status_code=404, detail="Not found")
    
    index_file = NUXT_DIST_PATH / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    else:
        raise HTTPException(status_code=404, detail="Frontend not found")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8002)
