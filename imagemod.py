from PIL import Image
from colorsys import rgb_to_hsv, hsv_to_rgb
import numpy as np
import logging


VERSION = (0, 1, 1, 0)

def get_version():
    return ".".join([str(x) for x in VERSION])

LOG = logging.getLogger(__name__)


def _mod_pixel_cached(modder, r, g, b, a):
    color = (r, g, b, a)
    newcolor = modder._mods.get(color, None)
    if not newcolor:
        newcolor = modder.mod_pixel(r, g, b, a)
        modder._mods[color] = newcolor
    return newcolor


_mod_pixels = np.vectorize(_mod_pixel_cached, excluded=["modder"])


class ImageModder(object):
    position_idependant = True

    @classmethod
    def modimage(cls, img):
        cls(img)
        return cls.get_mod()

    def __init__(self, img):
        self.image = img.mode == "RGBA" and img or img.convert("RGBA")
        self._mods = {}

    def _pixel_count(self):
        return self.image.size[0] * self.image.size[1]
    pixel_count = property(_pixel_count)

    def get_mod(self):
        self.analyze()
        self.draw()
        return self.mod_image

    mod_pixel_cached = _mod_pixel_cached

    def mod_pixels(self, r, g, b, a):
        return np.array(_mod_pixels(self, r, g, b, a))

    def mod_pixel(self, r, g, b, a):
        h, s, v = rgb_to_hsv(r, g, b)
        nh, ns, nv, na = self.mod_pixel_hsv(h, s, v, a)
        nr, ng, nb = hsv_to_rgb(nh, ns, nv)
        return (nr, ng, nb, na)

    def mod_pixel_hsv(self, h, s, v, a):
        raise NotImplementedError()

    def analyze(self):
        pass

    def draw(self):
        arr = np.asarray(self.image).astype("float")
        arr = np.rollaxis(arr, -1)
        result = self.mod_pixels(*arr)
        result = np.rollaxis(result, 0, len(result.shape)).astype("uint8")
        self.mod_image = Image.fromarray(result, "RGBA")
