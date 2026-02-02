"""
Instagram Image Downloader
Télécharge les dernières images d'un compte Instagram
"""

import instaloader
import re
import os
from pathlib import Path


def extract_username(input_str: str) -> str:
    """Extrait le nom d'utilisateur d'un lien Instagram ou retourne l'input directement."""
    # Pattern pour les URLs Instagram
    patterns = [
        r"instagram\.com/([^/?]+)",
        r"^@?([a-zA-Z0-9._]+)$"
    ]

    for pattern in patterns:
        match = re.search(pattern, input_str.strip())
        if match:
            return match.group(1)

    return input_str.strip()


def download_images(username: str, max_images: int = 100, output_dir: str = "downloads"):
    """
    Télécharge les dernières images d'un compte Instagram.

    Args:
        username: Nom d'utilisateur ou lien Instagram
        max_images: Nombre maximum d'images à télécharger (défaut: 100)
        output_dir: Dossier de destination
    """
    username = extract_username(username)

    # Créer le dossier de sortie
    output_path = Path(output_dir) / username
    output_path.mkdir(parents=True, exist_ok=True)

    # Configurer instaloader
    loader = instaloader.Instaloader(
        dirname_pattern=str(output_path),
        filename_pattern="{date_utc}__{shortcode}",
        download_videos=False,
        download_video_thumbnails=False,
        download_geotags=False,
        download_comments=False,
        save_metadata=False,
        post_metadata_txt_pattern=""
    )

    # Charger la session si elle existe (demander le nom d'utilisateur Instagram)
    insta_user = os.environ.get("INSTA_USER")
    if insta_user:
        try:
            loader.load_session_from_file(insta_user)
            print(f"Session Instagram chargée pour: {insta_user}")
        except Exception as e:
            print(f"Impossible de charger la session: {e}")

    print(f"Récupération du profil: {username}")

    try:
        profile = instaloader.Profile.from_username(loader.context, username)
    except instaloader.exceptions.ProfileNotExistsException:
        print(f"Erreur: Le profil '{username}' n'existe pas.")
        return
    except instaloader.exceptions.ConnectionException as e:
        print(f"Erreur de connexion: {e}")
        return

    print(f"Profil trouvé: {profile.full_name}")
    print(f"Posts totaux: {profile.mediacount}")
    print(f"Téléchargement des {max_images} dernières images vers: {output_path}")
    print("-" * 50)

    downloaded_posts = 0
    skipped = 0
    total_files = 0

    for post in profile.get_posts():
        if downloaded_posts >= max_images:
            break

        # Ne télécharger que les images (pas les vidéos)
        if post.is_video:
            continue

        try:
            # Compter les fichiers avant le téléchargement
            files_before = len(list(output_path.glob("*.jpg")))

            loader.download_post(post, target=str(output_path))

            # Compter les fichiers après le téléchargement
            files_after = len(list(output_path.glob("*.jpg")))
            new_files = files_after - files_before
            total_files += new_files

            downloaded_posts += 1
            print(f"[{downloaded_posts}/{max_images}] Téléchargé: {post.shortcode} ({new_files} image{'s' if new_files > 1 else ''})")
        except Exception as e:
            skipped += 1
            print(f"Erreur lors du téléchargement de {post.shortcode}: {e}")

    print("-" * 50)
    print(f"Terminé! {downloaded_posts} posts traités, {total_files} images téléchargées, {skipped} ignorés.")
    print(f"Emplacement: {output_path.absolute()}")


def main():
    print("=" * 50)
    print("   Instagram Image Downloader")
    print("=" * 50)

    # Demander le lien ou nom d'utilisateur
    user_input = input("\nEntrez le lien Instagram ou le nom d'utilisateur: ").strip()

    if not user_input:
        print("Erreur: Aucun input fourni.")
        return

    # Demander le nombre d'images
    try:
        max_images = input("Nombre d'images à télécharger (défaut: 100): ").strip()
        max_images = int(max_images) if max_images else 100
    except ValueError:
        max_images = 100

    download_images(user_input, max_images)


if __name__ == "__main__":
    main()
