from modules.multimodal.screen_service import ScreenService


def main():

    print("=" * 60)
    print("COMMON SCREEN SERVICE TEST")
    print("=" * 60)

    service = ScreenService()

    try:

        print()
        print("1. Read full screen")
        print("2. Select screen region")
        print("0. Exit")

        choice = input(
            "Select: "
        ).strip()

        if choice == "1":

            service.read_screen()

        elif choice == "2":

            service.open_context_menu()

        elif choice == "0":

            return

        else:

            print(
                "Invalid option."
            )

    finally:

        service.close()

        print(
            "[SCREEN] Service stopped."
        )


if __name__ == "__main__":
    main()