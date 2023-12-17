import random


def get_coordinates_slug(lat: float, lon: float, verbose: bool = False) -> str:
    """Return a slug for the location

    verbose = false: `48N011E``
    verbose = true: `48.00N_11.00E`"""

    latv = str(round(abs(lat))).zfill(2)
    latd = "S" if lat < 0 else "N"
    lonv = str(round(abs(lon))).zfill(3)
    lond = "W" if lon < 0 else "E"

    if verbose:
        return f"{latv}.00{latd}_{lonv}.00{lond}"
    else:
        return f"{latv}{latd}{lonv}{lond}"


# Source: https://github.com/moby/moby/blob/master/pkg/namesgenerator/names-generator.go
# I added a few to make it >= 128 adjectives

adjectives = [
    'admiring', 'adoring', 'affectionate', 'agitated', 'amazing', 'ambitious',
    'amused', 'angry', 'astonished', 'audacious', 'awesome', 'backstabbing',
    'beautiful', 'berserk', 'big', 'blissed', 'blissful', 'bohemian', 'bold',
    'boring', 'brave', 'bubbly', 'busy', 'captivating', 'caring', 'charming',
    'clever', 'compassionate', 'competent', 'condescending', 'confident',
    'cool', 'courageous', 'cranky', 'crazy', 'daring', 'dazzling', 'deadly',
    'determined', 'distracted', 'dreamy', 'dynamic', 'eager', 'eccentric',
    'ecstatic', 'elastic', 'elated', 'elegant', 'eloquent', 'enchanting',
    'epic', 'exciting', 'fearless', 'fervent', 'festive', 'flamboyant',
    'focused', 'friendly', 'frosty', 'funny', 'gallant', 'generous', 'gifted',
    'goofy', 'gracious', 'great', 'happy', 'hardcore', 'heuristic', 'hopeful',
    'hungry', 'infallible', 'inspiring', 'intelligent', 'interesting', 'jolly',
    'jovial', 'keen', 'kind', 'laughing', 'loving', 'lucid', 'magical',
    'modest', 'musing', 'mystifying', 'naughty', 'nervous', 'nice', 'nifty',
    'nostalgic', 'objective', 'optimistic', 'peaceful', 'pedantic', 'pensive',
    'practical', 'priceless', 'quirky', 'quizzical', 'recursing', 'relaxed',
    'reverent', 'romantic', 'ruthless', 'sad', 'savage', 'serene', 'sharp',
    'silly', 'sleepy', 'spiritual', 'stoic', 'strange', 'stupefied',
    'suspicious', 'sweet', 'tender', 'thirsty', 'trusting', 'unruffled',
    'upbeat', 'vibrant', 'vigilant', 'vigorous', 'wizardly', 'wonderful',
    'wondering', 'xenodochial', 'youthful', 'zealous', 'zen'
]
assert len(adjectives) >= 128, "Not enough adjectives to generate unique names"
assert "-" not in "".join(adjectives), "Adjectives should not contain '-'"

names = [
    "agnesi", "albattani", "allen", "almeida", "antonelli", "archimedes",
    "ardinghelli", "aryabhata", "austin", "babbage", "banach", "banzai",
    "bardeen", "bartik", "bassi", "beaver", "bell", "benz", "bhabha",
    "bhaskara", "black", "blackburn", "blackwell", "bohr", "booth", "borg",
    "bose", "bouman", "boyd", "brahmagupta", "brattain", "brown", "buck",
    "burnell", "cannon", "carson", "cartwright", "carver", "cerf",
    "chandrasekhar", "chaplygin", "chatelet", "chatterjee", "chaum",
    "chebyshev", "clarke", "cohen", "colden", "cori", "cray", "curie", "curran",
    "darwin", "davinci", "dewdney", "dhawan", "diffie", "dijkstra", "dirac",
    "driscoll", "dubinsky", "easley", "edison", "einstein", "elbakyan",
    "elgamal", "elion", "ellis", "engelbart", "euclid", "euler", "faraday",
    "feistel", "fermat", "fermi", "feynman", "franklin", "gagarin", "galileo",
    "galois", "ganguly", "gates", "gauss", "germain", "goldberg", "goldstine",
    "goldwasser", "golick", "goodall", "gould", "greider", "grothendieck",
    "haibt", "hamilton", "haslett", "hawking", "heisenberg", "hellman",
    "hermann", "herschel", "hertz", "heyrovsky", "hodgkin", "hofstadter",
    "hoover", "hopper", "hugle", "hypatia", "ishizaka", "jackson", "jang",
    "jemison", "jennings", "jepsen", "johnson", "joliot", "jones", "kalam",
    "kapitsa", "kare", "keldysh", "keller", "kepler", "khayyam", "khorana",
    "kilby", "kirch", "knuth", "kowalevski", "lalande", "lamarr", "lamport",
    "leakey", "leavitt", "lederberg", "lehmann", "lewin", "lichterman",
    "liskov", "lovelace", "lumiere", "mahavira", "margulis", "matsumoto",
    "maxwell", "mayer", "mccarthy", "mcclintock", "mclaren", "mclean",
    "mcnulty", "meitner", "mendel", "mendeleev", "meninsky", "merkle",
    "mestorf", "mirzakhani", "montalcini", "moore", "morse", "moser", "murdock",
    "napier", "nash", "neumann", "newton", "nightingale", "nobel", "noether",
    "northcutt", "noyce", "panini", "pare", "pascal", "pasteur", "payne",
    "perlman", "pike", "poincare", "poitras", "proskuriakova", "ptolemy",
    "raman", "ramanujan", "rhodes", "ride", "ritchie", "robinson", "roentgen",
    "rosalind", "rubin", "saha", "sammet", "sanderson", "satoshi", "shamir",
    "shannon", "shaw", "shirley", "shockley", "shtern", "sinoussi", "snyder",
    "solomon", "spence", "stonebraker", "sutherland", "swanson", "swartz",
    "swirles", "taussig", "tesla", "tharp", "thompson", "torvalds", "tu",
    "turing", "varahamihira", "vaughan", "villani", "visvesvaraya", "volhard",
    "wescoff", "wilbur", "wiles", "williams", "williamson", "wilson", "wing",
    "wozniak", "wright", "wu", "yalow", "yonath", "zhukovsky"
]


def get_random_container_name(currently_used_names: list[str] = []) -> str:
    forbidden_adjectives = [x.split("-")[0] for x in currently_used_names]
    allowed_adjectives = set(adjectives) - set(forbidden_adjectives)
    assert len(
        allowed_adjectives
    ) > 0, "Not enough adjectives to generate unique names"
    return random.choice(list(allowed_adjectives)) + "-" + random.choice(names)
