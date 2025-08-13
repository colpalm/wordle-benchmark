"""Database schema definitions for views and custom SQL.

This module contains SQL definitions for database views, functions, and other
custom schema elements that need to be shared between migrations and tests.
"""

# Game usage summary view for LLM interaction analytics
GAME_USAGE_SUMMARY_VIEW = """
    CREATE VIEW game_usage_summary AS
    SELECT
        game_id,
        SUM(prompt_tokens) as total_tokens_input,
        SUM(completion_tokens) as total_tokens_output,
        SUM(reasoning_tokens) as total_tokens_reasoning,
        SUM(total_tokens) as total_tokens_all,
        SUM(cost_usd) as total_cost_usd,
        AVG(response_time_ms) as response_time_avg_ms,
        COUNT(*) as total_requests
    FROM llm_interactions
    WHERE parse_success = true
    GROUP BY game_id;
"""

# Leaderboard statistics view for model performance comparison
LEADERBOARD_STATS_VIEW = """
    CREATE VIEW leaderboard_stats AS
    SELECT
        model_name,
        COUNT(*) as total_games,
        SUM(CASE WHEN won THEN 1 ELSE 0 END) as wins,
        ROUND(AVG(CASE WHEN won THEN 1.0 ELSE 0.0 END) * 100, 1) as win_rate,
        ROUND(AVG(CASE WHEN won THEN guesses_count::numeric ELSE NULL END), 1) as avg_guesses,
        SUM(golf_score) as total_golf_score,
        MIN(date) as first_game_date,
        MAX(date) as last_game_date
    FROM games
    GROUP BY model_name;
"""

# View cleanup SQL
DROP_GAME_USAGE_SUMMARY_VIEW = "DROP VIEW IF EXISTS game_usage_summary;"
DROP_LEADERBOARD_STATS_VIEW = "DROP VIEW IF EXISTS leaderboard_stats;"
