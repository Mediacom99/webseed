<script setup lang="ts">
import { ChevronDown } from "lucide-vue-next";
import { formatType } from "~/utils/formatters";

const model = defineModel<string[]>({ default: () => [] });

const open = ref(false);
const containerRef = ref<HTMLElement | null>(null);

const TYPE_GROUPS = [
  {
    label: "Food & Drink",
    types: [
      "restaurant",
      "cafe",
      "bar",
      "bakery",
      "meal_delivery",
      "meal_takeaway",
      "food",
    ],
  },
  {
    label: "Beauty & Wellness",
    types: [
      "beauty_salon",
      "hair_care",
      "spa",
      "nail_salon",
      "skin_care",
      "tanning_studio",
    ],
  },
  {
    label: "Health",
    types: [
      "dentist",
      "doctor",
      "physiotherapist",
      "veterinary_care",
      "pharmacy",
      "optician",
    ],
  },
  {
    label: "Automotive",
    types: [
      "car_repair",
      "car_wash",
      "car_dealer",
      "gas_station",
      "auto_parts_store",
    ],
  },
  {
    label: "Accommodation",
    types: ["lodging", "hotel", "bed_and_breakfast", "hostel", "campground"],
  },
  {
    label: "Fitness",
    types: ["gym", "yoga_studio", "pilates_studio", "swimming_pool"],
  },
  {
    label: "Retail",
    types: [
      "store",
      "clothing_store",
      "shoe_store",
      "jewelry_store",
      "furniture_store",
      "florist",
      "pet_store",
      "book_store",
      "electronics_store",
      "hardware_store",
    ],
  },
  {
    label: "Services",
    types: [
      "laundry",
      "locksmith",
      "plumber",
      "electrician",
      "painter",
      "moving_company",
      "real_estate_agency",
      "insurance_agency",
      "accounting",
      "lawyer",
      "travel_agency",
    ],
  },
] as const;

function toggle(type: string) {
  const idx = model.value.indexOf(type);
  if (idx >= 0) {
    model.value = model.value.filter((t) => t !== type);
  } else {
    model.value = [...model.value, type];
  }
}

function remove(type: string) {
  model.value = model.value.filter((t) => t !== type);
}

function handleClickOutside(e: MouseEvent) {
  if (containerRef.value && !containerRef.value.contains(e.target as Node)) {
    open.value = false;
  }
}

function handleKeydown(e: KeyboardEvent) {
  if (e.key === "Escape") open.value = false;
}

onMounted(() => {
  document.addEventListener("mousedown", handleClickOutside);
  document.addEventListener("keydown", handleKeydown);
});

onUnmounted(() => {
  document.removeEventListener("mousedown", handleClickOutside);
  document.removeEventListener("keydown", handleKeydown);
});
</script>

<template>
  <div ref="containerRef" class="relative">
    <label class="label">
      <span class="label-text">Business Types</span>
    </label>

    <button
      type="button"
      class="btn btn-outline btn-sm w-full justify-between"
      @click="open = !open"
    >
      {{ model.length > 0 ? `${model.length} selected` : "Select types..." }}
      <ChevronDown class="h-4 w-4" />
    </button>

    <!-- Selected chips -->
    <div v-if="model.length > 0" class="mt-2 flex flex-wrap gap-1">
      <span
        v-for="type in model"
        :key="type"
        class="badge badge-primary badge-sm gap-1"
      >
        {{ formatType(type) }}
        <button
          type="button"
          class="ml-0.5 hover:text-primary-content/70"
          @click="remove(type)"
          :aria-label="`Remove ${formatType(type)}`"
        >
          &times;
        </button>
      </span>
    </div>

    <!-- Dropdown -->
    <div
      v-if="open"
      class="absolute z-50 mt-1 max-h-72 w-full overflow-auto rounded-lg border border-base-300 bg-base-100 shadow-lg"
    >
      <div v-for="group in TYPE_GROUPS" :key="group.label" class="p-2">
        <div class="px-2 py-1 text-xs font-semibold text-base-content/60 uppercase">
          {{ group.label }}
        </div>
        <label
          v-for="type in group.types"
          :key="type"
          class="flex cursor-pointer items-center gap-2 rounded px-2 py-1 hover:bg-base-200"
        >
          <input
            type="checkbox"
            class="checkbox checkbox-xs checkbox-primary"
            :checked="model.includes(type)"
            @change="toggle(type)"
          />
          <span class="text-sm">{{ formatType(type) }}</span>
        </label>
      </div>
    </div>
  </div>
</template>
