<script setup lang="ts">
import {
  Search,
  Building2,
  Settings,
  PanelLeftClose,
  PanelLeftOpen,
  LogOut,
  Menu,
  X,
} from "lucide-vue-next";

const auth = useAuthStore();
const ws = useWebSocketStore();
const route = useRoute();

const navItems = [
  { to: "/search", icon: Search, label: "Search" },
  { to: "/businesses", icon: Building2, label: "Businesses" },
  { to: "/settings", icon: Settings, label: "Settings" },
] as const;

const collapsed = ref(false);
const mobileOpen = ref(false);
const isMobile = ref(false);
const isTablet = ref(false);

let mqMobile: MediaQueryList | null = null;
let mqTablet: MediaQueryList | null = null;

function onMobileChange(e: MediaQueryListEvent) {
  isMobile.value = e.matches;
}

function onTabletChange(e: MediaQueryListEvent) {
  isTablet.value = e.matches;
  if (e.matches && !isMobile.value) {
    collapsed.value = true;
  }
}

onMounted(() => {
  mqMobile = window.matchMedia("(max-width: 768px)");
  mqTablet = window.matchMedia("(max-width: 1024px)");

  isMobile.value = mqMobile.matches;
  isTablet.value = mqTablet.matches;

  if (mqTablet.matches && !mqMobile.matches) {
    collapsed.value = true;
  }

  mqMobile.addEventListener("change", onMobileChange);
  mqTablet.addEventListener("change", onTabletChange);
});

onUnmounted(() => {
  mqMobile?.removeEventListener("change", onMobileChange);
  mqTablet?.removeEventListener("change", onTabletChange);
});

function handleLogout() {
  ws.disconnect();
  auth.clearApiKey();
  navigateTo("/login");
}

function isActive(path: string) {
  if (path === "/businesses") {
    return route.path.startsWith("/businesses");
  }
  return route.path === path;
}
</script>

<template>
  <!-- Mobile: hamburger + drawer -->
  <template v-if="isMobile">
    <button
      class="btn btn-ghost btn-sm fixed left-3 top-3 z-50 md:hidden"
      @click="mobileOpen = !mobileOpen"
      :aria-label="mobileOpen ? 'Close menu' : 'Open menu'"
    >
      <X v-if="mobileOpen" class="h-5 w-5" />
      <Menu v-else class="h-5 w-5" />
    </button>

    <Teleport to="body">
      <template v-if="mobileOpen">
        <div
          class="fixed inset-0 z-40 bg-black/50"
          @click="mobileOpen = false"
        />
        <aside
          class="fixed inset-y-0 left-0 z-50 flex w-56 flex-col border-r border-base-300 bg-base-200"
          role="navigation"
          aria-label="Main navigation"
        >
          <div class="flex h-14 items-center px-4">
            <span class="text-lg font-semibold tracking-tight">webseed</span>
          </div>
          <div class="divider my-0" />
          <nav class="flex flex-1 flex-col gap-1 p-2">
            <NuxtLink
              v-for="item in navItems"
              :key="item.to"
              :to="item.to"
              :class="[
                'flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors',
                isActive(item.to)
                  ? 'bg-primary text-primary-content'
                  : 'hover:bg-base-300',
              ]"
              @click="mobileOpen = false"
            >
              <component :is="item.icon" class="h-4 w-4 shrink-0" />
              <span>{{ item.label }}</span>
            </NuxtLink>
          </nav>
          <div class="divider my-0" />
          <div class="p-2">
            <button
              class="btn btn-ghost btn-sm w-full justify-start gap-3"
              @click="handleLogout"
            >
              <LogOut class="h-4 w-4" />
              Logout
            </button>
          </div>
        </aside>
      </template>
    </Teleport>
  </template>

  <!-- Desktop/Tablet: inline sidebar -->
  <aside
    v-else
    :class="[
      'flex h-screen flex-col border-r border-base-300 bg-base-200 transition-all duration-200',
      collapsed ? 'w-16' : 'w-56',
    ]"
    role="navigation"
    aria-label="Main navigation"
  >
    <div class="flex h-14 items-center px-4">
      <span v-if="!collapsed" class="text-lg font-semibold tracking-tight">
        webseed
      </span>
      <button
        :class="[
          'btn btn-ghost btn-sm btn-square',
          collapsed ? 'mx-auto' : 'ml-auto',
        ]"
        @click="collapsed = !collapsed"
        :aria-label="collapsed ? 'Expand sidebar' : 'Collapse sidebar'"
      >
        <PanelLeftOpen v-if="collapsed" class="h-4 w-4" />
        <PanelLeftClose v-else class="h-4 w-4" />
      </button>
    </div>

    <div class="divider my-0" />

    <nav class="flex flex-1 flex-col gap-1 p-2">
      <div v-for="item in navItems" :key="item.to" class="tooltip tooltip-right" :data-tip="collapsed ? item.label : undefined">
        <NuxtLink
          :to="item.to"
          :class="[
            'flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors w-full',
            isActive(item.to)
              ? 'bg-primary text-primary-content'
              : 'hover:bg-base-300',
            collapsed ? 'justify-center px-0' : '',
          ]"
        >
          <component :is="item.icon" class="h-4 w-4 shrink-0" />
          <span v-if="!collapsed">{{ item.label }}</span>
        </NuxtLink>
      </div>
    </nav>

    <div class="divider my-0" />

    <div class="p-2">
      <div class="tooltip tooltip-right" :data-tip="collapsed ? 'Logout' : undefined">
        <button
          v-if="collapsed"
          class="btn btn-ghost btn-sm btn-square mx-auto flex"
          @click="handleLogout"
          aria-label="Logout"
        >
          <LogOut class="h-4 w-4" />
        </button>
        <button
          v-else
          class="btn btn-ghost btn-sm w-full justify-start gap-3"
          @click="handleLogout"
        >
          <LogOut class="h-4 w-4" />
          Logout
        </button>
      </div>
    </div>
  </aside>
</template>
