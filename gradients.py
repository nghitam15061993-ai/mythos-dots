"""Thư viện gradient rực rỡ (uiGradients / WebGradients) — (tên, [hex stops])."""

GRADIENTS = [
    ("Warm Flame", ["#ff9a9e", "#fad0c4"]),
    ("Night Fade", ["#a18cd1", "#fbc2eb"]),
    ("Spring Warmth", ["#fad0c4", "#ffd1ff"]),
    ("Juicy Peach", ["#ffecd2", "#fcb69f"]),
    ("Young Passion", ["#ff8177", "#ff867a", "#ff8c7f", "#f99185", "#cf556c", "#b12a5b"]),
    ("Lady Lips", ["#ff9a9e", "#fecfef", "#fecfef"]),
    ("Sunny Morning", ["#f6d365", "#fda085"]),
    ("Rainy Ashville", ["#fbc2eb", "#a6c1ee"]),
    ("Frozen Dreams", ["#fdcbf1", "#e6dee9"]),
    ("Winter Neva", ["#a1c4fd", "#c2e9fb"]),
    ("Dusty Grass", ["#d4fc79", "#96e6a1"]),
    ("Tempting Azure", ["#84fab0", "#8fd3f4"]),
    ("Amy Crisp", ["#a6c0fe", "#f68084"]),
    ("Mean Fruit", ["#fccb90", "#d57eeb"]),
    ("Deep Blue", ["#6a11cb", "#2575fc"]),
    ("Ripe Malinka", ["#f093fb", "#f5576c"]),
    ("True Sunset", ["#fa709a", "#fee140"]),
    ("Near Moon", ["#5ee7df", "#b490ca"]),
    ("Happy Fisher", ["#89f7fe", "#66a6ff"]),
    ("Plum Plate", ["#667eea", "#764ba2"]),
    ("Everlasting Sky", ["#fdfcfb", "#e2d1c3"]),
    ("Happy Memories", ["#ff5858", "#f857a6"]),
    ("Aqua Splash", ["#13547a", "#80d0c7"]),
    ("Big Mango", ["#c71d6f", "#d09693"]),
    ("Healthy Water", ["#96deda", "#50c9c3"]),
    ("Amour Amour", ["#f77062", "#fe5196"]),
    ("Palo Alto", ["#16a085", "#f4d03f"]),
    ("Phoenix Start", ["#f83600", "#f9d423"]),
    ("October Silence", ["#b721ff", "#21d4fd"]),
    ("Faraway River", ["#6e45e2", "#88d3ce"]),
    ("Alchemist Lab", ["#d558c8", "#24d292"]),
    ("Over Sun", ["#abecd6", "#fbed96"]),
    ("Burning Spring", ["#4fb576", "#44107a", "#ff1361", "#fff800"]),
    ("Night Party", ["#0250c5", "#d43f8d"]),
    ("Summer Games", ["#92fe9d", "#00c9ff"]),
    ("Passionate Bed", ["#ff758c", "#ff7eb3"]),
    ("Phoenix Smart", ["#f83600", "#fe8c00"]),
    ("Smart Indigo", ["#b224ef", "#7579ff"]),
    ("Juicy Cake", ["#e14fad", "#f9d423"]),
    ("Norse Beauty", ["#ec77ab", "#7873f5"]),
    ("Aqua Guidance", ["#007adf", "#00ecbc"]),
    ("Sun Veggie", ["#20e2d7", "#f9fea5"]),
    ("Sea Lord", ["#2cd8d5", "#c5c1ff", "#ffbac3"]),
    ("Grass Shampoo", ["#dfffcd", "#90f9c4", "#39f3bb"]),
    ("Witch Dance", ["#a8bfff", "#884d80"]),
    ("Sleepless Night", ["#5271c4", "#b19fff", "#eca1fe"]),
    ("Angel Care", ["#ffd3a5", "#fd6585"]),
    ("Crystalline", ["#00cdac", "#8ddad5"]),
    ("Mind Crawl", ["#473b7b", "#3584a7", "#30d2be"]),
    ("Cochiti Lake", ["#93a5cf", "#e4efe9"]),
]


def _hex2rgb(h):
    h = h.lstrip("#")
    return [int(h[i:i + 2], 16) for i in (0, 2, 4)]


def build_lut(stops, n=256):
    """Nội suy tuyến tính RGB qua các stop → mảng (n,3) uint8."""
    import numpy as np
    cols = np.array([_hex2rgb(s) for s in stops], dtype=float)
    if len(cols) == 1:
        return np.tile(cols[0], (n, 1)).astype("uint8")
    seg = np.linspace(0, len(cols) - 1, n)
    lo = np.floor(seg).astype(int).clip(0, len(cols) - 2)
    frac = (seg - lo)[:, None]
    return (cols[lo] * (1 - frac) + cols[lo + 1] * frac).round().astype("uint8")
