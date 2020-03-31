import logging
import os
import threading
import time
import typing
from collections import OrderedDict
from concurrent.futures import Future
from concurrent.futures.thread import ThreadPoolExecutor
from hashlib import sha224 as hash
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple, Type, Union

import numpy
import torch.utils.data
import z5py
from inferno.io.transform import Transform
from scipy.ndimage import zoom
from tifffile import imread

from lnet import settings
from lnet.datasets.utils import get_image_paths, split_off_glob
from lnet.registration import (
    BDVTransform,
    Heart_tightCrop_Transform,
    fast_cropped_6ms_Transform,
    fast_cropped_8ms_Transform,
    staticHeartFOV_Transform,
    wholeFOV_Transform,
)
from lnet.stat import DatasetStat

logger = logging.getLogger(__name__)

GKRESHUK = os.environ.get("GKRESHUK", "/g/kreshuk")
GHUFNAGELLFLenseLeNet_Microscope = os.environ.get(
    "GHUFNAGELLFLenseLeNet_Microscope", "/g/hufnagel/LF/LenseLeNet_Microscope"
)


class PathOfInterest:
    def __init__(self, *points: Tuple[int, int, int, int], sigma: int = 1):
        self.points = points
        self.sigma = sigma


class NamedDatasetInfo:
    x_path: Path
    y_path: Path
    paths: List[Path]
    x_roi: Tuple[slice, slice, slice]
    y_roi: Tuple[slice, slice, slice, slice]
    rois: List[Tuple[slice, ...]]
    # stat: Optional[DatasetStat]
    interesting_paths: Optional[List[PathOfInterest]]

    description: str = ""
    common_path: Path = Path("/")

    def __init__(
        self,
        path: Union[str, Path],
        x_dir: str,
        y_dir: Optional[str] = None,
        description="",
        x_roi: Optional[Tuple[slice, slice]] = None,
        y_roi: Optional[Tuple[slice, slice, slice]] = None,
        # stat: Optional[DatasetStat] = None,
        interesting_paths: Optional[List[PathOfInterest]] = None,
        length: Optional[int] = None,
        x_shape: Optional[Tuple[int, int]] = None,
        y_shape: Optional[Tuple[int, int, int]] = None,
        AffineTransform: Optional[Union[str, Type[BDVTransform]]] = None,
        z_slices: Optional[Sequence[int]] = None,
        dynamic_z_slice_mod: Optional[int] = None,
    ):
        if z_slices is not None:
            assert AffineTransform is not None

        self.x_path = self.common_path / path / x_dir
        self.y_path = None if y_dir is None else self.common_path / path / y_dir

        self.description = description or self.description

        if isinstance(AffineTransform, str):
            if AffineTransform == "from_x_path":
                posix_path = self.x_path.as_posix()
                indicators_and_AffineTransforms = {
                    "fast_cropped_6ms": fast_cropped_6ms_Transform,
                    "fast_cropped_8ms": fast_cropped_8ms_Transform,
                    "Heart_tightCrop": Heart_tightCrop_Transform,
                    "staticHeartFOV": staticHeartFOV_Transform,
                    "wholeFOV": wholeFOV_Transform,
                }
                for tag, TransformClass in indicators_and_AffineTransforms.items():
                    if tag in posix_path:
                        assert AffineTransform == "from_x_path"  # make sure tag is found only once
                        AffineTransform = TransformClass

            else:
                raise NotImplementedError(AffineTransform)

        self.DefaultAffineTransform = AffineTransform
        if AffineTransform is not None:
            x_shape = x_shape or AffineTransform.lf_shape[1:]

            auto_y_shape = tuple(
                y - y_crop[0] - y_crop[1] for y_crop, y in zip(AffineTransform.lf2ls_crop, AffineTransform.ls_shape)
            )
            auto_y_roi = tuple(
                slice(y_crop[0], y - y_crop[1])
                for y_crop, y in zip(AffineTransform.lf2ls_crop, AffineTransform.ls_shape)
            )
            if z_slices is not None or dynamic_z_slice_mod is not None:
                # auto_y_shape = auto_y_shape[1:]
                auto_y_roi = auto_y_roi[1:]

            y_shape = y_shape or auto_y_shape
            y_roi = y_roi or auto_y_roi

            if z_slices is not None or dynamic_z_slice_mod is not None:
                assert len(y_shape) == 3
                assert len(y_roi) == 2

        self.x_roi = (slice(None), slice(None), slice(None)) if x_roi is None else (slice(None),) + x_roi
        self.y_roi = (slice(None), slice(None), slice(None), slice(None)) if y_roi is None else (slice(None),) + y_roi

        self.interesting_paths = interesting_paths
        self.length = length

        self.x_shape = x_shape
        self.y_shape = y_shape

        self.z_slices = z_slices
        self.dynamic_z_slice_mod = dynamic_z_slice_mod

        self.paths = [self.x_path]
        self.rois = [self.x_roi]
        self.shapes = [self.x_shape]
        if self.y_path is not None:
            self.paths.append(self.y_path)
            self.rois.append(self.y_roi)
            self.shapes.append(self.y_shape)


def resize(
    arr: numpy.ndarray, output_shape: Tuple[int, ...], roi: Optional[Tuple[slice, ...]] = None, order: int = 1
) -> numpy.ndarray:
    assert 0 <= order <= 5, order
    if roi is not None:
        assert len(arr.shape) == len(roi)
        arr = arr[roi]

    assert len(arr.shape) == len(output_shape), (arr.shape, output_shape)
    assert all([sin >= sout for sin, sout in zip(arr.shape, output_shape)]), (arr.shape, output_shape)

    if arr.shape == output_shape:
        return arr
    else:
        return zoom(arr, [sout / sin for sin, sout in zip(arr.shape, output_shape)], order=order)


class N5ChunkAsSampleDataset(torch.utils.data.Dataset):
    paths: Tuple[List[str], ...]
    z_out: Optional[int]

    data_file: z5py.File

    executor: Optional[ThreadPoolExecutor] = None

    futures: Optional[Dict[int, Future]] = None
    submit_lock = threading.Lock()

    def __init__(
        self,
        *,
        info: NamedDatasetInfo,
        nnum: int,
        z_out: int,
        interpolation_order: int,
        data_cache_path: Path,
        get_model_scaling: Callable[[Tuple[int, int]], Tuple[float, float]],
        transform: Optional[Transform] = None,
        ls_affine_transform_class: Optional[BDVTransform] = None,
    ):

        assert data_cache_path.exists(), data_cache_path.absolute()
        super().__init__()

        self.description = info.description
        x_folder = info.x_path
        y_folder = info.y_path
        self.info = info

        if "*" in str(x_folder):
            x_folder, x_glob = split_off_glob(x_folder)
            logger.info("split x_folder into %s and %s", x_folder, x_glob)
        elif x_folder.exists():
            x_glob = "*.tif"
        else:
            raise NotImplementedError

        assert x_folder.exists(), x_folder.absolute()
        x_img_name = next(x_folder.glob(x_glob)).as_posix()
        if info.x_shape is None:
            original_x_shape: Tuple[int, int] = imread(x_img_name)[info.x_roi].shape
            logger.info("determined x shape of %s to be %s", x_img_name, original_x_shape)
        else:
            original_x_shape = info.x_shape

        self.z_out = z_out
        x_shape = (1,) + original_x_shape

        if info.z_slices is None and info.dynamic_z_slice_mod is not None:
            z_crop = info.DefaultAffineTransform.lf2ls_crop[0]
            z_min = z_crop[1]
            z_max = info.dynamic_z_slice_mod - z_crop[0] - 1
            z_dim = info.dynamic_z_slice_mod - z_crop[1] - z_crop[0]
        else:
            z_crop = None
            z_min = None
            z_max = None
            z_dim = None

        self.z_dim = z_dim
        self.z_min = z_min

        if y_folder is None:
            self.with_target = False
            y_shape = None
            y_glob = None
        else:
            self.with_target = True
            if "*" in y_folder.as_posix():
                y_folder, y_glob = split_off_glob(y_folder)
                logger.info("split y_folder into %s and %s", y_folder, y_glob)
            elif y_folder.exists():
                y_glob = "*.tif"
            else:
                raise NotImplementedError

            assert y_folder.exists(), y_folder.absolute()
            try:
                img_name = next(y_folder.glob(y_glob)).as_posix()
            except StopIteration:
                logger.error(y_folder.absolute())
                raise

            if info.y_shape is None:
                original_y_shape = imread(img_name)[info.y_roi].shape
                logger.info("determined y shape of %s to be %s", img_name, original_y_shape)
                assert original_y_shape[1:] == original_x_shape, (original_y_shape[1:], original_x_shape)
            elif info.z_slices is not None or info.dynamic_z_slice_mod is not None:
                original_y_shape = info.y_shape[1:]
            else:
                original_y_shape = info.y_shape

            model_scaling = get_model_scaling(original_x_shape)
            scaling = (model_scaling[0] / nnum, model_scaling[1] / nnum)

            y_dims_12 = tuple(int(oxs * sc) for oxs, sc in zip(original_x_shape, scaling))
            if len(original_y_shape) == 2:
                # dynamic z slices to original size
                if info.y_shape is None:
                    raise NotImplementedError
                else:
                    y_dim_0 = info.y_shape[0]

                y_shape = y_dims_12
            else:
                y_dim_0 = self.z_out
                y_shape = (y_dim_0,) + y_dims_12

            if ls_affine_transform_class is not None:
                assert info.y_shape is not None, "when working with transforms the output shape needs to be given"

                self.ls_affine_transform = ls_affine_transform_class(
                    order=interpolation_order, output_shape=(y_dim_0,) + y_dims_12
                )
            else:
                self.ls_affine_transform = None

            y_shape = (1,) + y_shape  # add channel dim

        self.shapes = [x_shape]
        if y_shape is not None:
            self.shapes.append(y_shape)

        self.interpolation_order = interpolation_order
        shapestr = (
            f"interpolation_order: {interpolation_order}\n"
            f"x_roi: {info.x_roi}\ny_roi: {info.y_roi}\n"
            f"x_shape: {x_shape}\ny_shape: {y_shape}\n"
            f"x_folder: {x_folder}\ny_folder: {y_folder}"
        )
        if ls_affine_transform_class is not None:
            shapestr += f"\nls_affine_transform: {ls_affine_transform_class.__name__}"

        data_file_name = data_cache_path / f"{self.description}_{hash(shapestr.encode()).hexdigest()}.n5"
        data_file_name.with_suffix(".txt").write_text(shapestr)

        logger.info("data_file_name %s", data_file_name)

        self.tmp_data_file_name = data_file_name.with_suffix(".tmp.n5")
        self.part_data_file_name = data_file_name.with_suffix(".part.n5")

        for attempt in range(100):
            if self.tmp_data_file_name.exists():
                logger.warning(f"waiting for data (found {self.tmp_data_file_name})")
                time.sleep(300)
            else:
                break
        else:
            raise FileExistsError(self.tmp_data_file_name)

        self.tensor_names = ["lf"]
        if self.with_target:
            self.tensor_names.append("ls")

        if data_file_name.exists():
            self.tmp_data_file_name = None
            self.data_file = z5py.File(path=data_file_name.as_posix(), mode="r", use_zarr_format=False)
            self._len = self.data_file[self.tensor_names[0]].shape[0]
            self.ready = lambda idx: True
        else:
            self.paths = get_image_paths(
                x_folder,
                x_glob,
                y_folder,
                y_glob,
                z_crop=z_crop,
                z_min=z_min,
                z_max=z_max,
                z_dim=z_dim,
                dynamic_z_slice_mod=info.dynamic_z_slice_mod,
            )
            self._len = len(self.paths[0])
            assert len(self) >= 1, "corrupt existing datasets file?"
            logger.info("datasets length: %s  x shape: %s  y shape: %s", len(self), x_shape, y_shape)

            if self.part_data_file_name.exists():
                self.part_data_file_name.rename(self.tmp_data_file_name)

            data_file = z5py.File(path=str(self.tmp_data_file_name), mode="a", use_zarr_format=False)

            self.n5datasets = OrderedDict()

            for idx, name in enumerate(self.tensor_names):
                if name in data_file:
                    self.n5datasets[name] = data_file[name]
                else:
                    self.n5datasets[name] = data_file.create_dataset(
                        name, shape=(len(self),) + self.shapes[idx], chunks=(1,) + self.shapes[idx], dtype=numpy.float32
                    )

            self.futures = {}
            self.executor = ThreadPoolExecutor(max_workers=settings.max_workers_per_dataset)

            worker_nr = 0
            self.nr_background_workers = (
                settings.max_workers_per_dataset - settings.reserved_workers_per_dataset_for_getitem
            )
            idx = 0
            while (
                worker_nr < settings.max_workers_per_dataset - settings.reserved_workers_per_dataset_for_getitem
                and idx < len(self)
            ):
                fut = self.submit(idx)
                if isinstance(fut, Future):
                    fut.add_done_callback(self.background_worker_callback)
                    idx += 1
                    worker_nr += 1
                else:
                    idx += 1

        stat_path = Path(data_file_name.as_posix().replace(".n5", "_stat.yml"))

        self.transform = None  # for computing stat
        self.stat = DatasetStat(path=stat_path, dataset=self)
        self.transform = transform

    def __len__(self):
        return self._len

    def __getitem__(self, idx) -> typing.OrderedDict[str, Union[numpy.ndarray, int, DatasetStat]]:
        idx = int(idx)
        fut = self.submit(idx)
        if isinstance(fut, Future):
            fut = fut.result()

        assert isinstance(fut, int) and fut == idx
        sample = OrderedDict([(name, self.n5datasets[name][idx][None, ...]) for name in self.tensor_names])

        if self.info.z_slices is not None:
            neg_z_slice = self.info.z_slices[idx % len(self.info.z_slices)]
        elif self.info.dynamic_z_slice_mod is not None:
            neg_z_slice = self.z_min + (idx % self.z_dim) + 1
        else:
            neg_z_slice = None

        z_slice = None if neg_z_slice is None else self.info.dynamic_z_slice_mod - neg_z_slice
        sample["meta"] = [{"stat": self.stat, "idx": idx, "z_slice": z_slice}]

        logger.debug("apply transform %s", self.transform)
        if self.transform is not None:
            sample = self.transform(sample)

        return OrderedDict(
            [
                (key, item) if isinstance(item, int) else (key, numpy.ascontiguousarray(item))
                for key, item in sample.items()
            ]
        )

    def __del__(self):
        if self.tmp_data_file_name is not None:
            self.tmp_data_file_name.rename(self.part_data_file_name)

    def background_worker_callback(self, fut: Future):
        idx = fut.result()["idx"]
        for next_idx in range(idx, len(self), self.nr_background_workers):
            next_fut = self.submit(idx + self.nr_background_workers)
            if next_fut is not None:
                next_fut.add_done_callback(self.background_worker_callback)
                break

    def ready(self, idx: int) -> bool:
        chunk_idx = tuple([idx] + [0] * (len(self.shapes[0]) - 1))
        return self.n5datasets[self.tensor_names[0]].chunk_exists(chunk_idx)

    def submit(self, idx: int) -> Union[int, Future]:
        with self.submit_lock:
            if self.ready(idx) or idx in self.futures:
                return idx
            else:
                fut = self.executor.submit(self.process, idx)
                self.futures[idx] = fut
                return fut

    def process(self, idx: int) -> int:
        for t, name in enumerate(self.tensor_names):
            img = imread(self.paths[t][idx])[None, ...]
            if name == "ls" and self.ls_affine_transform is not None:
                img = self.ls_affine_transform(img)

            img = resize(arr=img, output_shape=self.shapes[t], roi=self.info.rois[t], order=self.interpolation_order)
            assert img.shape == self.shapes[t], (img.shape, self.shapes[t])
            self.n5datasets[name][idx, ...] = img

        return idx


def collate_fn(samples: List[typing.OrderedDict[str, Any]]):
    assert len(samples) > 0
    batch = OrderedDict()
    for b in zip(*[s.items() for s in samples]):
        keys, values = zip(*b)
        k0 = keys[0]
        v0 = values[0]
        assert all(k0 == k for k in keys[1:])
        assert all(type(v0) is type(v) for v in values[1:])
        if isinstance(v0, numpy.ndarray):
            values = numpy.concatenate(values, axis=0)
        elif isinstance(v0, torch.Tensor):
            values = torch.cat(values, dim=0)
        elif isinstance(v0, list):
            assert all(len(v) == 1 for v in values)  # expect explicit batch dimension! (list of len 1 for all samples)
            values = [vv for v in values for vv in v]
        batch[k0] = values

    return batch


class ConcatDataset(torch.utils.data.ConcatDataset):
    def __init__(self, datasets: List[torch.utils.data.Dataset], transform: Optional[Transform] = None):
        self.transform = transform
        super().__init__(datasets=datasets)

    def __getitem__(self, item):
        sample = super().__getitem__(item)
        if self.transform is not None:
            sample = self.transform(sample)

        return sample