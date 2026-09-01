import { Link } from "react-router";

export function NotFoundPage() {
  return (
    <div className="empty-state empty-state--page">
      <h1>404</h1>
      <p>This page does not exist.</p>
      <Link to="/movies" className="button">
        Back to movies
      </Link>
    </div>
  );
}
