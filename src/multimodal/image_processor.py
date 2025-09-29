"""
Image processing for UAE documents
"""

import cv2
import numpy as np
from PIL import Image
import pytesseract
import io
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class ImageProcessor:
    """Advanced image processing for UAE documents"""

    def __init__(self):
        self.ocr_config = r'--oem 3 --psm 6 -l eng+ara'

    async def preprocess_id_document(self, image_data: bytes) -> bytes:
        """Preprocess Emirates ID for OCR"""
        try:
            # Convert bytes to numpy array
            nparr = np.frombuffer(image_data, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

            # Resize if too large
            height, width = image.shape[:2]
            if width > 1200:
                scale = 1200 / width
                new_width = int(width * scale)
                new_height = int(height * scale)
                image = cv2.resize(image, (new_width, new_height))

            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

            # Apply CLAHE for contrast
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
            enhanced = clahe.apply(gray)

            # Noise reduction
            denoised = cv2.bilateralFilter(enhanced, 9, 75, 75)

            # Convert back to bytes
            _, buffer = cv2.imencode('.png', denoised)
            return buffer.tobytes()

        except Exception as e:
            logger.error(f"Image preprocessing failed: {e}")
            return image_data

    async def extract_text_ocr(self, image_data: bytes) -> str:
        """Extract text using OCR"""
        try:
            image = Image.open(io.BytesIO(image_data))
            text = pytesseract.image_to_string(image, config=self.ocr_config)
            return text.strip()
        except Exception as e:
            logger.error(f"OCR extraction failed: {e}")
            return ""

    async def validate_emirates_id_image(self, image_data: bytes) -> Dict[str, Any]:
        """Validate Emirates ID image quality"""
        try:
            nparr = np.frombuffer(image_data, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

            # Calculate quality metrics
            blur_score = cv2.Laplacian(gray, cv2.CV_64F).var()
            brightness = np.mean(gray)
            contrast = gray.std()

            # Quality assessment
            quality_score = 0
            if blur_score > 100:
                quality_score += 30
            if 50 < brightness < 200:
                quality_score += 35
            if contrast > 30:
                quality_score += 35

            return {
                "quality_score": quality_score,
                "blur_score": blur_score,
                "brightness": brightness,
                "contrast": contrast,
                "is_acceptable": quality_score >= 70
            }

        except Exception as e:
            logger.error(f"Image validation failed: {e}")
            return {"quality_score": 0, "is_acceptable": False}
