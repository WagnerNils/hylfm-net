# BEADS
## precision and recall
### 1.4mu in xy
01highc_f4 applied to 01highc/4mu: `/g/kreshuk/LF_computed/lnet/logs/beads/z_out51/01highc_f4/20-04-29_17-08-09`
/g/kreshuk/LF_computed/lnet/logs/beads/01highc_f4/20-04-21_10-49-27/train/checkpoints/v1_checkpoint_SmoothL1Loss=-0.00016112386947497725.pth
4mu_f4 applied to 4mu/01highc: `/g/kreshuk/LF_computed/lnet/logs/beads/z_out51/4mu_f4/20-04-29_17-09-19`
01highc_f4_lr applied to 01highc/4mu: `/g/kreshuk/LF_computed/lnet/logs/beads/z_out51/01highc_f4_lr/20-04-29_17-55-30`

### 0.7mu in xy
01highc_f8 applied to 01highc/4mu: `/g/kreshuk/LF_computed/lnet/logs/beads/z_out51/01highc_f8/20-04-29_17-09-06`  # THE beads net (beads/01highc/20-04-21_11-41-43/train/checkpoints/v1_checkpoint_SmoothL1Loss=-0.00012947025970788673.pth)
/g/kreshuk/LF_computed/lnet/logs/beads/01highc/20-04-21_11-41-43/train/checkpoints/v1_checkpoint_SmoothL1Loss=-0.00012947025970788673.pth

4mu_f8 applied to 4mu/01highc: `/g/kreshuk/LF_computed/lnet/logs/beads/z_out51/4mu_f8/20-04-29_17-10-01`
f8_lr applied to 01highc: `/g/kreshuk/LF_computed/lnet/logs/beads/z_out51/01highc_f8_lr/20-04-29_18-38-22`

# HEART
best static: /g/kreshuk/LF_computed/lnet/logs/heart2/test_z_out49/f4/z_out49/static_f4_b2_with5_pois/20-06-13_20-26-33/train2/v1_checkpoint_498_MS_SSIM=0.9710696664723483 
/g/kreshuk/LF_computed/lnet/logs/heart2/z_out49/static_f4_b2_with5_pois/20-06-13_20-26-33/train2/run000/checkpoints/v1_checkpoint_498_MS_SSIM=0.9710696664723483.pth

best static best refined: /g/kreshuk/LF_computed/lnet/logs/heart2/z_out49/f4_b2_refine_pois/20-06-16_16-35-51/train/run000/checkpoints/v1_checkpoint_155000_MS_SSIM\=0.9682732355651673.pth
best dynamic training: /g/kreshuk/LF_computed/lnet/logs/heart2/z_out49/f4_b2/20-05-20_10-18-11/train/run000/checkpoints/v1_checkpoint_MSSSIM\=0.6722144321961836.pth

static_f4_b2_with5_pois_dir = 'M:\lnet\logs\heart2\test_z_out49\f4\z_out49\static_f4_b2_with5_pois\20-06-13_20-26-33\train2\v1_checkpoint_498_MS_SSIM=0.9710696664723483';
refined_network_dir = 'M:\lnet\logs\heart2\test_z_out49\f4\z_out49\f4_b2_refine_pois\20-06-16_16-35-51\v1_checkpoint_57250_MS_SSIM\=0.9605052428382436';
lr_dir = 'M:\lnet\logs\heart2\test_z_out49\lr_f4\';
purely_dyn_network_dir = 'M:\lnet\logs\heart2\test_z_out49\f4\z_out49\f4_b2\20-05-20_10-18-11\v1_checkpoint_MSSSIM=0.6722144321961836\';

dyn_on_stat:
from scratch: /g/kreshuk/beuttenm/pycharm_tmp/repos/hylfm-net/logs/train/heart/fake_dyn/from_scratch/21-01-12_21-05-48/train_01/run000/checkpoints/v1_checkpoint_27500_ms_ssim-scaled=0.8430055000565269.pth

# BRAIN
best: K:\LF_computed\lnet\logs\brain1\test_z_out49\f4\z_out49\f4_b2_only11_2\20-06-06_17-59-42\v1_checkpoint_37500_MS_SSIM=0.8822072593371073

## Cropping
rect_LF = [174, 324, 1700, 1400]; %[xmin, ymin, width, height]; -> after this crop, rectified
rect_LS = [124, 274, 1800, 1500] %[xmin, ymin, width, height];

for data: \TestOutputGcamp\LenseLeNet_Microscope\20200311_Gcamp\fish2\10Hz\slideThrough
extra crop on rectified: [323, 133, 1273, 988] %[xmin, ymin, width, height]
    

20200311 (best day)
    fish2 (best fish)
        5 Hz
        10 Hz


## 10Hz
#### fish 1 of day 9

#### fish 4 of day 9
TestOutputGcamp\LenseLeNet_Microscope\20200309_Gcamp\fish4_promising\longRun\fov2\2020-03-09_09.06.55\stack_28_channel_4\SwipeThrough_-450_-210_nimages_49\TP_00000\RC_rectified

not all planes:
TestOutputGcamp\LenseLeNet_Microscope\20200309_Gcamp\fish4_promising\fov/single_planes/fov1

all 25:
TestOutputGcamp\LenseLeNet_Microscope\20200309_Gcamp\fish4_promising\fov/single_planes/fov2

#### fish 2
80 x 121 planes (0-121)  (possibly filter)
TestOutputGcamp\LenseLeNet_Microscope\20200311_Gcamp\fish2\10Hz\2020-03-11_07.34.47\stack_33_channel_3\SwipeThrough_-390_-270_nimages_121

31+15 x 121 planes (60-181)
TestOutputGcamp\LenseLeNet_Microscope\20200311_Gcamp\fish2\10Hz\241Planes
<!-- \2020-03-11_09.08.00\stack_1_channel_3\SwipeThrough_-450_-210_nimages_241 -->

7 * 8 x 121 planes
TestOutputGcamp\LenseLeNet_Microscope\20200311_Gcamp\fish2\10Hz\slideThrough




#### fish 4 single planes


## resolution

gcamp: day11, 10Hz,
 z:  ls: 121um in 1um steps, 5um, -> z_out: 25
 xy: ls: 6.5/22.2=.29  ... -> 2.8um (factor 2)


 ### fish 1 single planes
 L:\LenseLeNet_Microscope\20200309_Gcamp\fish1_awesome\2020-03-09_04.35.55

## predictions
preliminary volume prediction 1.3mu xy: `/g/kreshuk/LF_computed/lnet/logs/brain/z_out51/f4_vol/20-04-28_16-44-06/predict_volume/run000`
