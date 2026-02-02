"""
Instagram Image Downloader using Playwright
Utilise un vrai navigateur Firefox pour contourner les protections anti-bot
"""

import asyncio
import re
import os
import time
import requests
from pathlib import Path
from playwright.async_api import async_playwright


def extract_username(input_str: str) -> str:
    """Extrait le nom d'utilisateur d'un lien Instagram."""
    patterns = [
        r"instagram\.com/([^/?]+)",
        r"^@?([a-zA-Z0-9._]+)$"
    ]
    for pattern in patterns:
        match = re.search(pattern, input_str.strip())
        if match:
            return match.group(1)
    return input_str.strip()


async def download_images(username: str, max_images: int = 100, output_dir: str = "downloads"):
    """Télécharge les images d'un profil Instagram avec Playwright."""

    username = extract_username(username)
    output_path = Path(output_dir) / username
    output_path.mkdir(parents=True, exist_ok=True)

    # Fichier pour sauvegarder la session
    session_file = Path("instagram_session.json")

    print(f"Démarrage du navigateur Firefox...")

    async with async_playwright() as p:
        browser = await p.firefox.launch(headless=False)

        # Charger la session si elle existe
        if session_file.exists():
            print("Chargement de la session sauvegardée...")
            context = await browser.new_context(
                storage_state=str(session_file),
                viewport={'width': 1280, 'height': 800},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:132.0) Gecko/20100101 Firefox/132.0'
            )
        else:
            print("Nouvelle session (première connexion)...")
            context = await browser.new_context(
                viewport={'width': 1280, 'height': 800},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:132.0) Gecko/20100101 Firefox/132.0'
            )

        page = await context.new_page()

        # Aller sur la page du profil
        profile_url = f"https://www.instagram.com/{username}/"
        print(f"Navigation vers: {profile_url}")

        try:
            await page.goto(profile_url, wait_until='domcontentloaded', timeout=30000)
            await asyncio.sleep(3)
        except Exception as e:
            print(f"Première navigation: {e}")

        # Vérifier si on est connecté (chercher le bouton de login)
        login_button = await page.query_selector('text="Log in"')
        if login_button:
            print("\n" + "=" * 50)
            print("Vous n'êtes pas connecté à Instagram!")
            print("Connectez-vous manuellement dans la fenêtre du navigateur,")
            print("puis appuyez sur Entrée ici pour continuer...")
            print("=" * 50)
            input()

            # Sauvegarder la session après connexion
            await context.storage_state(path=str(session_file))
            print(f"✓ Session sauvegardée dans {session_file}")

            # Re-naviguer vers le profil après connexion
            print(f"Navigation vers le profil: {profile_url}")
            await page.goto(profile_url, wait_until='domcontentloaded', timeout=30000)
            await asyncio.sleep(3)

        # Récupérer le nom du profil
        try:
            title = await page.title()
            print(f"Page chargée: {title}")
        except:
            pass

        # Attendre que les images se chargent
        await asyncio.sleep(3)

        # Collecter les URLs des images en scrollant
        print(f"Collecte des images (max: {max_images})...")
        image_urls = set()
        last_count = 0
        no_new_images_count = 0

        while len(image_urls) < max_images and no_new_images_count < 5:
            # Essayer plusieurs sélecteurs pour trouver les images
            selectors = [
                'article img',
                'img[src*="instagram"]',
                'a[href*="/p/"] img',
                'div._aagv img',  # Sélecteur spécifique Instagram
                'img[alt]'
            ]

            all_images = []
            for selector in selectors:
                try:
                    imgs = await page.query_selector_all(selector)
                    all_images.extend(imgs)
                except:
                    pass

            if not all_images:
                print("\nAucune image détectée avec les sélecteurs standards.")
                print("Tentative de détection avec tous les éléments img...")
                all_images = await page.query_selector_all('img')

            print(f"\n  Éléments img trouvés: {len(all_images)}")

            for img in all_images:
                src = await img.get_attribute('src')
                if src and ('instagram' in src or 'fbcdn' in src):
                    # Éviter les photos de profil et icônes
                    if any(skip in src for skip in ['profile_pic', 's150x150', 's50x50', 'icon']):
                        continue

                    # Récupérer l'image en haute qualité si possible
                    srcset = await img.get_attribute('srcset')
                    if srcset:
                        # Prendre la plus grande image du srcset
                        urls = srcset.split(',')
                        for url in urls:
                            parts = url.strip().split(' ')
                            if parts and len(parts[0]) > 50:  # URL valide
                                image_urls.add(parts[0])
                    elif src and len(src) > 50:
                        image_urls.add(src)

            # Vérifier si on a trouvé de nouvelles images
            if len(image_urls) == last_count:
                no_new_images_count += 1
            else:
                no_new_images_count = 0
                last_count = len(image_urls)

            print(f"  Images uniques trouvées: {len(image_urls)}", end='\r')

            # Scroller vers le bas
            await page.evaluate('window.scrollBy(0, 800)')
            await asyncio.sleep(2)

        print(f"\nTotal images trouvées: {len(image_urls)}")

        # Sauvegarder la session avant de fermer
        if not session_file.exists() or session_file.stat().st_size == 0:
            await context.storage_state(path=str(session_file))
            print(f"✓ Session sauvegardée dans {session_file}")

        await browser.close()

    # Télécharger les images
    if not image_urls:
        print("Aucune image trouvée!")
        return

    print(f"\nTéléchargement des images vers: {output_path}")
    print("-" * 50)

    downloaded = 0
    for i, url in enumerate(list(image_urls)[:max_images]):
        try:
            response = requests.get(url, timeout=30)
            if response.status_code == 200:
                # Générer un nom de fichier unique
                filename = f"{username}_{i+1:04d}.jpg"
                filepath = output_path / filename

                with open(filepath, 'wb') as f:
                    f.write(response.content)

                downloaded += 1
                print(f"[{downloaded}/{min(len(image_urls), max_images)}] {filename}")
        except Exception as e:
            print(f"Erreur: {e}")

        time.sleep(0.5)  # Petit délai entre les téléchargements

    print("-" * 50)
    print(f"Terminé! {downloaded} images téléchargées.")
    print(f"Emplacement: {output_path.absolute()}")


def main():
    print("=" * 50)
    print("   Instagram Image Downloader (Playwright)")
    print("=" * 50)

    user_input = input("\nEntrez le lien Instagram ou le nom d'utilisateur: ").strip()
    if not user_input:
        print("Erreur: Aucun input fourni.")
        return

    try:
        max_images = input("Nombre d'images à télécharger (défaut: 100): ").strip()
        max_images = int(max_images) if max_images else 100
    except ValueError:
        max_images = 100

    asyncio.run(download_images(user_input, max_images))


if __name__ == "__main__":
    main()
