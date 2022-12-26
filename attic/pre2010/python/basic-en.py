# Word lists from http://en.wiktionary.org/wiki/Appendix:Basic_English_word_list

operations = "come, get, give, go, keep, let, make, put, seem, take, be, do, have, say, see, send, may, will, about, across, after, against, among, at, before, between, by, down, from, in, off, on, over, through, to, under, up, with, as, for, of, till, than, a, the, all, any, every, no, other, some, such, that, this, I, he, you, who, and, because, but, or, if, though, while, how, when, where, why, again, ever, far, forward, here, near, now, out, still, then, there, together, well, almost, enough, even, little, much, not, only, quite, so, very, tomorrow, yesterday, north, south, east, west, please, yes"
operations = operations.split(', ')
assert len(operations) == 100

general_words = [
  "account", "act", "addition", "adjustment", "advertisement", "agreement",
  "air", "amount", "amusement", "animal", "answer", "apparatus", "approval",
  "argument", "art", "attack", "attempt", "attention", "attraction",
  "authority",

  "back", "balance", "base", "behaviour", "belief", "birth", "bit", "bite",
  "blood", "blow", "body", "brass", "bread", "breath", "brother", "building",
  "burn", "burst", "business", "butter",

  "canvas", "care", "cause", "chalk", "chance", "change", "cloth", "coal",
  "colour", "comfort", "committee", "company", "comparison", "competition",
  "condition", "connection", "control", "cook", "copper", "copy", "cork",
  "cotton", "cough", "country", "cover", "crack", "credit", "crime", "crush",
  "cry", "current", "curve",

  "damage", "danger", "daughter", "day", "death",
  "debt", "decision", "degree", "design", "desire", "destruction", "detail",
  "development", "digestion", "direction", "discovery", "discussion", "disease",
  "disgust", "distance", "distribution", "division", "doubt", "drink",
  "driving", "dust",

  "earth", "edge", "education", "effect", "end", "error", "event", "example",
  "exchange", "existence", "expansion", "experience", "expert", "fact", "fall",
  "family", "father", "fear", "feeling", "fiction", "field", "fight", "fire",
  "flame", "flight", "flower", "fold", "food", "force", "form", "friend",
  "front", "fruit",

  "glass", "gold", "government", "grain", "grass", "grip", "group", "growth",
  "guide",

  "harbour", "harmony", "hate", "hearing", "heat", "help", "history",
  "hole", "hope", "hour", "humour",

  "ice", "idea", "impulse", "increase", "industry", "ink", "insect",
  "instrument", "insurance", "interest", "invention", "iron",
  "jelly", "join", "journey", "judge", "jump", "kick", "kiss", "knowledge",
  "land", "language", "laugh", "law", "lead", "learning", "leather", "letter",
  "level", "lift", "light", "limit", "linen", "liquid", "list", "look", "loss",
  "love", "machine", "man", "manager", "mark", "market", "mass", "meal",
  "measure", "meat", "meeting", "memory", "metal", "middle", "milk", "mind",
  "mine", "minute", "mist", "money", "month", "morning", "mother", "motion",
  "mountain", "move", "music", "name", "nation", "need", "news", "night",
  "noise", "note", "number",

  "observation", "offer", "oil", "operation", "opinion", "order",
  "organization", "ornament", "owner",

  "page", "pain", "paint", "paper", "part", "paste", "payment", "peace",
  "person", "place", "plant", "play", "pleasure", "point", "poison", "polish",
  "porter", "position", "powder", "power", "price", "print", "process",
  "produce", "profit", "property", "prose", "protest", "pull", "punishment",
  "purpose", "push", "quality", "question",
  "rain", "range", "rate", "ray", "reaction", "reading", "reason", "record",
  "regret", "relation", "religion", "representative", "request", "respect",
  "rest", "reward", "rhythm", "rice", "river", "road", "roll", "room", "rub",
  "rule", "run", "salt", "sand", "scale", "science", "sea", "seat", "secretary",
  "selection", "self", "sense", "servant", "sex", "shade", "shake", "shame",
  "shock", "side", "sign", "silk", "silver", "sister", "size", "sky", "sleep",
  "slip", "slope", "smash", "smell", "smile", "smoke", "sneeze", "snow", "soap",
  "society", "son", "song", "sort", "sound", "soup", "space", "stage", "start",
  "statement", "steam", "steel", "step", "stitch", "stone", "stop", "story",
  "stretch", "structure", "substance", "sugar", "suggestion", "summer",
  "support", "surprise", "swim", "system",

  "talk", "taste", "tax", "teaching", "tendency", "test", "theory", "thing",
  "thought", "thunder", "time", "tin", "top", "touch", "trade", "transport",
  "trick", "trouble", "turn", "twist",

  "unit", "use",

  "value", "verse", "vessel", "view", "voice",

  "walk", "war", "wash", "waste", "water", "wave", "wax", "way", "weather",
  "week", "weight", "wind", "wine", "winter", "woman", "wood", "wool", "word",
  "work", "wound", "writing",

  "year"]

assert len(general_words) == 400

things = ["angle", "ant", "apple", "arch", "arm", "army", "baby", "bag", "ball", "band", "basin", "basket", "bath", "bed", "bee", "bell", "berry", "bird", "blade", "board", "boat", "bone", "book", "boot", "bottle", "box", "boy", "brain", "brake", "branch", "brick", "bridge", "brush", "bucket", "bulb", "button", "cake", "camera", "card", "cart", "carriage", "cat", "chain", "cheese", "chest", "chin", "church", "circle", "clock", "cloud", "coat", "collar", "comb", "cord", "cow", "cup", "curtain", "cushion", "dog", "door", "drain", "drawer", "dress", "drop", "ear", "egg", "engine", "eye", "face", "farm", "feather", "finger", "fish", "flag", "floor", "fly", "foot", "fork", "fowl", "frame", "garden", "girl", "glove", "goat", "gun", "hair", "hammer", "hand", "hat", "head", "heart", "hook", "horn", "horse", "hospital", "house", "island", "jewel", "kettle", "key", "knee", "knife", "knot", "leaf", "leg", "library", "line", "lip", "lock", "map", "match", "monkey", "moon", "mouth", "muscle", "nail", "neck", "needle", "nerve", "net", "nose", "nut", "office", "orange", "oven", "parcel", "pen", "pencil", "picture", "pig", "pin", "pipe", "plane", "plate", "plough", "pocket", "pot", "potato", "prison", "pump", "rail", "rat", "receipt", "ring", "rod", "roof", "root", "sail", "school", "scissors", "screw", "seed", "sheep", "shelf", "ship", "shirt", "shoe", "skin", "skirt", "snake", "sock", "spade", "sponge", "spoon", "spring", "square", "stamp", "star", "station", "stem", "stick", "stocking", "stomach", "store", "street", "sun", "table", "tail", "thread", "throat", "thumb", "ticket", "toe", "tongue", "tooth", "town", "train", "tray", "tree", "trousers", "umbrella", "wall", "watch", "wheel", "whip", "whistle", "window", "wing", "wire", "worm"]
assert len(things) == 200

qualities = ["able", "acid", "angry", "automatic", "beautiful", "black", "boiling", "bright", "broken", "brown", "cheap", "chemical", "chief", "clean", "clear", "common", "complex", "conscious", "cut", "deep", "dependent", "early", "elastic", "electric", "equal", "fat", "fertile", "first", "fixed", "flat", "free", "frequent", "full", "general", "good", "great", "grey", "hanging", "happy", "hard", "healthy", "high", "hollow", "important", "kind", "like", "living", "long", "male", "married", "material", "medical", "military", "natural", "necessary", "new", "normal", "open", "parallel", "past", "physical", "political", "poor", "possible", "present", "private", "probable", "quick", "quiet", "ready", "red", "regular", "responsible", "right", "round", "same", "second", "separate", "serious", "sharp", "smooth", "sticky", "stiff", "straight", "strong", "sudden", "sweet", "tall", "thick", "tight", "tired", "true", "violent", "waiting", "warm", "wet", "wide", "wise", "yellow", "young"]
assert len(qualities) == 100

qualities_oposite = ["awake", "bad", "bent", "bitter", "blue", "certain", "cold", "complete", "cruel", "dark", "dead", "dear", "delicate", "different", "dirty", "dry", "false", "feeble", "female", "foolish", "future", "green", "ill", "last", "late", "left", "loose", "loud", "low", "mixed", "narrow", "old", "opposite", "public", "rough", "sad", "safe", "secret", "short", "shut", "simple", "slow", "small", "soft", "solid", "special", "strange", "thin", "white", "wrong"]
assert len(qualities_oposite) == 50


all_words = operations + general_words + things + qualities + qualities_oposite
assert len(all_words) == 850

# Logic here:
paragraph = """1 And it came about that after saying these words, Jesus went away from Galilee, and came into the parts of Judaea on the other side of Jordan. 2 And a great number went after him; and he made them well there. 3 And certain Pharisees came to him, testing him, and saying, Is it right for a man to put away his wife for every cause? 4 And he said in answer, Have you not seen in the Writings, that he who made them at the first made them male and female, and said, 5 For this cause will a man go away from his father and mother, and be joined to his wife; and the two will become one flesh? 6 So that they are no longer two, but one flesh. Then let not that which has been joined by God be parted by man. 7 They say to him, Why then did Moses give orders that a husband might give her a statement in writing and be free from her? 8 He says to them, Moses, because of your hard hearts, let you put away your wives: but it has not been so from the first. 9 And I say to you, Whoever puts away his wife for any other cause than the loss of her virtue, and takes another, is a false husband: and he who takes her as his wife when she is put away, is no true husband to her. 10 The disciples say to him, If this is the position of a man in relation to his wife, it is better not to be married. 11 But he said to them, Not all men are able to take in this saying, but only those to whom it is given. 12 For there are men who, from birth, were without sex: and there are some who were made so by men: and there are others who have made themselves so for the kingdom of heaven. He who is able to take it, let him take it."""


def strip_punctuation(word):
  if len(word) < 2: return word

  punctuation_marks = [',', '.', ':', ';', '?']

  # Remove punctuation_marks from the end of the word.
  if word[-1] in punctuation_marks:
    return word[:-1]

  return word

def sanitise(word):
  word = strip_punctuation(word)
  return word.lower()

def paragraph_iterator(paragraph):
  """Returns a generate that splits a paragraph by words and strips out
  punctuation and drops the words to lower case as well as removing any numbers
  """

  for word in paragraph.split(" "):
    word = strip_punctuation(word)
    word = word.lower()

    try:
      int(word)
    except ValueError:
      yield word

words = set(paragraph_iterator(paragraph))

valid_words = [word for word in words if word in all_words]
invalid_words = [word for word in words if word not in all_words]

print len(valid_words), ' basic words out of ', len(words),
print ' %.0f%%' % (100 * len(valid_words) / float(len(words)))
print invalid_words





