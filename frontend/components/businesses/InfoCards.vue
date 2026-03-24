<script setup lang="ts">
import {
  MapPin,
  Phone,
  Mail,
  ExternalLink,
  Star,
  Clock,
  CreditCard,
  AlertTriangle,
  Calendar,
} from "lucide-vue-next";
import type { BusinessDetail } from "~/types";
import { formatDate } from "~/utils/formatters";

const props = defineProps<{
  business: BusinessDetail;
}>();

const emit = defineEmits<{
  refresh: [];
}>();

const { patchStatus } = useBusinessActions();
const toast = useToast();

const RESET_STATUSES = [
  "searched",
  "enriched",
  "generated",
  "tested",
  "deployed",
] as const;

const resetTo = ref("");
const resetPending = ref(false);

async function handleReset() {
  if (!resetTo.value) return;
  resetPending.value = true;
  try {
    await patchStatus(props.business.place_id, resetTo.value);
    toast.push(`Status reset to ${resetTo.value}`, "success");
    emit("refresh");
  } catch (e) {
    toast.push(e instanceof Error ? e.message : "Reset failed", "error");
  } finally {
    resetPending.value = false;
    resetTo.value = "";
  }
}

const hasContact = computed(
  () => props.business.address || props.business.phone || props.business.email || props.business.maps_url,
);

const hasScores = computed(
  () => props.business.lead_score > 0 || props.business.rating > 0,
);

const hasBusinessInfo = computed(
  () =>
    props.business.types?.length ||
    props.business.opening_hours_summary ||
    props.business.editorial_summary,
);

const hasReviews = computed(
  () => props.business.review_texts && props.business.review_texts.length > 0,
);

const hasSiteDeployment = computed(() => !!props.business.vercel_url);

const hasTesting = computed(() => props.business.test_iterations > 0);

const hasError = computed(() => !!props.business.error_detail);
</script>

<template>
  <div class="grid grid-cols-1 gap-4 md:grid-cols-2">
    <!-- Contact Card -->
    <div v-if="hasContact" class="card bg-base-200 card-compact">
      <div class="card-body">
        <h3 class="card-title text-sm">Contact</h3>
        <div class="space-y-2 text-sm">
          <div v-if="business.address" class="flex items-start gap-2">
            <MapPin class="h-4 w-4 shrink-0 text-base-content/60" />
            <span>{{ business.address }}</span>
          </div>
          <div v-if="business.phone" class="flex items-center gap-2">
            <Phone class="h-4 w-4 shrink-0 text-base-content/60" />
            <a :href="`tel:${business.phone}`" class="link link-primary">
              {{ business.phone }}
            </a>
          </div>
          <div v-if="business.email" class="flex items-center gap-2">
            <Mail class="h-4 w-4 shrink-0 text-base-content/60" />
            <a :href="`mailto:${business.email}`" class="link link-primary">
              {{ business.email }}
            </a>
          </div>
          <div v-if="business.maps_url" class="flex items-center gap-2">
            <ExternalLink class="h-4 w-4 shrink-0 text-base-content/60" />
            <a
              :href="business.maps_url"
              target="_blank"
              rel="noopener"
              class="link link-primary"
            >
              View on Google Maps
            </a>
          </div>
        </div>
      </div>
    </div>

    <!-- Scores Card -->
    <div v-if="hasScores" class="card bg-base-200 card-compact">
      <div class="card-body">
        <h3 class="card-title text-sm">Scores</h3>
        <div class="space-y-3">
          <div v-if="business.lead_score > 0">
            <div class="flex items-center justify-between text-sm">
              <span>Lead Score</span>
              <span class="font-semibold">{{ business.lead_score }}/100</span>
            </div>
            <progress
              class="progress progress-primary w-full"
              :value="business.lead_score"
              max="100"
            />
          </div>
          <div v-if="business.rating > 0" class="flex items-center gap-2 text-sm">
            <Star class="h-4 w-4 text-warning" />
            <span class="font-medium">{{ business.rating.toFixed(1) }}</span>
            <span class="text-base-content/60">({{ business.reviews }} reviews)</span>
          </div>
          <div v-if="business.price_level" class="text-sm text-base-content/60">
            Price: {{ business.price_level }}
          </div>
        </div>
      </div>
    </div>

    <!-- Business Info Card -->
    <div v-if="hasBusinessInfo" class="card bg-base-200 card-compact">
      <div class="card-body">
        <h3 class="card-title text-sm">Business Info</h3>
        <div class="space-y-2 text-sm">
          <div v-if="business.types?.length" class="flex flex-wrap gap-1">
            <span
              v-for="type in business.types"
              :key="type"
              class="badge badge-outline badge-xs"
            >
              {{ type.replace(/_/g, " ") }}
            </span>
          </div>
          <div v-if="business.business_status" class="text-base-content/60">
            Status: {{ business.business_status }}
          </div>
          <div v-if="business.opening_hours_summary" class="flex items-start gap-2">
            <Clock class="h-4 w-4 shrink-0 text-base-content/60" />
            <span>{{ business.opening_hours_summary }}</span>
          </div>
          <div v-if="business.accepts_credit_cards !== null" class="flex items-center gap-2">
            <CreditCard class="h-4 w-4 text-base-content/60" />
            <span>{{ business.accepts_credit_cards ? "Accepts cards" : "Cash only" }}</span>
          </div>
          <p v-if="business.editorial_summary" class="text-base-content/70 italic">
            {{ business.editorial_summary }}
          </p>
        </div>
      </div>
    </div>

    <!-- Reviews Card -->
    <div v-if="hasReviews" class="card bg-base-200 card-compact">
      <div class="card-body">
        <h3 class="card-title text-sm">Reviews</h3>
        <div class="space-y-2">
          <blockquote
            v-for="(review, i) in business.review_texts"
            :key="i"
            class="border-l-2 border-base-300 pl-3 text-sm text-base-content/70 italic"
          >
            "{{ review }}"
          </blockquote>
        </div>
      </div>
    </div>

    <!-- Site & Deployment Card -->
    <div v-if="hasSiteDeployment" class="card bg-base-200 card-compact">
      <div class="card-body">
        <h3 class="card-title text-sm">Site & Deployment</h3>
        <div class="space-y-2 text-sm">
          <div class="flex items-center gap-2">
            <ExternalLink class="h-4 w-4 text-base-content/60" />
            <a
              :href="business.vercel_url ?? undefined"
              target="_blank"
              rel="noopener"
              class="link link-primary"
            >
              {{ business.vercel_url }}
            </a>
          </div>
          <div v-if="business.email_sent_at" class="text-base-content/60">
            Email sent: {{ formatDate(business.email_sent_at) }}
          </div>
        </div>
      </div>
    </div>

    <!-- Testing Card -->
    <div v-if="hasTesting" class="card bg-base-200 card-compact">
      <div class="card-body">
        <h3 class="card-title text-sm">Testing</h3>
        <div class="text-sm">
          <p>Iterations: {{ business.test_iterations }}</p>
          <details v-if="business.test_issues?.length" class="mt-2">
            <summary class="cursor-pointer text-base-content/60">
              {{ business.test_issues.length }} issues
            </summary>
            <ul class="mt-1 space-y-1 pl-4">
              <li
                v-for="(issue, i) in business.test_issues"
                :key="i"
                class="text-xs text-base-content/60"
              >
                {{ typeof issue === "object" ? JSON.stringify(issue) : issue }}
              </li>
            </ul>
          </details>
        </div>
      </div>
    </div>

    <!-- Error Card -->
    <div v-if="hasError" class="card bg-error/10 border border-error card-compact">
      <div class="card-body">
        <h3 class="card-title text-sm text-error">
          <AlertTriangle class="h-4 w-4" />
          Error
        </h3>
        <div class="space-y-2 text-sm">
          <p class="text-error">{{ business.error_detail }}</p>
          <div class="flex items-center gap-2">
            <select
              v-model="resetTo"
              class="select select-bordered select-sm"
            >
              <option value="" disabled>Reset to...</option>
              <option v-for="s in RESET_STATUSES" :key="s" :value="s">
                {{ s }}
              </option>
            </select>
            <button
              class="btn btn-warning btn-sm"
              :disabled="!resetTo || resetPending"
              @click="handleReset"
            >
              <span v-if="resetPending" class="loading loading-spinner loading-xs" />
              Reset
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Metadata Card -->
    <div class="card bg-base-200 card-compact">
      <div class="card-body">
        <h3 class="card-title text-sm">
          <Calendar class="h-4 w-4" />
          Metadata
        </h3>
        <div class="space-y-1 text-sm text-base-content/60">
          <p>Created: {{ formatDate(business.created_at) }}</p>
          <p>Updated: {{ formatDate(business.updated_at) }}</p>
        </div>
      </div>
    </div>
  </div>
</template>
