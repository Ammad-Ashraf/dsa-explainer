import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { createBrowserRouter, Link, RouterProvider } from "react-router-dom";
import { Layout } from "./components/Layout";
import Home from "./pages/Home";
import { LessonPage, LessonsPage } from "./pages/Lessons";
import { AlgorithmPage, LibraryPage } from "./pages/Library";
import SettingsPage from "./pages/Settings";
import { Composer, JobPage } from "./pages/Studio";
import "./styles.css";

function NotFound() {
  return (
    <div className="container page empty">
      <h1 className="page-title">This page is not here</h1>
      <p style={{ marginTop: 12 }}><Link to="/">Go home</Link> or <Link to="/library">browse the library</Link>.</p>
    </div>
  );
}

const router = createBrowserRouter([
  {
    element: <Layout />,
    children: [
      { path: "/", element: <Home /> },
      { path: "/studio", element: <Composer /> },
      { path: "/studio/job/:jobId", element: <JobPage /> },
      { path: "/library", element: <LibraryPage /> },
      { path: "/library/:algorithmId", element: <AlgorithmPage /> },
      { path: "/lessons", element: <LessonsPage /> },
      { path: "/lessons/:lessonId", element: <LessonPage /> },
      { path: "/settings", element: <SettingsPage /> },
      { path: "*", element: <NotFound /> },
    ],
  },
]);

const queryClient = new QueryClient({ defaultOptions: { queries: { retry: 1, refetchOnWindowFocus: false } } });

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <RouterProvider router={router} />
    </QueryClientProvider>
  </StrictMode>,
);
