import torch

from lnet.metrics.msssim import SSIM, SSIM_SkImage


def test_mssim(beads_dataset):
    ls_trf = beads_dataset[0]["ls_trf"]
    assert len(ls_trf.shape) == 5, ls_trf.shape
    lr = beads_dataset[0]["ls_reg"]
    assert ls_trf.shape == lr.shape, (ls_trf.shape, lr.shape)

    ls_trf = torch.from_numpy(ls_trf)
    lr = torch.from_numpy(lr)

    kwargs = {"window_size": 11, "size_average": True, "val_range": None}
    torch_metric = SSIM(**kwargs)
    skimage_metric = SSIM_SkImage(**kwargs)

    torch_metric.update((lr, ls_trf))
    skimage_metric.update((lr, ls_trf))

    torch_mssim = torch_metric.compute()
    skimage_mssim = skimage_metric.compute()

    assert torch_mssim == skimage_mssim, (torch_mssim, skimage_mssim)
