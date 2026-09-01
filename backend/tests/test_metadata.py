import app.models  # noqa: F401
from app.db.base import Base


def test_expected_tables_registered():
    expected = {
        "users", "movies", "people", "movie_people", "genres", "movie_genres",
        "countries", "movie_countries", "languages", "movie_languages", "studios",
        "movie_studios", "user_movies", "user_reviews", "external_ratings", "movie_links",
        "audit_logs",
    }
    assert set(Base.metadata.tables) == expected
