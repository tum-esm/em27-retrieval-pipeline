from src import main

if __name__ == "__main__":
    # TODO: Only run main function if this script is not already running
    # This can be done by looking for "python .../automated-proffast
    # -pylot/run.py" inside the stdout from calling "ps -af"
    main.run()
