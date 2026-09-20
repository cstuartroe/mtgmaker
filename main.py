import dataclasses
import datetime

from PIL import Image, ImageDraw, ImageFont
from tqdm import tqdm

from svg_gen.src import mtg, utils


SPACES = " \u200b"


TITLE_LEFT_PADDING = mtg.EM//4
COST_RIGHT_PADDING = mtg.EM//2
BODY_LEFT_PADDING = mtg.EM
BODY_LINE_HEIGHT = mtg.EM
PARAGRAPH_BREAK_HEIGHT = round(mtg.EM*.5)
BODY_LEFT_MARGIN = mtg.SIDE_PADDING + BODY_LEFT_PADDING
BODY_RIGHT_MARGIN = mtg.CARD_WIDTH - mtg.SIDE_PADDING - BODY_LEFT_PADDING

FONT_COLOR = utils.Color.EARTH_BROWN.value


IMAGE_X = round(mtg.SIDE_PADDING + mtg.INTERNAL_BORDER_WIDTH / 2)
IMAGE_Y = round(mtg.TITLE_BADGE_HEIGHT + mtg.BADGE_HEIGHT + mtg.INTERNAL_BORDER_WIDTH / 2)
IMAGE_WIDTH = round(mtg.CARD_WIDTH - 2 * mtg.SIDE_PADDING - mtg.INTERNAL_BORDER_WIDTH)
IMAGE_HEIGHT = round(mtg.TYPE_BADGE_HEIGHT - mtg.INTERNAL_BORDER_WIDTH / 2 - IMAGE_Y)

@dataclasses.dataclass
class FontFamily:
    title_font: ImageFont.FreeTypeFont
    rules_font: ImageFont.FreeTypeFont
    flavor_font: ImageFont.FreeTypeFont
    mana_number_font: ImageFont.FreeTypeFont
    photo_descriptor_font: ImageFont.FreeTypeFont


FONTS = {
    "en": FontFamily(
        title_font=ImageFont.truetype("font/GentiumPlus-Bold.ttf", 1.2*mtg.EM),
        rules_font=ImageFont.truetype("font/GentiumPlus-Regular.ttf", .85 * mtg.EM),
        flavor_font=ImageFont.truetype("font/GentiumPlus-Italic.ttf", .85 * mtg.EM),
        mana_number_font=ImageFont.truetype("font/GentiumPlus-Regular.ttf", .7 * mtg.EM),
        photo_descriptor_font=ImageFont.truetype("font/GentiumPlus-Bold.ttf", .4*mtg.EM),
    ),
    "lv": FontFamily(
        title_font=ImageFont.truetype("font/LauvinkoHandwritten-UltraBold.ttf", 1.2*mtg.EM),
        rules_font=ImageFont.truetype("font/LauvinkoHandwritten-Normal.ttf", .85*mtg.EM),
        flavor_font=ImageFont.truetype("font/LauvinkoHandwritten-Normal.ttf", .85*mtg.EM),
        mana_number_font=ImageFont.truetype("font/LauvinkoHandwritten-Normal.ttf", .7*mtg.EM),
        photo_descriptor_font=ImageFont.truetype("font/LauvinkoHandwritten-SemiBold.ttf", .4*mtg.EM),
    ),
}

set_number_font = ImageFont.truetype("font/GentiumPlus-Regular.ttf", .4*mtg.EM)

INVARIABLE_SYMBOLS = {
    "{T}": Image.open("svg_gen/pngs/mtg/tap.png"),

    "{B}": Image.open("svg_gen/pngs/mtg/mana_B.png"),
    "{G}": Image.open("svg_gen/pngs/mtg/mana_G.png"),
    "{R}": Image.open("svg_gen/pngs/mtg/mana_R.png"),
    "{U}": Image.open("svg_gen/pngs/mtg/mana_U.png"),
    "{W}": Image.open("svg_gen/pngs/mtg/mana_W.png"),
    "{Y}": Image.open("svg_gen/pngs/mtg/mana_Y.png"),
}

for pair in mtg.MANA_PAIRS:
    INVARIABLE_SYMBOLS["{" + pair[0] + "/" + pair[1] + "}"] = Image.open(f"svg_gen/pngs/mtg/mana_{pair}.png")

VARIABLE_SYMBOLS = {}

for mana_count in [*range(10), "X"]:
    d = {}
    VARIABLE_SYMBOLS["{" + str(mana_count) + "}"] = d

    for lang in FONTS:
        img = Image.open(f"svg_gen/pngs/mtg/mana_number.png")

        draw = ImageDraw.Draw(img)
        draw.text(
            (img.width//2, img.height*.45),
            text=str(mana_count),
            fill=FONT_COLOR,
            font=FONTS[lang].mana_number_font,
            anchor="mm",
        )

        d[lang] = img

SYMBOLS = {*INVARIABLE_SYMBOLS.keys(), *VARIABLE_SYMBOLS.keys()}

def get_symbol(symbol: str, language: str) -> Image.Image:
    if symbol in INVARIABLE_SYMBOLS:
        return INVARIABLE_SYMBOLS[symbol]

    if symbol in VARIABLE_SYMBOLS:
        return VARIABLE_SYMBOLS[symbol][language]

    raise ValueError


RELEASE_LOGOS = {
    set_id: Image.open(f"svg_gen/pngs/mtg/release_{set_id}.png")
    for set_id in ["cts"]
}


PT_BADGES = {
    color: Image.open(f"svg_gen/pngs/mtg/badge_pt_{color}.png")
    for color in "BCGRUWY"
}


CAMERA_ICON_SIZE = round(mtg.MANA_SYMBOL_HEIGHT*.6)

def convert_palette_color(img: Image.Image, i: int, color: str):
    r, g, b = utils.hex_to_rgb(color)

    palette = img.getpalette()

    palette[3*i] = r
    palette[3*i + 1] = g
    palette[3*i + 2] = b

    img.putpalette(palette)

    return img

camera_icon = Image.open("dslr-camera.png")
dark_camera_icon = convert_palette_color(camera_icon, 252, utils.Color.EARTH_BROWN.value).convert("RGBA").resize((CAMERA_ICON_SIZE, CAMERA_ICON_SIZE))
light_camera_icon = convert_palette_color(camera_icon, 252, utils.Color.CREAM.value).convert("RGBA").resize((CAMERA_ICON_SIZE, CAMERA_ICON_SIZE))

PHOTO_DESCRIPTION_Y = round(mtg.CARD_HEIGHT - mtg.BOTTOM_PADDING + .5*mtg.EM)


GRADIENT_WIDTH = .1

SET_SIZES = {
    "cts": 324,
}


@dataclasses.dataclass
class Cursor:
    x: int
    y: int

    def newline(self):
        self.x = BODY_LEFT_MARGIN
        self.y += BODY_LINE_HEIGHT


@dataclasses.dataclass
class CardImage:
    filename: str
    x: int = 0
    y: int = 0
    width: int | None = None


@dataclasses.dataclass
class Card:
    set_id: str
    number_in_set: int
    frame: str
    title: str
    image: CardImage
    card_type: str
    photo_descriptor: str
    rules_text: str | None = None
    flavor_text: str | None = None
    language: str = "en"
    cost: list[str] | None = None
    pt: tuple[int, int] | None = None

    def identity(self):
        return self.set_id, self.number_in_set, self.language

    def slug(self):
        return f"{self.set_id}_{str(self.number_in_set).zfill(3)}_{self.language}_{self.title}"

    def make_translation(self, new_language: str, new_title: str, new_card_type: str, new_rules_text: str | None = None, new_flavor_text: str | None = None, new_photo_descriptor: str = "") -> "Card":
        return Card(
            title=new_title,
            set_id=self.set_id,
            number_in_set=self.number_in_set,
            frame=self.frame,
            card_type=new_card_type,
            image=self.image,
            rules_text=new_rules_text,
            flavor_text=new_flavor_text,
            language=new_language,
            cost=self.cost,
            pt=self.pt,
            photo_descriptor=new_photo_descriptor,
        )

    def with_translation(self, *args, **kwargs):
        return self, self.make_translation(*args, **kwargs)

def add_text(draw: ImageDraw.ImageDraw, text: str, cursor: Cursor, language: str):
    font = FONTS[language]

    if text.startswith("\n"):
        cursor.newline()
        cursor.y += PARAGRAPH_BREAK_HEIGHT
        text = text[1:]

    num_chars = len(text)
    start_continuation = None
    if cursor.x + font.rules_font.getlength(text[:num_chars]) > BODY_RIGHT_MARGIN:
        while True:
            num_chars -= 1

            if text[num_chars] in SPACES and (
                    cursor.x + font.rules_font.getlength(text[:num_chars]) <= BODY_RIGHT_MARGIN):
                start_continuation = num_chars + 1
                break
    draw.text(
        (cursor.x, cursor.y),
        text=text[:num_chars],
        fill=FONT_COLOR,
        font=font.rules_font,
        anchor="lm",
    )
    cursor.x += round(font.rules_font.getlength(text[:num_chars]))

    if start_continuation is not None:
        cursor.newline()
        add_text(draw, text[start_continuation:], cursor, language)


def add_rules_text(img: Image.Image, draw: ImageDraw.ImageDraw, rules_text: str, language: str):
    rules_text_pieces = []
    piece_start = 0
    i = 0
    while i < len(card.rules_text or ""):
        seq = card.rules_text[i:i + 3]

        if seq in INVARIABLE_SYMBOLS or seq in VARIABLE_SYMBOLS:
            if i - piece_start > 0:
                rules_text_pieces.append(card.rules_text[piece_start:i])

            rules_text_pieces.append(get_symbol(seq, language))

            i += 3
            piece_start = i
        elif card.rules_text[i] == "\n":
            rules_text_pieces.append(card.rules_text[piece_start:i])
            piece_start = i
            i += 1
        else:
            i += 1
    rules_text_pieces.append(card.rules_text[piece_start:])

    cursor = Cursor(
        x=BODY_LEFT_MARGIN,
        y=mtg.TYPE_BADGE_HEIGHT + mtg.BADGE_HEIGHT + 1.5 * mtg.EM,
    )

    for piece in rules_text_pieces:
        if isinstance(piece, Image.Image):
            symbol_img: Image.Image = piece

            if cursor.x + symbol_img.width > BODY_RIGHT_MARGIN:
                cursor.newline()

            img.paste(symbol_img, (round(cursor.x), round(cursor.y - symbol_img.height * .45)), mask=symbol_img)

            cursor.x += symbol_img.width

        elif isinstance(piece, str):
            add_text(draw, piece, cursor, language)

        else:
            raise ValueError(f"Unknown piece type: {piece}")


def make_card(card: Card):
    if "/" in card.frame:
        img = Image.new("RGBA", (mtg.CARD_WIDTH, mtg.CARD_HEIGHT))

        left_color, right_color = card.frame.split("/")
        left_img = Image.open(f"svg_gen/pngs/mtg/frame_{left_color}_dual.png")
        right_img = Image.open(f"svg_gen/pngs/mtg/frame_{right_color}_dual.png")

        left_threshold = round(mtg.CARD_WIDTH*(.5 - GRADIENT_WIDTH))
        right_threshold = mtg.CARD_WIDTH*(.5 + GRADIENT_WIDTH)

        for x in range(mtg.CARD_WIDTH):
            for y in range(mtg.CARD_HEIGHT):
                if x < left_threshold:
                    img.putpixel((x, y), left_img.getpixel((x, y)))
                elif x > right_threshold:
                    img.putpixel((x, y), right_img.getpixel((x, y)))
                else:
                    img.putpixel((x, y), (*utils.mix_rgb_colors(left_img.getpixel((x, y))[:3], right_img.getpixel((x, y))[:3], (right_threshold - x)/(right_threshold - left_threshold)), 255))

        badge_color = "C"

    else:
        img = Image.open(f"svg_gen/pngs/mtg/frame_{card.frame}.png")
        badge_color = card.frame

    draw = ImageDraw.Draw(img)

    font = FONTS[card.language]

    draw.text(
        (mtg.SIDE_PADDING + TITLE_LEFT_PADDING, mtg.TITLE_BADGE_HEIGHT + mtg.BADGE_HEIGHT / 2),
        text=card.title,
        fill=FONT_COLOR,
        font=font.title_font,
        anchor="lm",
    )

    if card.cost:
        for i, symbol in enumerate(card.cost):
            sym = get_symbol("{" + symbol + "}", card.language)
            img.paste(
                sym,
                box=(
                    mtg.CARD_WIDTH - mtg.SIDE_PADDING - COST_RIGHT_PADDING - mtg.MANA_SYMBOL_HEIGHT*(len(card.cost) - i),
                    mtg.TITLE_BADGE_HEIGHT + mtg.BADGE_HEIGHT//2 - mtg.MANA_SYMBOL_HEIGHT//2,
                ),
                mask=sym,
            )

    art_img = Image.open(f"images/{card.image.filename}")
    if card.image.width is None:
        requested_width = min(
            art_img.width - card.image.x,
            round((art_img.height - card.image.y)*IMAGE_WIDTH/IMAGE_HEIGHT)
        )
    else:
        requested_width = card.image.width
    if art_img.width < card.image.x + requested_width:
        raise ValueError(f"Excessive requested width: requested {card.image.x} + {requested_width} = {card.image.x + requested_width}, actual {art_img.width}")
    requested_height = round(requested_width*IMAGE_HEIGHT/IMAGE_WIDTH)
    if art_img.height < card.image.y + requested_height:
        raise ValueError(f"Excessive requested height: requested {card.image.y} + {requested_height} = {card.image.y + requested_height}, actual {art_img.height}")
    art_img = art_img.crop((card.image.x, card.image.y, card.image.x + requested_width, card.image.y + requested_height))
    if art_img.width/art_img.height - IMAGE_WIDTH/IMAGE_HEIGHT > .001:
        raise ValueError(f"Improperly cropped image for {card.title}: {art_img.size[0]/art_img.size[1] - IMAGE_WIDTH/IMAGE_HEIGHT}")

    art_img = art_img.resize((IMAGE_WIDTH, IMAGE_HEIGHT))
    img.paste(art_img, (IMAGE_X, IMAGE_Y))

    draw.text(
        (mtg.SIDE_PADDING + TITLE_LEFT_PADDING, mtg.TYPE_BADGE_HEIGHT + mtg.BADGE_HEIGHT / 2),
        text=card.card_type,
        fill=FONT_COLOR,
        font=font.title_font,
        anchor="lm",
    )

    img.paste(
        RELEASE_LOGOS[card.set_id],
        (
            round(mtg.CARD_WIDTH - mtg.SIDE_PADDING - COST_RIGHT_PADDING - mtg.MANA_SYMBOL_HEIGHT),
            round(mtg.TYPE_BADGE_HEIGHT + mtg.BADGE_HEIGHT/2 - mtg.MANA_SYMBOL_HEIGHT/2),
        ),
        RELEASE_LOGOS[card.set_id],
    )

    if card.rules_text:
        add_rules_text(img, draw, card.rules_text, card.language)

    if card.pt:
        p, t = card.pt
        img.paste(
            PT_BADGES[badge_color],
            (
                mtg.CARD_WIDTH - mtg.PT_BADGE_WIDTH,
                round(mtg.CARD_HEIGHT - mtg.BOTTOM_PADDING - mtg.BADGE_HEIGHT/2 - mtg.INTERNAL_BORDER_WIDTH/2),
            ),
            mask=PT_BADGES[badge_color],
        )
        draw.text(
            (mtg.CARD_WIDTH - mtg.PT_BADGE_WIDTH//2, mtg.CARD_HEIGHT - mtg.BOTTOM_PADDING),
            text=f"{p}/{t}",
            fill=FONT_COLOR,
            font=font.title_font,
            anchor="mm",
        )

    has_dark_background = "B" in card.frame #or "U" in card.frame
    outer_font_color = utils.Color.CREAM.value if has_dark_background else FONT_COLOR
    img.paste(
        light_camera_icon if has_dark_background else dark_camera_icon,
        (round(mtg.SIDE_PADDING - mtg.INTERNAL_BORDER_WIDTH/2), round(PHOTO_DESCRIPTION_Y - CAMERA_ICON_SIZE/2)),
        dark_camera_icon,
    )
    if len(card.photo_descriptor) > 80:
        print(f"Photo caption too long: {repr(card.photo_descriptor)}")
    draw.text(
        (round(mtg.SIDE_PADDING - mtg.INTERNAL_BORDER_WIDTH/2 + CAMERA_ICON_SIZE + mtg.EM/5), PHOTO_DESCRIPTION_Y),
        text=card.photo_descriptor,
        fill=outer_font_color,
        font=font.photo_descriptor_font,
        anchor="lm",
    )

    draw.text(
        (mtg.CARD_WIDTH - mtg.SIDE_PADDING, mtg.CARD_HEIGHT - mtg.BORDER_THICKNESS - .4*mtg.EM),
        text=f"© {datetime.date.today().year} Conor Stuart-Roe {card.set_id.upper()} {card.number_in_set}/{SET_SIZES[card.set_id]}",
        fill=outer_font_color,
        font=set_number_font,
        anchor="rm",
    )

    img.save(f"cards/{card.slug()}.png")


class CardLibrary:
    def __init__(self, cards: list[Card]):
        self.cards = {}
        for card in cards:
            self.add(card)

    def add(self, card: Card):
        if card.identity() in self.cards:
            raise ValueError(F"Duplicate card: {card.identity()}")
        self.cards[card.identity()] = card

    def find_by_title(self, title: str) -> Card | None:
        for card in self.cards.values():
            if card.title == title:
                return card

        return None

    def find_by_identity(self, identity: tuple[str, int, str]) -> Card:
        return self.cards[identity]

    def __iter__(self):
        return self.cards.values().__iter__()


CARDS = CardLibrary(
    [
        *Card(
            set_id="cts",
            number_in_set=101,
            title="Whale Shark",
            card_type="Creature — Fish",
            frame="U",
            rules_text="Defender\nProtection from yellow\nWard {2} (Whenever this creature becomes the target of a spell or ability an opponent controls, counter it unless that player pays {2}.)",
            flavor_text=None,
            image=CardImage(
                # https://commons.wikimedia.org/wiki/File:Whale_Shark_(Rhincodon_typus)_with_open_mouth_in_La_Paz,_Mexico.jpg
                filename="whale shark.jpg",
            ),
            photo_descriptor="Whale Shark in La Paz, Mexico by Matthew T. Rader",
            cost=["2", "U"],
            pt=(0, 4),
        ).with_translation(
            new_language="lv",
            new_title="pehuli",
            new_card_type="binvtvM,ikvM",
            new_rules_text=(
                "tuqvego\n"
                "vko-pu\u200bkvlileqv\n"
                "ko-pu\u200b{2}\u200b"
                "(la\u200bniepi\u200bi-di\u200bvitubinvtvM\u200bewvyvwvyv\u200bvtW\u200bdv\u200bvme-to\u200betuvyvti\u200b"
                "do\u200btvkv\u200bnv\u200b"
                "la\u200bpibutu\u200bgv\u200bv{2}\u200bi-ino\u200btuqvesi)"
            ),
            new_photo_descriptor="pehulinisolilvpvsilimekisikonipotoi-mvtiule-lv",
        ),
        Card(
            set_id="cts",
            number_in_set=275,
            title="Bleeding Bonnet",
            card_type="Instant",
            frame="B/G",
            image=CardImage(
                # https://commons.wikimedia.org/wiki/File:Haematopus-on-oak.jpg
                filename="Haematopus.jpg",
            ),
            photo_descriptor="Mycena haematopus in Samuel P. Taylor State Park, CA, USA by Alan Rockefeller",
            cost=["B/G"],
            rules_text="Place a -1/-1 counter on a creature that dealt combat damage to you this turn.",
        ),
        Card(
            set_id="cts",
            number_in_set=289,
            title="Crankshaft",
            card_type="Artifact",
            frame="C",
            image=CardImage(
                filename="Striltsivskyi Steppe.jpg",
            ),
            photo_descriptor="A crankshaft"
        ),
        Card(
            set_id="cts",
            number_in_set=301,
            title="Steppe",
            card_type="Basic Land — Steppe",
            frame="steppe",
            image=CardImage(
                # https://commons.wikimedia.org/wiki/File:Філія_ЛПЗ_НАНУ_"Стрільцівський_степ"_Stipa_tirsa_(ЧКУ).jpg
                filename="Striltsivskyi Steppe.jpg",
            ),
            photo_descriptor="Striltsivsky Steppe nature reserve, Luhansk Oblast, Ukraine by Galina Gouz",
        ),
        Card(
            set_id="cts",
            number_in_set=305,
            title="Desert",
            card_type="Basic Land — Desert",
            frame="desert",
            image=CardImage(
                # https://commons.wikimedia.org/wiki/File:Libya_5101_Fozzigiaren_Arch_Tadrart_Acacus_Luca_Galuzzi_2007.jpg
                filename="Forzhaga Arch.jpg",
            ),
            photo_descriptor="Forzhaga Arch in Tadrart Acacus, Libya by Luca Galuzzi",
        ),
        *Card(
            set_id="cts",
            number_in_set=309,
            title="Island",
            card_type="Basic Land — Island",
            frame="island",
            image=CardImage(
                # https://www.liveaboard.com/nl/diving/maldives/addu-atoll
                filename="Addu Atoll.webp",
                x=400,
            ),
            photo_descriptor="Addu Atoll, Maldives",
        ).with_translation(
            new_language="lv",
            new_title="iru",
            new_card_type="pvkvpaliwini,iru",
            new_photo_descriptor="vtoluvdulidiwehi",
        ),
        Card(
            set_id="cts",
            number_in_set=313,
            title="Floodplain",
            card_type="Basic Land — Floodplain",
            frame="floodplain",
            image=CardImage(
                # https://www.flickr.com/photos/150678186@N03/44653103312/
                filename="Bac Son.jpg",
            ),
            photo_descriptor="Bắc Sơn, Lạng Sơn province, Vietnam by Miền Tây Người",
        ),
        Card(
            set_id="cts",
            number_in_set=314,
            title="Floodplain",
            card_type="Basic Land — Floodplain",
            frame="floodplain",
            image=CardImage(
                # https://maps.app.goo.gl/qHqVp4kt6GLWQ6st8
                filename="Atchafalaya.jpg",
            ),
            photo_descriptor="Atchafalaya National Wildlife Refuge, Louisiana, USA by Emile Legendre",
        ),
        Card(
            set_id="cts",
            number_in_set=317,
            title="Mountain",
            card_type="Basic Land — Mountain",
            frame="mountain",
            image=CardImage(
                # https://discoverrussia.travel/destinations/caucasus
                filename="Elbrus.webp",
                x=1000,
            ),
            photo_descriptor="Mount Elbrus, Russia",
        ),
        Card(
            set_id="cts",
            number_in_set=321,
            title="Forest",
            card_type="Basic Land — Forest",
            frame="forest",
            image=CardImage(
                # https://commons.wikimedia.org/wiki/File:Parc_amazonien_de_Guyane,_une_balade_%C3%A0_Sa%C3%BCl.jpg
                filename="Guiana Amazonian Park.jpg",
            ),
            photo_descriptor="Guiana Amazonian Park, French Guiana by Melanie Dinane",
        ),
    ],
)


if __name__ == "__main__":
    for card in tqdm(list(CARDS)):
        make_card(card)
