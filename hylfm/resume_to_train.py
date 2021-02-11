import collections
from pathlib import Path
from typing import Optional

import typer

from hylfm import settings
from hylfm.checkpoint import Checkpoint
from hylfm.hylfm_types import DatasetChoice
from hylfm.train import train_from_checkpoint

app = typer.Typer()


@app.command()
def resume(
    checkpoint: Path,
    dataset: Optional[DatasetChoice] = None,
    impatience: Optional[int] = typer.Option(None, "--impatience"),
    best_validation_score: Optional[float] = typer.Option(None, "--best_validation_score"),
):
    checkpoint = Checkpoint.load(checkpoint)

    # checkpoints are made at the end of an epoch e.g. ep: 0, it: 99; reset epoch and iteration to start the next epoch
    checkpoint.epoch += 1
    checkpoint.iteration = 0

    changes = collections.OrderedDict()
    if dataset is not None:
        checkpoint.config.dataset = dataset
        changes["dataset"] = dataset.value
        if impatience is None:
            impatience = 0

    if best_validation_score is not None:
        checkpoint.best_validation_score = best_validation_score
        changes["best_validation_score"] = best_validation_score

    if impatience is not None:
        checkpoint.impatience = impatience
        changes["impatience"] = impatience

    if changes:
        notes = "resumed with changes: " + " ".join([f"{k}: {v}" for k, v in changes.items()])
    else:
        notes = "resumed without changes"

    import wandb

    config = checkpoint.config.as_dict(for_logging=True)
    config["resumed_from"] = checkpoint.training_run_name

    wandb_run = wandb.init(
        project="HyLFM-train", dir=str(settings.cache_dir), config=config, resume="allow", notes=notes
    )
    checkpoint.training_run_name = wandb_run.name
    checkpoint.training_run_id = wandb_run.id

    train_from_checkpoint(wandb_run, checkpoint)


if __name__ == "__main__":
    app()
