import axios from "axios";

const api = axios.create({
  baseURL:
    import.meta.env.VITE_API_URL ||
    (import.meta.env.DEV ? "http://127.0.0.1:8000" : "/"),
  timeout: 15000,
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response) {
      console.error("API error", error.response.status, error.response.data);
    } else {
      console.error("Network error", error.message);
    }
    return Promise.reject(error);
  }
);

export const fetchScreenshots = async ({
  page = 1,
  pageSize = 50,
  filter = "all",
  category,
  search,
  groupId,
}) => {
  const params = { page, page_size: pageSize, filter };
  if (category) params.category = category;
  if (search) params.search = search;
  if (groupId) params.group_id = groupId;
  const { data } = await api.get("/screenshots", { params });
  return data;
};

export const fetchScreenshot = async (id) => {
  const { data } = await api.get(`/screenshots/${id}`);
  return data;
};

export const updateScreenshot = async (id, payload) => {
  const { data } = await api.put(`/screenshots/${id}`, payload);
  return data;
};

export const batchUpdateScreenshots = async (payload) => {
  const { data } = await api.post("/screenshots/batch", payload);
  return data;
};

export const fetchCategories = async () => {
  const { data } = await api.get("/categories");
  return data;
};

export const createCategory = async (payload) => {
  const { data } = await api.post("/categories", payload);
  return data;
};

export const updateCategory = async (id, payload) => {
  const { data } = await api.put(`/categories/${id}`, payload);
  return data;
};

export const deleteCategory = async (id) => {
  const { data } = await api.delete(`/categories/${id}`);
  return data;
};

export const fetchLexicon = async () => {
  const { data } = await api.get("/lexicon");
  return data;
};

export const createLexiconEntry = async (payload) => {
  const { data } = await api.post("/lexicon", payload);
  return data;
};

export const deleteLexiconEntry = async (id) => {
  const { data } = await api.delete(`/lexicon/${id}`);
  return data;
};

export const reclassifyScreenshots = async (payload) => {
  const { data } = await api.post("/screenshots/reclassify", payload);
  return data;
};

export default api;
