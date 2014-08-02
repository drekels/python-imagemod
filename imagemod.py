from PIL import Image
from colorsys import rgb_to_hsv, hsv_to_rgb
import numpy as np
import logging


VERSION = (0, 1, 1, 0)
LOG = logging.getLogger(__name__)


def _filter_pixel_cached(image_filter, r, g, b, a):
    color = (r, g, b, a)
    newcolor = image_filter._filters.get(color, None)
    if not newcolor:
        newcolor = image_filter.filter_pixel(r, g, b, a)
        image_filter._filters[color] = newcolor
    return newcolor


_filter_pixels = np.vectorize(_filter_pixel_cached, excluded=["image_filter"])


class ImageFilter(object):

    @classmethod
    def filter_image(cls, img):
        cls(img)
        return cls.get_filtered()

    def __init__(self, img):
        self.image = img.mode == "RGBA" and img or img.convert("RGBA")
        self._filters = {}

    def _pixel_count(self):
        return self.image.size[0] * self.image.size[1]
    pixel_count = property(_pixel_count)

    def get_filtered(self):
        self.analyze()
        self.draw()
        return self.filter_image

    filter_pixel_cached = _filter_pixel_cached

    def filter_pixels(self, r, g, b, a):
        return np.array(_filter_pixels(self, r, g, b, a))

    def filter_pixel(self, r, g, b, a):
        h, s, v = rgb_to_hsv(r, g, b)
        nh, ns, nv, na = self.filter_pixel_hsv(h, s, v, a)
        nr, ng, nb = hsv_to_rgb(nh, ns, nv)
        return (nr, ng, nb, na)

    def filter_pixel_hsv(self, h, s, v, a):
        raise NotImplementedError()

    def analyze(self):
        pass

    def draw(self):
        arr = np.asarray(self.image).astype("float")
        arr = np.rollaxis(arr, -1)
        result = self.filter_pixels(*arr)
        result = np.rollaxis(result, 0, len(result.shape)).astype("uint8")
        self.filter_image = Image.fromarray(result, "RGBA")
