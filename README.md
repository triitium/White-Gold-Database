# White Gold Database

White Gold Database (WGDB) is a small hobby project of mine for keeping track of movies in my own database.

It started out as an Excel sheet and eventually turned into a proper web app because apparently a spreadsheet wasn't complicated enough.

The database contains movie metadata, posters, genres, cast/crew, external ratings and some personal stuff like watched status, favourites, ratings and reviews.

Movie data and posters can also be pulled from TMDB.

## Tech

The project uses:

- Python / FastAPI
- PostgreSQL
- SQLAlchemy
- React
- TypeScript
- Vite
- Podman
- nginx

The production version runs on a small server using rootless Podman containers and systemd Quadlets.

## Features

- browse and search movies
- filter by year and genre
- TMDB import and poster enrichment
- user accounts
- ratings from 0–100
- watched / favourite status
- reviews
- admin tools
- audit log

Ratings are also displayed as 0–5 white "Bricks", because stars would have been too normal.

## Live version

https://wgdb.insignita.de

## TMDB

This product uses the TMDB API but is not endorsed or certified by TMDB.
