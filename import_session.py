"""
Import Instagram session from Firefox browser cookies
"""

import sqlite3
import shutil
import tempfile
import os
from pathlib import Path

import instaloader


def get_firefox_profile_path():
    """Get the default Firefox profile path on Windows."""
    appdata = os.environ.get('APPDATA')
    firefox_dir = Path(appdata) / "Mozilla" / "Firefox" / "Profiles"

    if not firefox_dir.exists():
        print(f"Firefox Profiles directory not found: {firefox_dir}")
        return None

    # Find any profile that has cookies.sqlite (the active profile)
    profiles_with_cookies = []
    for profile_dir in firefox_dir.iterdir():
        if profile_dir.is_dir():
            cookies_file = profile_dir / "cookies.sqlite"
            if cookies_file.exists():
                profiles_with_cookies.append(profile_dir)

    if not profiles_with_cookies:
        print("No Firefox profile with cookies found")
        return None

    # Prefer 'default-release' profile if available
    for profile in profiles_with_cookies:
        if 'default-release' in profile.name:
            return profile

    # Otherwise return the first one found
    return profiles_with_cookies[0]


def get_firefox_cookies():
    """Extract Instagram cookies from Firefox."""
    profile_path = get_firefox_profile_path()
    if not profile_path:
        print("Firefox profile not found!")
        return None

    cookies_path = profile_path / "cookies.sqlite"
    if not cookies_path.exists():
        print(f"Cookies file not found at: {cookies_path}")
        return None

    print(f"Found Firefox profile: {profile_path.name}")
    print(f"Cookies file: {cookies_path}")

    # Copy cookies file to temp location (Firefox may have it locked)
    temp_dir = tempfile.mkdtemp()
    temp_cookies = Path(temp_dir) / "cookies.sqlite"
    shutil.copy2(cookies_path, temp_cookies)

    conn = sqlite3.connect(temp_cookies)
    cursor = conn.cursor()

    # Get Instagram cookies (Firefox stores them unencrypted!)
    cursor.execute("""
        SELECT name, value, host
        FROM moz_cookies
        WHERE host LIKE '%instagram.com'
    """)

    cookies = {}
    for name, value, host in cursor.fetchall():
        if value:
            cookies[name] = value

    conn.close()

    # Cleanup
    try:
        os.remove(temp_cookies)
        os.rmdir(temp_dir)
    except:
        pass

    return cookies


def create_instaloader_session(username, cookies):
    """Create and save an instaloader session from cookies."""
    loader = instaloader.Instaloader()

    # The essential cookies for Instagram
    essential_cookies = ['sessionid', 'csrftoken', 'ds_user_id', 'mid', 'ig_did']

    print("\nCookies found:")
    for name in essential_cookies:
        if name in cookies:
            print(f"  + {name}")
        else:
            print(f"  - {name} (missing)")

    if 'sessionid' not in cookies:
        print("\nERROR: sessionid cookie not found!")
        print("Make sure you're logged into Instagram in Firefox.")
        return False

    # Set cookies in the session
    for name, value in cookies.items():
        loader.context._session.cookies.set(name, value, domain='.instagram.com')

    # Test the session
    try:
        test_user = loader.test_login()
        if test_user:
            print(f"\n+ Session valid! Logged in as: {test_user}")
            # Save using the actual logged-in username
            try:
                loader.save_session_to_file(test_user)
                print(f"+ Session saved for: {test_user}")
            except Exception as e:
                print(f"- Could not save session file: {e}")
                print("  (This is OK - session is still valid in memory)")
            return True
        else:
            print("\n- Session invalid - cookies may be expired")
            return False
    except Exception as e:
        print(f"\n- Error testing session: {e}")
        return False


def main():
    print("=" * 50)
    print("  Import Instagram Session from Firefox")
    print("=" * 50)
    print("\nPre-requisites:")
    print("  1. Firefox installed")
    print("  2. Logged into Instagram in Firefox")
    print("  3. Firefox closed")
    print("")
    input("Press Enter when ready...")

    username = input("\nEnter your Instagram username: ").strip()
    if not username:
        print("No username provided!")
        return

    print("\nExtracting cookies from Firefox...")
    cookies = get_firefox_cookies()

    if not cookies:
        print("No cookies found!")
        return

    print(f"Found {len(cookies)} Instagram cookies")

    create_instaloader_session(username, cookies)


if __name__ == "__main__":
    main()
