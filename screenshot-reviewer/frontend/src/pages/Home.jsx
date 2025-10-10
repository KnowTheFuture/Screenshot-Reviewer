import { useEffect, useMemo, useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  fetchScreenshots,
  fetchCategories,
  fetchLexicon,
  batchUpdateScreenshots,
  updateScreenshot,
  createCategory,
  deleteCategory,
  updateCategory,
  createLexiconEntry,
  deleteLexiconEntry,
} from "../api/client.js";
import Sidebar from "../components/Sidebar.jsx";
import Toolbar from "../components/Toolbar.jsx";
import ScreenshotGrid from "../components/ScreenshotGrid.jsx";
import ScreenshotModal from "../components/ScreenshotModal.jsx";
import LexiconPanel from "../components/LexiconPanel.jsx";
import SettingsModal from "../components/SettingsModal.jsx";
import useSelectionStore from "../store/selectionStore.js";
import useSelectionPersistence from "../hooks/useSelectionPersistence.js";
import useSelectionActions from "../hooks/useSelectionActions.js";
import useCategoryColorStore from "../store/categoryColorStore.js";
import useLocalSettings from "../hooks/useLocalSettings.js";

const computePageSize = (settings) => {
  const cols = Math.max(1, Math.min(10, settings?.gridColumns ?? 5));
  const rows = Math.max(1, Math.min(10, settings?.gridRows ?? 5));
  return cols * rows;
};

export default function Home() {
  const queryClient = useQueryClient();
  const [filter, setFilter] = useState("all");
  const [search, setSearch] = useState("");
  const [categoryFilter, setCategoryFilter] = useState("all");
  const [groupId, setGroupId] = useState(null);
  const [activeScreenshot, setActiveScreenshot] = useState(null);
  const [batchCategory, setBatchCategory] = useState("none");
  const [showSettings, setShowSettings] = useState(false);

  const { page, setPage, selected, clear, setSelection, setTriggerSave } = useSelectionStore();
  const { clearPersistence } = useSelectionPersistence();
  const { markAsPending, isReclassifying } = useSelectionActions();
  const ensureCategoryColor = useCategoryColorStore((state) => state.ensureColor);
  const renameCategoryColor = useCategoryColorStore((state) => state.renameCategoryColor);
  const removeCategoryColor = useCategoryColorStore((state) => state.removeColor);
  const [settings, setSettings] = useLocalSettings();

  const gridColumns = Math.max(1, Math.min(10, settings?.gridColumns ?? 5));
  const gridRows = Math.max(1, Math.min(10, settings?.gridRows ?? 5));
  const gridGap = Math.max(0, Math.min(32, settings?.gridGap ?? 2));
  const pageSize = computePageSize(settings);

  const effectiveFilter = categoryFilter === "pending" ? "pending" : filter;
  const categoryParam = categoryFilter === "all" || categoryFilter === "pending" ? undefined : categoryFilter;

  const screenshotsQuery = useQuery({
    queryKey: ["screenshots", { page, filter: effectiveFilter, search, categoryFilter, groupId, pageSize }],
    queryFn: () =>
      fetchScreenshots({
        page,
        pageSize,
        filter: effectiveFilter,
        search,
        category: categoryParam,
        groupId,
      }),
    keepPreviousData: true,
  });

  const categoriesQuery = useQuery({ queryKey: ["categories"], queryFn: fetchCategories });
  const lexiconQuery = useQuery({ queryKey: ["lexicon"], queryFn: fetchLexicon });

  const batchMutation = useMutation({
    mutationFn: batchUpdateScreenshots,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["screenshots"] });
      queryClient.invalidateQueries({ queryKey: ["categories"] });
      clear();
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, payload }) => updateScreenshot(id, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["screenshots"] });
      queryClient.invalidateQueries({ queryKey: ["categories"] });
    },
  });

  const createCategoryMutation = useMutation({
    mutationFn: (name) => createCategory({ name }),
    onSuccess: (data, name) => {
      if (data?.name) {
        ensureCategoryColor(data.name);
      } else if (typeof name === "string") {
        ensureCategoryColor(name);
      }
      queryClient.invalidateQueries({ queryKey: ["categories"] });
    },
  });

  const deleteCategoryMutation = useMutation({
    mutationFn: ({ id }) => deleteCategory(id),
    onSuccess: (_data, variables) => {
      if (variables?.name) {
        removeCategoryColor(variables.name);
      }
      queryClient.invalidateQueries({ queryKey: ["categories"] });
    },
  });

  const renameCategoryMutation = useMutation({
    mutationFn: ({ id, name }) => updateCategory(id, { name }),
    onSuccess: (data, variables) => {
      if (variables?.previousName || variables?.name) {
        renameCategoryColor(variables.previousName ?? variables.name, data?.name ?? variables.name);
      }
      queryClient.invalidateQueries({ queryKey: ["categories"] });
    },
  });

  const createLexiconMutation = useMutation({
    mutationFn: (payload) => createLexiconEntry(payload),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["lexicon"] }),
  });

  const deleteLexiconMutation = useMutation({
    mutationFn: (id) => deleteLexiconEntry(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["lexicon"] }),
  });

  const screenshots = useMemo(() => {
    const items = screenshotsQuery.data?.items ?? [];
    return items.map((item) => {
      if (item?.primary_category || item?.status === "deleted") {
        return item;
      }
      if (item?.status === "pending") {
        return item;
      }
      return { ...item, status: "pending" };
    });
  }, [screenshotsQuery.data]);
  const totalPages = screenshotsQuery.data?.total_pages ?? 1;
  const progress = screenshotsQuery.data?.progress ?? { reviewed: 0, deferred: 0, remaining: 0 };
  const groupMeta = screenshotsQuery.data?.groups ?? { items: [], current_index: 0 };

  useEffect(() => {
    setTriggerSave(() => () => {});
  }, [setTriggerSave]);

  useEffect(() => {
    if (!Array.isArray(categoriesQuery.data)) return;
    categoriesQuery.data.forEach((category) => ensureCategoryColor(category.name));
  }, [categoriesQuery.data, ensureCategoryColor]);

  useEffect(() => {
    if (page !== 1) {
      setPage(1);
    }
  }, [pageSize, page, setPage]);

  const categoryList = useMemo(() => {
    const raw = categoriesQuery.data;
    if (raw !== undefined && !Array.isArray(raw)) {
      console.warn("⚠️ Unexpected categories response:", raw);
      return [];
    }
    return (Array.isArray(raw) ? raw : []).map((cat) => ({
      ...cat,
      count: cat?.count ?? 0,
      pending: cat?.pending ?? 0,
    }));
  }, [categoriesQuery.data]);

  const lexiconEntries = lexiconQuery.data ?? [];
  const isPendingFilter = effectiveFilter === "pending";
  const emptyMessage = isPendingFilter
    ? "🎉 All screenshots are categorized!"
    : "No screenshots match the current filters.";

  const handleAssignCategory = (categoryId) => {
    if (!selected.size) return;
    batchMutation.mutate({
      ids: Array.from(selected),
      payload: { primary_category: categoryId, status: "reviewed" },
    });
  };

  const handleDelete = () => {
    if (!selected.size) return;
    batchMutation.mutate({
      ids: Array.from(selected),
      payload: { status: "deleted", primary_category: null },
    });
  };

  const handleMarkPending = () => {
    if (!selected.size) return;
    const ids = Array.from(selected);
    if (!ids.length) return;
    const shouldProceed = window.confirm("Move selected screenshots back to Pending?");
    if (!shouldProceed) return;
    markAsPending(ids, {
      onSuccess: () => {
        clear();
      },
    });
  };

  const handleModalSave = (draft) => {
    const payload = { ...draft };
    if (!payload.primary_category) {
      payload.status = "pending";
    }
    setActiveScreenshot(null);
    updateMutation.mutate({ id: payload.id, payload });
  };

  const handleGroupNavigate = (offset) => {
    if (!groupMeta.items.length) return;
    let nextIndex = groupMeta.current_index + offset;
    if (nextIndex < 0) nextIndex = groupMeta.items.length - 1;
    if (nextIndex >= groupMeta.items.length) nextIndex = 0;
    setGroupId(groupMeta.items[nextIndex].group_id);
    setPage(1);
    clear();
  };

  return (
    <div className="app-shell flex h-screen w-screen overflow-hidden">
      <Sidebar
        categories={categoryList}
        activeCategory={categoryFilter}
        onSelect={(value) => {
          setCategoryFilter(value);
          setPage(1);
        }}
        onCreate={(name) => createCategoryMutation.mutate(name)}
        onDelete={(id, name) => deleteCategoryMutation.mutate({ id, name })}
        onRename={(id, name, previousName) => renameCategoryMutation.mutate({ id, name, previousName })}
      />
      <main className="flex min-w-0 flex-1 flex-col overflow-hidden">
        <Toolbar
          filter={filter}
          onFilterChange={(value) => {
            setFilter(value);
            setPage(1);
          }}
          search={search}
          onSearchChange={(value) => {
            setSearch(value);
            setPage(1);
          }}
          progress={progress}
          onGroupPrev={() => handleGroupNavigate(-1)}
          onGroupNext={() => handleGroupNavigate(1)}
          currentGroup={groupMeta.current_index + 1}
          totalGroups={groupMeta.items.length}
        />
        <div className="batch-bar flex flex-wrap items-center justify-between gap-3 px-4 py-2.5 text-sm">
          <div className="flex items-center gap-3">
            <select
              className="rounded border border-theme bg-[var(--surface-color)] px-3 py-2 text-sm text-theme shadow-sm focus:border-[var(--accent-color)] focus:outline-none"
              value={batchCategory}
              onChange={(event) => setBatchCategory(event.target.value)}
            >
              <option value="none">Assign to…
              </option>
              {categoryList.map((category) => (
                <option key={category.id} value={category.id}>
                  {category.name}
                </option>
              ))}
            </select>
            <button
              type="button"
              className="rounded bg-[var(--accent-color)] px-3 py-2 text-sm font-medium text-white shadow-sm transition hover:bg-[var(--accent-strong)] disabled:cursor-not-allowed disabled:opacity-40"
              disabled={!selected.size || batchCategory === "none"}
              onClick={() => handleAssignCategory(batchCategory)}
            >
              Apply category
            </button>
            <button
              type="button"
              className="rounded border border-red-200 px-3 py-2 text-sm font-medium text-red-500 transition hover:border-red-400 hover:bg-[rgba(248,113,113,0.12)] hover:text-red-600 disabled:cursor-not-allowed disabled:opacity-40"
              disabled={!selected.size}
              onClick={handleDelete}
            >
              Mark for deletion
            </button>
            <button
              type="button"
              className="rounded border border-amber-300 px-3 py-2 text-sm font-medium text-amber-600 transition hover:border-amber-400 hover:bg-[rgba(251,191,36,0.12)] hover:text-amber-700 disabled:cursor-not-allowed disabled:opacity-40"
              disabled={!selected.size || isReclassifying}
              onClick={handleMarkPending}
            >
              Mark as Pending
            </button>
          </div>
          <span className="text-muted">{selected.size} selected</span>
        </div>
        <ScreenshotGrid
          screenshots={screenshots}
          selected={selected}
          onSelectionChange={setSelection}
          onOpen={(screenshot) => setActiveScreenshot(screenshot)}
          page={page}
          totalPages={totalPages}
          onPageChange={(value) => {
            setPage(value);
            clear();
          }}
          categoryFilter={categoryFilter}
          gridColumns={gridColumns}
          gridRows={gridRows}
          gridGap={gridGap}
          pageSize={pageSize}
        />
        {screenshots.length === 0 && (
          <div className="mt-8 text-center text-muted">{emptyMessage}</div>
        )}
      </main>
      <LexiconPanel
        entries={lexiconEntries}
        onCreate={(payload) => createLexiconMutation.mutate(payload)}
        onDelete={(id) => deleteLexiconMutation.mutate(id)}
        onOpenSettings={() => setShowSettings(true)}
      />
      <ScreenshotModal
        isOpen={Boolean(activeScreenshot)}
        screenshot={activeScreenshot}
        suggestions={activeScreenshot?.suggestions || []}
        onClose={() => setActiveScreenshot(null)}
        onSave={handleModalSave}
      />
      <SettingsModal
        isOpen={showSettings}
        onClose={() => setShowSettings(false)}
        onClearSelection={clearPersistence}
        categories={categoryList}
        settings={settings}
        onChangeSettings={setSettings}
      />
    </div>
  );
}
