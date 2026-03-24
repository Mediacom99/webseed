import type { ToastItem } from "~/types";

const toasts = ref<ToastItem[]>([]);
const timers = new Map<number, ReturnType<typeof setTimeout>>();
let nextId = 0;

export function useToast() {
  function push(message: string, type: ToastItem["type"] = "info") {
    const id = ++nextId;
    toasts.value.push({ id, message, type });
    timers.set(id, setTimeout(() => dismiss(id), 4000));
  }

  function dismiss(id: number) {
    const timer = timers.get(id);
    if (timer) {
      clearTimeout(timer);
      timers.delete(id);
    }
    toasts.value = toasts.value.filter((t) => t.id !== id);
  }

  return { toasts, push, dismiss };
}
