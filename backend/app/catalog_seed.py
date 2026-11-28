"""Catalog copied from the existing frontend; no stock policy is inferred."""
COLLECTIONS = [
    dict(slug="tiger-black", title="Tiger × Black", animal="Tiger", colour="Black", tagline="Power in every stripe.", description="The current King Stripe collection. Tiger artwork, a black-led identity and six hoodie silhouettes to explore.", status="Available", artwork="assets/tiger_crowned.svg", accent="#191916", featured=True),
    dict(slug="wolf-grey", title="Wolf × Grey", animal="Wolf", colour="Grey", tagline="Independence · Loyalty · Strength", description="A grey-led identity built around the wolf.", status="Concept example", artwork="assets/collections/wolf-grey.svg", accent="#30383A", featured=False),
    dict(slug="panther-red", title="Panther × Red", animal="Panther", colour="Red", tagline="Stealth · Confidence · Intensity", description="A red-led identity built around the panther.", status="Concept example", artwork="assets/collections/panther-red.png", accent="#651D26", featured=False),
    dict(slug="eagle-blue", title="Eagle × Blue", animal="Eagle", colour="Blue", tagline="Vision · Freedom · Ambition", description="A blue-led identity built around the eagle.", status="Concept example", artwork="assets/collections/eagle-blue.svg", accent="#20364F", featured=False),
]
PRODUCTS = [
    ("crowned-tiger", "Crowned Tiger", "Pullover", 3499, ["Bone", "Midnight", "Ember"]),
    ("midnight-king", "Midnight King", "Zip", 3999, ["Midnight", "Ash"]),
    ("rock-throne", "Rock Throne", "Oversized", 4299, ["Bone", "Ash"]),
    ("ember-stripe", "Ember Stripe", "Pullover", 3599, ["Ember", "Midnight"]),
    ("ash-prowl", "Ash Prowl", "Zip", 3899, ["Ash", "Bone"]),
    ("night-orbit", "Night Orbit", "Oversized", 4499, ["Midnight", "Ember"]),
]
SIZES = ["S", "M", "L", "XL", "XXL"]
