import Image from "next/image";

/**
 * Image slot. Shows the photo when `src` is set, otherwise a labelled placeholder
 * so missing client assets never block the build.
 */
export default function Frame({
  src,
  alt,
  label,
  className = "",
  sizes = "50vw",
}: {
  src?: string;
  alt: string;
  label: string;
  className?: string;
  sizes?: string;
}) {
  return (
    <div className={`relative overflow-hidden bg-panel ${className}`}>
      {src ? (
        <Image src={src} alt={alt} fill sizes={sizes} className="object-cover" />
      ) : (
        <div
          className="absolute inset-0 flex items-end p-5"
          style={{
            background:
              "radial-gradient(120% 80% at 80% 0%, rgba(255,43,214,.16), transparent 60%), radial-gradient(90% 70% at 0% 100%, rgba(139,92,246,.14), transparent 60%)",
          }}
        >
          <span className="absolute left-4 top-4 h-3 w-3 border-l border-t border-neon/60" />
          <span className="absolute right-4 top-4 h-3 w-3 border-r border-t border-neon/60" />
          <span className="absolute bottom-4 right-4 h-3 w-3 border-b border-r border-neon/60" />
          <span className="label">{label}</span>
        </div>
      )}
      <div className="pointer-events-none absolute inset-0 ring-1 ring-inset ring-line" />
    </div>
  );
}
