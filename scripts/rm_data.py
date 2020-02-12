from pathlib import Path

import shutil

data_path = Path("../data")

delete = """
fish1_20191208_t0638_static_affine_55ce0ccd184c0c7f1298de6c5458a529df538060472a629fff33f582
fish1_20191208_t0641_static_affine_51f318769bc1de663ee995a730b255a125186904f75424050a7df844
fish1_20191208_t0610_static_affine_5339cd299947fa5ff3190f55d869648bec3efe553a5660088dc418a5
fish1_20191208_t0618_static_affine_72e11884a4a81656037b848938e16493fb9f38b4fc192728dbe58ce8
fish1_20191208_t0623_static_affine_e9b25b1d193190f867cfc50ff36f9b0397c4a3ca9cf6e6eaadaad971
fish1_20191208_t0625_static_affine_a0d8ce950b56aec034b2fedb9b6b9068f98dc5356a496d4e7f602dd0
fish1_20191207_t0625_static_affine_db8915692de445982d1722c380e18ea60a6636e08d29f0e4c5f227bf
fish1_20191207_t0657_static_affine_f5e703308ab7437564c74eaa80bc5c5bca952016b4aba79ffc212d41
fish1_20191207_t0659_static_affine_3fe5f41a3246d56ae6823edf79591d5b6a64a21144e72d60e1b0034e
fish1_20191207_t1032_static_affine_af6169468e065de6a8a6eb3778f30b9204822e2400008731929047a6
fish1_20191207_t0610_static_affine_d38bfe3076159f5bfbae2baa03e74364de87e1a7e997a0321d5ecc6d
fish1_20191207_t0618_static_affine_234e30ffb61d0c53b94f71a22e66e3f589565bc4057764ef2ed163e5
fish1_20191207_t0623_static_affine_9979b546ee1c33a19ee1f6be8d8565fc58f2a108db53969cdcfde301
fish1_20191207_t0641_static_affine_2895e691f8ed953de88d7fd607de4980c8510ea82cca785292fdb7a2
fish1_20191207_t0646_static_affine_170df5f3b0bebeadd49b495ee79355cf1b16e2425e5b807092841531
fish1_20191207_t0649_static_affine_1a2fd334fd2971fe72af736413f9f81de3b8ec9c82601ff5c903912f
fish1_20191207_t0651_static_affine_50d9ea3cc31e037d2775ec0a0e45e87cbd1279e3d31606e8e12e6580
fish1_20191207_t0635_static_affine_26d77ccd5319d44c670b5350df1f9ed7fa0d65c7d112511c71e5da00
fish1_20191207_t0638_static_affine_525f552017201310735a7c1ec4cb1a17f3687fd2116509382164ff2b
fish1_20191207_t0630_static_affine_b4982c30a2062ed44d8fbe46e4a8808ce4cc5c7828a21dcf33a2000e
fish3_20191209_t0625_static_affine_6b0ac6f9b2fad87df466ff0527e748bf90ded26533112e81c5752863
fish3_20191209_t0424_static_9b51fb2273081c4c3e504361c39c62f35cf2ea8eb88a6477ccc898f9
fish3_20191209_t0514_static_affine_62425136db5fcc082b2d7569848c7a67bf966e6d0de21934bbd59037
fish3_20191209_t0541_static_affine_e517962ec55dc723827daf3beeba319aa53b4d0a774e892a8475e628
fish3_20191209_t0603_static_affine_b5e1e8e63e1922e3974d1120eb7e70481e5daff25b710b0d60cd72ca
fish2_20191209_t0901_static_affine_b9b44d37b1c2a015e69969dd3dba61280792dbc71957237396829af9
fish2_20191209_t0911_static_affine_ca077b8f9c4d441c628d07efcb8fda784d253b6ecb434b73f9e444d0
fish2_20191209_t0952_static_affine_3c81c72f18a01deca5004e50c6123d89473768a05ae8dde96fa3becf
fish2_20191209_t0827_static_affine_34674721a7573b8692b209b8df19fc170b2aa44a2ea4220207b4095a
fish2_20191209_t0834_static_affine_941e9ad4ebb635fe6ac3e2d42dff1ef0392ef93cc6ac6283be02137d
fish2_20191209_t0841_static_affine_b3d9279f9e12f970815ddb9f05948e2f6323e94c0d9ed2d8b3abf2e8
fish2_20191209_t0851_static_affine_7bad67bec6c44fe78bcd011a640ccfca4782124195bc076ac9ff999d
fish1_20191209_fish_20191208_0254_static_affine_a7cbd6f82fadee9b1ad43a41854082d408aee2411aaabdbe7db39b13
fish2_20191209_t0819_static_affine_2fadcd640e8c752b594706a65f478402a682261f4f2a559ca612e915
fish1_20191209_t0229_static_affine_758684705d247748af74d9ee9e3e461114a6cc583f31bed7d0dfd829
fish1_20191209_t0235_static_affine_ed64b6345004efed106aa5e2961c1730bcb1d21f180feab060f5d22e
fish1_20191209_t0242_static_affine_d99ee489d36a7eff2e1c876842de5d8997df080a2a7cfbc0e7ed9254
fish1_20191209_t0248_static_affine_cf3215530815d20ebb591d47191b6dea82dd015bb8ac145ac6942fa7
fish1_20191208_t0646_static_affine_a6eb14c46c85f658597893ed2cc2ae8d5d60617024f7a147db006237
fish1_20191208_t0649_static_affine_d52c7b2b2001f753536821248a3654b2335a1c678e87f2e1a7804746
fish1_20191208_t0630_static_affine_220b8646118b0515ab0ccb7e51c8163850ea4f00e7e84c89fa0dd596
fish1_20191208_t0635_static_affine_f80e89170e187d9304a6f24177e934318698d85459b40cbd48bd5a2b
"""

for name in delete.strip("\n").split("\n"):
    shutil.rmtree(data_path / f"{name}.n5")
    for file_path in data_path.glob(f"{name}.*"):
        file_path.unlink()
