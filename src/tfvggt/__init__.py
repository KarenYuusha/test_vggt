"""tfvggt: training-free faster inference for VGGT (compressed global attention, frozen VGGT-1B weights).

Main entry points:
    tfvggt.core.build_model / tfvggt.core.configure   build VGGT-1B and switch its global attention scheme
    tfvggt.configs.CONFIGS                             named configurations used in the experiments
    tfvggt.runner.run                                  evaluate configurations on sequences
    the `tfvggt` command (tfvggt.cli)
Importing this package does not import torch or FlashVGGT; the submodules do.
"""
__version__ = "0.1.0"
