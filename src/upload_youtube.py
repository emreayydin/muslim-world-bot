"""Uploads a video to YouTube using the YouTube Data API v3."""
import os
import json
from pathlib import Path
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload


SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
TOKEN_FILE = "youtube_token.json"
CREDENTIALS_FILE = "client_secrets.json"


def get_youtube_service():
    """Authenticates and returns a YouTube API service object."""
    creds = None

    # In GitHub Actions, use the token JSON from a secret
    token_json = os.environ.get("YOUTUBE_TOKEN_JSON")
    if token_json:
        token_data = json.loads(token_json)
        creds = Credentials(
            token=token_data.get("token"),
            refresh_token=token_data.get("refresh_token"),
            token_uri="https://oauth2.googleapis.com/token",
            client_id=token_data.get("client_id"),
            client_secret=token_data.get("client_secret"),
            scopes=SCOPES,
        )

    # Local development: use token file
    elif Path(TOKEN_FILE).exists():
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    # Refresh if expired
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        if Path(TOKEN_FILE).exists():
            with open(TOKEN_FILE, "w") as f:
                f.write(creds.to_json())

    # First-time local auth flow
    if not creds or not creds.valid:
        if not Path(CREDENTIALS_FILE).exists():
            raise FileNotFoundError(
                f"'{CREDENTIALS_FILE}' not found. "
                "Download your OAuth2 credentials from the Google Cloud Console."
            )
        flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
        creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, "w") as f:
            f.write(creds.to_json())
        print(f"Token saved: {TOKEN_FILE}")
        print("\nAdd this JSON as the GitHub secret 'YOUTUBE_TOKEN_JSON':")
        print(creds.to_json())

    return build("youtube", "v3", credentials=creds)


def upload_short(
    video_path: str,
    title: str,
    description: str,
    tags: list[str],
    category_id: str = "27",  # 27 = Education
    privacy: str = "public",
    is_short: bool = True,
) -> str:
    """
    Uploads a video. With is_short=True the description carries #Shorts so YouTube
    classifies it as a Short; with is_short=False it uploads as a normal video.
    Returns the video ID.
    """
    youtube = get_youtube_service()

    base_tags = "#islam #muslim #quran #islamicreminder #deen #allah"
    if is_short:
        full_description = f"{description}\n\n#Shorts {base_tags}"
    else:
        full_description = f"{description}\n\n{base_tags} #islamicknowledge #seerah"
    if tags:
        full_description += "\n" + " ".join(f"#{t.replace(' ', '')}" for t in tags[:5])

    body = {
        "snippet": {
            "title": title,
            "description": full_description,
            "tags": tags + (["Shorts"] if is_short else []) + ["Islam", "Muslim", "Quran", "Islamic reminder"],
            "categoryId": category_id,
            "defaultLanguage": "en",
            "defaultAudioLanguage": "en",
        },
        "status": {
            "privacyStatus": privacy,
            "selfDeclaredMadeForKids": False,
        },
    }

    media = MediaFileUpload(video_path, mimetype="video/mp4", resumable=True)
    request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"Upload: {int(status.progress() * 100)}%")

    video_id = response["id"]
    print(f"Video uploaded: https://youtube.com/watch?v={video_id}")
    return video_id


def set_thumbnail(video_id: str, thumbnail_path: str) -> bool:
    """Sets a custom thumbnail. Needs a verified channel; fails gracefully."""
    try:
        youtube = get_youtube_service()
        youtube.thumbnails().set(
            videoId=video_id,
            media_body=MediaFileUpload(thumbnail_path, mimetype="image/png"),
        ).execute()
        print(f"Thumbnail set for {video_id}")
        return True
    except Exception as e:
        print(f"Could not set thumbnail ({e}). Video keeps its auto-thumbnail.")
        return False


if __name__ == "__main__":
    print("Starting YouTube authentication...")
    get_youtube_service()
    print("Authentication successful!")
