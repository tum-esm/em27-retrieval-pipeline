import ftplib
import io
import os
import sys
import tum_esm_utils
import click

_PROJECT_DIR = tum_esm_utils.files.get_parent_dir_path(__file__)
_RETRIEVAL_ENTRYPOINT = os.path.join(
    _PROJECT_DIR,
    "src",
    "entrypoints",
    "run_retrieval.py",
)

cli = click.Group(name="cli")
retrieval_command_group = click.Group(name="retrieval")
profiles_command_group = click.Group(name="profiles")
export_command_group = click.Group(name="export")


@retrieval_command_group.command(
    name="start",
    help=
    "Start the retrieval as a background process. Prevents spawning multiple processes. The logs and the current processing queue from this process can be found at `logs/retrieval`.",
)
def start():
    pid = tum_esm_utils.processes.start_background_process(
        sys.executable, _RETRIEVAL_ENTRYPOINT
    )
    click.echo(f"Started automated retrieval background process with PID {pid}")


@retrieval_command_group.command(
    name="is-running",
    help=
    "Checks whether the retrieval background process is running. The logs and the current processing queue from this process can be found at `logs/retrieval`.",
)
def is_running():
    pids = tum_esm_utils.processes.get_process_pids(_RETRIEVAL_ENTRYPOINT)
    if len(pids) > 0:
        click.echo(f"automated retrieval is running with PID(s) {pids}")
    else:
        click.echo("automated retrieval is not running")


@retrieval_command_group.command(
    name="watch",
    help="Opens an active watch window for the retrieval background process.",
)
def watch():
    pids = tum_esm_utils.processes.get_process_pids(_RETRIEVAL_ENTRYPOINT)
    if len(pids) == 0:
        click.echo("automated retrieval is not running")
    else:
        import src
        src.retrieval.utils.queue_watcher.start_retrieval_watcher()


@retrieval_command_group.command(
    name="stop",
    help=
    "Stop the retrieval background process. The logs and the current processing queue from this process can be found at `logs/retrieval`.",
)
def stop():
    pids = tum_esm_utils.processes.terminate_process(_RETRIEVAL_ENTRYPOINT)
    if len(pids) == 0:
        click.echo("No active process to be terminated")
    else:
        click.echo(
            f"Terminated {len(pids)} automated retrieval " +
            f"background processe(s) with PID(s) {pids}"
        )


@profiles_command_group.command(
    name="run",
    help=
    "Run the profiles download script. This will check, which profiles are not yet present locally, request and download them from the `ccycle.gps.caltech.edu` FTP server. The logs from this process can be found at `logs/profiles`.",
)
def run_profiles_download() -> None:
    from src.entrypoints.download_profiles import run
    run()


@profiles_command_group.command(
    name="request-ginput-status",
    help=
    "Request ginput status. This will upload a file `upload/ginput_status.txt` to the `ccycle.gps.caltech.edu` FTP server containing the configured email address. You will receive an email with the ginput status which normally takes less than two minutes.",
)
def request_ginput_status():
    from src import utils
    config = utils.config.Config.load()
    assert config.profiles is not None, "No profiles config found"
    with ftplib.FTP(
        host="ccycle.gps.caltech.edu",
        passwd=config.profiles.ftp_server.email,
        user="anonymous",
        timeout=60,
    ) as ftp:
        with io.BytesIO(config.profiles.ftp_server.email.encode("utf-8")) as f:
            ftp.storbinary(f"STOR upload/ginput_status.txt", f)
    click.echo(
        f"Requested ginput status for email address {config.profiles.ftp_server.email}"
    )


@export_command_group.command(
    name="run",
    help=
    "Run the export script. The logs from this process can be found at `logs/export`.",
)
def run_export():
    from src.entrypoints.export_outputs import run
    run()


cli.add_command(retrieval_command_group)
cli.add_command(profiles_command_group)
cli.add_command(export_command_group)

if __name__ == "__main__":
    cli()
