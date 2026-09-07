import { createBrowserRouter } from "react-router";

import { AppLayout } from "./components/AppLayout";
import { AdminRoute, ProtectedRoute } from "./components/ProtectedRoute";
import { AddMoviePage } from "./pages/AddMoviePage";
import { AdminPage } from "./pages/AdminPage";
import { CatalogPage } from "./pages/CatalogPage";
import { HomePage } from "./pages/HomePage";
import { LoginPage } from "./pages/LoginPage";
import { ListDetailPage } from "./pages/ListDetailPage";
import { ListsPage } from "./pages/ListsPage";
import { MovieDetailPage } from "./pages/MovieDetailPage";
import { MovieEditPage } from "./pages/MovieEditPage";
import { MoviesPage } from "./pages/MoviesPage";
import { NotFoundPage } from "./pages/NotFoundPage";

export const router = createBrowserRouter([
  {
    element: <AppLayout />,
    children: [
      {
        path: "/",
        element: <HomePage />,
      },
      {
        path: "/movies",
        element: <MoviesPage />,
      },
      {
        path: "/lists",
        element: <ListsPage />,
      },
      {
        path: "/lists/:listId",
        element: <ListDetailPage />,
      },
      {
        path: "/movies/:movieId",
        element: <MovieDetailPage />,
      },
      {
        path: "/login",
        element: <LoginPage />,
      },
      {
        element: <ProtectedRoute />,
        children: [
          {
            path: "/movies/add",
            element: <AddMoviePage />,
          },
          {
            path: "/catalog",
            element: <CatalogPage />,
          },
          {
            path: "/movies/:movieId/edit",
            element: <MovieEditPage />,
          },
        ],
      },
      {
        element: <AdminRoute />,
        children: [
          {
            path: "/admin",
            element: <AdminPage />,
          },
        ],
      },
      {
        path: "*",
        element: <NotFoundPage />,
      },
    ],
  },
]);
