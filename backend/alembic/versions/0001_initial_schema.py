"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-08-22
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("username", sa.String(50), nullable=False),
        sa.Column("email", sa.String(320), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("role", sa.String(20), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("role IN ('user', 'admin')", name="role_valid"),
        sa.PrimaryKeyConstraint("id", name="pk_users"),
    )
    op.create_index("uq_users_username_lower", "users", [sa.text("lower(username)")], unique=True)
    op.create_index("uq_users_email_lower", "users", [sa.text("lower(email)")], unique=True)

    op.create_table(
        "people",
        sa.Column("name", sa.String(300), nullable=False),
        sa.Column("birth_date", sa.Date()),
        sa.Column("death_date", sa.Date()),
        sa.Column("biography", sa.Text()),
        sa.Column("profile_url", sa.Text()),
        sa.Column("profile_path", sa.Text()),
        sa.Column("tmdb_id", sa.BigInteger()),
        sa.Column("imdb_id", sa.String(20)),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_people"),
        sa.UniqueConstraint("tmdb_id", name="uq_people_tmdb_id"),
        sa.UniqueConstraint("imdb_id", name="uq_people_imdb_id"),
    )
    op.create_index("ix_people_name", "people", ["name"])

    op.create_table(
        "genres",
        sa.Column("name", sa.String(150), nullable=False),
        sa.Column("tmdb_id", sa.BigInteger()),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_genres"),
        sa.UniqueConstraint("name", name="uq_genres_name"),
        sa.UniqueConstraint("tmdb_id", name="uq_genres_tmdb_id"),
    )

    op.create_table(
        "countries",
        sa.Column("name", sa.String(150), nullable=False),
        sa.Column("iso2", sa.String(2)),
        sa.Column("iso3", sa.String(3)),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_countries"),
        sa.UniqueConstraint("name", name="uq_countries_name"),
        sa.UniqueConstraint("iso2", name="uq_countries_iso2"),
        sa.UniqueConstraint("iso3", name="uq_countries_iso3"),
    )

    op.create_table(
        "languages",
        sa.Column("iso_code", sa.String(10), nullable=False),
        sa.Column("name", sa.String(150), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_languages"),
        sa.UniqueConstraint("iso_code", name="uq_languages_iso_code"),
        sa.UniqueConstraint("name", name="uq_languages_name"),
    )

    op.create_table(
        "studios",
        sa.Column("name", sa.String(300), nullable=False),
        sa.Column("tmdb_id", sa.BigInteger()),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_studios"),
        sa.UniqueConstraint("tmdb_id", name="uq_studios_tmdb_id"),
    )
    op.create_index("ix_studios_name", "studios", ["name"])

    op.create_table(
        "movies",
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("original_title", sa.String(500)),
        sa.Column("release_year", sa.Integer()),
        sa.Column("release_date", sa.Date()),
        sa.Column("runtime_minutes", sa.Integer()),
        sa.Column("overview", sa.Text()),
        sa.Column("editorial_note", sa.Text()),
        sa.Column("poster_url", sa.Text()),
        sa.Column("poster_path", sa.Text()),
        sa.Column("tmdb_id", sa.BigInteger()),
        sa.Column("imdb_id", sa.String(20)),
        sa.Column("created_by_id", sa.Uuid()),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
        sa.Column("deleted_by_id", sa.Uuid()),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("release_year IS NULL OR (release_year >= 1880 AND release_year <= 2200)", name="release_year_range"),
        sa.CheckConstraint("runtime_minutes IS NULL OR runtime_minutes > 0", name="runtime_positive"),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"], name="fk_movies_created_by_id_users", ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["deleted_by_id"], ["users.id"], name="fk_movies_deleted_by_id_users", ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id", name="pk_movies"),
        sa.UniqueConstraint("tmdb_id", name="uq_movies_tmdb_id"),
        sa.UniqueConstraint("imdb_id", name="uq_movies_imdb_id"),
    )
    op.create_index("ix_movies_title", "movies", ["title"])
    op.create_index("ix_movies_release_date", "movies", ["release_date"])

    op.create_table(
        "movie_people",
        sa.Column("movie_id", sa.Uuid(), nullable=False),
        sa.Column("person_id", sa.Uuid(), nullable=False),
        sa.Column("credit_type", sa.String(10), nullable=False),
        sa.Column("job", sa.String(150)),
        sa.Column("character_name", sa.String(300)),
        sa.Column("billing_order", sa.Integer()),
        sa.Column("tmdb_credit_id", sa.String(100)),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.CheckConstraint("credit_type IN ('cast', 'crew')", name="credit_type_valid"),
        sa.CheckConstraint("billing_order IS NULL OR billing_order >= 0", name="billing_order_nonnegative"),
        sa.ForeignKeyConstraint(["movie_id"], ["movies.id"], name="fk_movie_people_movie_id_movies", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["person_id"], ["people.id"], name="fk_movie_people_person_id_people", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name="pk_movie_people"),
    )
    op.create_index("ix_movie_people_movie_id", "movie_people", ["movie_id"])
    op.create_index("ix_movie_people_person_id", "movie_people", ["person_id"])

    for table, target, target_table in [
        ("movie_genres", "genre_id", "genres"),
        ("movie_countries", "country_id", "countries"),
        ("movie_studios", "studio_id", "studios"),
    ]:
        op.create_table(
            table,
            sa.Column("movie_id", sa.Uuid(), nullable=False),
            sa.Column(target, sa.Uuid(), nullable=False),
            sa.ForeignKeyConstraint(["movie_id"], ["movies.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint([target], [f"{target_table}.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("movie_id", target),
        )

    op.create_table(
        "movie_languages",
        sa.Column("movie_id", sa.Uuid(), nullable=False),
        sa.Column("language_id", sa.Uuid(), nullable=False),
        sa.Column("is_original", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(["movie_id"], ["movies.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["language_id"], ["languages.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("movie_id", "language_id"),
    )

    op.create_table(
        "user_movies",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("movie_id", sa.Uuid(), nullable=False),
        sa.Column("rating", sa.Integer()),
        sa.Column("watched", sa.Boolean(), nullable=False),
        sa.Column("favorite", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("rating IS NULL OR (rating >= 0 AND rating <= 100)", name="rating_range"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["movie_id"], ["movies.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id", "movie_id"),
    )

    op.create_table(
        "user_reviews",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("movie_id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(300)),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("contains_spoilers", sa.Boolean(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["movie_id"], ["movies.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "movie_id", name="uq_user_reviews_user_movie_once"),
    )
    op.create_index("ix_user_reviews_user_id", "user_reviews", ["user_id"])
    op.create_index("ix_user_reviews_movie_id", "user_reviews", ["movie_id"])

    op.create_table(
        "external_ratings",
        sa.Column("movie_id", sa.Uuid(), nullable=False),
        sa.Column("source", sa.String(50), nullable=False),
        sa.Column("rating_type", sa.String(50), nullable=False),
        sa.Column("value", sa.Numeric(7, 3), nullable=False),
        sa.Column("scale", sa.Numeric(7, 3), nullable=False),
        sa.Column("vote_count", sa.Integer()),
        sa.Column("source_url", sa.Text()),
        sa.Column("retrieved_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["movie_id"], ["movies.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("movie_id", "source", "rating_type", name="uq_external_ratings_movie_source_type"),
    )
    op.create_index("ix_external_ratings_movie_id", "external_ratings", ["movie_id"])

    op.create_table(
        "movie_links",
        sa.Column("movie_id", sa.Uuid(), nullable=False),
        sa.Column("source", sa.String(50), nullable=False),
        sa.Column("url", sa.String(2000), nullable=False),
        sa.Column("label", sa.String(150)),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["movie_id"], ["movies.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("movie_id", "source", "url", name="uq_movie_links_movie_source_url"),
    )
    op.create_index("ix_movie_links_movie_id", "movie_links", ["movie_id"])

    op.create_table(
        "audit_logs",
        sa.Column("actor_user_id", sa.Uuid()),
        sa.Column("action", sa.String(50), nullable=False),
        sa.Column("entity_type", sa.String(100), nullable=False),
        sa.Column("entity_id", sa.Uuid(), nullable=False),
        sa.Column("before_data", postgresql.JSONB()),
        sa.Column("after_data", postgresql.JSONB()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["actor_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_audit_logs_entity", "audit_logs", ["entity_type", "entity_id"])
    op.create_index("ix_audit_logs_created_at", "audit_logs", ["created_at"])


def downgrade() -> None:
    for table in [
        "audit_logs", "movie_links", "external_ratings", "user_reviews", "user_movies",
        "movie_languages", "movie_studios", "movie_countries", "movie_genres", "movie_people",
        "movies", "studios", "languages", "countries", "genres", "people", "users",
    ]:
        op.drop_table(table)
