# todo: rename file to heart_static.py
import argparse

from lnet.datasets.base import TensorInfo, get_dataset_from_info
from lnet.datasets.heart_utils import get_transformations, idx2z_slice_241, get_raw_ls_crop, get_ls_shape, get_lf_shape


def get_tensor_info(tag: str, name: str, meta: dict):
    meta = dict(meta)
    assert "z_out" in meta
    assert "nnum" in meta
    assert "interpolation_order" in meta
    assert "scale" in meta
    assert "z_ls_rescaled" in meta
    assert "pred_z_min" in meta
    assert "pred_z_max" in meta

    root = "GKRESHUK"
    insert_singleton_axes_at = [0, 0]
    z_slice = None
    samples_per_dataset = 1

    if "_repeat" in name:
        name, repeat = name.split("_repeat")
        repeat = int(repeat)
    else:
        repeat = 1

    if tag == "beads_ref_Heart_tightCrop":
        crop_name = "Heart_tightCrop"
        transformations = get_transformations(name, "Heart_tightCrop", meta=meta)
        location = "LF_partially_restored/LenseLeNet_Microscope/20191208_dynamic_static_heart/beads/after_fish2/definitelyNotMoving/Heart_tightCrop/200msExp/2019-12-09_22.23.27/"
        if name == "lf":
            location += "stack_0_channel_0/TP_*/RC_rectified/Cam_Right_*_rectified.tif"
        elif name == "ls" or name == "ls_trf":
            location += "stack_1_channel_1/Cam_Left_*.h5/Data"

    elif tag == "beads_ref_Heart_tightCrop_tif":
        crop_name = "Heart_tightCrop"
        location = "LF_partially_restored/LenseLeNet_Microscope/20191208_dynamic_static_heart/beads/after_fish2/definitelyNotMoving/Heart_tightCrop/200msExp/2019-12-09_22.23.27/"
        if name == "ls":
            location += "*Cam_Left.tif"
            transformations = [
                {"Assert": {"apply_to": name, "expected_tensor_shape": [1, 1, 241, 1451, 1651]}},  # raw tif
                {"Crop": {"apply_to": name, "crop": [[0, None]] + get_raw_ls_crop("Heart_tightCrop", wrt_ref=True)}},
                {"Assert": {"apply_to": name, "expected_tensor_shape": [1, 1] + get_ls_shape("Heart_tightCrop")}},
                {
                    "Resize": {
                        "apply_to": name,
                        "shape": [
                            1.0,
                            meta["z_ls_rescaled"],
                            meta["scale"] / meta["nnum"],
                            meta["scale"] / meta["nnum"],
                        ],
                        "order": meta["interpolation_order"],
                    }
                },
                {
                    "Assert": {
                        "apply_to": name,
                        "expected_tensor_shape": [None, 1, meta["z_ls_rescaled"]]
                        + [s / meta["nnum"] * meta["scale"] for s in get_ls_shape("Heart_tightCrop")[1:]],
                    }
                },
            ]
        elif name == "ls_reg":
            location += "*Cam_Left_registered.tif"
            transformations = [
                {
                    "Assert": {
                        "apply_to": name,
                        "expected_tensor_shape": [1, 1, 838] + get_lf_shape("Heart_tightCrop"),
                    }  # raw tif
                },
                {
                    "Resize": {
                        "apply_to": name,
                        "shape": [1.0, meta["z_out"] / 838, meta["scale"] / meta["nnum"], meta["scale"] / meta["nnum"]],
                        "order": meta["interpolation_order"],
                    }
                },
            ]

    elif tag == "beads_should_fit_Heart_tightCrop_0":
        crop_name = "Heart_tightCrop"
        transformations = get_transformations(name, "Heart_tightCrop", meta=meta)
        location = "LF_partially_restored/LenseLeNet_Microscope/20191207_StaticHeart/Beads/Heart_tightCrop/2019-12-08_05.10.30/"
        if name == "lf":
            location += "stack_0_channel_0/TP_*/RC_rectified/Cam_Right_*_rectified.tif"
        if name == "ls" or name == "ls_trf":
            location += "stack_1_channel_1/Cam_Left_*.h5/Data"

    elif tag in ["2019-12-08_06.57.57", "2019-12-08_06.59.59", "2019-12-08_10.32.03"]:
        crop_name = "staticHeartFOV"
        transformations = get_transformations(name, "staticHeartFOV", meta=meta)
        location = f"LF_partially_restored/LenseLeNet_Microscope/20191207_StaticHeart/fish1/static/staticHeartFOV/Sliding_stepsize2_CompleteSlide/{tag}/"
        if name == "lf":
            location += "stack_3_channel_0/TP_*/RC_rectified/Cam_Right_001_rectified.tif"
        elif name == "lr":
            location = location.replace("LF_partially_restored/", "LF_computed/")
            location += "stack_3_channel_0/TP_*/RCout/Cam_Right_001.tif"
        elif name == "ls" or name == "ls_trf":
            location += "stack_4_channel_1/Cam_Left_*.h5/Data"
        elif name == "ls_fake_slice":
            location += "stack_4_channel_1/Cam_Left_*.h5/Data"
            samples_per_dataset = 241
            z_slice = idx2z_slice_241

    elif tag in [
        "2019-12-08_06.35.52",
        "2019-12-08_06.38.47",
        "2019-12-08_06.10.34",
        "2019-12-08_06.41.39",
        "2019-12-08_06.18.09",
        "2019-12-08_06.46.09",
        "2019-12-08_06.23.13",
        "2019-12-08_06.49.08",
        "2019-12-08_06.25.02",
        "2019-12-08_06.51.57",
        "2019-12-08_06.30.40",
    ]:
        crop_name = "Heart_tightCrop"
        transformations = get_transformations(name, "Heart_tightCrop", meta=meta)
        location = f"LF_partially_restored/LenseLeNet_Microscope/20191207_StaticHeart/fish1/static/Heart_tightCrop/centeredPos_5steps_stepsize8/probablyStatic/{tag}/"
        if name == "lf":
            location += "stack_3_channel_0/TP_*/RC_rectified/Cam_Right_001_rectified.tif"
        elif name == "lr":
            location = location.replace("LF_partially_restored/", "LF_computed/")
            location += "stack_3_channel_0/TP_*/RCout/Cam_Right_001.tif"
        elif name == "ls" or name == "ls_trf":
            location += "stack_4_channel_1/Cam_Left_*.h5/Data"
        elif name == "ls_fake_slice":
            location += "stack_4_channel_1/Cam_Left_*.h5/Data"
            samples_per_dataset = 241
            z_slice = idx2z_slice_241

    elif tag in [
        "2019-12-09_02.16.30",
        "2019-12-09_02.23.01",
        "2019-12-09_02.29.34",
        "2019-12-09_02.35.49",
        "2019-12-09_02.42.03",
        "2019-12-09_02.48.24",
        "2019-12-09_02.54.46",
    ]:
        crop_name = "Heart_tightCrop"
        transformations = get_transformations(name, "Heart_tightCrop", meta=meta)
        location = f"LF_partially_restored/LenseLeNet_Microscope/20191208_dynamic_static_heart/fish1/static/Heart_tightCrop/centered_5steps_stepsize8/{tag}/"
        if name == "lf":
            location += "stack_3_channel_0/TP_*/RC_rectified/Cam_Right_001_rectified.tif"
        elif name == "lr":
            location = location.replace("LF_partially_restored/", "LF_computed/")
            location += "stack_3_channel_0/TP_*/RCout/Cam_Right_001.tif"
        elif name == "ls" or name == "ls_trf":
            location += "stack_4_channel_1/Cam_Left_*.h5/Data"
        elif name == "ls_fake_slice":
            location += "stack_4_channel_1/Cam_Left_*.h5/Data"
            samples_per_dataset = 241
            z_slice = idx2z_slice_241

    elif tag in ["2019-12-08_06.59.59", "2019-12-08_10.32.03"]:
        crop_name = "staticHeartFOV"
        transformations = get_transformations(name, "staticHeartFOV", meta=meta)
        location = f"LF_partially_restored/LenseLeNet_Microscope/20191207_StaticHeart/fish1/static/staticHeartFOV/Sliding_stepsize2_CompleteSlide/{tag}/"
        if name == "lf":
            location += "stack_3_channel_0/TP_*/RC_rectified/Cam_Right_001_rectified.tif"
        elif name == "lr":
            location = location.replace("LF_partially_restored/", "LF_computed/")
            location += "stack_3_channel_0/TP_*/RCout/Cam_Right_001.tif"
        elif name == "ls" or name == "ls_trf":
            location += "stack_4_channel_1/Cam_Left_*.h5/Data"
        elif name == "ls_fake_slice":
            location += "stack_4_channel_1/Cam_Left_*.h5/Data"
            samples_per_dataset = 241
            z_slice = idx2z_slice_241

    elif tag in ["2019-12-09_07.42.47"]:
        crop_name = "Heart_tightCrop"
        transformations = get_transformations(name, "Heart_tightCrop", meta=meta)
        location = f"LF_partially_restored/LenseLeNet_Microscope/20191208_dynamic_static_heart/fish2/dynamic/Heart_tightCrop/2019-12-09_05.41.14_theGoldenOne/staticHeart_samePos/{tag}/stack_1_channel_3/"
        if name == "lf":
            location += "TP_*/RC_rectified/Cam_Right_*_rectified.tif"
        # elif name == "lr":
        #     location = location.replace("LF_partially_restored/", "LF_computed/")
        #     location += "TP_*/RCout/Cam_Right_001.tif"
        elif name == "ls" or name == "ls_trf":
            location += "Cam_Left_*.h5/Data"
        elif name == "ls_fake_slice":
            location += "Cam_Left_*.h5/Data"
            samples_per_dataset = 241
            z_slice = idx2z_slice_241

    elif tag in ["2019-12-09_07.50.24"]:
        crop_name = "Heart_tightCrop"
        transformations = get_transformations(name, "Heart_tightCrop", meta=meta)
        location = f"LF_partially_restored/LenseLeNet_Microscope/20191208_dynamic_static_heart/fish2/dynamic/Heart_tightCrop/2019-12-09_05.41.14_theGoldenOne/staticHeart_samePos/{tag}/stack_1_channel_3/"
        if name == "lf":
            location += "TP_*/RC_rectified/Cam_Right_001_rectified.tif"
        # elif name == "lr":
        #     location = location.replace("LF_partially_restored/", "LF_computed/")
        #     location += "TP_*/RCout/Cam_Right_001.tif"
        elif name == "ls" or name == "ls_trf":
            location += "Cam_Left_*.h5/Data"
        elif name == "ls_fake_slice":
            location += "Cam_Left_*.h5/Data"
            samples_per_dataset = 241
            z_slice = idx2z_slice_241

    elif tag in [
        "2019-12-09_08.34.44",
        "2019-12-09_08.41.41",
        "2019-12-09_08.51.01",
        "2019-12-09_09.01.28",
        "2019-12-09_09.11.59",
        "2019-12-09_09.18.01",
    ]:
        crop_name = "Heart_tightCrop"
        transformations = get_transformations(name, "Heart_tightCrop", meta=meta)
        location = f"LF_partially_restored/LenseLeNet_Microscope/20191208_dynamic_static_heart/fish2/static/Heart_tightCrop/5steps_stepsize15/{tag}/"
        if name == "lf":
            location += "stack_3_channel_0/TP_*/RC_rectified/Cam_Right_001_rectified.tif"
        elif name == "lr":
            location = location.replace("LF_partially_restored/", "LF_computed/")
            location += "stack_3_channel_0/TP_*/RCout/Cam_Right_001.tif"
        elif name == "ls" or name == "ls_trf":
            location += "stack_4_channel_1/Cam_Left_*.h5/Data"
        elif name == "ls_fake_slice":
            location += "stack_4_channel_1/Cam_Left_*.h5/Data"
            samples_per_dataset = 241
            z_slice = idx2z_slice_241

    elif tag in ["2019-12-09_08.15.07", "2019-12-09_08.19.40", "2019-12-09_08.27.14"]:
        crop_name = "Heart_tightCrop"
        transformations = get_transformations(name, "Heart_tightCrop", meta=meta)
        location = f"LF_partially_restored/LenseLeNet_Microscope/20191208_dynamic_static_heart/fish2/static/Heart_tightCrop/5steps_stepsize8/{tag}/"
        if name == "lf":
            location += "stack_3_channel_0/TP_*/RC_rectified/Cam_Right_001_rectified.tif"
        elif name == "lr":
            location = location.replace("LF_partially_restored/", "LF_computed/")
            location += "stack_3_channel_0/TP_*/RCout/Cam_Right_001.tif"
        elif name == "ls" or name == "ls_trf":
            location += "stack_4_channel_1/Cam_Left_*.h5/Data"
        elif name == "ls_fake_slice":
            location += "stack_4_channel_1/Cam_Left_*.h5/Data"
            samples_per_dataset = 241
            z_slice = idx2z_slice_241

    elif tag in ["2019-12-09_09.52.38"]:
        crop_name = "staticHeartFOV"
        transformations = get_transformations(name, "staticHeartFOV", meta=meta)
        location = f"LF_partially_restored/LenseLeNet_Microscope/20191208_dynamic_static_heart/fish2/static/staticHeartFOV/completeSlideThrough_125steps_stepsize2/{tag}/"
        if name == "lf":
            location += "stack_3_channel_0/TP_*/RC_rectified/Cam_Right_001_rectified.tif"
        elif name == "lr":
            location = location.replace("LF_partially_restored/", "LF_computed/")
            location += "stack_3_channel_0/TP_*/RCout/Cam_Right_001.tif"
        elif name == "ls" or name == "ls_trf":
            location += "stack_4_channel_1/Cam_Left_*.h5/Data"
        elif name == "ls_fake_slice":
            location += "stack_4_channel_1/Cam_Left_*.h5/Data"
            samples_per_dataset = 241
            z_slice = idx2z_slice_241

    elif tag in [
        "2019-12-10_04.24.29",
        "2019-12-10_05.14.57",
        "2019-12-10_05.41.48",
        "2019-12-10_06.03.37",
        "2019-12-10_06.25.14",
    ]:
        crop_name = "staticHeartFOV"
        transformations = get_transformations(name, "staticHeartFOV", meta=meta)
        location = f"LF_partially_restored/LenseLeNet_Microscope/20191208_dynamic_static_heart/fish3/static/staticHeartFOV/20steps_stepsize5/{tag}/"
        if name == "lf":
            location += "stack_3_channel_0/TP_*/RC_rectified/Cam_Right_001_rectified.tif"
        elif name == "lr":
            location = location.replace("LF_partially_restored/", "LF_computed/")
            location += "stack_3_channel_0/TP_*/RCout/Cam_Right_001.tif"
        elif name == "ls" or name == "ls_trf":
            location += "stack_4_channel_1/Cam_Left_*.h5/Data"
        elif name == "ls_fake_slice":
            location += "stack_4_channel_1/Cam_Left_*.h5/Data"
            samples_per_dataset = 241
            z_slice = idx2z_slice_241

    else:
        raise NotImplementedError(tag)

    if location is None or location.endswith("/"):
        raise NotImplementedError(f"tag: {tag}, name: {name}")

    assert "beads" in tag or tag in location, (tag, name, location)
    if "crop_names" in meta:
        assert crop_name in meta["crop_names"]

    if "crop_name" in meta:
        assert meta["crop_name"] == crop_name
    else:
        meta["crop_name"] = crop_name

    return TensorInfo(
        name=name,
        root=root,
        location=location,
        insert_singleton_axes_at=insert_singleton_axes_at,
        transformations=transformations,
        z_slice=z_slice,
        samples_per_dataset=samples_per_dataset,
        repeat=repeat,
        tag=tag.replace("-", "").replace(".", ""),
        meta=meta,
    )


def debug():
    tight_heart_bdv = [
        [
            0.97945,
            0.0048391,
            -0.096309,
            -88.5296,
            -0.0074754,
            0.98139,
            0.15814,
            -91.235,
            0.016076,
            0.0061465,
            4.0499,
            -102.0931,
        ]
    ]

    def get_vol_trf(name: str):
        return [
            {
                "Resize": {
                    "apply_to": name,
                    "shape": [1.0, 1.0, 0.21052631578947368421052631578947, 0.21052631578947368421052631578947],
                    # "shape": [1.0, 1.0, 0.42105263157894736842105263157895, 0.42105263157894736842105263157895],
                    "order": 2,
                }
            }
        ]

    # ds_ls = get_dataset_from_info(f20191209_081940_ls, transformations=get_vol_trf("ls"), cache=True, indices=[0])
    # print("len ls", len(ds_ls))

    # ds_ls_trf = get_dataset_from_info(
    #     f20191209_081940_ls_trf, transformations=get_vol_trf("ls_trf"), cache=True, indices=[0]
    # )
    # print("len ls_trf", len(ds_ls_trf))
    # ds_ls_trf = get_dataset_from_info(
    #     f20191209_081940_ls_trf, transformations=[], cache=True, indices=[0]
    # )

    # ds_ls_tif = get_dataset_from_info(
    #     f20191209_081940_ls_tif, transformations=get_vol_trf("ls_tif"), cache=True, indices=[0]
    # )
    # print("len ls tif", len(ds_ls_tif))

    # slice_indices = [0, 1, 2, 3, 4, 40, 80, 120, 160, 200, 240]
    # ds_ls_slice = get_dataset_from_info(
    #     f20191209_081940_ls_slice, transformations=get_vol_trf("ls_slice"), cache=True, indices=slice_indices
    # )

    # print("len ls_tif", len(ds))
    # ls_tif = ds[0]["ls_tif"]
    # print("ls_tif", ls_tif.shape)
    #
    # print("diff max", ls.max(), ls_tif.max())
    # print("max diff", (ls - ls_tif).max())
    #
    #
    # plt.imshow(ls[0, 0].max(0))
    # plt.title("ls0")
    # plt.show()
    # plt.imshow(ls[0, 0].max(1))
    # plt.title("ls1")
    # plt.show()
    #
    # plt.imshow(ls_tif[0, 0].max(0))
    # plt.title("ls_tif0")
    # plt.show()
    # plt.imshow(ls_tif[0, 0].max(1))
    # plt.title("ls_tif1")
    # plt.show()

    # ds_lr = get_dataset_from_info(f20191209_081940_lr, transformations=get_vol_trf("lr"), cache=False, indices=[0])
    # print("len ds_lr", len(ds_lr))
    # ds_lr_repeat = get_dataset_from_info(
    #     f20191209_081940_lr_repeat, transformations=get_vol_trf("lr"), cache=True, indices=slice_indices
    # )
    # print("len ds_lr_repeat", len(ds_lr_repeat))

    # ds_zip_slice = ZipDataset(
    #     datasets={"lr": ds_lr_repeat, "ls_slice": ds_ls_slice},
    #     transformation=AffineTransformation(
    #         apply_to={"lr": "lr_trf"},
    #         target_to_compare_to="ls_slice",
    #         order=2,
    #         ref_input_shape=[838, 1273, 1463],
    #         bdv_affine_transformations=tight_heart_bdv,
    #         ref_output_shape=[241, 1451, 1651],
    #         ref_crop_in=[[0, None], [0, None], [0, None]],
    #         ref_crop_out=[[0, None], [0, None], [0, None]],
    #         inverted=False,
    #         padding_mode="border",
    #     ),
    # )

    # ds_zip = ZipDataset(
    #     datasets={"ls": ds_ls, "lr": ds_lr, "ls_tif": ds_ls_tif},
    #     # transformation=AffineTransformation(
    #     #     apply_to={"lr": "lr_trf"},
    #     #     target_to_compare_to="ls",
    #     #     order=2,
    #     #     ref_input_shape=[838, 1273, 1463],
    #     #     bdv_affine_transformations=tight_heart_bdv,
    #     #     ref_output_shape=[241, 1451, 1651],
    #     #     ref_crop_in=[[0, None], [0, None], [0, None]],
    #     #     ref_crop_out=[[0, None], [0, None], [0, None]],
    #     #     inverted=False,
    #     #     padding_mode="border",
    #     # ),
    # )
    # sample = ds_zip[0]

    # ds_zip = ZipDataset(datasets={"ls_trf": ds_ls_trf, "lr": ds_lr})
    # sample = ds_zip[0]

    # def save_vol(name):
    #     vol = sample[name]
    #     imageio.volwrite(f"/g/kreshuk/LF_computed/lnet/debug_affine_fish_trf/{name}.tif", numpy.squeeze(vol))
    #
    # def plot_vol(name):
    #     vol = sample[name]
    #     fig, ax = plt.subplots(2)
    #     for i in range(2):
    #         ax[i].imshow(vol[0, 0].max(i))
    #         ax[i].set_title(f"{name}_super_big{i}")
    #
    #     plt.show()
    #
    # for name in ["ls_trf"]:
    #     save_vol(name)
    #     plot_vol(name)

    # for idx in range(11):
    #     sample = ds_zip_slice[idx]
    #     fig, ax = plt.subplots(2)
    #     ax[0].imshow(sample["ls_slice"][0, 0, 0])
    #     ax[0].set_title(f"ls_slice idx: {idx} z: {sample['meta'][0]['ls_slice']['z_slice']}")
    #     ax[1].imshow(sample["lr_trf"][0, 0, 0])
    #     ax[1].set_title(f"lr_trf idx: {idx}")
    #     plt.show()


def check_data(tag: str, comment: str, meta: dict):
    print("get lf")
    lf = get_dataset_from_info(get_tensor_info(tag, "lf", meta=meta), cache=True)
    print("get lr")
    lr = get_dataset_from_info(get_tensor_info(tag, "lr", meta=meta))
    print("get ls")
    ls = get_dataset_from_info(get_tensor_info(tag, "ls", meta=meta), cache=False)
    print("get ls_trf")
    ls_trf = get_dataset_from_info(get_tensor_info(tag, "ls_trf", meta=meta), cache=True)

    print(tag, len(lf), comment)
    assert len(lf) == len(lr), (tag, len(lf), len(lr))
    assert len(lf) == len(ls), (tag, len(lf), len(ls))
    assert len(lf) == len(ls_trf), (tag, len(lf), len(ls_trf))
    assert len(lf) > 0, tag

    print("get lr_repeat")
    lf_repeat = get_dataset_from_info(get_tensor_info(tag, "lf_repeat241", meta=meta), cache=True)
    print("get ls_fake_slice")
    ls_fake_slice = get_dataset_from_info(get_tensor_info(tag, "ls_fake_slice", meta=meta))

    assert len(lf_repeat) == len(ls_fake_slice), (tag, len(lf_repeat), len(ls_fake_slice))
    assert len(lf_repeat) > 0, tag
    # print(tag, len(lf), comment)

    # lf = lf[0]["lf"]
    # lr = lr[0]["lr"]
    # ls = ls[0]["ls_trf"]
    # print("\tlf", lf.shape)
    # print("\tlr", lr.shape)
    # print("\tpr", [s / 19 * 4 - 16 for s in lf.shape[-2:]])
    # print("\tls", ls.shape, [s - 2 * 38 for s in ls.shape[-2:]])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="heart_dynamic")
    parser.add_argument("idx", type=int)

    args = parser.parse_args()
    idx = args.idx

    meta = {
        "z_out": 49,
        "nnum": 19,
        "scale": 4,
        "interpolation_order": 2,
        "z_ls_rescaled": 241,
        "pred_z_min": 0,
        "pred_z_max": 838,
        "crop_names": ["Heart_tightCrop"],  # staticHeartFOV
        "shrink": 8,
    }

    # depug()
    # search_data()

    tags = """
# beads_ref_Heart_tightCrop
# beads_should_fit_Heart_tightCrop_0
2019-12-08_06.35.52  # fish5 val selected
2019-12-08_06.38.47  # fish5 val selected
2019-12-08_06.10.34  # fish5 val selected
2019-12-08_06.41.39  # fish5 val selected
2019-12-08_06.18.09  # fish5 val selected
2019-12-08_06.46.09  # fish5 val selected
2019-12-08_06.23.13  # fish5 val selected
2019-12-08_06.49.08  # fish5 val selected
2019-12-08_06.25.02  # fish5 val selected
2019-12-08_06.51.57  # fish5 val selected
2019-12-08_06.30.40  # fish5 val selected
# 2019-12-08_06.57.57  # fish5 val
# 2019-12-08_06.59.59  # fish5 val
# 2019-12-08_10.32.03  # fish5 val
# 2019-12-09_09.52.38  # fish2 test
# 2019-12-09_08.34.44  # fish2 test 
2019-12-09_08.41.41  # fish2 test
# 2019-12-09_08.51.01  # fish2 test 
# 2019-12-09_09.01.28  # fish2 test 
# 2019-12-09_09.11.59  # fish2 test 
# 2019-12-09_09.18.01  # fish2 test 
# 2019-12-09_08.15.07  # fish2 test
# 2019-12-09_08.19.40  # fish2 test
# 2019-12-09_08.27.14  # fish2 test
# 2019-12-09_02.16.30  # fish1
# 2019-12-09_02.23.01  # fish1
# 2019-12-09_02.29.34  # fish1
# 2019-12-09_02.35.49  # fish1
# 2019-12-09_02.42.03  # fish1
# 2019-12-09_02.48.24  # fish1
# 2019-12-09_02.54.46  # fish1
# 2019-12-09_07.42.47  # fish2 test
# 2019-12-09_07.50.24  # fish2 test
# 2019-12-10_04.24.29  # fish3
# 2019-12-10_05.14.57  # fish3
# 2019-12-10_05.41.48  # fish3
# 2019-12-10_06.03.37  # fish3
# 2019-12-10_06.25.14  # fish3
""".split(
        "\n"
    )

    full_tags = [tag for tag in tags if tag and not tag.startswith("#")]
    tags = []
    comments = []

    for full_tag in full_tags:
        if "#" in full_tag:
            tag, comment = full_tag.split("#")
            tag = tag.strip()
        else:
            tag = full_tag
            comment = ""

        tags.append(tag)
        comments.append(comment)

    check_data(tags[idx], comments[idx], meta=meta)
