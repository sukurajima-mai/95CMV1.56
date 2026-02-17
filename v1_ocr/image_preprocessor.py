# -*- coding: utf-8 -*-
"""
OCR图像预处理模块
提供多种图像预处理方法，提高OCR识别准确率
"""

import cv2
import numpy as np
from typing import Tuple, Optional


class ImagePreprocessor:
    """图像预处理器"""

    def __init__(self):
        self.methods = {
            'grayscale': self.to_grayscale,
            'binary': self.to_binary,
            'denoise': self.denoise,
            'enhance': self.enhance_contrast,
            'sharpen': self.sharpen,
            'morphology': self.morphology_operation
        }

    def to_grayscale(self, image: np.ndarray) -> np.ndarray:
        """
        转换为灰度图像

        Args:
            image: 输入图像

        Returns:
            灰度图像
        """
        if len(image.shape) == 3:
            return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        return image

    def to_binary(self, image: np.ndarray, method: str = 'otsu') -> np.ndarray:
        """
        二值化处理

        Args:
            image: 输入图像
            method: 二值化方法 ('otsu', 'adaptive', 'simple')

        Returns:
            二值化图像
        """
        # 先转换为灰度图
        gray = self.to_grayscale(image)

        if method == 'otsu':
            # Otsu二值化
            _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        elif method == 'adaptive':
            # 自适应二值化
            binary = cv2.adaptiveThreshold(
                gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY, 11, 2
            )
        else:
            # 简单二值化
            _, binary = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)

        return binary

    def denoise(self, image: np.ndarray, method: str = 'gaussian') -> np.ndarray:
        """
        降噪处理

        Args:
            image: 输入图像
            method: 降噪方法 ('gaussian', 'median', 'bilateral', 'nlm')

        Returns:
            降噪后的图像
        """
        if method == 'gaussian':
            # 高斯滤波
            return cv2.GaussianBlur(image, (3, 3), 0)
        elif method == 'median':
            # 中值滤波
            return cv2.medianBlur(image, 3)
        elif method == 'bilateral':
            # 双边滤波
            return cv2.bilateralFilter(image, 9, 75, 75)
        elif method == 'nlm':
            # 非局部均值降噪
            return cv2.fastNlMeansDenoisingColored(image, None, 10, 10, 7, 21)
        else:
            return image

    def enhance_contrast(self, image: np.ndarray, method: str = 'clahe') -> np.ndarray:
        """
        增强对比度

        Args:
            image: 输入图像
            method: 增强方法 ('clahe', 'histogram', 'gamma')

        Returns:
            增强后的图像
        """
        if method == 'clahe':
            # CLAHE (对比度受限的自适应直方图均衡化)
            gray = self.to_grayscale(image)
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            return clahe.apply(gray)
        elif method == 'histogram':
            # 直方图均衡化
            gray = self.to_grayscale(image)
            return cv2.equalizeHist(gray)
        elif method == 'gamma':
            # Gamma校正
            gray = self.to_grayscale(image)
            gamma = 1.5
            inv_gamma = 1.0 / gamma
            table = np.array([((i / 255.0) ** inv_gamma) * 255
                             for i in np.arange(0, 256)]).astype('uint8')
            return cv2.LUT(gray, table)
        else:
            return image

    def sharpen(self, image: np.ndarray) -> np.ndarray:
        """
        锐化处理

        Args:
            image: 输入图像

        Returns:
            锐化后的图像
        """
        # 锐化核
        kernel = np.array([[-1, -1, -1],
                          [-1,  9, -1],
                          [-1, -1, -1]])

        return cv2.filter2D(image, -1, kernel)

    def morphology_operation(self, image: np.ndarray, operation: str = 'close') -> np.ndarray:
        """
        形态学操作

        Args:
            image: 输入图像
            operation: 操作类型 ('dilate', 'erode', 'open', 'close')

        Returns:
            处理后的图像
        """
        # 先二值化
        binary = self.to_binary(image, method='otsu')

        # 定义核
        kernel = np.ones((3, 3), np.uint8)

        if operation == 'dilate':
            return cv2.dilate(binary, kernel, iterations=1)
        elif operation == 'erode':
            return cv2.erode(binary, kernel, iterations=1)
        elif operation == 'open':
            return cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)
        elif operation == 'close':
            return cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
        else:
            return binary

    def preprocess_for_ocr(self, image: np.ndarray, steps: list = None) -> np.ndarray:
        """
        为OCR准备图像（组合多种预处理方法）

        Args:
            image: 输入图像
            steps: 预处理步骤列表，例如 ['grayscale', 'denoise', 'binary']

        Returns:
            预处理后的图像
        """
        if steps is None:
            # 默认预处理流程
            steps = ['grayscale', 'denoise', 'enhance', 'binary']

        result = image.copy()

        for step in steps:
            if step in self.methods:
                result = self.methods[step](result)

        return result

    def auto_preprocess(self, image: np.ndarray) -> np.ndarray:
        """
        自动选择最佳预处理方法

        Args:
            image: 输入图像

        Returns:
            预处理后的图像
        """
        # 分析图像特征
        gray = self.to_grayscale(image)

        # 计算图像对比度
        contrast = gray.std()

        # 计算图像亮度
        brightness = gray.mean()

        # 根据图像特征选择预处理方法
        if contrast < 50:
            # 低对比度图像，增强对比度
            result = self.enhance_contrast(image, method='clahe')
        elif brightness < 100:
            # 暗图像，提高亮度
            result = self.enhance_contrast(image, method='gamma')
        else:
            # 正常图像，使用标准预处理
            result = self.preprocess_for_ocr(image, steps=['grayscale', 'denoise', 'binary'])

        return result


def test_preprocessor():
    """测试预处理器"""
    import os

    # 创建预处理器
    preprocessor = ImagePreprocessor()

    # 测试图像路径
    test_image_path = "script/debug/01_detection_region.jpg"

    if os.path.exists(test_image_path):
        # 读取测试图像
        image = cv2.imread(test_image_path)

        if image is not None:
            print("测试图像预处理...")

            # 测试各种预处理方法
            methods = ['grayscale', 'binary', 'denoise', 'enhance', 'sharpen']

            for method in methods:
                result = preprocessor.methods[method](image)
                output_path = f"script/debug/preprocess_{method}.jpg"
                cv2.imwrite(output_path, result)
                print(f"✓ {method}: {output_path}")

            # 测试自动预处理
            auto_result = preprocessor.auto_preprocess(image)
            cv2.imwrite("script/debug/preprocess_auto.jpg", auto_result)
            print("✓ auto: script/debug/preprocess_auto.jpg")

            print("\n预处理测试完成！")
        else:
            print("❌ 无法读取测试图像")
    else:
        print(f"❌ 测试图像不存在: {test_image_path}")


if __name__ == '__main__':
    test_preprocessor()
