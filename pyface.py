import sys
import os
import _io
from collections import namedtuple
from PIL import Image

class face(object):
    Skin = namedtuple('Skin', 'id skin region x y')

    def __init__(self, path_or_image):
        if isinstance(path_or_image, Image.Image):
            self.image = path_or_image

        elif isinstance(path_or_image, str):
            self.image = Image.open(path_or_image)

        bands = self.image.getbands()

        if len(bands) == 1:
            new_img = Image.new('RGB', self.image.size)
            new_img.paste(self.image)
            f = self.image.filename
            self.image = new_img
            self.image.filename = f

        self.Skin_map = []
        self.detected_regions = []
        self.merge_regions = []
        self.Skin_regions = []
        self.last_from, self.last_to = -1, -1    #这个是什么意思没看懂。。。
        self.result = None
        self.message = None
        self.width, self.heigh = self.image.size
        self.total_pixels = self.width * self.heigh

    def resize(self, percent = 0.75, max_width = 1000, max_heigh = 1000):
        self.new_width = percent * self.width
        self.new_heigh = percent * self.heigh
        ret = 0

        if self.width > max_width and self.heigh > max_heigh:
            filename = self.image.filename
            self.image = self.image.resize((self.new_width, self.new_heigh), Image.LANCZOS)
            self.image.filename = filename
            self.width, self.heigh = self.image.size
            self.total_pixels = self.width * self.heigh
            ret = 1
        return ret

    def parse(self):
        if self.result is not None:
            return self

        pixels = self.image.load()

        for y in range(self.heighth):
            for x in range(self.width):
                r = pixels[x, y][0]
                g = pixels[x, y][1]
                b = pixels[x, y][2]

                IsSkin = True if self._classify_skin(r, g, b) else False
                _id = x + y * self.width + 1
                self.Skin_map.append(self.Skin(_id, IsSkin, None, x, y))

                if not IsSkin:
                    continue

                check = [_id - 2,                # 左边像素
                         _id - self.width - 2,    # 左上角像素
                         _id - self.width - 1,    # 上方像素
                         _id - self.width        # 右上角像素
                        ]

                region = -1

                for index in check:
                    try:
                        self.Skin_map[index]

                    except IndexError:
                        break

                    if self.Skin_map[index].skin:
                        if (self.Skin_map[index].region != None and
                            region != None and region != -1 and
                            self.Skin_map[index].region != region and
                            self.last_from != region and
                            self.last_to != self.Skin_map[index].region):

                            self._add_merge(region, self.Skin_map[index].region)
                        region = self.Skin_map[index].region

                if region == -1:
                    _skin = self.Skin_map[_id - 1]._replace(region = len(self.detected_regions))
                    self.Skin_map[_id - 1] = _skin
                    self.detected_regions.append([self.Skin_map[_id - 1]])
                elif region != None:
                    _skin = self.Skin_map[_id - 1]._replace(region = region)
                    self.detected_regions[region].append(self.Skin_map[_id - 1])

                self._merge(self.detected_regions, self.merge_regions)
                self._analyse_regions()
                return self

    def _classify_skin(self, r, g, b):
        rgb_classifier = r > 95 and \
            g > 40 and g < 100 and \
            b > 20 and \
            max([r, g, b]) - min([r, g, b]) > 15 and \
            abs(r - g) > 15 and \
            r > g and \
            r > b

        nr, ng, nb = self._to_normalized(r, g, b)
        norm_rgb_classifier = nr / ng > 1.185 and \
            float(r * b) / ((r + g + b) ** 2) > 0.107 and \
            float(r * g) / ((r + g + b) ** 2) > 0.112

        h, s, v = self._to_hsv(r, g, b)
        hsv_classifier = h > 0 and \
            h < 35 and \
            s > 0.23 and \
            s < 0.68

        y, cb, cr = self._to_ycbcr(r, g, b)
        ycbcr_classifier = 97.5 <= cb <= 142.5 and 134 <= cr <= 176

        return ycbcr_classifier

    def _to_normalized(self, r, g, b):
        if r == 0:
            r = 0.0001

        if g == 0:
            g = 0.0001

        if b == 0:
            b = 0.0001

        _sum = float(r + g + b)

        return [r / _sum, g / _sum, b / _sum]

    def _to_ycbcr(self, r, g, b):
        # http://stackoverflow.com/questions/19459831/rgb-to-ycbcr-conversion-problems
        y = 0.299 * r + 0.587 * g + 0.114 * b
        cb = 128 - 0.168736 * r - 0.331364 * g + 0.5 * b
        cr = 128 + 0.5 * r - 0.418688 * g - 0.081312 * b

        return y, cb, cr

    def _to_hsv(self, r, g, b):
        h = 0
        _sum = float(r + g + b)
        _max = float(max([r, g, b]))
        _min = float(min([r, g, b]))
        diff = _max - _min
        if _sum == 0:
            _sum = 0.0001

        if _max == r:
            if diff == 0:
                h = sys.maxsize
            else:
                h = (g - b) / diff

        elif _max == g:
            h = 2 + ((g - r) / diff)

        else:
            h = 4 + ((r - g) / diff)

        h *= 60
        if h < 0:
            h += 360

        return [h, 1.0 - (3.0 * (_min / _sum)), (1.0 / 3.0) * _max]

    def _add_merge(self, _from, _to):
        self.last_from = _from
        self.last_to = _to
        from_index = -1
        to_index = -1

        for index, region in enumerate(self.merge_regions):
            for r_index in region:
                if r_index == _from:
                    from_index = index
                if r_index == _to:
                    to_index = index

        if from_index != -1 and to_index != -1:
            if from_index != to_index:
                self.merge_regions[from_index].extend(self.merge_regions[to_index])
                del(self.merge_regions[to_index])

            return None

        if from_index == -1 and to_index == -1:
            self.merge_regions.append([_from, _to])
            return None

        if from_index != -1 and to_index == -1:
            self.merge_regions[from_index].append(_to)
            return None

        if from_index == -1 and to_index != -1:
            self.merge_regions[to_index].append(_from)
            return None

    def _merge(self, detected_regions, merge_regions):
        new_detected_regions = []
        for index, region in enumerate(merge_regions):
            try:
                new_detected_regions[index]
            except IndexError:
                new_detected_regions.append([])

            for r_index in region:
                
