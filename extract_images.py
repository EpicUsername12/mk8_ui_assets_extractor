import oead
import os
import struct
from PIL import Image
import time
import sys
import addrlib

os.makedirs('assets/icons/', exist_ok=True)

formats = {
    0x00000000: 'GX2_SURFACE_FORMAT_INVALID',
    0x0000001a: 'GX2_SURFACE_FORMAT_TCS_R8_G8_B8_A8_UNORM',
    0x0000041a: 'GX2_SURFACE_FORMAT_TCS_R8_G8_B8_A8_SRGB',
    0x00000019: 'GX2_SURFACE_FORMAT_TCS_R10_G10_B10_A2_UNORM',
    0x00000008: 'GX2_SURFACE_FORMAT_TCS_R5_G6_B5_UNORM',
    0x0000000a: 'GX2_SURFACE_FORMAT_TC_R5_G5_B5_A1_UNORM',
    0x0000000b: 'GX2_SURFACE_FORMAT_TC_R4_G4_B4_A4_UNORM',
    0x00000001: 'GX2_SURFACE_FORMAT_TC_R8_UNORM',
    0x00000007: 'GX2_SURFACE_FORMAT_TC_R8_G8_UNORM',
    0x00000002: 'GX2_SURFACE_FORMAT_TC_R4_G4_UNORM',
    0x00000031: 'GX2_SURFACE_FORMAT_T_BC1_UNORM',
    0x00000431: 'GX2_SURFACE_FORMAT_T_BC1_SRGB',
    0x00000032: 'GX2_SURFACE_FORMAT_T_BC2_UNORM',
    0x00000432: 'GX2_SURFACE_FORMAT_T_BC2_SRGB',
    0x00000033: 'GX2_SURFACE_FORMAT_T_BC3_UNORM',
    0x00000433: 'GX2_SURFACE_FORMAT_T_BC3_SRGB',
    0x00000034: 'GX2_SURFACE_FORMAT_T_BC4_UNORM',
    0x00000035: 'GX2_SURFACE_FORMAT_T_BC5_UNORM',
}

BCn_formats = [0x31, 0x431, 0x32, 0x432, 0x33, 0x433, 0x34, 0x35]


class FLIMData:
    pass


class FLIMHeader(struct.Struct):
    def __init__(self, bom):
        super().__init__(bom + '4s2H2IH2x')

    def data(self, data, pos):
        (self.magic,
         self.endian,
         self.size_,
         self.version,
         self.fileSize,
         self.numBlocks) = self.unpack_from(data, pos)


class imagHeader(struct.Struct):
    def __init__(self, bom):
        super().__init__(bom + '4sI3H2BI')

    def data(self, data, pos):
        (self.magic,
         self.infoSize,
         self.width,
         self.height,
         self.alignment,
         self.format_,
         self.swizzle_tileMode,
         self.imageSize) = self.unpack_from(data, pos)


def computeSwizzleTileMode(tileModeAndSwizzlePattern):
    if isinstance(tileModeAndSwizzlePattern, int):
        tileMode = tileModeAndSwizzlePattern & 0x1F
        swizzlePattern = ((tileModeAndSwizzlePattern >> 5) & 7) << 8
        if tileMode not in [1, 2, 3, 16]:
            swizzlePattern |= 0xd0000

        return swizzlePattern, tileMode

    return tileModeAndSwizzlePattern[0] << 5 | tileModeAndSwizzlePattern[1]  # swizzlePattern << 5 | tileMode


def readFLIM(f):
    flim = FLIMData()

    pos = len(f) - 0x28

    if f[pos + 4:pos + 6] == b'\xFF\xFE':
        bom = '<'

    elif f[pos + 4:pos + 6] == b'\xFE\xFF':
        bom = '>'

    header = FLIMHeader(bom)
    header.data(f, pos)

    if header.magic != b'FLIM':
        raise ValueError("Invalid file header!")

    pos += header.size

    info = imagHeader(bom)
    info.data(f, pos)

    if info.magic != b'imag':
        raise ValueError("Invalid imag header!")

    flim.width = info.width
    flim.height = info.height

    if info.format_ == 0x00:
        flim.format = 0x01
        flim.compSel = [0, 0, 0, 5]

    elif info.format_ == 0x01:
        flim.format = 0x01
        flim.compSel = [5, 5, 5, 0]

    elif info.format_ == 0x02:
        flim.format = 0x02
        flim.compSel = [0, 0, 0, 1]

    elif info.format_ == 0x03:
        flim.format = 0x07
        flim.compSel = [0, 0, 0, 1]

    elif info.format_ in [0x05, 0x19]:
        flim.format = 0x08
        flim.compSel = [2, 1, 0, 5]

    elif info.format_ == 0x06:
        flim.format = 0x1a
        flim.compSel = [0, 1, 2, 5]

    elif info.format_ == 0x07:
        flim.format = 0x0a
        flim.compSel = [0, 1, 2, 3]

    elif info.format_ == 0x08:
        flim.format = 0x0b
        flim.compSel = [2, 1, 0, 3]

    elif info.format_ == 0x09:
        flim.format = 0x1a
        flim.compSel = [0, 1, 2, 3]

    elif info.format_ == 0x0a:
        flim.format = 0x31
        flim.format_ = "ETC1"
        flim.compSel = [0, 1, 2, 3]

    elif info.format_ == 0x0C:
        flim.format = 0x31
        flim.format_ = "BC1"
        flim.compSel = [0, 1, 2, 3]

    elif info.format_ == 0x0D:
        flim.format = 0x32
        flim.compSel = [0, 1, 2, 3]

    elif info.format_ == 0x0E:
        flim.format = 0x33
        flim.compSel = [0, 1, 2, 3]

    elif info.format_ in [0x0F, 0x10]:
        flim.format = 0x34
        flim.compSel = [0, 1, 2, 3]

    elif info.format_ == 0x11:
        flim.format = 0x35
        flim.compSel = [0, 1, 2, 3]

    elif info.format_ == 0x14:
        flim.format = 0x41a
        flim.compSel = [0, 1, 2, 3]

    elif info.format_ == 0x15:
        flim.format = 0x431
        flim.format_ = "BC1"
        flim.compSel = [0, 1, 2, 3]

    elif info.format_ == 0x16:
        flim.format = 0x432
        flim.compSel = [0, 1, 2, 3]

    elif info.format_ == 0x17:
        flim.format = 0x433
        flim.compSel = [0, 1, 2, 3]

    elif info.format_ == 0x18:
        flim.format = 0x19
        flim.compSel = [0, 1, 2, 3]

    else:
        print("")
        print("Unsupported texture format: " + hex(info.format_))
        print("Exiting in 5 seconds...")
        time.sleep(5)
        sys.exit(1)

    flim.imageSize = info.imageSize

    # Calculate swizzle and tileMode
    flim.swizzle, flim.tileMode = computeSwizzleTileMode(info.swizzle_tileMode)
    if not 1 <= flim.tileMode <= 16:
        print("")
        print("Invalid tileMode!")
        print("Exiting in 5 seconds...")
        time.sleep(5)
        sys.exit(1)

    flim.alignment = info.alignment

    surfOut = addrlib.getSurfaceInfo(flim.format, flim.width, flim.height, 1, 1, flim.tileMode, 0, 0)

    tilingDepth = surfOut.depth
    if surfOut.tileMode == 3:
        tilingDepth //= 4

    if tilingDepth != 1:
        print("")
        print("Unsupported depth!")
        print("Exiting in 5 seconds...")
        time.sleep(5)
        sys.exit(1)

    flim.pitch = surfOut.pitch

    flim.data = f[:info.imageSize]

    flim.surfOut = surfOut

    if flim.format in BCn_formats:
        flim.realSize = ((flim.width + 3) >> 2) * ((flim.height + 3) >> 2) * (
            addrlib.surfaceGetBitsPerPixel(flim.format) // 8)

    else:
        flim.realSize = flim.width * flim.height * (addrlib.surfaceGetBitsPerPixel(flim.format) // 8)

    return flim


def get_deswizzled_data(flim):
    if flim.format == 0x01:
        format_ = 61

    elif flim.format == 0x02:
        format_ = 112

    elif flim.format == 0x07:
        format_ = 49

    elif flim.format == 0x08:
        format_ = 85

    elif flim.format == 0x0a:
        format_ = 86

    elif flim.format == 0x0b:
        format_ = 115

    elif flim.format in [0x1a, 0x41a]:
        format_ = 28

    elif flim.format == 0x19:
        format_ = 24

    elif flim.format in [0x31, 0x431]:
        format_ = flim.format_

    elif flim.format in [0x32, 0x432]:
        format_ = "BC2"

    elif flim.format in [0x33, 0x433]:
        format_ = "BC3"

    elif flim.format == 0x34:
        format_ = "BC4U"

    elif flim.format == 0x35:
        format_ = "BC5U"

    result = addrlib.deswizzle(flim.width, flim.height, 1, flim.format, 0, 1, flim.surfOut.tileMode,
                               flim.swizzle, flim.pitch, flim.surfOut.bpp, 0, 0, flim.data)

    return result


def dxt5_decode_alphablock(pixdata, blksrc, i, j):
    alpha0 = pixdata[blksrc]
    alpha1 = pixdata[blksrc + 1]

    bits = (pixdata[blksrc] | (pixdata[blksrc + 1] << 8) |
            (pixdata[blksrc + 2] << 16) | (pixdata[blksrc + 3] << 24) |
            (pixdata[blksrc + 4] << 32) | (pixdata[blksrc + 5] << 40) |
            (pixdata[blksrc + 6] << 48) | (pixdata[blksrc + 7] << 56)) >> 16

    for y in range(4):
        for x in range(4):
            if (x, y) == (i, j):
                code = bits & 0x07
                break

            bits >>= 3

    if code == 0:
        ACOMP = alpha0

    elif code == 1:
        ACOMP = alpha1

    elif alpha0 > alpha1:
        ACOMP = (alpha0 * (8 - code) + (alpha1 * (code - 1))) // 7

    elif code < 6:
        ACOMP = (alpha0 * (6 - code) + (alpha1 * (code - 1))) // 5

    elif code == 6:
        ACOMP = 0

    else:
        ACOMP = 255

    return ACOMP


def fetch_2d_texel_rg_bc5(srcRowStride, pixdata, i, j):
    blksrc = ((srcRowStride + 3) // 4 * (j // 4) + (i // 4)) * 16

    RCOMP = dxt5_decode_alphablock(pixdata, blksrc, i & 3, j & 3)
    GCOMP = dxt5_decode_alphablock(pixdata, blksrc + 8, i & 3, j & 3)

    return RCOMP, GCOMP


def EXP5TO8R(packedcol):
    return (((packedcol) >> 8) & 0xf8) | (((packedcol) >> 13) & 0x07)


def EXP6TO8G(packedcol):
    return (((packedcol) >> 3) & 0xfc) | (((packedcol) >> 9) & 0x03)


def EXP5TO8B(packedcol):
    return (((packedcol) << 3) & 0xf8) | (((packedcol) >> 2) & 0x07)


def EXP4TO8(col):
    return col | col << 4


def dxt135_decode_imageblock(pixdata, img_block_src, i, j, dxt_type):
    color0 = pixdata[img_block_src] | (pixdata[img_block_src + 1] << 8)
    color1 = pixdata[img_block_src + 2] | (pixdata[img_block_src + 3] << 8)
    bits = pixdata[img_block_src + 4] | (pixdata[img_block_src + 5] << 8) |      \
        (pixdata[img_block_src + 6] << 16) | (pixdata[img_block_src + 7] << 24)

    bit_pos = 2 * (j * 4 + i)
    code = (bits >> bit_pos) & 3

    ACOMP = 255
    if code == 0:
        RCOMP = EXP5TO8R(color0)
        GCOMP = EXP6TO8G(color0)
        BCOMP = EXP5TO8B(color0)

    elif code == 1:
        RCOMP = EXP5TO8R(color1)
        GCOMP = EXP6TO8G(color1)
        BCOMP = EXP5TO8B(color1)

    elif code == 2:
        if color0 > color1:
            RCOMP = ((EXP5TO8R(color0) * 2 + EXP5TO8R(color1)) // 3)
            GCOMP = ((EXP6TO8G(color0) * 2 + EXP6TO8G(color1)) // 3)
            BCOMP = ((EXP5TO8B(color0) * 2 + EXP5TO8B(color1)) // 3)

        else:
            RCOMP = ((EXP5TO8R(color0) + EXP5TO8R(color1)) // 2)
            GCOMP = ((EXP6TO8G(color0) + EXP6TO8G(color1)) // 2)
            BCOMP = ((EXP5TO8B(color0) + EXP5TO8B(color1)) // 2)

    elif code == 3:
        if dxt_type > 1 or color0 > color1:
            RCOMP = ((EXP5TO8R(color0) + EXP5TO8R(color1) * 2) // 3)
            GCOMP = ((EXP6TO8G(color0) + EXP6TO8G(color1) * 2) // 3)
            BCOMP = ((EXP5TO8B(color0) + EXP5TO8B(color1) * 2) // 3)

        else:
            RCOMP = 0
            GCOMP = 0
            BCOMP = 0

            if dxt_type == 1:
                ACOMP = 0

    return ACOMP, RCOMP, GCOMP, BCOMP


def fetch_2d_texel_rgba_dxt5(srcRowStride, pixdata, i, j):
    blksrc = ((srcRowStride + 3) // 4 * (j // 4) + (i // 4)) * 16

    ACOMP = dxt5_decode_alphablock(pixdata, blksrc, i & 3, j & 3)
    _, RCOMP, GCOMP, BCOMP = dxt135_decode_imageblock(pixdata, blksrc + 8, i & 3, j & 3, 2)

    return RCOMP, GCOMP, BCOMP, ACOMP


def decompressBC5(data, width, height):
    output = bytearray(width * height * 4)

    for y in range(height):
        for x in range(width):
            R, G = fetch_2d_texel_rg_bc5(width, data, x, y)

            pos = (y * width + x) * 4

            output[pos + 0] = R
            output[pos + 1] = R
            output[pos + 2] = R
            output[pos + 3] = G

    return bytes(output)


def decompressDXT5(data, width, height):
    output = bytearray(width * height * 4)

    for y in range(height):
        for x in range(width):
            R, G, B, A = fetch_2d_texel_rgba_dxt5(width, data, x, y)

            pos = (y * width + x) * 4

            output[pos + 0] = R
            output[pos + 1] = G
            output[pos + 2] = B
            output[pos + 3] = A

    return bytes(output)


def save_bflim(type: str, data: bytes):
    flim = readFLIM(data)
    if flim.format != 0x41a and flim.format != 0x0035 and flim.format != 0x0433:  # RGBA8_SRGB | BC5_UNORM | BC3_UNORM
        raise ValueError("Unsupported format 0x%04x" % flim.format)

    result = addrlib.deswizzle(flim.width, flim.height, 1, flim.format, 0, 1, flim.surfOut.tileMode,
                               flim.swizzle, flim.pitch, flim.surfOut.bpp, 0, 0, flim.data)

    if flim.format == 0x0035:
        result = decompressBC5(result, flim.width, flim.height)

    if flim.format == 0x0433:
        result = decompressDXT5(result, flim.width, flim.height)

    image = Image.new('RGBA', (flim.width, flim.height))
    for y in range(flim.height):
        for x in range(flim.width):
            offset = (x + y*flim.width)*4
            r, g, b, a = struct.unpack(">BBBB", result[offset:offset+4])
            image.putpixel((x, y), (r, g, b, a))

    image.save('assets/icons/%s.png' % type)
    return data


character_list = [
    'Mario',        'Luigi',      'Peach',
    'Daisy',       'Yoshi',      'Kinopio',
    'Kinopico',    'Nokonoko',    'Koopa',
    'DK',          'Wario',      'Waluigi',
    'Rosetta',     'MetalMario', 'MetalPeach',
    'Jugem',       'Heyho',      'BbMario',
    'BbLuigi',     'BbPeach',    'BbDaisy',
    'BbRosetta',   'Larry',      'Lemmy',
    'Wendy',       'Ludwig',     'Iggy',
    'Roy',         'Morton',     'Mii',
    'TanukiMario', 'Link',       'AnimalBoyA',
    'Shizue',      'CatPeach',   'HoneKoopa',
    'AnimalGirlA'
]

body_list = [
    'K_Std', 'K_Skl', 'K_Ufo', 'K_Sbm',
    'K_Cat', 'K_Fml', 'K_Tri', 'K_Wld',
    'K_Pch', 'K_Ten', 'K_Shp', 'K_Snk',
    'K_Spo', 'K_Gld', 'B_Std', 'B_Fro',
    'B_Mgp', 'B_Big', 'B_Amb', 'B_Mix',
    'B_Kid', 'B_Jet', 'B_Ysi', 'V_Atv',
    'V_Hnc', 'V_Bea', 'K_Gla', 'K_Slv',
    'K_Rst', 'K_Bfl', 'K_Tnk', 'K_Bds',
    'B_Zlb', 'K_A00', 'K_A01', 'K_Btl',
    'K_Pwc', 'B_Sct', 'V_Drb'
]

tire_list = [
    'Std', 'Big', 'Sml', 'Rng',
    'Slk', 'Mtl', 'Btn', 'Ofr',
    'Spg', 'Wod', 'Fun', 'Zst',
    'Zbi', 'Zsm', 'Zrn', 'Zsl',
    'Zof', 'Gld', 'Gla', 'Tri',
    'Anm'
]

menu_arc = open('ui/cmn/menu.szs', 'rb').read()
menu_sarc = oead.Sarc(oead.yaz0.decompress(menu_arc))

common_arc = open('ui/cmn/common.szs', 'rb').read()
common_sarc = oead.Sarc(oead.yaz0.decompress(common_arc))

question_mark = menu_sarc.get_file('timg/tc_edChara_Question^t.bflim')
question_data = question_mark.data.tobytes()
save_bflim("Invalid", question_data)

mii_icon = menu_sarc.get_file('timg/tc_Chara_Mii^l.bflim')
mii_data = mii_icon.data.tobytes()
save_bflim("Mii", mii_data)

for chara in character_list:

    old_chara = chara
    if chara == "MetalPeach":
        chara = "PGoldPeach"

    if chara == "Jugem":
        chara = "Jugemu"

    if chara == "Mii":
        continue

    file = common_sarc.get_file('timg/tc_edChara_%s^l.bflim' % chara)
    if not file:
        file = common_sarc.get_file('timg/tc_edChara_%s00^l.bflim' % chara)

    data = file.data.tobytes()

    print("Saving image for character:", old_chara)
    save_bflim(old_chara, data)


for body in body_list:

    old_body = body
    if body == 'B_Zlb':
        body = 'B_Zld'

    if body in ['K_Std', 'K_Skl', 'B_Std', 'V_Atv']:
        data = open('ui/cmn/a_menu/timg/tc_KP_%s_Mro^q.bflim' % (body), 'rb').read()
    elif body in ['K_Fml', 'K_Ten', 'K_Shp', 'K_Gla', 'K_Snk', 'B_Mgp', 'B_Sct']:
        data = open('ui/cmn/a_menu/timg/tc_KP_%s_00^q.bflim' % (body), 'rb').read()
    elif body in ['K_A00', 'K_A01']:
        data = question_data
    else:
        file = menu_sarc.get_file('timg/tc_KP_%s^q.bflim' % body)
        if not file:
            raise ValueError("No file for body part %s" % body)
        data = file.data.tobytes()

    print("Saving image for kart body:", old_body)
    save_bflim(old_body, data)


for tire in tire_list:
    tire = "T_" + tire
    file = menu_sarc.get_file('timg/tc_KP_%s^q.bflim' % tire)
    if not file:
        raise ValueError("No file for tire part %s" % tire)
    data = file.data.tobytes()

    print("Saving image for kart tire:", tire)
    save_bflim(tire, data)
