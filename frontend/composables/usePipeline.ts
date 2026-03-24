import type { JobResponse, SearchRequest } from "~/types";

export function usePipeline() {
  const { apiFetch } = useApi();

  function triggerSearch(body: SearchRequest) {
    return apiFetch<JobResponse>("/pipeline/search", {
      method: "POST",
      body: JSON.stringify(body),
    });
  }

  function triggerEnrich(placeIds: string[]) {
    return apiFetch<JobResponse>("/pipeline/enrich", {
      method: "POST",
      body: JSON.stringify({ place_ids: placeIds }),
    });
  }

  function triggerGenerate(placeIds: string[]) {
    return apiFetch<JobResponse>("/pipeline/generate", {
      method: "POST",
      body: JSON.stringify({ place_ids: placeIds }),
    });
  }

  function triggerTest(placeIds: string[]) {
    return apiFetch<JobResponse>("/pipeline/test", {
      method: "POST",
      body: JSON.stringify({ place_ids: placeIds }),
    });
  }

  function triggerDeploy(placeIds: string[]) {
    return apiFetch<JobResponse>("/pipeline/deploy", {
      method: "POST",
      body: JSON.stringify({ place_ids: placeIds }),
    });
  }

  function triggerEmail(placeIds: string[]) {
    return apiFetch<JobResponse>("/pipeline/email", {
      method: "POST",
      body: JSON.stringify({ place_ids: placeIds }),
    });
  }

  function triggerRun(
    placeIds: string[],
    opts?: {
      model?: string;
      test_model?: string;
      max_fix_iterations?: number;
      no_email?: boolean;
      playwright?: boolean;
    },
  ) {
    return apiFetch<JobResponse>("/pipeline/run", {
      method: "POST",
      body: JSON.stringify({ place_ids: placeIds, ...opts }),
    });
  }

  return {
    triggerSearch,
    triggerEnrich,
    triggerGenerate,
    triggerTest,
    triggerDeploy,
    triggerEmail,
    triggerRun,
  };
}
