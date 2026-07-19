import { createContext, useContext, useState, useCallback, useEffect, ReactNode } from "react";
import { api, Dataset } from "../api/client";
import { useDefaultProject } from "./useDefaultProject";

interface DatasetsContextValue {
  datasets: Dataset[];
  selectedDataset: Dataset | null;
  setSelectedDataset: (dataset: Dataset | null) => void;
  refreshDatasets: () => Promise<void>;
  uploadDataset: (file: File) => Promise<Dataset>;
  projectLoading: boolean;
  projectError: string | null;
}

const DatasetsContext = createContext<DatasetsContextValue | null>(null);

export function DatasetsProvider({ children }: { children: ReactNode }) {
  const { project, loading: projectLoading, error: projectError } = useDefaultProject();
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [selectedDataset, setSelectedDataset] = useState<Dataset | null>(null);

  const refreshDatasets = useCallback(async () => {
    if (!project) return;
    const list = await api.listDatasets(project.id);
    setDatasets(list);
    setSelectedDataset((current) => current ?? list[0] ?? null);
  }, [project]);

  const uploadDataset = useCallback(
    async (file: File) => {
      if (!project) throw new Error("No active project yet");
      const dataset = await api.uploadDataset(project.id, file);
      setDatasets((prev) => [dataset, ...prev]);
      setSelectedDataset(dataset);
      return dataset;
    },
    [project]
  );

  useEffect(() => {
    refreshDatasets();
  }, [refreshDatasets]);

  return (
    <DatasetsContext.Provider
      value={{ datasets, selectedDataset, setSelectedDataset, refreshDatasets, uploadDataset, projectLoading, projectError }}
    >
      {children}
    </DatasetsContext.Provider>
  );
}

export function useDatasets() {
  const ctx = useContext(DatasetsContext);
  if (!ctx) throw new Error("useDatasets must be used within DatasetsProvider");
  return ctx;
}
