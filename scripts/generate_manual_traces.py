import argparse
import logging
import shutil
import warnings
from collections import OrderedDict
from dataclasses import dataclass
from datetime import datetime
from itertools import chain
from pathlib import Path
from typing import Dict, Optional, Tuple
from ruamel.yaml import YAML

import matplotlib.pyplot as plt
import numpy

from hylfm.datasets.base import TensorInfo, TiffDataset
from hylfm.utils.cache import cached_to_disk
from hylfm.utils.tracer import trace_and_plot

yaml = YAML(typ="safe")

logger = logging.getLogger(__name__)


def get_data_to_trace(name: str, root: Path, tmin=0, tmax=None, roi: Tuple[slice] = (slice(None), slice(None))):

    ds = TiffDataset(info=TensorInfo(name=name, root=root, location=f"{name}/*.tif"))
    if tmax is None:
        tmax = len(ds)

    return numpy.stack([ds[t][name].squeeze()[roi] for t in range(tmin, tmax)])


@dataclass
class AutoTraceKwargs:
    n_radii: int = 1


class Tracker:
    def __init__(
        self,
        name: str,
        root: Path,
        save_traces_to: Path,
        tmin: int = 0,
        tmax: Optional[int] = None,
        radius: int = 2,
        auto_trace_kwargs: Optional[AutoTraceKwargs] = None,
        plot_with: Dict[str, Path] = None,
        reduce_peak_area: str = "mean",
        roi: Tuple[slice] = (slice(25, 225), slice(55, 305)),
    ):
        logger.warning("save traces to %s", save_traces_to)
        self.save_traces_to = save_traces_to

        plt.rcParams["keymap.save"].remove("s")  # use wasd for trace movement, save still available with `ctrl+s`
        if plot_with is None:
            plot_with = {}

        plot_config = [
            {k: {"smooth": [(None, None)], "path": v} for k, v in plot_with.items()},
            {k: {"smooth": [(("flat", 11), ("flat", 11))], "path": v} for k, v in plot_with.items()},
            {
                k: {
                    "smooth": [
                        (
                            ("savgol_filter", {"window_length": 11, "polyorder": 3}),
                            ("savgol_filter", {"window_length": 11, "polyorder": 3}),
                        )
                    ],
                    "path": v,
                }
                for k, v in plot_with.items()
            },
        ]
        self.plot_trace_kwargs = {
            "tgt_path": root,
            "tgt": name,
            "output_path": save_traces_to / f"plots_{datetime.now():%Y-%m-%d_%H-%M}",
            "nr_traces": 1,
            "trace_radius": radius,
            "time_range": (tmin, tmax),
            "plots": plot_config,
            "roi": roi,
            "reduce_peak_area": reduce_peak_area,
        }

        self.videos = OrderedDict([(name, get_data_to_trace(name, root=root, tmin=tmin, tmax=tmax, roi=roi))])
        self._video_idx = 0
        self._video = self.videos[name]
        for pred, path in plot_with.items():
            self.videos[pred] = get_data_to_trace(pred, root=path, tmin=tmin, tmax=tmax, roi=roi)

        self.T = self.video.shape[0]
        self._t = -1
        self._active_trace = -1
        self.radius = radius
        self.tmin = tmin
        self.tmax = tmax
        self.auto_trace_kwargs = auto_trace_kwargs

        self.traces = []
        self.all_trace_markers = []
        self.trace_views = []
        self.fig, self.ax = plt.subplots()
        self.im = self.ax.imshow(self.video[self.t])
        self.ax.autoscale(False)

        if save_traces_to.exists():
            for saved_trace in chain.from_iterable(
                [save_traces_to.glob(f"manual_trace_{'[0-9]'*digits}.yml") for digits in range(1, 4)]
            ):
                self.add_trace(saved_trace)
        else:
            save_traces_to.mkdir(parents=True)
            self.add_trace()

        cid = self.fig.canvas.mpl_connect("button_press_event", self.on_click)
        self.fig.canvas.mpl_connect("key_press_event", self.on_key)
        self.fig.canvas.mpl_connect("scroll_event", self.on_scroll)
        self.ax.callbacks.connect("xlim_changed", self.get_on_axlims_changed("x"))
        self.ax.callbacks.connect("ylim_changed", self.get_on_axlims_changed("y"))
        self.active_trace = 0
        plt.show()
        print(self.traces)
        self.save_traces()

    def save_traces(self):
        for i, trace in enumerate(self.traces):
            yaml.dump([[y, x, self.radius] for y, x in trace.tolist()], self.save_traces_to / f"manual_trace_{i}.yml")

        for i in range(len(self.traces)):
            yaml.dump(self.trace_views[i], self.save_traces_to / f"manual_trace_{i}.view.yml")

    @property
    def video_idx(self):
        return self._video_idx

    @video_idx.setter
    def video_idx(self, new_idx):
        new_idx = max(0, min(len(self.videos) - 1, new_idx))
        if new_idx != self._video_idx:
            self._video_idx = new_idx
            self.video = list(self.videos.values())[new_idx]

    @property
    def video(self):
        return self._video

    @video.setter
    def video(self, new_video):
        self._video = new_video
        self.t = self.t

    @property
    def t(self):
        return self._t

    @t.setter
    def t(self, new_t):
        xlim = tuple(self.trace_views[self.active_trace]["x"])
        ylim = tuple(self.trace_views[self.active_trace]["y"])
        new_t = max(0, min(self.T - 1, new_t))
        self.im.set_data(self.video[new_t])
        for i, (y, x) in enumerate([trace[new_t] for trace in self.traces]):
            # if self.all_trace_markers[i] is not None:
            #     self.all_trace_markers[i].set_visible(False)

            if i == self.active_trace:
                if y == -1:
                    y, x = self.get_trace_suggestion(new_t)
                    if y == -1:
                        continue

                    color = "orange"
                else:
                    color = "green"
            else:
                if y == -1:
                    continue
                else:
                    color = "grey"

            if self.all_trace_markers[i] is None:
                self.all_trace_markers[i] = plt.Circle((x, y), self.radius, color=color, linewidth=2, fill=False)
                self.ax.add_patch(self.all_trace_markers[i])
            else:
                self.all_trace_markers[i].set_color(color)
                self.all_trace_markers[i].set_center((x, y))
                # self.all_trace_markers[i].set_visible(True)
                # self.ax.text(x + 2 * int(self.radius + 0.5), y, str(i))

        self._t = new_t
        self.ax.set_title(
            f"video: {list(self.videos.keys())[self.video_idx]} ({self.video_idx + 1}/{len(self.videos)}) time: {new_t + 1}/{self.video.shape[0]}, trace: {self.active_trace + 1}/{len(self.traces)}"
        )
        self.fig.tight_layout()
        current_xlim = self.ax.get_xlim()
        current_ylim = self.ax.get_ylim()
        if xlim != current_xlim:
            self.ax.set_xlim(*xlim)

        if ylim != current_ylim:
            self.ax.set_ylim(*ylim)

        self.fig.canvas.draw_idle()

    @property
    def active_trace(self):
        return self._active_trace

    @active_trace.setter
    def active_trace(self, new_active_trace):
        new_active_trace = max(0, min(len(self.traces) - 1, new_active_trace))
        if new_active_trace != self._active_trace:
            self._active_trace = new_active_trace
            self.t = self.t
            self.save_traces()

    def on_click(self, event):
        mode = self.fig.canvas.manager.toolbar.mode
        if mode:
            # print("ignoring click in mode", mode)
            return

        # print(
        #     f"{'double' if `event.`dblclick else 'single'} click: button={event.button}, x={event.x}, y={event.y}, xdata={event.xdata}, ydata={event.ydata}"
        # )
        if not event.dblclick and event.button == 1 or event.button == 3:
            if event.ydata is not None and event.xdata is not None:  # can happen during closing?!
                self.traces[self.active_trace][self.t] = [round(event.ydata), round(event.xdata)]
                self.t += 1 if event.button == 1 else -1

    def on_scroll(self, event):
        mode = self.fig.canvas.manager.toolbar.mode
        if mode:
            # print("ignoring scroll in mode", mode)
            return

        self.t += int(event.step)

    def on_key(self, event):
        """
        hotkeys:
        - arrow up/down: move in time
        - space bar: move forward in time
        - page up/down: move in time by 10% of total time
        - ctrl + arrow key up/down: switch active trace
        - wasd: move active trace position
        - c: get information about missing annotations and move to annotation edge
        - n: add a new trace
        - t: plot active trace
        """
        if event.key == "right":
            pass
            # self.t += 1 # does not go well with 'redo' action
        elif event.key == "left":
            pass
            # self.t -= 1  # does not go well with 'undo' action
        elif event.key in ["up", "down"]:
            trace_marker = self.all_trace_markers[self.active_trace]
            if trace_marker is not None:
                x, y = trace_marker.get_center()
                self.traces[self.active_trace][self.t][:] = [y, x]

            dt = 1 if event.key == "up" else -1
            self.t += dt
        elif event.key == "ctrl+up":
            self.active_trace += 1
        elif event.key == "ctrl+down":
            self.active_trace -= 1
        elif event.key in ["shift+up", "shift+down"]:
            self.video_idx += 1 if event.key == "shift+up" else -1
        elif event.key in "wasd":
            trace_marker: Optional[plt.Circle] = self.all_trace_markers[self.active_trace]
            if trace_marker is not None:
                dydx = {"w": (0, -1), "s": (0, 1), "a": (-1, 0), "d": (1, 0)}[event.key]
                new_center = tuple([c + d for c, d in zip(trace_marker.get_center(), dydx)])
                trace_marker.set_center(new_center)
                self.fig.canvas.draw_idle()
            else:
                print("no trace marker")
        elif event.key == "c":
            nr_missing, start_at_t = self.get_missing(self.traces[self.active_trace])
            if nr_missing:
                print(f"{nr_missing} coordinates missing in active trace")
                self.t = start_at_t
            else:
                for i, trace in enumerate(self.traces):
                    nr_missing, start_at_t = self.get_missing(trace)
                    if nr_missing:
                        print(f"{nr_missing} coordinates missing in trace {i + 1}")
                        self.active_trace = i
                        self.t = start_at_t
                        break
                else:
                    print("all traces fully annotated")
        elif event.key == "n":
            missing = numpy.where(self.traces[self.active_trace][:, 0] == -1)[0].tolist()
            if missing:
                print(f"{len(missing)} coordinates missing in trace {len(self.traces) + 1}")

            self.add_trace()
        elif event.key == " ":
            trace_marker = self.all_trace_markers[self.active_trace]
            if trace_marker is not None:
                x, y = trace_marker.get_center()
                self.traces[self.active_trace][self.t][:] = [y, x]
                self.t += 1
            else:
                print("no trace marker")
        elif event.key == "pageup":
            self.t += self.T // 10
        elif event.key == "pagedown":
            self.t -= self.T // 10
        elif event.key == "t":
            self.save_traces()
            _, _, _, figs, _ = trace_and_plot(
                **self.plot_trace_kwargs,
                tag=f"trace {self.active_trace + 1}",
                compensated_peak_path=self.save_traces_to / f"manual_trace_{self.active_trace}.yml",
            )
        elif event.key == "j":
            for t in range(self.t, self.T):
                trace_marker = self.all_trace_markers[self.active_trace]
                if trace_marker is not None:
                    x, y = trace_marker.get_center()
                    self.traces[self.active_trace][self.t][:] = [y, x]

                self.t += 1

        elif event.key == "ctrl+alt+d":
            self.traces.pop(self.active_trace)
            self.all_trace_markers.pop(self.active_trace)
            self.active_trace = 0
            self.t = self.t

    def get_on_axlims_changed(self, a: str):
        assert a == "x" or a == "y"

        def on_axlims_changed(ax):
            lims = getattr(ax, f"get_{a}lim")()
            self.trace_views[self.active_trace][a] = [float(lim) for lim in lims]
            print(f"{a}lims changed", lims)

        return on_axlims_changed

    def get_missing(self, trace):
        missing = trace[:, 0] == -1
        nr_missing = missing.sum()
        for i in numpy.where(missing)[0]:
            if i < len(missing) - 1 and not missing[i + 1]:
                start_at_t = i + 1
                break
            elif i > 1 and not missing[i - 1]:
                start_at_t = i - 1
                break
        else:
            start_at_t = 0

        return nr_missing, start_at_t

    def add_trace(self, from_path: Optional[Path] = None):
        default_trace_view = {"y": (None, None), "x": (None, None)}
        if from_path:
            trace = numpy.array(yaml.load(from_path))
            try:
                trace_view = yaml.load(from_path.with_suffix(".view.yml"))
                trace_view = None  # todo: implement
            except FileNotFoundError:
                trace_view = default_trace_view
            else:
                if trace_view is None:
                    trace_view = default_trace_view

            assert trace.shape == (self.T, 3), trace.shape
            if any([r != self.radius for r in trace[:, 2]]):
                trace[:, 2] = self.radius
                warnings.warn("loaded trace had different radius!")

            trace = trace[:, :2]
            nr_missing, start_at_t = self.get_missing(trace)
            if nr_missing:
                print(f"{nr_missing} coordinates missing in trace {len(self.traces) + 1}")
        else:
            trace = numpy.full((self.T, 2), -1, dtype=numpy.int)
            start_at_t = 0
            trace_view = default_trace_view

        assert trace.shape == (self.T, 2)
        self.traces.append(trace)
        self.all_trace_markers.append(None)
        self.trace_views.append(trace_view)
        self.active_trace = len(self.traces) - 1
        self.t = start_at_t

    def get_trace_suggestion(self, t):
        neighbor_t = t - 1
        y = -1
        x = -1

        if t != 0:
            y, x = self.traces[self.active_trace][neighbor_t]

        if y == -1:
            neighbor_t = t + 1
            if neighbor_t < self.traces[self.active_trace].shape[0]:
                y, x = self.traces[self.active_trace][neighbor_t]

        if self.auto_trace_kwargs is None or y == -1:
            return y, x

        r = self.auto_trace_kwargs.n_radii * self.radius
        last_frame = numpy.pad(self.video[t - 1], pad_width=r, mode="edge")[y : y + 2 * r + 1, x : x + 2 * r + 1]
        frame = numpy.pad(self.video[t], pad_width=2 * r, mode="edge")[y : y + 4 * r + 1, x : x + 4 * r + 1]

        dydx_candidates = [(dy, dx) for dy in range(-r, r + 1) for dx in range(-r, r + 1)]
        roi_candidates = [tuple([slice(2 * r + d, 2 * r + d + 1) for d in dydx]) for dydx in dydx_candidates]
        frame_candidates = numpy.stack([frame[roi] for roi in roi_candidates])

        frame_mse = ((frame_candidates - last_frame[None, ...]) ** 2).sum(axis=(1, 2))
        dy, dx = dydx_candidates[numpy.argmin(frame_mse).item()]
        return y + dy, x + dx


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="lnet generate manual traces")
    parser.add_argument("--tag", type=str, default="11_2__2020-03-11_07.30.39__SinglePlane_-310")
    # parser.add_argument("--ls_slice_path", type=Path, default=None)
    parser.add_argument("--plot_with_pred", type=str, default="pred_only_11_2_a")
    parser.add_argument("--plot_with_pred_path", type=Path, default=None)
    parser.add_argument("--tmin", type=int, default=0)
    parser.add_argument("--tmax", type=int, default=None)

    args = parser.parse_args()

    tag = args.tag
    # tag = "09_3__2020-03-09_06.43.40__SinglePlane_-330"
    # tag = "11_2__2020-03-11_07.30.39__SinglePlane_-310"
    # tag = "11_2__2020-03-11_10.17.34__SinglePlane_-280"
    tmin = args.tmin
    tmax = args.tmax
    plot_with_pred = args.plot_with_pred

    pred_path = args.plot_with_pred_path
    if pred_path is None and args.plot_with_pred:
        pred_path = {"pred_only_11_2_a": Path(f"C:/Users/fbeut/Desktop/lnet_stuff/manual_traces/{tag}")}[
            args.plot_with_pred
        ]

    name = "ls_slice"
    save_traces_to = Path(
        f"C:/Users/fbeut/Desktop/lnet_stuff/manual_traces/{tag}/manual_on_{name}_tmin{tmin}_tmax{tmax}"
    )
    if str(save_traces_to).endswith("debug") and save_traces_to.exists():
        shutil.rmtree(save_traces_to)

    Tracker(
        name=name,
        root=Path(f"C:/Users/fbeut/Desktop/lnet_stuff/manual_traces/{tag}"),
        save_traces_to=save_traces_to,
        # auto_trace_kwargs=AutoTraceKwargs(),
        radius=3,
        tmin=tmin,
        tmax=tmax,
        plot_with=None if pred_path is None else {args.plot_with_pred: pred_path},
        reduce_peak_area="max",
    )
