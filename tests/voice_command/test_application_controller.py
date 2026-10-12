from modules.voice_command.application_controller import (
    ApplicationController
)


def main():
    controller = ApplicationController()

    print("\n====================================")
    print(" MAX APPLICATION CONTROLLER TEST")
    print("====================================\n")

    print("Supported applications:")

    for app in controller.get_supported_applications():
        print(" -", app)

    print("\nTest complete.")


if __name__ == "__main__":
    main()