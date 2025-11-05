import datetime
from typing import Any, Optional

import rich.align
import rich.box
import rich.columns
import rich.console
import rich.live
import rich.panel
import rich.table
import rich.spinner
import tum_esm_utils

from .retrieval_status import RetrievalStatusList

_RETRIEVAL_ENTRYPOINT = tum_esm_utils.files.rel_to_abs_path("../main.py")


def _prettify_timedelta(dt: datetime.timedelta) -> str:
    out: str = ""
    total_seconds = dt.total_seconds()

    days = int(total_seconds // (3600 * 24))
    total_seconds = total_seconds % (3600 * 24)
    hours = int(total_seconds // 3600)
    total_seconds = total_seconds % 3600
    minutes = int(total_seconds // 60)

    if days > 0:
        out += f"{days}d "
    if days > 0 or hours > 0:
        out += f"{hours}h "
    if minutes > 0 or hours > 0 or days > 0:
        out += f"{minutes}m "

    return out.strip()


def _render(cluster_mode: bool) -> Any:
    processes = RetrievalStatusList.load()
    pending_process_count = len([x for x in processes if x.process_start_time is None])
    done_process_count = len([x for x in processes if x.process_end_time is not None])
    in_progress_process_count = len(processes) - pending_process_count - done_process_count

    if cluster_mode:
        message: Optional[str] = None
        if len(processes) == 0:
            message = "[white]No Processes In the Queue[/white]"
        elif len(processes) == done_process_count:
            message = "[green]All Processes Done[/green]"
        if message is not None:
            grid = rich.table.Table.grid(expand=True)
            grid.add_row(rich.panel.Panel(rich.align.Align.center(message), height=3))
            grid.add_row(
                rich.align.Align.center(
                    "[white]Watching the queue only. Does not detect whether the pipeline is running or not.[/white]"
                )
            )
            return grid
    else:
        if len(processes) == done_process_count:
            pipeline_pids = tum_esm_utils.processes.get_process_pids(_RETRIEVAL_ENTRYPOINT)
            if len(pipeline_pids) == 0:
                return rich.panel.Panel("[white]Pipeline is not running[/white]", height=3)
            else:
                if len(processes) == 0:
                    return rich.panel.Panel(
                        "[white]Pipeline is spinning up - wait a bit[/white]", height=3
                    )
                else:
                    return rich.panel.Panel(
                        "[white]Pipeline is shutting down - wait a bit[/white]", height=3
                    )

    table = rich.table.Table(expand=True, box=rich.box.ROUNDED)
    table.add_column("Container ID")
    table.add_column("Job Suffix")
    table.add_column("Sensor ID")
    table.add_column("Datetime")
    table.add_column("Location ID")
    table.add_column("IFG Count")
    table.add_column("Run Time")

    first_start_time: Optional[datetime.datetime] = None
    last_end_time: Optional[datetime.datetime] = None

    for p in processes:
        # process not started
        if p.process_start_time is None:
            continue

        if (first_start_time is None) or (p.process_start_time < first_start_time):
            first_start_time = p.process_start_time

        # process is running
        if p.process_end_time is None:
            dt = datetime.datetime.now(tz=datetime.timezone.utc) - p.process_start_time.replace(
                tzinfo=datetime.timezone.utc
            )
            table.add_row(
                p.container_id,
                "-" if p.output_suffix is None else p.output_suffix,
                p.sensor_id,
                f"{p.from_datetime} - {p.to_datetime}",
                p.location_id,
                "N/A" if p.ifg_count is None else str(p.ifg_count),
                f"{dt.seconds // 60}m {str(dt.seconds % 60).zfill(2)}s",
            )
            continue

        # process is done
        if (last_end_time is None) or (p.process_end_time > last_end_time):
            last_end_time = p.process_end_time

    grid = rich.table.Table.grid(expand=True)
    grid.add_row(
        rich.align.Align.center(
            rich.columns.Columns(
                [
                    f"[white]{pending_process_count} processes pending[/white]",
                    rich.spinner.Spinner("simpleDots", style="white"),
                    f"[yellow]{in_progress_process_count} processes in progress[/yellow]",
                    rich.spinner.Spinner("simpleDots", style="yellow"),
                    f"[green]{done_process_count} processes done[/green]",
                ],
            )
        )
    )
    grid.add_row(table)
    if (first_start_time is not None) and (last_end_time is not None) and (done_process_count > 0):
        avg_time_per_job = (
            last_end_time.replace(tzinfo=datetime.timezone.utc)
            - first_start_time.replace(tzinfo=datetime.timezone.utc)
        ) / done_process_count
        estimated_end_time = (avg_time_per_job * len(processes)) + first_start_time
        estimated_remaining_time = estimated_end_time - datetime.datetime.now(datetime.timezone.utc)
        grid.add_row(
            rich.align.Align.center(
                rich.columns.Columns(
                    [
                        "[yellow]Pipeline is estimated to finish in "
                        + f"{_prettify_timedelta(estimated_remaining_time)} "
                        + f"({estimated_end_time.strftime('%Y-%m-%d %H:%M UTC')})[/yellow]\n",
                    ]
                ),
            )
        )

    grid.add_row(
        rich.align.Align.center(
            "[white]Press Ctrl+C or close the terminal to stop watching. This "
            + "will [underline]not[/underline] stop the automation[/white]"
        )
    )

    if cluster_mode:
        grid.add_row(
            rich.align.Align.center(
                "[white]Watching the queue only. Does not detect whether the pipeline is running or not.[/white]"
            )
        )

    return grid


def start_retrieval_watcher(cluster_mode: bool = False) -> None:
    console = rich.console.Console()
    console.clear()
    with rich.live.Live(refresh_per_second=1) as live:
        try:
            while True:
                with tum_esm_utils.timing.ensure_section_duration(1):
                    live.update(_render(cluster_mode))
        except KeyboardInterrupt:
            console.clear()
            live.update("[white]Stopped watching.[/white]")
