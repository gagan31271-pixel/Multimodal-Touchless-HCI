
import sys
from pathlib import Path

# Add the project root to Python's import path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from modules.security.face_authentication import FaceAuthentication


def main():
    auth = FaceAuthentication()

    print("\n=== FACE AUTHENTICATION TEST ===")
    print("1. Register face")
    print("2. Verify face")
    print("3. Check registration status")

    choice = input("Choose (1-3): ").strip()

    if choice == "1":
        username = input("Enter username: ").strip() or "authorized_user"
        result = auth.register_face(username)
        print(result["message"])

    elif choice == "2":
        result = auth.verify_face()
        print(result["message"])

        if result["distance"] is not None:
            print(f"Face distance: {result['distance']:.4f}")

        print("Authenticated:", result["authenticated"])

    elif choice == "3":
        print("Registered:", auth.is_registered())

    else:
        print("Invalid choice.")


if __name__ == "__main__":
    main()
