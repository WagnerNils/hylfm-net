from hylfm import __version__, metrics, settings  # noqa: first line to set numpy env vars

import logging
from pathlib import Path
from typing import Optional

from hylfm.checkpoint import Checkpoint, TestRunConfig
from hylfm.datasets.named import DatasetChoice
from hylfm.run.eval_run import TestRun

try:
    from typing import Literal
except ImportError:
    from typing_extensions import Literal

import typer

logger = logging.getLogger(__name__)


app = typer.Typer()


@app.command(name="test")
def tst(
    checkpoint: Path,
    batch_size: Optional[int] = typer.Option(None, "--batch_size"),
    data_range: Optional[float] = typer.Option(None, "--data_range"),
    dataset: Optional[DatasetChoice] = None,
    heavy_logging: bool = typer.Option(False, "--heavy_logging"),
    interpolation_order: Optional[int] = typer.Option(None, "--interpolation_order"),
    light_logging: bool = typer.Option(False, "--light_logging"),
    ui_name: Optional[str] = typer.Option(None, "--ui_name"),
    win_sigma: Optional[float] = typer.Option(None, "--win_sigma"),
    win_size: Optional[int] = typer.Option(None, "--win_size"),
    point_cloud_threshold: float = typer.Option(1.0, "--point_cloud_threshold"),
):
    checkpoint = Checkpoint.load(checkpoint)
    if ui_name is None:
        if checkpoint.training_run_name is None:
            raise ValueError("couldn't find name from checkpoint, don't you want to specify a ui_name?")

        ui_name = checkpoint.training_run_name
    elif checkpoint.training_run_name is not None:
        logger.warning(
            "ui_name %s overwrites training_run_name %s from checkpoint", ui_name, checkpoint.training_run_name
        )

    save_output_to_disk = {}
    if not light_logging or heavy_logging:
        save_output_to_disk["pred"] = settings.log_dir / ui_name / "test" / "output_tensors" / "pred"

    if heavy_logging:
        for key in ("spim", "lf"):
            save_output_to_disk[key] = settings.log_dir / ui_name / "test" / "output_tensors" / key

    config = TestRunConfig(
        batch_size=batch_size or checkpoint.config.eval_batch_size,
        checkpoint=checkpoint,
        data_range=data_range or checkpoint.config.data_range,
        dataset=dataset or checkpoint.config.dataset,
        interpolation_order=interpolation_order or checkpoint.config.interpolation_order,
        win_sigma=win_sigma or checkpoint.config.win_sigma,
        win_size=win_size or checkpoint.config.win_size,
        save_output_to_disk=save_output_to_disk,
        hylfm_version=__version__,
        point_cloud_threshold=point_cloud_threshold,
    )

    import wandb

    wandb_run = wandb.init(project=f"HyLFM-test", dir=str(settings.cache_dir), config=config.as_dict(), name=ui_name)

    test_run = TestRun(config=config, wandb_run=wandb_run, log_pred_vs_spim=not light_logging)

    test_run.run()


if __name__ == "__main__":
    app()
