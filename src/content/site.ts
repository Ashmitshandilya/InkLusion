/**
 * Everything the client can change lives here.
 * Images: drop files in /public/artist or /public/work and set `src`.
 * While `src` is empty the site shows a labelled placeholder.
 */

export const site = {
  name: "InkLusion",
  tagline: "Tattoos with a story",
  description:
    "Custom tattoos, drawn for you and nobody else. See the work, find your direction, book a slot.",
  city: "", // TODO: city
  contact: { instagram: "", whatsapp: "", email: "" }, // TODO
};

export const hero = {
  eyebrow: "Custom tattoo studio",
  lines: ["Your skin.", "Your story."],
  sub: "Every piece starts as a conversation and ends as something only you wear.",
};

export const styles = [
  "Fine line",
  "Blackwork",
  "Realism",
  "Botanical",
  "Dotwork",
  "Neo-traditional",
  "Script",
  "Geometric",
];

/** PLACEHOLDER story — replace with the artist's answers (docs/artist-questionnaire.md). */
export const story = {
  artist: "The artist", // TODO: name
  portrait: "", // e.g. "/artist/portrait.jpg"
  chapters: [
    {
      no: "01",
      title: "The first line",
      text: "It started with a pen and the back of a school notebook. Long before the machine, there was the need to draw on everything in reach.",
    },
    {
      no: "02",
      title: "Learning the craft",
      text: "Years of practice skin, patient mentors and steady hands. Thousands of lines pulled before the first one that stayed on someone forever.",
    },
    {
      no: "03",
      title: "Why it matters",
      text: "A tattoo is trust made permanent. So every piece is drawn from scratch, for one person, and never repeated.",
    },
  ],
};

export const process = [
  {
    no: "01",
    title: "Talk",
    text: "You bring an idea, a feeling or just a placement. We talk through meaning, size and budget.",
  },
  {
    no: "02",
    title: "Sketch",
    text: "Your piece is drawn from scratch and refined with you until it feels right.",
  },
  {
    no: "03",
    title: "Stencil",
    text: "The design goes on your skin in violet first. We move it until it sits perfectly with your body.",
  },
  {
    no: "04",
    title: "Ink",
    text: "Sterile setup, single-use needles, steady hands. Breaks whenever you need them.",
  },
  {
    no: "05",
    title: "Heal",
    text: "You leave with clear aftercare and a free touch-up once it has settled.",
  },
];

/** PLACEHOLDER work — replace with real pieces. Later this comes from Supabase (admin can add). */
export const work = [
  { title: "Piece 01", style: "Fine line", placement: "Forearm", src: "" },
  { title: "Piece 02", style: "Botanical", placement: "Calf", src: "" },
  { title: "Piece 03", style: "Blackwork", placement: "Back", src: "" },
  { title: "Piece 04", style: "Realism", placement: "Upper arm", src: "" },
  { title: "Piece 05", style: "Dotwork", placement: "Thigh", src: "" },
  { title: "Piece 06", style: "Script", placement: "Ribs", src: "" },
];

export const booking = {
  heading: ["Ready when", "you are."],
  text: "Pick a slot, tell us the idea, and we will reply with a quote.",
  // TODO: real starting prices
  prices: [
    { label: "Small", note: "up to 5 cm", from: "—" },
    { label: "Medium", note: "palm size", from: "—" },
    { label: "Large", note: "half sleeve and up", from: "—" },
  ],
  negotiable: "Prices are starting points. Every quote is open to a conversation.",
};
