export default function HomePage() {
  return (
    <div className="container mx-auto px-4 py-8">
      {/* Header Section */}
      <div className="mb-8 text-center">
        <h1 className="text-4xl font-bold text-[var(--color-text)] mb-4">
          LLM Wordle Performance Leaderboard
        </h1>
        <p className="text-lg text-[var(--color-text-secondary)] mb-6 max-w-2xl mx-auto">
          Comparing how different Large Language Models perform at Wordle. 
          Updated daily with new games and comprehensive performance metrics.
        </p>
        
        {/* Quick Stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 max-w-2xl mx-auto">
          <div className="bg-[var(--color-section-background)] rounded-lg p-4 border border-[var(--color-border)]">
            <div className="text-2xl font-bold text-[var(--color-primary)]">847</div>
            <div className="text-sm text-[var(--color-text-secondary)]">Total Games</div>
          </div>
          <div className="bg-[var(--color-section-background)] rounded-lg p-4 border border-[var(--color-border)]">
            <div className="text-2xl font-bold text-[var(--color-primary)]">7</div>
            <div className="text-sm text-[var(--color-text-secondary)]">Models</div>
          </div>
          <div className="bg-[var(--color-section-background)] rounded-lg p-4 border border-[var(--color-border)]">
            <div className="text-2xl font-bold text-[var(--color-primary)]">78%</div>
            <div className="text-sm text-[var(--color-text-secondary)]">Avg Win Rate</div>
          </div>
          <div className="bg-[var(--color-section-background)] rounded-lg p-4 border border-[var(--color-border)]">
            <div className="text-2xl font-bold text-[var(--color-primary)]">4.2</div>
            <div className="text-sm text-[var(--color-text-secondary)]">Avg Guesses</div>
          </div>
        </div>
      </div>

      {/* Leaderboard Table */}
      <div className="bg-[var(--color-section-background)] rounded-lg border border-[var(--color-border)] overflow-hidden">
        <div className="px-6 py-4 border-b border-[var(--color-border)]">
          <h2 className="text-xl font-semibold text-[var(--color-text)]">
            Model Performance Rankings
          </h2>
        </div>
        
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-[var(--color-background)]">
              <tr className="text-left">
                <th className="px-6 py-3 text-sm font-medium text-[var(--color-text)] border-b border-[var(--color-border)]">
                  Rank
                </th>
                <th className="px-6 py-3 text-sm font-medium text-[var(--color-text)] border-b border-[var(--color-border)]">
                  Model
                </th>
                <th className="px-6 py-3 text-sm font-medium text-[var(--color-text)] border-b border-[var(--color-border)]">
                  Win Rate
                </th>
                <th className="px-6 py-3 text-sm font-medium text-[var(--color-text)] border-b border-[var(--color-border)]">
                  Avg Guesses
                </th>
                <th className="px-6 py-3 text-sm font-medium text-[var(--color-text)] border-b border-[var(--color-border)]">
                  Games Played
                </th>
                <th className="px-6 py-3 text-sm font-medium text-[var(--color-text)] border-b border-[var(--color-border)]">
                  Recent Games
                </th>
              </tr>
            </thead>
            <tbody>
              {[
                { rank: 1, model: "GPT-4o", winRate: "87%", avgGuesses: "3.8", games: 142, color: "#6aaa64" },
                { rank: 2, model: "Claude Sonnet 4", winRate: "83%", avgGuesses: "4.1", games: 138, color: "#6aaa64" },
                { rank: 3, model: "O3", winRate: "81%", avgGuesses: "4.0", games: 124, color: "#c9b458" },
                { rank: 4, model: "Gemini 2.5 Pro", winRate: "78%", avgGuesses: "4.3", games: 119, color: "#c9b458" },
                { rank: 5, model: "Claude Opus 4", winRate: "74%", avgGuesses: "4.4", games: 115, color: "#c9b458" },
                { rank: 6, model: "GPT-4o-mini", winRate: "69%", avgGuesses: "4.6", games: 109, color: "#787c7e" },
                { rank: 7, model: "Gemini 2.5 Flash", winRate: "65%", avgGuesses: "4.8", games: 100, color: "#787c7e" },
              ].map((row) => (
                <tr key={row.rank} className="hover:bg-[var(--color-background)] transition-colors">
                  <td className="px-6 py-4 text-sm text-[var(--color-text)] border-b border-[var(--color-border)]">
                    #{row.rank}
                  </td>
                  <td className="px-6 py-4 text-sm font-medium text-[var(--color-text)] border-b border-[var(--color-border)]">
                    {row.model}
                  </td>
                  <td className="px-6 py-4 text-sm text-[var(--color-text)] border-b border-[var(--color-border)]">
                    <span className="font-medium" style={{ color: row.color }}>
                      {row.winRate}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-sm text-[var(--color-text)] border-b border-[var(--color-border)]">
                    {row.avgGuesses}
                  </td>
                  <td className="px-6 py-4 text-sm text-[var(--color-text-secondary)] border-b border-[var(--color-border)]">
                    {row.games}
                  </td>
                  <td className="px-6 py-4 border-b border-[var(--color-border)]">
                    <div className="flex space-x-1">
                      {Array.from({ length: 5 }, (_, i) => (
                        <div 
                          key={i}
                          className="w-4 h-4 rounded-sm"
                          style={{ 
                            backgroundColor: i < 3 ? '#6aaa64' : i === 3 ? '#c9b458' : '#787c7e'
                          }}
                          title={i < 3 ? 'Won' : i === 3 ? 'Won in 6' : 'Lost'}
                        />
                      ))}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Last Updated */}
      <div className="mt-6 text-center text-sm text-[var(--color-text-secondary)]">
        Last updated: January 15, 2024 • Next update in 18 hours
      </div>
    </div>
  );
}
