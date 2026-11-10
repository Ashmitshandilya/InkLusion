/**
 * Everything the client can change lives here.
 * Images: drop files in /public/artist or /public/work and set `src`.
 * While `src` is empty the site shows a labelled placeholder.
 *
 * Copy rule: plain and specific. Facts and the artist's own voice, no slogans.
 */

export const site = {
  name: "InkLusion",
  tagline: "Tattoo studio in Roorkee",
  description:
    "InkLusion is Shaurya's tattoo studio in Roorkee, Uttarakhand. Custom tattoos, drawn by hand. See the work and book on WhatsApp.",
  city: "Roorkee, Uttarakhand",
  contact: {
    whatsapp: "916398330495",
    whatsappDisplay: "+91 63983 30495",
    instagram: "https://www.instagram.com/inklusiontattoo___",
    instagramHandle: "@inklusiontattoo___",
    email: "", // TODO
  },
};

/** WhatsApp link with the message already typed. */
export const wa = (text: string) => `https://wa.me/${site.contact.whatsapp}?text=${encodeURIComponent(text)}`;

export const hero = {
  eyebrow: "Tattoo studio · Roorkee, Uttarakhand",
  sub: "Custom tattoos by Shaurya, trained at Aliens Tattoo School, Mumbai.",
};

export const styles = [
  "Fine line",
  "Blackwork",
  "Realism",
  "Botanical",
  "Dotwork",
  "Portraits",
  "Script",
  "Cover-ups",
];

/**
 * DRAFT in the artist's voice. Only the Mumbai training and the Roorkee studio are confirmed.
 * Replace with his own answers (docs/artist-questionnaire.md) before going live.
 */
export const story = {
  artist: "Shaurya",
  portrait: "", // e.g. "/artist/portrait.jpg"
  chapters: [
    {
      no: "01",
      title: "Mumbai",
      text: "I trained at Aliens Tattoo School in Mumbai. Months on practice skin before I was allowed near anyone's arm.",
    },
    {
      no: "02",
      title: "Roorkee",
      text: "Then I opened InkLusion in Roorkee. You shouldn't need a train to Delhi to get a tattoo done properly.",
    },
    {
      no: "03",
      title: "How I work",
      text: "I draw your tattoo myself. If I think an idea won't age well on that spot, I'll say so before we start.",
    },
  ],
};

export const process = [
  {
    no: "01",
    title: "Talk",
    text: "Message me on WhatsApp or walk in. Tell me the idea, where you want it and what you want to spend.",
  },
  {
    no: "02",
    title: "Sketch",
    text: "I draw it. You see the drawing before the day and can ask for changes.",
  },
  {
    no: "03",
    title: "Stencil",
    text: "The outline goes on your skin in purple first. We move it around until the position is right.",
  },
  {
    no: "04",
    title: "Ink",
    text: "New needle, opened in front of you. Say the word if you need a break.",
  },
  {
    no: "05",
    title: "Heal",
    text: "You go home with aftercare steps on WhatsApp. If a spot heals patchy, come back and I'll fix it.",
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
  text: "Send your idea and where you want it. You'll get a price and a date back.",
  message: "Hi Shaurya, I want to book a tattoo.\nIdea: \nPlacement: \nSize: ",
  // TODO: real starting prices
  prices: [
    { label: "Small", note: "up to 5 cm", from: "—" },
    { label: "Medium", note: "palm size", from: "—" },
    { label: "Large", note: "half sleeve and up", from: "—" },
  ],
  negotiable: "These are starting prices. Size, detail and placement change the quote, and there is room to talk.",
};
