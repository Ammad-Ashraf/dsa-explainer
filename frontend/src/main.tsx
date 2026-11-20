import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { createBrowserRouter, RouterProvider } from "react-router-dom";
import { Layout } from "./components/Layout";
import { NotFound, RouteError } from "./components/RouteError";
import Home from "./pages/Home";
import { LessonPage, LessonsPage } from "./pages/Lessons";
import { AlgorithmPage, LibraryPage } from "./pages/Library";
import SettingsPage from "./pages/Settings";
import { Composer, JobPage } from "./pages/Studio";
import "./styles.css";

const pages = [
  { path: "/", element: <Home /> },
  { path: "/studio", element: <Composer /> },
  { path: "/studio/job/:jobId", element: <JobPage /> },
  { path: "/library", element: <LibraryPage /> },
  { path: "/library/:algorithmId", element: <AlgorithmPage /> },
  { path: "/lessons", element: <LessonsPage /> },
  { path: "/lessons/:lessonId", element: <LessonPage /> },
  { path: "/settings", element: <SettingsPage /> },
  { path: "*", element: <NotFound /> },
];

const router = createBrowserRouter([
  {
    element: <Layout />,
    errorElement: <RouteError />, // the layout itself failed: last resort
    // a page that fails is replaced by an error screen inside the layout, so the header and footer stay
    children: [{ errorElement: <RouteError />, children: pages }],
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
