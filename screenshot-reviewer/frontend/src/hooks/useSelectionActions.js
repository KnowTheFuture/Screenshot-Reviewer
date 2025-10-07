import { useMutation, useQueryClient } from "@tanstack/react-query";

import { reclassifyScreenshots } from "../api/client.js";

export default function useSelectionActions() {
  const queryClient = useQueryClient();

  const reclassifyMutation = useMutation({
    mutationFn: ({ ids, newCategory }) => reclassifyScreenshots({
      ids,
      new_category: newCategory,
    }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["screenshots"] });
      queryClient.invalidateQueries({ queryKey: ["categories"] });
    },
  });

  const markAsPending = (ids, options) =>
    reclassifyMutation.mutate(
      { ids, newCategory: "pending" },
      options
    );

  return {
    markAsPending,
    isReclassifying: reclassifyMutation.isPending,
  };
}
