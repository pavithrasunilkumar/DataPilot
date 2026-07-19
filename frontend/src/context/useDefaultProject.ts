import { useEffect, useState } from "react";
import { api, Project } from "../api/client";

const DEFAULT_PROJECT_NAME = "My Workspace";

export function useDefaultProject() {
  const [project, setProject] = useState<Project | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    (async () => {
      try {
        const projects = await api.listProjects();
        if (cancelled) return;

        if (projects.length > 0) {
          setProject(projects[0]);
        } else {
          const created = await api.createProject(DEFAULT_PROJECT_NAME);
          if (!cancelled) setProject(created);
        }
      } catch (err) {
        if (!cancelled) setError(err instanceof Error ? err.message : "Failed to load workspace");
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();

    return () => {
      cancelled = true;
    };
  }, []);

  return { project, loading, error };
}
