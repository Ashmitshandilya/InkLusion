/**
 * Idea finder rules. Suggests a direction (style + why), never a finished design.
 * Used by the landing teaser now and the full /ideas page later.
 */

export const interests = ["Nature", "Animals", "Myth", "Geometry", "Words", "Dark art", "Memory"] as const;
export const placements = ["Forearm", "Upper arm", "Calf", "Thigh", "Back", "Ribs", "Hand", "Neck"] as const;
export const tones = [
  { id: "light", label: "Light", hex: "#f1d3bd" },
  { id: "medium", label: "Medium", hex: "#c98f6b" },
  { id: "tan", label: "Tan", hex: "#9a6a48" },
  { id: "deep", label: "Deep", hex: "#5a3a28" },
] as const;

export type Interest = (typeof interests)[number];
export type Placement = (typeof placements)[number];
export type Tone = (typeof tones)[number]["id"];

export type Direction = { style: string; idea: string; why: string };

const byInterest: Record<Interest, { style: string; idea: string }[]> = {
  Nature: [
    { style: "Botanical fine line", idea: "wildflowers, ferns or a single branch that follows the muscle" },
    { style: "Black & grey landscape", idea: "a forest, mountain or river scene wrapped around the limb" },
  ],
  Animals: [
    { style: "Realism", idea: "a portrait of the animal with soft grey shading" },
    { style: "Neo-traditional", idea: "the animal framed with bold lines and ornamental detail" },
  ],
  Myth: [
    { style: "Blackwork illustration", idea: "a deity, creature or symbol in etched, engraving-style lines" },
    { style: "Ornamental", idea: "a mythic symbol set inside mandala or filigree work" },
  ],
  Geometry: [
    { style: "Geometric dotwork", idea: "sacred geometry built from stippled gradients" },
    { style: "Minimal line", idea: "clean shapes and negative space, small and precise" },
  ],
  Words: [
    { style: "Script", idea: "a short line in hand-drawn lettering that follows the body" },
    { style: "Fine line with symbol", idea: "a word paired with a tiny matching icon" },
  ],
  "Dark art": [
    { style: "Blackwork", idea: "heavy black, skulls, serpents or gothic ornament" },
    { style: "Dark surrealism", idea: "dream-like scenes in deep black and grey" },
  ],
  Memory: [
    { style: "Micro realism", idea: "a small portrait, date or object that holds the memory" },
    { style: "Fine line", idea: "a handwriting copy, a birth flower or a simple outline" },
  ],
};

const placementNote: Record<Placement, string> = {
  Forearm: "The forearm is a long, flat canvas: vertical pieces read best and you see them every day.",
  "Upper arm": "The upper arm takes round, medium pieces well and is easy to cover or show.",
  Calf: "The calf suits tall compositions that wrap slightly, like scenes and botanicals.",
  Thigh: "The thigh gives the most room for detail and is one of the easier spots to sit for.",
  Back: "The back is the biggest canvas: go larger and symmetric, it carries detail for decades.",
  Ribs: "Ribs suit flowing, light pieces. It is a tender spot, so shorter sessions work better.",
  Hand: "Hands fade faster: bolder lines and simpler shapes hold up best.",
  Neck: "The neck is always visible: small, bold and simple ages best there.",
};

const toneNote: Record<Tone, string> = {
  light: "On lighter skin, fine lines and soft grey shading show clearly.",
  medium: "On medium skin, black and grey reads beautifully; keep fine lines a touch bolder.",
  tan: "On tan skin, strong outlines and clear contrast keep the piece crisp as it heals.",
  deep: "On deeper skin, bold black, open spacing and high contrast look striking and age best.",
};

export function suggest(interest: Interest, placement: Placement, tone: Tone): Direction[] {
  let picks = byInterest[interest];
  // fine detail does not hold on hands / neck, or with very low contrast: lead with the bolder option
  const bold = placement === "Hand" || placement === "Neck" || tone === "deep";
  if (bold) picks = [...picks].sort((a) => (/fine|micro|minimal/i.test(a.style) ? 1 : -1));
  return picks.map((p, i) => ({
    ...p,
    why: i === 0 ? placementNote[placement] : toneNote[tone],
  }));
}
