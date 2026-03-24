<script setup lang="ts">
import {
  Search,
  Sparkles,
  Code,
  TestTube,
  Rocket,
  Mail,
  Check,
  X,
  Loader2,
} from "lucide-vue-next";
import type { Component } from "vue";

const props = defineProps<{
  status: string;
}>();

const STEPS = [
  { key: "search", label: "Search", icon: Search },
  { key: "enrich", label: "Enrich", icon: Sparkles },
  { key: "generate", label: "Generate", icon: Code },
  { key: "test", label: "Test", icon: TestTube },
  { key: "deploy", label: "Deploy", icon: Rocket },
  { key: "email", label: "Email", icon: Mail },
] as const;

const STATUS_ORDER: Record<string, number> = {
  searched: 0,
  running_enrich: 0,
  error_enrich: 0,
  enriched: 1,
  running_generate: 1,
  error_generate: 1,
  generated: 2,
  running_test: 2,
  error_test: 2,
  tested: 3,
  running_deploy: 3,
  error_deploy: 3,
  deployed: 4,
  running_email: 4,
  error_email: 4,
  email_queued: 5,
  emailed: 5,
  error_run: 0,
  opted_out: -1,
};

type NodeState = "completed" | "running" | "error" | "current" | "future";

function getNodeState(stepIndex: number, status: string): NodeState {
  const currentIndex = STATUS_ORDER[status] ?? -1;
  const isRunning = status.startsWith("running_");
  const isError = status.startsWith("error_");

  if (stepIndex < currentIndex) return "completed";
  if (stepIndex === currentIndex) {
    if (isRunning) return "running";
    if (isError) return "error";
    return "current";
  }
  return "future";
}

const NODE_CLASSES: Record<NodeState, string> = {
  completed: "border-success bg-success/10 text-success",
  running: "border-info bg-info/10 text-info",
  error: "border-error bg-error/10 text-error",
  current: "border-primary bg-primary/10 text-primary ring-2 ring-primary/30",
  future: "border-base-300 bg-base-200/50 text-base-content/40",
};

function getNodeIcon(state: NodeState): Component {
  if (state === "completed") return Check;
  if (state === "error") return X;
  if (state === "running") return Loader2;
  return Check; // placeholder, actual icon comes from step
}

const nodes = computed(() =>
  STEPS.map((step, i) => {
    const state = getNodeState(i, props.status);
    return {
      ...step,
      state,
      classes: NODE_CLASSES[state],
      showStepIcon: state === "current" || state === "future",
    };
  }),
);
</script>

<template>
  <div class="flex items-center gap-2 overflow-x-auto py-2">
    <template v-for="(node, i) in nodes" :key="node.key">
      <div
        :class="[
          'flex flex-col items-center gap-1 rounded-lg border-2 px-3 py-2 min-w-[72px]',
          node.classes,
        ]"
      >
        <component
          :is="node.showStepIcon ? node.icon : getNodeIcon(node.state)"
          :class="[
            'h-4 w-4',
            node.state === 'running' ? 'animate-spin' : '',
          ]"
        />
        <span class="text-xs font-medium">{{ node.label }}</span>
      </div>
      <div
        v-if="i < nodes.length - 1"
        :class="[
          'h-0.5 w-4 shrink-0',
          nodes[i].state === 'completed'
            ? 'bg-success'
            : 'bg-base-300',
        ]"
      />
    </template>
  </div>
</template>
