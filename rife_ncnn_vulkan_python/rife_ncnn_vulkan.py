#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Name: RIFE ncnn Vulkan Python wrapper
Author: ArchieMeng
Date Created: March 29, 2021
Last Modified: May 21, 2021

Dev: K4YT3X
Last Modified: August 17, 2021
"""

# built-in imports
import importlib
import pathlib
import sys

# third-party imports
from PIL import Image
import numpy as np
import cv2
# local imports
if __package__ is None:
    import rife_ncnn_vulkan_wrapper as wrapped
else:
    wrapped = importlib.import_module(f"{__package__}.rife_ncnn_vulkan_wrapper")
try:
    import torch
except:
    pass

class Rife:
    def __init__(
        self,
        gpuid: int = -1,
        model: str = "rife-v2.3",
        scale: int = 2,
        tta_mode: bool = False,
        tta_temporal_mode: bool = False,
        uhd_mode: bool = False,
        num_threads: int = 1,
    ):
        self.image0_bytes = None
        self.height = None
        # scale must be a power of 2
        if (scale & (scale - 1)) == 0:
            self.scale = scale
        else:
            raise ValueError("scale should be a power of 2")

        # determine if rife-v2 is used
        rife_v2 = ("rife-v2" in model) or ("rife-v3" in model)
        rife_v4 = "rife-v4" in model or "rife4" in model or "rife-4" in model

        # create raw RIFE wrapper object
        self._rife_object = wrapped.RifeWrapped(
            gpuid, tta_mode, tta_temporal_mode, uhd_mode, num_threads, rife_v2, rife_v4
        )
        self._load(model)
        

    def _load(self, model: str, model_dir: pathlib.Path = None):

        # if model_dir is not specified
        if model_dir is None:
            model_dir = pathlib.Path(model)
            if not model_dir.is_absolute() and not model_dir.is_dir():
                model_dir = pathlib.Path(__file__).parent / "models" / model

        # if the model_dir is specified and exists
        if model_dir.exists():
            modeldir_str = wrapped.StringType()
            if sys.platform in ("win32", "cygwin"):
                modeldir_str.wstr = wrapped.new_wstr_p()
                wrapped.wstr_p_assign(modeldir_str.wstr, str(model_dir))
            else:
                modeldir_str.str = wrapped.new_str_p()
                wrapped.str_p_assign(modeldir_str.str, str(model_dir))

            self._rife_object.load(modeldir_str)

        # if no model_dir is specified but doesn't exist
        else:
            raise FileNotFoundError(f"{model_dir} not found")

    def process(self, image0: Image, image1: Image, timestep: float = 0.5) -> Image:
        # Return the image immediately instead of doing the copy in the upstream part which cause black output problems
        # The reason is that the upstream code use ncnn::Mat::operator=(const Mat& m) does a reference copy which won't
        # change our OutImage data.
        if timestep == 0.:
            return image0
        elif timestep == 1.:
            return image1

        image0_bytes = bytearray(image0.tobytes())
        image1_bytes = bytearray(image1.tobytes())
        channels = int(len(image0_bytes) / (image0.width * image0.height))
        output_bytes = bytearray(len(image0_bytes))

        # convert image bytes into ncnn::Mat Image
        raw_in_image0 = wrapped.Image(
            image0_bytes, image0.width, image0.height, channels
        )
        raw_in_image1 = wrapped.Image(
            image1_bytes, image1.width, image1.height, channels
        )
        raw_out_image = wrapped.Image(
            output_bytes, image0.width, image0.height, channels
        )

        self._rife_object.process(raw_in_image0, raw_in_image1, timestep, raw_out_image)
        return Image.frombytes(
            image0.mode, (image0.width, image0.height), bytes(output_bytes)
        )
    def process_cv2(self, image0: np.ndarray, image1: np.ndarray, timestep: float = 0.5) -> np.ndarray:
        if timestep == 0.:
            return image0
        elif timestep == 1.:
            return image1
        image0 = cv2.cvtColor(image0, cv2.COLOR_BGR2RGB)
        image1 = cv2.cvtColor(image1, cv2.COLOR_BGR2RGB)
        image0_bytes = bytearray(image0.tobytes())
        image1_bytes = bytearray(image1.tobytes())
        channels = int(len(image0_bytes) / (image0.shape[1] * image0.shape[0]))
        output_bytes = bytearray(len(image0_bytes))

        # convert image bytes into ncnn::Mat Image
        raw_in_image0 = wrapped.Image(
            image0_bytes, image0.shape[1], image0.shape[0], channels
        )
        raw_in_image1 = wrapped.Image(
            image1_bytes, image0.shape[1], image0.shape[0], channels
        )
        raw_out_image = wrapped.Image(
            output_bytes, image0.shape[1], image0.shape[0], channels
        )

        self._rife_object.process(raw_in_image0, raw_in_image1, timestep, raw_out_image)
        
        res = np.frombuffer(output_bytes, dtype=np.uint8).reshape(
            image0.shape[0], image0.shape[1], channels
        )
        return cv2.cvtColor(res, cv2.COLOR_RGB2BGR)
        
    def process_fast(self, image0: np.ndarray, image1: np.ndarray, timestep: float = 0.5, shape: tuple = None, channels: int = 3) -> np.ndarray:
        """
        An attempt at a faster implementation for NCNN that should speed it up significantly through better caching methods.

        :param image0: The first image to be processed.
        :param image1: The second image to be processed.
        :param timestep: The timestep value for the interpolation.
        :param shape: The shape of the images.
        :param channels: The number of channels in the images.

        :return: The processed image, format: np.ndarray.
        """
        
        if timestep == 0.:
            return np.array(image0)
        elif timestep == 1.:
            return np.array(image1)

        if self.height == None:
            if shape is None:
                self.height, self.width, self.channels = image0.shape
            else:
                self.height, self.width = shape

        image1_bytes = bytearray(image1.tobytes())
        raw_in_image1 = wrapped.Image(
            image1_bytes, self.width, self.height, channels
        )

        if self.image0_bytes is None:
            self.image0_bytes = bytearray(image0.tobytes())
            raw_in_image0 = wrapped.Image(
                self.image0_bytes, self.width, self.height, channels
            )
            self.output_bytes = bytearray(len(self.image0_bytes))
        else:
            raw_in_image0 = wrapped.Image(
                self.image0_bytes, self.width, self.height, channels
            )

        
        raw_out_image = wrapped.Image(
            self.output_bytes, self.width, self.height, channels
        )

        self._rife_object.process(raw_in_image0, raw_in_image1, timestep, raw_out_image)

        self.image0_bytes = image1_bytes

        return np.frombuffer(self.output_bytes, dtype=np.uint8).reshape(
            self.height, self.width, self.channels
        )
    
    def process_fast_torch(self, image0: np.ndarray, image1: np.ndarray, timestep: float = 0.5, shape: tuple = None, channels: int = 3) -> np.ndarray:
        """
        An attempt at a faster implementation for NCNN that should speed it up significantly through better caching methods.

        :param image0: The first image to be processed.
        :param image1: The second image to be processed.
        :param timestep: The timestep value for the interpolation.
        :param shape: The shape of the images.
        :param channels: The number of channels in the images.

        :return: The processed image, format: torch.uint8
        """
        if shape is None:
            height, width, channels = image0.shape
        else:
            height, width = shape

        image1_bytes = bytearray(image1)
        raw_in_image1 = wrapped.Image(
            image1_bytes, width, height, channels
        )

        if self.image0_bytes is None:
            self.image0_bytes = bytearray(image0)
            raw_in_image0 = wrapped.Image(
                self.image0_bytes, width, height, channels
            )
            self.output_bytes = bytearray(len(self.image0_bytes))
        else:
            raw_in_image0 = wrapped.Image(
                self.image0_bytes, width, height, channels
            )

        raw_out_image = wrapped.Image(
            self.output_bytes, width, height, channels
        )

        self._rife_object.process(raw_in_image0, raw_in_image1, timestep, raw_out_image)

        self.image0_bytes = image1_bytes

        return torch.frombuffer(self.output_bytes, dtype=torch.uint8).reshape(
            height, width, channels
        )
    
class RIFE(Rife):
    ...
