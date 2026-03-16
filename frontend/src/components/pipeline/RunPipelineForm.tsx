import { useState } from "react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useListBusinessesBusinessesGet } from "@/api/endpoints/businesses/businesses";
import {
  usePipelineRunPipelineRunPost,
  usePipelineEnrichPipelineEnrichPost,
  usePipelineGeneratePipelineGeneratePost,
  usePipelineTestPipelineTestPost,
  usePipelineDeployPipelineDeployPost,
  usePipelineEmailPipelineEmailPost,
} from "@/api/endpoints/pipeline/pipeline";

type PipelineStepOption =
  | "run"
  | "enrich"
  | "generate"
  | "test"
  | "deploy"
  | "email";

interface RunPipelineFormProps {
  onJobStarted: (jobId: string) => void;
}

export default function RunPipelineForm({ onJobStarted }: RunPipelineFormProps) {
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [step, setStep] = useState<PipelineStepOption>("run");
  const [model, setModel] = useState("");
  const [testModel, setTestModel] = useState("");
  const [maxFixIterations, setMaxFixIterations] = useState<string>("");
  const [noEmail, setNoEmail] = useState(false);
  const [playwright, setPlaywright] = useState(false);
  const [onlyMedia, setOnlyMedia] = useState(false);

  const { data: businessesData } = useListBusinessesBusinessesGet();
  const businesses = businessesData?.data ?? [];

  const runMutation = usePipelineRunPipelineRunPost();
  const enrichMutation = usePipelineEnrichPipelineEnrichPost();
  const generateMutation = usePipelineGeneratePipelineGeneratePost();
  const testMutation = usePipelineTestPipelineTestPost();
  const deployMutation = usePipelineDeployPipelineDeployPost();
  const emailMutation = usePipelineEmailPipelineEmailPost();

  const isPending =
    runMutation.isPending ||
    enrichMutation.isPending ||
    generateMutation.isPending ||
    testMutation.isPending ||
    deployMutation.isPending ||
    emailMutation.isPending;

  const toggleId = (placeId: string) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(placeId)) {
        next.delete(placeId);
      } else {
        next.add(placeId);
      }
      return next;
    });
  };

  const toggleAll = () => {
    if (selectedIds.size === businesses.length) {
      setSelectedIds(new Set());
    } else {
      setSelectedIds(
        new Set(businesses.map((b) => (b as Record<string, string>).place_id)),
      );
    }
  };

  const placeIds = Array.from(selectedIds);

  const handleSuccess = (jobId: string) => {
    toast.success(`Job started (${jobId.slice(0, 8)}...)`);
    onJobStarted(jobId);
  };

  const handleError = (error: unknown) => {
    toast.error(
      `Failed: ${error instanceof Error ? error.message : "Unknown error"}`,
    );
  };

  const handleSubmit = () => {
    if (placeIds.length === 0) return;

    const opts = {
      onSuccess: (r: { data: { job_id: string } }) =>
        handleSuccess(r.data.job_id),
      onError: handleError,
    };

    switch (step) {
      case "run":
        runMutation.mutate(
          {
            data: {
              place_ids: placeIds,
              model: model || undefined,
              test_model: testModel || undefined,
              max_fix_iterations: maxFixIterations
                ? parseInt(maxFixIterations)
                : undefined,
              no_email: noEmail,
              playwright,
            },
          },
          opts,
        );
        break;
      case "enrich":
        enrichMutation.mutate(
          { data: { place_ids: placeIds, only_media: onlyMedia } },
          opts,
        );
        break;
      case "generate":
        generateMutation.mutate(
          { data: { place_ids: placeIds, model: model || undefined } },
          opts,
        );
        break;
      case "test":
        testMutation.mutate(
          {
            data: {
              place_ids: placeIds,
              playwright,
              max_fix_iterations: maxFixIterations
                ? parseInt(maxFixIterations)
                : undefined,
              model: testModel || undefined,
            },
          },
          opts,
        );
        break;
      case "deploy":
        deployMutation.mutate({ data: { place_ids: placeIds } }, opts);
        break;
      case "email":
        emailMutation.mutate(
          { data: { place_ids: placeIds, model: model || undefined } },
          opts,
        );
        break;
    }
  };

  return (
    <div className="space-y-4">
      <Tabs
        value={step}
        onValueChange={(v) => setStep(v as PipelineStepOption)}
      >
        <TabsList>
          <TabsTrigger value="run">Full Run</TabsTrigger>
          <TabsTrigger value="enrich">Enrich</TabsTrigger>
          <TabsTrigger value="generate">Generate</TabsTrigger>
          <TabsTrigger value="test">Test</TabsTrigger>
          <TabsTrigger value="deploy">Deploy</TabsTrigger>
          <TabsTrigger value="email">Email</TabsTrigger>
        </TabsList>

        <TabsContent value="run" className="space-y-3">
          <div className="grid gap-3 md:grid-cols-2">
            <div className="space-y-1">
              <Label>Model</Label>
              <Input
                placeholder="Default model"
                value={model}
                onChange={(e) => setModel(e.target.value)}
              />
            </div>
            <div className="space-y-1">
              <Label>Test Model</Label>
              <Input
                placeholder="Default test model"
                value={testModel}
                onChange={(e) => setTestModel(e.target.value)}
              />
            </div>
          </div>
          <div className="grid gap-3 md:grid-cols-3">
            <div className="space-y-1">
              <Label>Max Fix Iterations</Label>
              <Input
                type="number"
                min={0}
                value={maxFixIterations}
                onChange={(e) => setMaxFixIterations(e.target.value)}
              />
            </div>
            <div className="flex items-center gap-2 pt-6">
              <Switch checked={noEmail} onCheckedChange={setNoEmail} />
              <Label>No Email</Label>
            </div>
            <div className="flex items-center gap-2 pt-6">
              <Switch checked={playwright} onCheckedChange={setPlaywright} />
              <Label>Playwright</Label>
            </div>
          </div>
        </TabsContent>

        <TabsContent value="enrich" className="space-y-3">
          <div className="flex items-center gap-2">
            <Switch checked={onlyMedia} onCheckedChange={setOnlyMedia} />
            <Label>Only Media</Label>
          </div>
        </TabsContent>

        <TabsContent value="generate" className="space-y-3">
          <div className="space-y-1">
            <Label>Model</Label>
            <Input
              placeholder="Default model"
              value={model}
              onChange={(e) => setModel(e.target.value)}
            />
          </div>
        </TabsContent>

        <TabsContent value="test" className="space-y-3">
          <div className="grid gap-3 md:grid-cols-3">
            <div className="space-y-1">
              <Label>Test Model</Label>
              <Input
                placeholder="Default test model"
                value={testModel}
                onChange={(e) => setTestModel(e.target.value)}
              />
            </div>
            <div className="space-y-1">
              <Label>Max Fix Iterations</Label>
              <Input
                type="number"
                min={0}
                value={maxFixIterations}
                onChange={(e) => setMaxFixIterations(e.target.value)}
              />
            </div>
            <div className="flex items-center gap-2 pt-6">
              <Switch checked={playwright} onCheckedChange={setPlaywright} />
              <Label>Playwright</Label>
            </div>
          </div>
        </TabsContent>

        <TabsContent value="deploy">
          <p className="text-sm text-muted-foreground">
            No additional options for deploy.
          </p>
        </TabsContent>

        <TabsContent value="email" className="space-y-3">
          <div className="space-y-1">
            <Label>Model</Label>
            <Input
              placeholder="Default model"
              value={model}
              onChange={(e) => setModel(e.target.value)}
            />
          </div>
        </TabsContent>
      </Tabs>

      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <Label>Select Businesses ({selectedIds.size} selected)</Label>
          {businesses.length > 0 && (
            <Button variant="ghost" size="sm" onClick={toggleAll}>
              {selectedIds.size === businesses.length
                ? "Deselect all"
                : "Select all"}
            </Button>
          )}
        </div>
        <div className="max-h-48 space-y-1 overflow-auto rounded border p-2">
          {businesses.length === 0 ? (
            <p className="text-sm text-muted-foreground">
              No businesses available
            </p>
          ) : (
            businesses.map((b) => {
              const biz = b as Record<string, string>;
              return (
                <label
                  key={biz.place_id}
                  className="flex cursor-pointer items-center gap-2 rounded px-2 py-1 hover:bg-muted"
                >
                  <Checkbox
                    checked={selectedIds.has(biz.place_id)}
                    onCheckedChange={() => toggleId(biz.place_id)}
                  />
                  <span className="text-sm">{biz.name ?? biz.place_id}</span>
                </label>
              );
            })
          )}
        </div>
      </div>

      <Button
        onClick={handleSubmit}
        disabled={isPending || selectedIds.size === 0}
      >
        {isPending
          ? "Starting..."
          : `Run ${step === "run" ? "Pipeline" : step} (${selectedIds.size})`}
      </Button>
    </div>
  );
}
