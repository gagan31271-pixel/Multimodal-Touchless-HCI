from modules.voice_command.max import MAX


def main() -> None:

    print(
        "\n================================="
    )
    print(
        "        MAX / PROTON TEST"
    )
    print(
        "================================="
    )
    print(
        "Say commands beginning with:"
    )
    print(
        "    MAX"
    )
    print(
        "\nExamples:"
    )
    print(
        "    Max hello"
    )
    print(
        "    Max what is your name"
    )
    print(
        "    Max what is the time"
    )
    print(
        "    Max open notepad"
    )
    print(
        "    Max search Python programming"
    )
    print(
        "    Max copy"
    )
    print(
        "    Max paste"
    )
    print(
        "    Max launch gesture recognition"
    )
    print(
        "    Max stop gesture recognition"
    )
    print(
        "    Max exit"
    )
    print(
        "=================================\n"
    )

    assistant = MAX()

    assistant.run()


if __name__ == "__main__":
    main()