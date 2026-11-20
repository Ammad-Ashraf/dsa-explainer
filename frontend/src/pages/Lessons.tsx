import { useState } from "react";
import { Link, useNavigate, useParams, useSearchParams } from "react-router-dom";
import { algorithmById, formatDate, formatSeconds, useCatalog, useDeleteLesson, useLesson, useLessons } from "../api";
import { Emblem } from "../components/art";
import { LessonView } from "../components/LessonView";
import { Button, ErrorNotice, LevelTag, LinkButton, Loading } from "../components/ui";

export function LessonsPage() {
  const { data: lessons, isLoading, error } = useLessons();
  const { data: catalog } = useCatalog();
  const remove = useDeleteLesson();
  const [query, setQuery] = useState("");
  const shown = (lessons ?? []).filter((l) => `${l.title} ${l.topic} ${l.structure}`.toLowerCase().includes(query.toLowerCase()));
  return (
    <div className="container page">
      <div className="page-head">
        <div className="row">
          <h1 className="page-title">My lessons</h1>
          <LinkButton to="/studio" small>New lesson</LinkButton>
        </div>
        <p>Every lesson made on this computer, with all its versions. They stay here, on your machine.</p>
      </div>
      {lessons && lessons.length > 0 && (
        <div className="toolbar">
          <input className="input" type="search" placeholder="Search your lessons" value={query} onChange={(e) => setQuery(e.target.value)} aria-label="Search your lessons" />
          <span className="small">{lessons.length} lesson{lessons.length === 1 ? "" : "s"}</span>
        </div>
      )}
      {isLoading && <Loading what="Loading your lessons" />}
      <ErrorNotice error={error ?? remove.error} />
      {lessons?.length === 0 && (
        <div className="empty">
          <p className="lead ink">No lessons yet.</p>
          <p>Make one in the <Link to="/studio">Studio</Link>, or watch one from the <Link to="/library">library</Link>.</p>
        </div>
      )}
      {shown.map((l) => {
        const algo = algorithmById(catalog, l.structure);
        return (
          <div key={l.id} className="lesson-row">
            <Emblem category={algo?.category ?? "linear"} size={48} />
            <div>
              <h3><Link to={`/lessons/${l.id}`} style={{ color: "inherit" }}>{l.title}</Link></h3>
              <div className="sub">
                <span>{algo?.title ?? l.structure}</span><span>{formatSeconds(l.seconds)}</span>
                <span>{l.versions} version{l.versions === 1 ? "" : "s"}</span><span>{formatDate(l.created)}</span>
                <LevelTag level={l.level} />
              </div>
            </div>
            <div className="actions-row">
              <LinkButton to={`/lessons/${l.id}`} small variant="secondary">Open</LinkButton>
              <Button small variant="danger" disabled={remove.isPending}
                onClick={() => { if (confirm(`Delete “${l.title}” and all its versions? This cannot be undone.`)) remove.mutate(l.id); }}>Delete</Button>
            </div>
          </div>
        );
      })}
    </div>
  );
}

export function LessonPage() {
  const { lessonId } = useParams();
  const [params, setParams] = useSearchParams();
  const navigate = useNavigate();
  const version = params.get("version") ? Number(params.get("version")) : undefined;
  const { data: lesson, isLoading, error } = useLesson(lessonId, version);
  return (
    <div className="container page" style={{ maxWidth: 1060 }}>
      <p style={{ marginBottom: 20 }}><button type="button" className="btn btn-ghost" onClick={() => navigate("/lessons")}>← My lessons</button></p>
      {isLoading && <Loading what="Opening the lesson" />}
      <ErrorNotice error={error} />
      {lesson && <LessonView lesson={lesson} onVersion={(v) => setParams({ version: String(v) })} />}
    </div>
  );
}
