import { site } from "@/content/site";

const links = [
  ["Story", "#story"],
  ["Process", "#process"],
  ["Work", "#work"],
  ["Ideas", "#ideas"],
];

export default function Nav() {
  return (
    <header className="fixed inset-x-0 top-0 z-50 flex items-center justify-between px-5 py-5 md:px-10">
      <a href="#top" className="font-display text-2xl tracking-tight">
        Ink<span className="italic text-neon">Lusion</span>
        <span className="sr-only">{site.name}</span>
      </a>
      <nav className="hidden gap-9 md:flex">
        {links.map(([name, href]) => (
          <a key={href} href={href} className="label transition-colors hover:text-ink">
            {name}
          </a>
        ))}
      </nav>
      <a href="#book" className="btn !px-5 !py-2.5 backdrop-blur-sm">
        Book
      </a>
    </header>
  );
}
