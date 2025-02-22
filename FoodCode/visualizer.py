"""Visualizer for results of prediction."""

# Copyright (C) 2021-2022 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
#

import abc
import time
from typing import Optional

import cv2
import numpy as np
import screeninfo

from otx.api.entities.annotation import AnnotationSceneEntity
from otx.api.utils.shape_drawer import ShapeDrawer
from otx.api.usecases.exportable_code.streamer import BaseStreamer


class IVisualizer(metaclass=abc.ABCMeta):
    """Interface for converter."""

    @abc.abstractmethod
    def draw(
        self,
        image: np.ndarray,
        annotation: AnnotationSceneEntity,
        meta: dict,
    ) -> np.ndarray:
        """Draw annotations on the image.

        Args:
            image: Input image
            annotation: Annotations to be drawn on the input image
            metadata: Metadata is needed to render

        Returns:
            Output image with annotations.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def show(self, image: np.ndarray) -> None:
        """Show result image."""

        raise NotImplementedError

    @abc.abstractmethod
    def is_quit(self) -> bool:
        """Check if user wishes to quit."""

        raise NotImplementedError

    @abc.abstractmethod
    def video_delay(self, elapsed_time: float, streamer: BaseStreamer) -> None:
        """Check if video frames were inferenced faster than the original video FPS and delay visualizer if so.

        Args:
            elapsed_time (float): Time spent on frame inference
            streamer (BaseStreamer): Streamer object
        """

        raise NotImplementedError


class Visualizer(IVisualizer):
    """Visualize the predicted output by drawing the annotations on the input image.

    Example:
        >>> predictions = inference_model.predict(frame)
        >>> annotation = prediction_converter.convert_to_annotation(predictions)
        >>> output = visualizer.draw(frame, annotation.shape, annotation.get_labels())
        >>> visualizer.show(output)
    """

    def __init__(
        self,
        window_name: Optional[str] = None,
        show_count: bool = False,
        is_one_label: bool = False,
        no_show: bool = False,
        delay: Optional[int] = None,
        output: Optional[str] = None,
    ) -> None:
        self.window_name = "Window" if window_name is None else window_name
        self.shape_drawer = ShapeDrawer(show_count, is_one_label)

        self.delay = delay
        self.no_show = no_show
        if delay is None:
            self.delay = 1
        self.output = output
        self.capture_window = None

        # 모니터의 절대 좌표를 가져옵니다.
        screen = screeninfo.get_monitors()[0]
        monitor_x = screen.x
        monitor_y = screen.y

        # 창을 표시할 위치를 지정합니다. 여기서는 모니터의 왼쪽 상단에 창을 표시하도록 설정합니다.
        window_x = monitor_x + 1200  # 원하는 X 좌표로 조정하세요.
        window_y = monitor_y + 300  # 원하는 Y 좌표로 조정하세요.
        
        # 창의 이름을 지정하고 창을 생성합니다.
        cv2.namedWindow(self.window_name, cv2.WINDOW_GUI_NORMAL)
        
        # 창의 크기를 조절합니다.
        cv2.resizeWindow(self.window_name, 960, 720)

        # 창을 지정된 위치로 이동시킵니다.
        cv2.moveWindow(self.window_name, window_x, window_y)


    def draw(
        self,
        image: np.ndarray,
        annotation: AnnotationSceneEntity,
        meta: Optional[dict] = None,
    ) -> np.ndarray:
        """Draw annotations on the image.

        Args:
            image: Input image
            annotation: Annotations to be drawn on the input image

        Returns:
            Output image with annotations.
        """

        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

        return self.shape_drawer.draw(image, annotation, labels=[])

    def show(self, image: np.ndarray) -> None:
        """Show result image and capture it.

        Args:
            image (np.ndarray): Image to be shown and captured.
        """

        if not self.no_show:
            cv2.imshow(self.window_name, image, cv2.WINDOW_GUI_NORMAL | cv2.WINDOW_AUTOSIZE)
            if self.output:
                cv2.imwrite(self.output, image)

    def is_quit(self) -> bool:
        """Check user wish to quit."""
        if self.no_show:
            return False

        return ord("q") == cv2.waitKey(self.delay)

    def video_delay(self, elapsed_time: float, streamer: BaseStreamer):
        """Check if video frames were inferenced faster than the original video FPS and delay visualizer if so.

        Args:
            elapsed_time (float): Time spent on frame inference
            streamer (BaseStreamer): Streamer object
        """
        if self.no_show:
            return
        if "VIDEO" in str(streamer.get_type()):
            orig_frame_time = 1 / streamer.fps()
            if elapsed_time < orig_frame_time:
                time.sleep(orig_frame_time - elapsed_time)
