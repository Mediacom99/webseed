<script setup lang="ts">
const props = withDefaults(
  defineProps<{
    title: string;
    description?: string;
    confirmLabel?: string;
    confirmClass?: string;
  }>(),
  {
    description: undefined,
    confirmLabel: "Confirm",
    confirmClass: "btn-primary",
  },
);

const emit = defineEmits<{
  confirm: [];
  cancel: [];
}>();

const dialogRef = ref<HTMLDialogElement | null>(null);

function open() {
  dialogRef.value?.showModal();
}

function close() {
  dialogRef.value?.close();
}

function handleConfirm() {
  emit("confirm");
  close();
}

function handleCancel() {
  emit("cancel");
  close();
}

defineExpose({ open, close });
</script>

<template>
  <dialog ref="dialogRef" class="modal">
    <div class="modal-box">
      <h3 class="text-lg font-bold">{{ props.title }}</h3>
      <p v-if="props.description" class="py-4">{{ props.description }}</p>
      <div class="modal-action">
        <button class="btn" @click="handleCancel">Cancel</button>
        <button :class="['btn', props.confirmClass]" @click="handleConfirm">
          {{ props.confirmLabel }}
        </button>
      </div>
    </div>
    <form method="dialog" class="modal-backdrop">
      <button @click="handleCancel">close</button>
    </form>
  </dialog>
</template>
