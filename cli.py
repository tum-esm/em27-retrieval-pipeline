import ftplib
import io
import sys
import pydantic
import tum_esm_utils
import click
import em27_metadata

_RETRIEVAL_ENTRYPOINT = tum_esm_utils.files.rel_to_abs_path("src", "retrieval", "main.py")

cli = click.Group(name="cli")
retrieval_command_group = click.Group(name="retrieval")
profiles_command_group = click.Group(name="profiles")
bundle_command_group = click.Group(name="bundle")


def _check_config_validity() -> None:
    import src
    try:
        src.types.Config.load()
        click.echo(click.style("Config is valid", fg="green", bold=True))
    except pydantic.ValidationError as e:
        click.echo(
            click.style(f"Detected {e.error_count()} error(s) in the config:", bold=True, fg="red")
        )
        for error in e.errors():
            loc = click.style('.'.join([str(l) for l in error['loc']]) + ":", bold=True)
            click.echo(f"  - {loc} {error['msg']}")
        exit(1)


@retrieval_command_group.command(
    name="start",
    help=
    "Start the retrieval as a background process. Prevents spawning multiple processes. The logs and the current processing queue from this process can be found at `logs/retrieval`.",
)
def start() -> None:
    _check_config_validity()
    pid = tum_esm_utils.processes.start_background_process(
        sys.executable, _RETRIEVAL_ENTRYPOINT, waiting_period=0.125
    )
    click.echo(f"Started automated retrieval background process with PID {pid}")


@retrieval_command_group.command(
    name="is-running",
    help=
    "Checks whether the retrieval background process is running. The logs and the current processing queue from this process can be found at `logs/retrieval`.",
)
def is_running() -> None:
    # no config check because this does not require a config

    pids = tum_esm_utils.processes.get_process_pids(_RETRIEVAL_ENTRYPOINT)
    if len(pids) > 0:
        click.echo(f"automated retrieval is running with PID(s) {pids}")
    else:
        click.echo("automated retrieval is not running")


@retrieval_command_group.command(
    name="watch",
    help="Opens an active watch window for the retrieval background process.",
)
def watch() -> None:
    # no config check because this does not require a config

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
def stop() -> None:
    # no config check so that the process can always be terminated

    pids = tum_esm_utils.processes.terminate_process(_RETRIEVAL_ENTRYPOINT)
    if len(pids) == 0:
        click.echo("No active process to be terminated")
    else:
        click.echo(
            f"Terminated {len(pids)} automated retrieval " +
            f"background processe(s) with PID(s) {pids}"
        )


@retrieval_command_group.command(
    name="download-algorithms",
    help="Downloads all retrieval algorithms into the local container factories",
)
def download_algorithms() -> None:
    import src
    src.retrieval.dispatching.container_factory.ContainerFactory.init_proffast10_code(click.echo)
    src.retrieval.dispatching.container_factory.ContainerFactory.init_proffast22_code(click.echo)
    src.retrieval.dispatching.container_factory.ContainerFactory.init_proffast23_code(click.echo)
    src.retrieval.dispatching.container_factory.ContainerFactory.init_proffast24_code(click.echo)


@profiles_command_group.command(
    name="run",
    help=
    "Run the profiles download script. This will check, which profiles are not yet present locally, request and download them from the `ccycle.gps.caltech.edu` FTP server. The logs from this process can be found at `logs/profiles`.",
)
def run_profiles_download() -> None:
    _check_config_validity()

    import src  # import here so that the CLI is more reactive
    src.profiles.main.run()


@profiles_command_group.command(
    name="request-ginput-status",
    help=
    "Request ginput status. This will upload a file `upload/ginput_status.txt` to the `ccycle.gps.caltech.edu` FTP server containing the configured email address. You will receive an email with the ginput status which normally takes less than two minutes.",
)
def request_ginput_status() -> None:
    _check_config_validity()

    import src  # import here so that the CLI is more reactive
    config = src.types.Config.load()
    assert config.profiles is not None, "No profiles config found"
    with ftplib.FTP(
        host="ccycle.gps.caltech.edu",
        passwd=config.profiles.server.email,
        user="anonymous",
        timeout=60,
    ) as ftp:
        with io.BytesIO(config.profiles.server.email.encode("utf-8")) as f:
            ftp.storbinary(f"STOR upload/ginput_status.txt", f)
    click.echo(f"Requested ginput status for email address {config.profiles.server.email}")


@bundle_command_group.command(name="run", help="Create a bundle of your entire retrieval dataset")
def run_bundle() -> None:
    _check_config_validity()

    import src  # import here so that the CLI is more reactive
    src.bundle.main.run()


@cli.command(
    name="data-report",
    help="exports a report of the data present on the configured system",
)
def print_data_report() -> None:
    _check_config_validity()

    import src  # import here so that the CLI is more reactive
    import rich.console

    console = rich.console.Console()
    console.print("Loading config")
    config = src.types.Config.load()

    # load metadata interface
    console.print("Loading metadata")
    em27_metadata_interface = src.utils.metadata.load_local_em27_metadata_interface()
    if em27_metadata_interface is not None:
        print("Found local metadata")
    else:
        print("Did not find local metadata -> fetching metadata from GitHub")
        assert config.general.metadata is not None, "Remote metadata not configured"
        em27_metadata_interface = em27_metadata.load_from_github(
            github_repository=config.general.metadata.github_repository,
            access_token=config.general.metadata.access_token,
        )
        print("Successfully fetched metadata from GitHub")

    console.print(
        f"Printing report for the data paths: " + config.general.data.model_dump_json(indent=4)
    )
    try:
        src.utils.report.export_data_report(
            config=config,
            em27_metadata_interface=em27_metadata_interface,
            console=console,
        )
    except KeyboardInterrupt:
        console.print("Aborted by user")


cli.add_command(retrieval_command_group)
cli.add_command(profiles_command_group)
cli.add_command(bundle_command_group)

if __name__ == "__main__":
    cli()
