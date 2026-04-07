import { ref } from 'vue'

export type ToastVariant = 'default' | 'success' | 'destructive'

export interface Toast {
  id: string
  title?: string
  description?: string
  variant: ToastVariant
  duration?: number
}

const toasts = ref<Toast[]>([])

let count = 0

export function useToast() {
  function toast({ title, description, variant = 'default', duration = 5000 }: Omit<Toast, 'id'>) {
    const id = String(++count)
    toasts.value.push({ id, title, description, variant })
    setTimeout(() => {
      toasts.value = toasts.value.filter((t) => t.id !== id)
    }, duration)
    return { id }
  }

  function dismiss(id?: string) {
    if (id) {
      toasts.value = toasts.value.filter((t) => t.id !== id)
    } else {
      toasts.value = []
    }
  }

  return {
    toasts,
    toast,
    dismiss,
  }
}
