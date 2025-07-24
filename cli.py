import ftplib
import io
import os
import sys
import tqdm
import click
import em27_metadata
import pydantic
import tum_esm_utils

_RETRIEVAL_ENTRYPOINT = tum_esm_utils.files.rel_to_abs_path("src", "retrieval", "main.py")

cli = click.Group(name="cli")
retrieval_command_group = click.Group(name="retrieval")
profiles_command_group = click.Group(name="profiles")
bundle_command_group = click.Group(name="bundle")
geoms_command_group = click.Group(name="geoms")


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
            loc = click.style(".".join([str(_l) for _l in error["loc"]]) + ":", bold=True)
            click.echo(f"  - {loc} {error['msg']}")
        exit(1)


@retrieval_command_group.command(
    name="start",
    short_help="Start Retrieval Process",
    help="Start the retrieval as a background process. Prevents spawning multiple processes. The logs and the current processing queue from this process can be found at `logs/retrieval`.",
)
def start() -> None:
    _check_config_validity()
    pid = tum_esm_utils.processes.start_background_process(
        sys.executable, _RETRIEVAL_ENTRYPOINT, waiting_period=0.125
    )
    click.echo(f"Started automated retrieval background process with PID {pid}")


@retrieval_command_group.command(
    name="is-running",
    short_help="Check If Retrieval Is Running",
    help="Checks whether the retrieval background process is running. The logs and the current processing queue from this process can be found at `logs/retrieval`.",
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
    short_help="Watch Retrieval Process",
    help="Opens an active watch window for the retrieval background process.",
)
@click.option(
    "--cluster-mode",
    is_flag=True,
    help=(
        "Watch the retrieval process when the retrieval is running on a cluster. "
        + "In this mode the watcher does not care whether it find an active "
        + "retrieval process on the current node, but only looks at the queue. "
        + "This means it can not detect when the pipeline has stopped (e.g. due "
        + "to a SLURM timeout)."
    ),
)
def watch(
    cluster_mode: bool,
) -> None:
    # no config check because this does not require a config

    if not cluster_mode:
        pids = tum_esm_utils.processes.get_process_pids(_RETRIEVAL_ENTRYPOINT)
        if len(pids) == 0:
            click.echo("automated retrieval is not running")
            return

    import src

    src.retrieval.utils.queue_watcher.start_retrieval_watcher(cluster_mode)


@retrieval_command_group.command(
    name="stop",
    short_help="Stop Retrieval Process",
    help="Stop the retrieval background process. The logs and the current processing queue from this process can be found at `logs/retrieval`.",
)
def stop() -> None:
    # no config check so that the process can always be terminated

    pids = tum_esm_utils.processes.terminate_process(_RETRIEVAL_ENTRYPOINT)
    if len(pids) == 0:
        click.echo("No active process to be terminated")
    else:
        click.echo(
            f"Terminated {len(pids)} automated retrieval "
            + f"background processe(s) with PID(s) {pids}"
        )


@retrieval_command_group.command(
    name="download-algorithms",
    short_help="Download Retrieval Algorithms",
    help="Downloads all retrieval algorithms into the local container factories. Can be used if you don't want to run the pipeline but download all algorithms.",
)
def download_algorithms() -> None:
    import src

    src.retrieval.dispatching.container_factory.ContainerFactory.init_proffast10_code(click.echo)
    src.retrieval.dispatching.container_factory.ContainerFactory.init_proffast22_code(click.echo)
    src.retrieval.dispatching.container_factory.ContainerFactory.init_proffast23_code(click.echo)
    src.retrieval.dispatching.container_factory.ContainerFactory.init_proffast24_code(click.echo)


@profiles_command_group.command(
    name="run",
    short_help="Run Atmospheric Profiles Download",
    help="Run the profiles download script. This will check, which profiles are not yet present locally, request and download them from the `ccycle.gps.caltech.edu` FTP server. The logs from this process can be found at `logs/profiles`.",
)
def run_profiles_download() -> None:
    _check_config_validity()

    import src  # import here so that the CLI is more reactive

    src.profiles.main.run()


@profiles_command_group.command(
    name="request-ginput-status",
    short_help="Request Ginput Status",
    help="Request ginput status. This will upload a file `upload/ginput_status.txt` to the `ccycle.gps.caltech.edu` FTP server containing the configured email address. You will receive an email with the ginput status which normally takes less than two minutes.",
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
            ftp.storbinary("STOR upload/ginput_status.txt", f)
    click.echo(f"Requested ginput status for email address {config.profiles.server.email}")


@profiles_command_group.command(
    name="migrate-storage-location",
    short_help="Migrate Atmospheric Profiles Storage Location",
    help="Migrate the storage location of the atmospheric profiles to the new directory structure introduced in the pipeline version 1.7.0. See https://github.com/tum-esm/em27-retrieval-pipeline/issues/127 for more details.",
)
def migrate_storage_location() -> None:
    _check_config_validity()

    import src  # import here so that the CLI is more reactive

    config = src.types.Config.load()
    profiles_dir = config.general.data.atmospheric_profiles.root
    click.echo(f"Migrating atmospheric profiles from {profiles_dir} to {profiles_dir}/YYYY/MM")

    for model in ["GGG2014", "GGG2020"]:
        model_dir = f"{profiles_dir}/{model}"
        filenames = sorted(
            [
                f
                for f in os.listdir(model_dir)
                if (
                    os.path.isfile(os.path.join(model_dir, f))
                    and (len(f) >= 8)
                    and (f.endswith(".map") or f.endswith(".mod") or f.endswith(".vmr"))
                    and f[:8].isdigit()
                )
            ]
        )
        progress = tqdm.tqdm(filenames, dynamic_ncols=True)
        for f in progress:
            progress.set_description(f"Moving {f}")
            dst_path = os.path.join(model_dir, f[:4], f[4:6])
            if not os.path.isdir(dst_path):
                progress.write(f"Creating subdirectory {dst_path}")
                os.makedirs(dst_path, exist_ok=True)
            os.rename(os.path.join(model_dir, f), os.path.join(dst_path, f))


@bundle_command_group.command(
    name="run",
    short_help="Create Retrieval Dataset Bundle",
    help="Create a bundle of your entire retrieval dataset",
)
def run_bundle() -> None:
    _check_config_validity()

    import src  # import here so that the CLI is more reactive

    src.bundle.main.run()


@geoms_command_group.command(
    name="run",
    short_help="Create GEOMS Files",
    help="Create GEOMS files for your entire retrieval dataset",
)
def run_geoms() -> None:
    _check_config_validity()

    import src  # import here so that the CLI is more reactive

    src.geoms.main.run()


@cli.command(
    name="data-report",
    short_help="Export Data Report",
    help="exports a report of the data present on the configured system",
)
def print_data_report() -> None:
    _check_config_validity()

    import rich.console

    import src  # import here so that the CLI is more reactive

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
        "Printing report for the data paths: " + config.general.data.model_dump_json(indent=4)
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
cli.add_command(geoms_command_group)

if __name__ == "__main__":
    cli()
