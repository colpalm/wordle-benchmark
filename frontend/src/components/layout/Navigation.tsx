"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const navItems = [
  { href: "/games", label: "Games" },
  { href: "/analytics", label: "Analytics" },
  { href: "/about", label: "About" },
];

export default function Navigation() {
  const pathname = usePathname();

  return (
    <header className="border-b border-[var(--color-border)] bg-[var(--color-background)]">
      <div className="container mx-auto px-4 py-4">
        <div className="flex items-center justify-between">
          <Link href="/" className="flex items-center space-x-3 text-xl font-bold text-[var(--color-text)]">
            <span>Word(le) Benchmark</span>
            <div className="flex space-x-1">
              <div
                className="w-5 h-5 rounded border-2 flex items-center justify-center text-white font-bold text-xs tile-flip"
                style={{
                  backgroundColor: "var(--color-wordle-green)",
                  borderColor: "var(--color-wordle-green)",
                }}
                title="Correct letter"
              >
                L
              </div>
              <div
                className="w-5 h-5 rounded border-2 flex items-center justify-center text-white font-bold text-xs tile-flip"
                style={{
                  backgroundColor: "var(--color-wordle-yellow)",
                  borderColor: "var(--color-wordle-yellow)",
                }}
                title="Letter in word, wrong position"
              >
                L
              </div>
              <div
                className="w-5 h-5 rounded border-2 flex items-center justify-center text-white font-bold text-xs tile-flip bg-neutral-600 border-neutral-600"
                title="Letter not in word"
              >
                M
              </div>
            </div>
          </Link>

          <nav className="flex space-x-3">
            {navItems.map(({ href, label }) => (
              <Link
                key={href}
                href={href}
                className={`px-3 py-2 rounded-md transition-colors ${
                  pathname === href
                    ? "bg-[var(--color-primary)] text-white"
                    : "text-[var(--color-text)] hover:bg-[var(--color-section-background)]"
                }`}
              >
                {label}
              </Link>
            ))}
          </nav>
        </div>
      </div>
    </header>
  );
}
