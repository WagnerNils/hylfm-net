from typing import Callable, List, Optional, Sequence, Tuple, Union, Any

import numpy
import logging
import torch
import typing
from scipy.ndimage import zoom

from lnet.transformations.base import Transform


logger = logging.getLogger(__name__)


class Crop(Transform):
    def __init__(
        self,
        crop: Optional[Tuple[Tuple[Union[int, float], Optional[Union[int, float]]], ...]] = None,
        crop_fn: Optional[
            Callable[[Tuple[int, ...]], Tuple[Tuple[Union[int, float], Optional[Union[int, float]]], ...]]
        ] = None,
        **super_kwargs,
    ):
        super().__init__(**super_kwargs)
        if crop is not None and crop_fn is not None:
            raise ValueError("exclusive arguments: `crop` and `crop_fn`")
        elif crop_fn is None:
            assert all(len(c) == 2 for c in crop)
            self.crop = crop
            self.crop_fn = None
        else:
            self.crop = None
            self.crop_fn = crop_fn

    def apply_to_tensor(
        self, tensor: Union[numpy.ndarray, torch.Tensor], *, name: str, idx: int, meta: Optional[dict]
    ) -> Union[numpy.ndarray, torch.Tensor]:
        crop = self.crop or self.crop_fn(tensor.shape[2:])
        assert len(tensor.shape) - 1 == len(crop), (tensor.shape, crop)
        int_crop = [[None if cc is None else int(cc) for cc in c] for c in crop]
        if any([crop[i][j] is not None and crop[i][j] != cc for i, c in enumerate(int_crop) for j, cc in enumerate(c)]):
            raise ValueError(f"Crop contains fractions: {crop}")

        out = tensor[(slice(None),) + tuple(slice(c[0], c[1]) for c in crop)]
        logger.debug("Crop tensor: %s %s by %s to %s", name, tensor.shape, crop, out.shape)
        return out


class Pad(Transform):
    def __init__(
        self, pad_width: Sequence[Sequence[int]], pad_mode: str = "lenslets", nnum: Optional[int] = None, **super_kwargs
    ):
        super().__init__(**super_kwargs)
        if any([len(p) != 2 for p in pad_width]) or any([pw < 0 for p in pad_width for pw in p]):
            raise ValueError(f"invalid pad_width sequence: {pad_width}")

        if pad_mode == "lenslets":
            if nnum is None:
                raise ValueError("nnum required to pad lenslets")
        else:
            raise NotImplementedError(pad_mode)

        self.pad_width = pad_width
        self.pad_mode = pad_mode
        self.nnum = nnum

    def apply_to_tensor(
        self, tensor: typing.Any, *, name: str, idx: int, meta: typing.List[dict]
    ) -> typing.Union[numpy.ndarray, torch.Tensor]:
        assert len(tensor.shape) - 1 == len(self.pad_width)
        if isinstance(tensor, numpy.ndarray):
            if self.pad_mode == "lenslets":
                for i, (pw0, pw1) in enumerate(self.pad_width):
                    if pw0:
                        border_lenslets = tensor[(slice(None),) * (i + 1) + (slice(0, pw0 * self.nnum),)]
                        tensor = numpy.concatenate([border_lenslets, tensor], axis=i + 1)
                    if pw1:
                        border_lenslets = tensor[(slice(None),) * (i + 1) + (slice(-pw1 * self.nnum),)]
                        tensor = numpy.concatenate([border_lenslets, tensor], axis=i + 1)

                return tensor
            else:
                raise NotImplementedError(self.pad_mode)
                # return numpy.pad(tensor, pad_width=)
        else:
            NotImplementedError(type(tensor))


class FlipAxis(Transform):
    def __init__(self, axis: int, **super_kwargs):
        super().__init__(**super_kwargs)
        self.axis = axis if axis < 0 else axis + 1  # add batch dim for positive axis

    def apply_to_tensor(
        self, tensor: Union[numpy.ndarray, torch.Tensor], *, name: str, idx: int, meta: List[dict]
    ) -> Union[numpy.ndarray, torch.Tensor]:
        if isinstance(tensor, numpy.ndarray):
            return numpy.flip(tensor, axis=self.axis)
        elif isinstance(tensor, torch.Tensor):
            return tensor.flip([self.axis])
        else:
            raise NotImplementedError


class RandomlyFlipAxis(Transform):
    meta_key_format = "flip_axis_{}"

    def __init__(self, axis: int, **super_kwargs):
        super().__init__(**super_kwargs)
        self.axis = axis

    def edit_meta_before(self, meta: List[dict]) -> List[dict]:
        key = self.meta_key_format.format(self.axis)
        for m in meta:
            assert key not in m, (key, m)
            m[key] = numpy.random.uniform() > 0.5

        return meta

    def apply_to_sample(
        self,
        sample: Union[numpy.ndarray, torch.Tensor],
        *,
        tensor_name: str,
        tensor_idx: int,
        batch_idx: int,
        meta: dict,
    ) -> Union[numpy.ndarray, torch.Tensor]:
        key = self.meta_key_format.format(self.axis)
        if meta[key]:
            if isinstance(sample, numpy.ndarray):
                return numpy.flip(sample, axis=self.axis)
            elif isinstance(sample, torch.Tensor):
                return sample.flip([self.axis])
            else:
                raise NotImplementedError

        return sample


class RandomIntensityScale(Transform):
    meta_key = "random_intensity_scaling"

    def __init__(self, factor_min: float = 0.9, factor_max: float = 1.1, **super_kwargs):
        super().__init__(**super_kwargs)
        self.factor_min = factor_min
        self.factor_max = factor_max

    def edit_meta_before(self, meta: List[dict]) -> List[dict]:
        for m in meta:
            assert self.meta_key not in m, m
            m[self.meta_key] = numpy.random.uniform(low=self.factor_min, high=self.factor_max)

        return meta

    def apply_to_sample(
        self,
        sample: Union[numpy.ndarray, torch.Tensor],
        *,
        tensor_name: str,
        tensor_idx: int,
        batch_idx: int,
        meta: dict,
    ):
        return sample * meta[self.meta_key]


class RandomRotate90(Transform):
    randomly_changes_shape = True
    meta_key = "random_rotate_90"

    def __init__(self, sample_axes: Tuple[int, int] = (-2, -1), **super_kwargs):
        super().__init__(**super_kwargs)
        self.sample_axes = sample_axes

    def edit_meta_before(self, meta: List[dict]) -> List[dict]:
        value = numpy.random.randint(4)  # same for whole batch
        for m in meta:
            assert self.meta_key not in m, m
            m[self.meta_key] = value

        return meta

    def apply_to_sample(
        self,
        sample: Union[numpy.ndarray, torch.Tensor],
        *,
        tensor_name: str,
        tensor_idx: int,
        batch_idx: int,
        meta: dict,
    ):
        return numpy.rot90(sample, k=meta[self.meta_key], axes=self.sample_axes)


class Resize(Transform):
    def __init__(self, shape: Sequence[Union[int, float]], order: int, **super_kwargs):
        super().__init__(**super_kwargs)
        self.shape = shape
        assert 0 <= order <= 5, order
        self.order = order

    def apply_to_sample(
        self,
        sample: Union[numpy.ndarray, torch.Tensor],
        *,
        tensor_name: str,
        tensor_idx: int,
        batch_idx: int,
        meta: dict,
    ):

        # tmeta = meta.get(tensor_name, {})
        # assert "shape_before_resize" not in tmeta
        # tmeta["shape_before_resize"] = sample.shape
        # meta[tensor_name] = tmeta

        assert len(sample.shape) == len(self.shape), (sample.shape, self.shape)

        zoom_factors = [sout if isinstance(sout, float) else sout / sin for sin, sout in zip(sample.shape, self.shape)]
        out = zoom(sample, zoom_factors, order=self.order)
        logger.debug("Resize sample: %s %s by %s to %s", tensor_name, sample.shape, zoom_factors, out.shape)
        return out


# for debugging purposes:
class SetPixelValue(Transform):
    def __init__(self, value: float, **super_kwargs):
        super().__init__(**super_kwargs)
        self.value = value

    def apply_to_tensor(
        self, tensor: typing.Any, *, name: str, idx: int, meta: typing.List[dict]
    ) -> typing.Union[numpy.ndarray, torch.Tensor]:
        tensor[...] = self.value
        return tensor
