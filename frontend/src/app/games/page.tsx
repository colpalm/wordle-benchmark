export default function GamesPage() {
  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-[var(--color-text)] mb-4">
          Individual Games
        </h1>
        <p className="text-[var(--color-text-secondary)] mb-6">
          View detailed Wordle game results with reasoning for each guess.
        </p>
        
        {/* Date picker will go here */}
        <div className="mb-6 p-4 bg-[var(--color-section-background)] rounded-lg border border-[var(--color-border)]">
          <p className="text-sm text-[var(--color-text-secondary)]">
            📅 Date picker component will go here
          </p>
        </div>
      </div>

      {/* Games grid will go here */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {/* Placeholder game cards */}
        {[1, 2, 3, 4, 5, 6].map((i) => (
          <div 
            key={i}
            className="bg-[var(--color-section-background)] rounded-lg p-6 border border-[var(--color-border)]"
          >
            <div className="mb-4">
              <h3 className="font-semibold text-[var(--color-text)] mb-2">
                GPT-4o-mini
              </h3>
              <p className="text-sm text-[var(--color-text-secondary)]">
                Target: ADIEU • Won in 4 guesses
              </p>
            </div>
            
            {/* Wordle grid placeholder */}
            <div className="mb-4">
              <div className="grid grid-cols-5 gap-1 w-fit">
                {Array.from({ length: 20 }, (_, i) => (
                  <div 
                    key={i}
                    className="w-8 h-8 border border-[var(--color-border)] rounded flex items-center justify-center text-sm font-bold"
                    style={{ 
                      backgroundColor: i < 15 ? 
                        (i % 3 === 0 ? '#6aaa64' : i % 3 === 1 ? '#c9b458' : '#787c7e') 
                        : 'transparent' 
                    }}
                  >
                    {i < 15 ? String.fromCharCode(65 + (i % 26)) : ''}
                  </div>
                ))}
              </div>
            </div>
            
            <button className="text-sm text-[var(--color-primary)] hover:text-[var(--color-accent)] transition-colors">
              Show reasoning →
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}