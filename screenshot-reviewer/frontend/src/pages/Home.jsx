import { useEffect, useState } from "react";
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
import useSelectionStore from "../store/selectionStore.js";

const PAGE_SIZE = 50;

export default function Home() {
  const queryClient = useQueryClient();
  const [filter, setFilter] = useState("all");
  const [search, setSearch] = useState("");
  const [categoryFilter, setCategoryFilter] = useState("all");
  const [groupId, setGroupId] = useState(null);
  const [activeScreenshot, setActiveScreenshot] = useState(null);
  const [batchCategory, setBatchCategory] = useState("none");

  const { page, setPage, selected, clear, setSelection, setTriggerSave } = useSelectionStore();

  const screenshotsQuery = useQuery({
    queryKey: ["screenshots", { page, filter, search, categoryFilter, groupId }],
    queryFn: () =>
      fetchScreenshots({
        page,
        pageSize: PAGE_SIZE,
        filter,
        search,
        category: categoryFilter === "all" ? undefined : categoryFilter,
        groupId,
      }),
    keepPreviousData: true,
  });

  const categoriesQuery = useQuery({
    queryKey: ["categories"],
    queryFn: fetchCategories,
  });

  const lexiconQuery = useQuery({
    queryKey: ["lexicon"],
    queryFn: fetchLexicon,
  });

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
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["categories"] }),
  });

  const deleteCategoryMutation = useMutation({
    mutationFn: (id) => deleteCategory(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["categories"] }),
  });

  const renameCategoryMutation = useMutation({
    mutationFn: ({ id, name }) => updateCategory(id, { name }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["categories"] }),
  });

  const createLexiconMutation = useMutation({
    mutationFn: (payload) => createLexiconEntry(payload),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["lexicon"] }),
  });

  const deleteLexiconMutation = useMutation({
    mutationFn: (id) => deleteLexiconEntry(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["lexicon"] }),
  });

  const screenshots = screenshotsQuery.data?.items ?? [];
  const totalPages = screenshotsQuery.data?.total_pages ?? 1;
  const progress = screenshotsQuery.data?.progress ?? { reviewed: 0, deferred: 0, remaining: 0 };
  const groupMeta = screenshotsQuery.data?.groups ?? { items: [], current_index: 0 };

  useEffect(() => {
    setTriggerSave(() => () => {});
  }, [setTriggerSave]);

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

  const handleModalSave = (draft) => {
    setActiveScreenshot(null);
    updateMutation.mutate({ id: draft.id, payload: draft });
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

  const categoryList = (categoriesQuery.data ?? []).map((cat) => ({
    ...cat,
    count: cat.count ?? 0,
    pending: cat.pending ?? 0,
  }));

  const lexiconEntries = lexiconQuery.data ?? [];

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-slate-100">
      <Sidebar
        categories={categoryList}
        activeCategory={categoryFilter}
        onSelect={(value) => {
          setCategoryFilter(value);
          setPage(1);
        }}
        onCreate={(name) => createCategoryMutation.mutate(name)}
        onDelete={(id) => deleteCategoryMutation.mutate(id)}
        onRename={(id, name) => renameCategoryMutation.mutate({ id, name })}
      />
      <main className="flex min-w-0 flex-1 flex-col">
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
        <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-200 bg-slate-50 px-6 py-3 text-sm">
          <div className="flex items-center gap-3">
            <select
              className="rounded border border-slate-200 px-3 py-2"
              value={batchCategory}
              onChange={(event) => setBatchCategory(event.target.value)}
            >
              <option value="none">Assign to…</option>
              {categoryList.map((category) => (
                <option key={category.id} value={category.id}>
                  {category.name}
                </option>
              ))}
            </select>
            <button
              type="button"
              className="rounded bg-brand-500 px-3 py-2 text-sm font-medium text-white hover:bg-brand-600 disabled:opacity-40"
              disabled={!selected.size || batchCategory === "none"}
              onClick={() => handleAssignCategory(batchCategory)}
            >
              Apply category
            </button>
            <button
              type="button"
              className="rounded border border-red-200 px-3 py-2 text-sm text-red-500 hover:border-red-400 hover:text-red-600 disabled:opacity-40"
              disabled={!selected.size}
              onClick={handleDelete}
            >
              Mark for deletion
            </button>
          </div>
          <span className="text-slate-500">{selected.size} selected</span>
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
        />
      </main>
      <LexiconPanel
        entries={lexiconEntries}
        onCreate={(payload) => createLexiconMutation.mutate(payload)}
        onDelete={(id) => deleteLexiconMutation.mutate(id)}
      />
      <ScreenshotModal
        isOpen={Boolean(activeScreenshot)}
        screenshot={activeScreenshot}
        suggestions={activeScreenshot?.suggestions || []}
        onClose={() => setActiveScreenshot(null)}
        onSave={handleModalSave}
      />
    </div>
  );
}
