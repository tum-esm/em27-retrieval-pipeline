import datetime
import time
from typing import Any
import rich.live, rich.table, rich.panel, rich.console, rich.align, rich.spinner, rich.columns, rich.box
from .process_status import ProcessStatusList


def _render() -> Any:
    processes = ProcessStatusList.load()

    if len(processes) == 0:
        return rich.panel.Panel("[white]No processes found.[/white]", height=3)

    pending_process_count = len([
        x for x in processes if x.process_start_time is None
    ])
    done_process_count = len([
        x for x in processes if x.process_end_time is not None
    ])
    in_progress_process_count = len(
        processes
    ) - pending_process_count - done_process_count

    table = rich.table.Table(expand=True, box=rich.box.ROUNDED)
    table.add_column("Container ID")
    table.add_column("Sensor ID")
    table.add_column("Date")
    table.add_column("Location ID")
    table.add_column("IFG Count")
    table.add_column("Run Time")

    for p in processes:
        if (p.process_start_time is None) or (p.process_end_time is not None):
            continue
        dt = datetime.datetime.utcnow().replace(
            tzinfo=datetime.timezone.utc
        ) - p.process_start_time.replace(tzinfo=datetime.timezone.utc)
        table.add_row(
            p.container_id,
            p.sensor_id,
            str(p.date),
            p.location_id,
            "N/A" if p.ifg_count is None else str(p.ifg_count),
            f"{dt.seconds // 60}m {str(dt.seconds % 60).zfill(2)}s",
        )

    grid = rich.table.Table.grid(expand=True)
    grid.add_row(
        rich.align.Align.center(
            rich.columns.Columns([
                f"[white]{pending_process_count} processes pending[/white]",
                rich.spinner.Spinner('simpleDots', style="white"),
                f"[yellow]{in_progress_process_count} processes in progress[/yellow]",
                rich.spinner.Spinner('simpleDots', style="yellow"),
                f"[green]{done_process_count} processes done[/green]",
            ], )
        )
    )
    grid.add_row(table)
    grid.add_row(
        rich.align.Align.center(
            "[white]Press Ctrl+C or close the terminal to stop watching. This "
            + "will [underline]not[/underline] stop the automation[/white]"
        )
    )

    return grid


def start_retrieval_watcher() -> None:
    console = rich.console.Console()
    console.clear()
    with rich.live.Live(refresh_per_second=4) as live:
        live
        try:
            while True:
                live.update(_render())
                time.sleep(2)
        except KeyboardInterrupt:
            live.update(
                "[white]Stopped watching, automation is still running.[/white]"
            )
