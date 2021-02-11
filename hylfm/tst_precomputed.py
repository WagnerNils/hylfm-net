from hylfm import metrics, settings  # noqa: first line to set numpy env vars

import logging
from typing import Optional

from hylfm.checkpoint import RunConfig
from hylfm.datasets.named import DatasetChoice
from hylfm.run.eval_run import TestPrecomputedRun

try:
    from typing import Literal
except ImportError:
    from typing_extensions import Literal

import typer

logger = logging.getLogger(__name__)


app = typer.Typer()


@app.command(name="test_precomputed")
def tst_precomputed(
    batch_size: int = typer.Option(1, "--batch_size"),
    data_range: float = typer.Option(1, "--data_range"),
    dataset: Optional[DatasetChoice] = None,
    interpolation_order: int = typer.Option(2, "--interpolation_order"),
    pred: str = "lfd",
    scale: int = 4,
    shrink: int = 0,
    ui_name: str = typer.Option(..., "--ui_name"),
    win_sigma: float = typer.Option(1.5, "--win_sigma"),
    win_size: int = typer.Option(11, "--win_size"),
):

    config = RunConfig(
        batch_size=batch_size,
        data_range=data_range,
        dataset=dataset,
        interpolation_order=interpolation_order,
        win_sigma=win_sigma,
        win_size=win_size,
        save_output_to_disk={},
    )

    import wandb

    wandb_run = wandb.init(
        project=f"HyLFM-test", dir=str(settings.cache_dir), config=config.as_dict(for_logging=True), name=ui_name
    )

    test_run = TestPrecomputedRun(
        config=config, wandb_run=wandb_run, pred_name=pred, log_pred_vs_spim=True, scale=scale, shrink=shrink
    )

    test_run.run()


if __name__ == "__main__":
    app()
