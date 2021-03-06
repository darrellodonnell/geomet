import unittest

from geomet import wkb

EXP_WKB_FMT = '%(endian)s%(type)s%(data)s'


class WKBTestCase(unittest.TestCase):

    def test_unsupported_geom_type(self):
        geom = dict(type='Tetrahedron', coordinates=[])
        with self.assertRaises(ValueError) as ar:
            wkb.dumps(geom)
        self.assertEqual("Unsupported geometry type 'Tetrahedron'",
                         ar.exception.message)


class PointDumpsTestCase(unittest.TestCase):

    def test_2d(self):
        # Tests a typical 2D Point case:
        pt = dict(type='Point', coordinates=[0.0, 1.0])
        expected = EXP_WKB_FMT
        expected %= dict(
            endian='\x01',
            type='\x01\x00\x00\x00',
            data=('\x00\x00\x00\x00\x00\x00\x00\x00'
                  '\x00\x00\x00\x00\x00\x00\xf0?'),
        )
        self.assertEqual(expected, wkb.dumps(pt, big_endian=False))

    def test_3d(self):
        # Test for an XYZ Point:
        pt = dict(type='Point', coordinates=[0.0, 1.0, 2.0])
        # Note that a 3d point could either be a XYZ or XYM type.
        # For simplicity, we always assume XYZ.

        data = ('\x00\x00\x00\x00\x00\x00\x00\x00'
                '?\xf0\x00\x00\x00\x00\x00\x00'
                '@\x00\x00\x00\x00\x00\x00\x00')

        expected = EXP_WKB_FMT
        expected %= dict(
            endian='\x00',
            type='\x00\x00\x10\x01',
            data=data,
        )
        self.assertEqual(expected, wkb.dumps(pt, big_endian=True))

    def test_4d(self):
        # Test for an XYZM Point:
        pt = dict(type='Point', coordinates=[0.0, 1.0, 2.0, 4.0])

        data = ('\x00\x00\x00\x00\x00\x00\x00\x00'
                '\x00\x00\x00\x00\x00\x00\xf0?'
                '\x00\x00\x00\x00\x00\x00\x00@'
                '\x00\x00\x00\x00\x00\x00\x10@')

        expected = EXP_WKB_FMT
        expected %= dict(
            endian='\x01',
            type='\x01\x30\x00\x00',
            data=data,
        )
        self.assertEqual(expected, wkb.dumps(pt, big_endian=False))


class PointLoadsTestCase(unittest.TestCase):

    def test_2d(self):
        pt = (
            '\x01'  # little endian
            '\x01\x00\x00\x00'  # type
            '\x00\x00\x00\x00\x00\x00\x00\x00'  # 0.0
            '\x00\x00\x00\x00\x00\x00\xf0?'  # 1.0
        )

        expected = dict(type='Point', coordinates=[0.0, 1.0])
        self.assertEqual(expected, wkb.loads(pt))

    def test_z(self):
        pt = (
            '\x00'  # big endian
            '\x00\x00\x10\x01'  # type
            '@\x01\x99\x99\x99\x99\x99\x9a'
            '@\x11\x99\x99\x99\x99\x99\x9a'
            '@\x08\xcc\xcc\xcc\xcc\xcc\xcd'
        )
        expected = dict(type='Point', coordinates=[2.2, 4.4, 3.1])
        self.assertEqual(expected, wkb.loads(pt))

    def test_m(self):
        pt = (
            '\x00'  # big endian
            '\x00\x00\x20\x01'  # type
            '@\x01\x99\x99\x99\x99\x99\x9a'
            '@\x11\x99\x99\x99\x99\x99\x9a'
            '@\x08\xcc\xcc\xcc\xcc\xcc\xcd'
        )

        # The generated GeoJSON is treated as XYZM, sidestep the ambiguity
        # created by XYM and XYZ geometries. The default value for Z is set to
        # 0.0.
        expected = dict(type='Point', coordinates=[2.2, 4.4, 0.0, 3.1])
        self.assertEqual(expected, wkb.loads(pt))

    def test_zm(self):
        pt = (
            '\x00'  # big endian
            '\x00\x00\x30\x01'  # type
            '@\x01\x99\x99\x99\x99\x99\x9a'
            '@\x11\x99\x99\x99\x99\x99\x9a'
            '@\x08\xcc\xcc\xcc\xcc\xcc\xcd'
            '\x00\x00\x00\x00\x00\x00\x00\x00'
        )
        expected = dict(type='Point', coordinates=[2.2, 4.4, 3.1, 0.0])
        self.assertEqual(expected, wkb.loads(pt))


class LineStringDumpsTestCase(unittest.TestCase):

    def test_2d(self):
        linestring = dict(type='LineString', coordinates=[[2.2, 4.4],
                                                          [3.1, 5.1]])
        data = (
            '@\x01\x99\x99\x99\x99\x99\x9a'  # 2.2
            '@\x11\x99\x99\x99\x99\x99\x9a'  # 4.4
            '@\x08\xcc\xcc\xcc\xcc\xcc\xcd'  # 3.1
            '@\x14ffffff'                    # 5.1
        )
        expected = EXP_WKB_FMT
        expected %= dict(
            endian='\x00',
            type='\x00\x00\x00\x02',
            data=data,
        )
        self.assertEqual(expected, wkb.dumps(linestring))

    def test_3d(self):
        linestring = dict(type='LineString', coordinates=[[2.2, 4.4, 10.0],
                                                          [3.1, 5.1, 20.0]])
        data = (
            '\x9a\x99\x99\x99\x99\x99\x01@'  # 2.2
            '\x9a\x99\x99\x99\x99\x99\x11@'  # 4.4
            '\x00\x00\x00\x00\x00\x00$@'     # 10.0
            '\xcd\xcc\xcc\xcc\xcc\xcc\x08@'  # 3.1
            'ffffff\x14@'                    # 5.1
            '\x00\x00\x00\x00\x00\x004@'     # 20.0
        )
        expected = EXP_WKB_FMT
        expected %= dict(
            endian='\x01',
            type='\x02\x10\x00\x00',
            data=data
        )
        self.assertEqual(expected, wkb.dumps(linestring, big_endian=False))

    def test_4d(self):
        linestring = dict(type='LineString',
                          coordinates=[[2.2, -4.4, -10.0, 0.1],
                                       [-3.1, 5.1, 20.0, -0.9]])

        data = (
            '@\x01\x99\x99\x99\x99\x99\x9a'     # 2.2
            '\xc0\x11\x99\x99\x99\x99\x99\x9a'  # -4.4
            '\xc0$\x00\x00\x00\x00\x00\x00'     # -10.0
            '?\xb9\x99\x99\x99\x99\x99\x9a'     # 0.1
            '\xc0\x08\xcc\xcc\xcc\xcc\xcc\xcd'  # -3.1
            '@\x14ffffff'                       # 5.1
            '@4\x00\x00\x00\x00\x00\x00'        # 20.0
            '\xbf\xec\xcc\xcc\xcc\xcc\xcc\xcd'  # -0.9
        )
        expected = EXP_WKB_FMT
        expected %= dict(
            endian='\x00',
            type='\x00\x00\x30\x02',
            data=data,
        )
        self.assertEqual(expected, wkb.dumps(linestring))


class LineStringLoadsTestCase(unittest.TestCase):

    def test_2d(self):
        linestring = (
            '\x00'  # big endian
            '\x00\x00\x00\x02'
            '@\x01\x99\x99\x99\x99\x99\x9a'  # 2.2
            '@\x11\x99\x99\x99\x99\x99\x9a'  # 4.4
            '@\x08\xcc\xcc\xcc\xcc\xcc\xcd'  # 3.1
            '@\x14ffffff'                    # 5.1
        )
        expected = dict(type='LineString', coordinates=[[2.2, 4.4],
                                                        [3.1, 5.1]])

        self.assertEqual(expected, wkb.loads(linestring))

    def test_z(self):
        linestring = (
            '\x01'  # little endian
            '\x02\x10\x00\x00'
            '\x9a\x99\x99\x99\x99\x99\x01@'  # 2.2
            '\x9a\x99\x99\x99\x99\x99\x11@'  # 4.4
            '\x00\x00\x00\x00\x00\x00$@'     # 10.0
            '\xcd\xcc\xcc\xcc\xcc\xcc\x08@'  # 3.1
            'ffffff\x14@'                    # 5.1
            '\x00\x00\x00\x00\x00\x004@'     # 20.0
        )
        expected = dict(type='LineString', coordinates=[[2.2, 4.4, 10.0],
                                                        [3.1, 5.1, 20.0]])

        self.assertEqual(expected, wkb.loads(linestring))

    def test_m(self):
        linestring = (
            '\x01'  # little endian
            '\x02\x20\x00\x00'
            '\x9a\x99\x99\x99\x99\x99\x01@'  # 2.2
            '\x9a\x99\x99\x99\x99\x99\x11@'  # 4.4
            '\x00\x00\x00\x00\x00\x00$@'     # 10.0
            '\xcd\xcc\xcc\xcc\xcc\xcc\x08@'  # 3.1
            'ffffff\x14@'                    # 5.1
            '\x00\x00\x00\x00\x00\x004@'     # 20.0
        )
        expected = dict(type='LineString', coordinates=[[2.2, 4.4, 0.0, 10.0],
                                                        [3.1, 5.1, 0.0, 20.0]])

        self.assertEqual(expected, wkb.loads(linestring))

    def test_zm(self):
        linestring = (
            '\x00'  # big endian
            '\x00\x00\x30\x02'
            '@\x01\x99\x99\x99\x99\x99\x9a'     # 2.2
            '\xc0\x11\x99\x99\x99\x99\x99\x9a'  # -4.4
            '\xc0$\x00\x00\x00\x00\x00\x00'     # -10.0
            '?\xb9\x99\x99\x99\x99\x99\x9a'     # 0.1
            '\xc0\x08\xcc\xcc\xcc\xcc\xcc\xcd'  # -3.1
            '@\x14ffffff'                       # 5.1
            '@4\x00\x00\x00\x00\x00\x00'        # 20.0
            '\xbf\xec\xcc\xcc\xcc\xcc\xcc\xcd'  # -0.9
        )
        expected = dict(type='LineString',
                        coordinates=[[2.2, -4.4, -10.0, 0.1],
                                     [-3.1, 5.1, 20.0, -0.9]])

        self.assertEqual(expected, wkb.loads(linestring))
