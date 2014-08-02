from unittest2 import TestCase
from pykfs import image_filter
from mock import Mock, patch
import numpy as np
import logging


LOG = logging.getLogger(__name__)


class DummyImageFilter(image_filter.ImageFilter):
    analyze = Mock()

    def __init__(self, *args, **kwargs):
        self.filter_pixel_calls = {}
        super(DummyImageFilter, self).__init__(*args, **kwargs)

    def filter_pixel(self, r, g, b, a):
        color = (r, g, b, a)
        self.filter_pixel_calls[color] = self.filter_pixel_calls.get(color, 0) + 1
        return (r, g, b, a)


class InvertImageFilter(image_filter.ImageFilter):

    def __init__(self, maxnum, *args, **kwargs):
        self.filter_pixel_calls = {}
        self.maxnum = maxnum
        super(InvertImageFilter, self).__init__(*args, **kwargs)

    def filter_pixel(self, r, g, b, a):
        color = (r, g, b, a)
        newcolor = (self.maxnum - r, self.maxnum - g, self.maxnum - b, self.maxnum - a)
        count, _ = self.filter_pixel_calls.get(color, (0, color))
        self.filter_pixel_calls[color] = (count+1, newcolor)
        return newcolor


image_colors = []
inverted_colors = []
rotating_colors = []
for i in range(10):
    image_colors.append([])
    inverted_colors.append([])
    rotating_colors.append([])
    for j in range(10):
        value = 10 * i + 1 * j
        image_colors[i].append([value for _ in range(4)])
        inverted_colors[i].append([99-value for _ in range(4)])
        rotating_colors[i].append([value%7 for _ in range(4)])


dummy_array = np.array(image_colors, dtype=np.uint8)
rotating_asarray = Mock()
rotating_asarray.return_value = np.array(rotating_colors, dtype=np.uint8)


@patch('pykfs.image_filter.np.asarray')
class TestImageFilter(TestCase):

    def setUp(self):
        self.dummy_img = Mock()
        self.dummy_img.mode = "RGBA"

    def test_does_nothing(self, mock_asarray):
        mock_asarray.return_value = np.array(image_colors, dtype=np.uint8)
        f = DummyImageFilter(self.dummy_img)
        new_image = f.get_filtered()
        self.assertIsNotNone(new_image)
        self.assertEqual(new_image, f.filter_image)
        mock_asarray.assert_called_with(self.dummy_img)
        self.assertEqual(new_image.mode, "RGBA")
        self.assertEqual(100, len(f.filter_pixel_calls))
        for i in range(100):
            self.assertEqual(1, f.filter_pixel_calls[(i, i, i, i)])

    def test_inverts_pixels(self, mock_asarray):
        mock_asarray.return_value = np.array(image_colors, dtype=np.uint8)
        f = InvertImageFilter(99, self.dummy_img)
        new_image = f.get_filtered()
        self.assertIsNotNone(new_image)
        self.assertEqual(new_image, f.filter_image)
        mock_asarray.assert_called_with(self.dummy_img)
        self.assertEqual(new_image.mode, "RGBA")
        self.assertEqual(100, len(f.filter_pixel_calls))
        for i in range(100):
            count, color = f.filter_pixel_calls[(i, i, i, i)]
            self.assertEqual(1, count)
            for x in color:
                self.assertEqual(float(99 - i), x)

    def test_caches_pixels(self, mock_asarray):
        mock_asarray.return_value = np.array(rotating_colors, dtype=np.uint8)
        f = InvertImageFilter(6, self.dummy_img)
        new_image = f.get_filtered()
        self.assertIsNotNone(new_image)
        self.assertEqual(new_image, f.filter_image)
        mock_asarray.assert_called_with(self.dummy_img)
        self.assertEqual(new_image.mode, "RGBA")
        self.assertEqual(7, len(f.filter_pixel_calls))
        for i in range(7):
            count, color = f.filter_pixel_calls[(i, i, i, i)]
            self.assertEqual(1, count)
            for x in color:
                self.assertEqual(float(6 - i), x)
