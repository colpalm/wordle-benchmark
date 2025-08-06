export default function AboutPage() {
  return (
    <div className="container mx-auto px-4 py-8 max-w-4xl">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-[var(--color-text)] mb-4">
          About Wordle Benchmark
        </h1>
        <p className="text-lg text-[var(--color-text-secondary)] mb-6">
          Evaluating Large Language Model performance on Wordle gameplay through systematic testing and analysis.
        </p>
      </div>

      <div className="space-y-8">
        {/* Project Overview */}
        <div className="bg-[var(--color-section-background)] rounded-lg p-6 border border-[var(--color-border)]">
          <h2 className="text-xl font-semibold text-[var(--color-text)] mb-4">
            Project Overview
          </h2>
          <p className="text-[var(--color-text-secondary)] mb-4">
            This project systematically evaluates how different Large Language Models (LLMs) perform at Wordle, 
            the popular word-guessing game. By running automated games with various models, we can analyze 
            their reasoning capabilities, strategic thinking, and word knowledge.
          </p>
          <p className="text-[var(--color-text-secondary)]">
            Each model plays using the same rules and constraints as human players, providing insights into 
            their linguistic reasoning and problem-solving approaches.
          </p>
        </div>

        {/* Methodology */}
        <div className="bg-[var(--color-section-background)] rounded-lg p-6 border border-[var(--color-border)]">
          <h2 className="text-xl font-semibold text-[var(--color-text)] mb-4">
            Methodology
          </h2>
          <ul className="space-y-2 text-[var(--color-text-secondary)]">
            <li>• <strong>Daily Games:</strong> Models play the official Wordle game each day</li>
            <li>• <strong>Standard Rules:</strong> 6 attempts maximum, valid English words only</li>
            <li>• <strong>Reasoning Capture:</strong> Each guess includes the model's reasoning</li>
            <li>• <strong>Performance Tracking:</strong> Win rate, average guesses, response times</li>
            <li>• <strong>Fair Comparison:</strong> All models use identical prompts and constraints</li>
          </ul>
        </div>

        {/* Models Tested */}
        <div className="bg-[var(--color-section-background)] rounded-lg p-6 border border-[var(--color-border)]">
          <h2 className="text-xl font-semibold text-[var(--color-text)] mb-4">
            Models Tested
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <h3 className="font-medium text-[var(--color-text)] mb-2">OpenAI Models</h3>
              <ul className="text-sm text-[var(--color-text-secondary)] space-y-1">
                <li>• GPT-4o-mini</li>
                <li>• GPT-4o</li>
                <li>• O3</li>
              </ul>
            </div>
            <div>
              <h3 className="font-medium text-[var(--color-text)] mb-2">Anthropic Models</h3>
              <ul className="text-sm text-[var(--color-text-secondary)] space-y-1">
                <li>• Claude Sonnet 4</li>
                <li>• Claude Opus 4</li>
              </ul>
            </div>
            <div>
              <h3 className="font-medium text-[var(--color-text)] mb-2">Google Models</h3>
              <ul className="text-sm text-[var(--color-text-secondary)] space-y-1">
                <li>• Gemini 2.5 Flash</li>
                <li>• Gemini 2.5 Pro</li>
              </ul>
            </div>
          </div>
        </div>

        {/* Technical Details */}
        <div className="bg-[var(--color-section-background)] rounded-lg p-6 border border-[var(--color-border)]">
          <h2 className="text-xl font-semibold text-[var(--color-text)] mb-4">
            Technical Details
          </h2>
          <p className="text-[var(--color-text-secondary)] mb-4">
            Built with Python 3.12+ for the game engine and Next.js with TypeScript for the frontend. 
            The system integrates with the New York Times Wordle API to fetch daily puzzles and uses 
            OpenRouter for LLM API access.
          </p>
          <div className="flex flex-wrap gap-2">
            <span className="px-3 py-1 bg-[var(--color-primary)] text-white text-sm rounded-full">Python</span>
            <span className="px-3 py-1 bg-[var(--color-primary)] text-white text-sm rounded-full">Next.js</span>
            <span className="px-3 py-1 bg-[var(--color-primary)] text-white text-sm rounded-full">TypeScript</span>
            <span className="px-3 py-1 bg-[var(--color-primary)] text-white text-sm rounded-full">PostgreSQL</span>
            <span className="px-3 py-1 bg-[var(--color-primary)] text-white text-sm rounded-full">Docker</span>
          </div>
        </div>

        {/* Contact */}
        <div className="bg-[var(--color-section-background)] rounded-lg p-6 border border-[var(--color-border)]">
          <h2 className="text-xl font-semibold text-[var(--color-text)] mb-4">
            Project Information
          </h2>
          <p className="text-[var(--color-text-secondary)]">
            This is an experimental project exploring AI capabilities in word games. 
            The results provide insights into model reasoning but should not be considered 
            comprehensive evaluations of overall model capabilities.
          </p>
        </div>
      </div>
    </div>
  );
}