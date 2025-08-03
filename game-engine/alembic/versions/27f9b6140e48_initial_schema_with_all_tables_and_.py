"""Initial schema with all tables and indexes

Revision ID: 27f9b6140e48
Revises:
Create Date: 2025-07-11 21:15:29.517280

"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "27f9b6140e48"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create games table
    op.create_table(
        "games",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("model_name", sa.String(length=100), nullable=False),
        sa.Column("template_name", sa.String(length=20), nullable=False),
        sa.Column("parser_name", sa.String(length=20), nullable=False),
        sa.Column("target_word", sa.String(length=5), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("guesses_count", sa.Integer(), nullable=False),
        sa.Column("won", sa.Boolean(), nullable=False),
        sa.Column("duration_seconds", sa.Float(), nullable=False),
        sa.Column("total_invalid_attempts", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create game_turns table
    op.create_table(
        "game_turns",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("game_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("turn_number", sa.Integer(), nullable=False),
        sa.Column("guess", sa.String(length=5), nullable=False),
        sa.Column("reasoning", sa.Text(), nullable=True),
        sa.Column("is_correct", sa.Boolean(), nullable=False),
        sa.Column("letter_results", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["game_id"], ["games.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create llm_interactions table
    op.create_table(
        "llm_interactions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("game_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("turn_number", sa.Integer(), nullable=False),
        sa.Column("prompt_text", sa.Text(), nullable=False),
        sa.Column("raw_response", sa.Text(), nullable=False),
        sa.Column("parse_success", sa.Boolean(), nullable=False),
        sa.Column("parse_error_message", sa.Text(), nullable=True),
        sa.Column("attempt_number", sa.Integer(), nullable=False),
        sa.Column("response_time_ms", sa.Integer(), nullable=True),
        # Usage tracking fields
        sa.Column("prompt_tokens", sa.Integer(), nullable=True),
        sa.Column("completion_tokens", sa.Integer(), nullable=True),
        sa.Column("reasoning_tokens", sa.Integer(), nullable=True),
        sa.Column("total_tokens", sa.Integer(), nullable=True),
        sa.Column("cost_usd", sa.Numeric(precision=10, scale=6), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["game_id"], ["games.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create invalid_word_attempts table
    op.create_table(
        "invalid_word_attempts",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("game_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("turn_number", sa.Integer(), nullable=False),
        sa.Column("attempted_word", sa.String(length=5), nullable=False),
        sa.Column("attempt_number", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["game_id"], ["games.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create indexes
    op.create_index("idx_games_daily_active", "games", ["model_name", "date"])
    op.create_index("idx_games_date_status", "games", ["date", "status", "won"])
    op.create_index("idx_games_model_performance", "games", ["model_name", "won", "guesses_count"])
    op.create_index("idx_games_target_word", "games", ["target_word", "won"])
    op.create_index("idx_game_turns_game_id", "game_turns", ["game_id", "turn_number"])
    op.create_index("idx_llm_interactions_game_id", "llm_interactions", ["game_id", "turn_number"])
    op.create_index("idx_invalid_attempts_game_id", "invalid_word_attempts", ["game_id"])

    # Create game usage summary view
    op.execute("""
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
    """)


def downgrade() -> None:
    """Downgrade schema."""
    # Drop view first
    op.execute("DROP VIEW IF EXISTS game_usage_summary;")

    # Drop indexes
    op.drop_index("idx_invalid_attempts_game_id", table_name="invalid_word_attempts")
    op.drop_index("idx_llm_interactions_game_id", table_name="llm_interactions")
    op.drop_index("idx_game_turns_game_id", table_name="game_turns")
    op.drop_index("idx_games_target_word", table_name="games")
    op.drop_index("idx_games_model_performance", table_name="games")
    op.drop_index("idx_games_date_status", table_name="games")
    op.drop_index("idx_games_daily_active", table_name="games")

    # Drop tables (in reverse order due to foreign keys)
    op.drop_table("invalid_word_attempts")
    op.drop_table("llm_interactions")
    op.drop_table("game_turns")
    op.drop_table("games")
