export default function AnalyticsPage() {
  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-[var(--color-text)] mb-4">
          Analytics
        </h1>
        <p className="text-[var(--color-text-secondary)] mb-6">
          Deep insights into model performance, trends, and patterns.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Win Rate Trends */}
        <div className="bg-[var(--color-section-background)] rounded-lg p-6 border border-[var(--color-border)]">
          <h2 className="text-xl font-semibold text-[var(--color-text)] mb-4">
            Win Rate Trends
          </h2>
          <div className="h-64 bg-white rounded border border-[var(--color-border)] flex items-center justify-center">
            <p className="text-[var(--color-text-secondary)]">📈 Chart placeholder</p>
          </div>
        </div>

        {/* Average Guesses Distribution */}
        <div className="bg-[var(--color-section-background)] rounded-lg p-6 border border-[var(--color-border)]">
          <h2 className="text-xl font-semibold text-[var(--color-text)] mb-4">
            Guess Distribution
          </h2>
          <div className="h-64 bg-white rounded border border-[var(--color-border)] flex items-center justify-center">
            <p className="text-[var(--color-text-secondary)]">📊 Chart placeholder</p>
          </div>
        </div>

        {/* Performance by Word Difficulty */}
        <div className="bg-[var(--color-section-background)] rounded-lg p-6 border border-[var(--color-border)]">
          <h2 className="text-xl font-semibold text-[var(--color-text)] mb-4">
            Performance by Word Difficulty
          </h2>
          <div className="h-64 bg-white rounded border border-[var(--color-border)] flex items-center justify-center">
            <p className="text-[var(--color-text-secondary)]">🎯 Chart placeholder</p>
          </div>
        </div>

        {/* Response Time Analysis */}
        <div className="bg-[var(--color-section-background)] rounded-lg p-6 border border-[var(--color-border)]">
          <h2 className="text-xl font-semibold text-[var(--color-text)] mb-4">
            Response Time Analysis
          </h2>
          <div className="h-64 bg-white rounded border border-[var(--color-border)] flex items-center justify-center">
            <p className="text-[var(--color-text-secondary)]">⏱️ Chart placeholder</p>
          </div>
        </div>
      </div>

      {/* Summary Stats */}
      <div className="mt-8 grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-[var(--color-section-background)] rounded-lg p-6 border border-[var(--color-border)] text-center">
          <div className="text-2xl font-bold text-[var(--color-primary)] mb-2">847</div>
          <div className="text-sm text-[var(--color-text-secondary)]">Total Games</div>
        </div>
        <div className="bg-[var(--color-section-background)] rounded-lg p-6 border border-[var(--color-border)] text-center">
          <div className="text-2xl font-bold text-[var(--color-primary)] mb-2">78%</div>
          <div className="text-sm text-[var(--color-text-secondary)]">Overall Win Rate</div>
        </div>
        <div className="bg-[var(--color-section-background)] rounded-lg p-6 border border-[var(--color-border)] text-center">
          <div className="text-2xl font-bold text-[var(--color-primary)] mb-2">4.2</div>
          <div className="text-sm text-[var(--color-text-secondary)]">Avg Guesses</div>
        </div>
        <div className="bg-[var(--color-section-background)] rounded-lg p-6 border border-[var(--color-border)] text-center">
          <div className="text-2xl font-bold text-[var(--color-primary)] mb-2">2.3s</div>
          <div className="text-sm text-[var(--color-text-secondary)]">Avg Response Time</div>
        </div>
      </div>
    </div>
  );
}