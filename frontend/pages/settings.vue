<script setup lang="ts">
const activeTab = ref("prompts");
</script>

<template>
  <div class="space-y-6">
    <h1 class="text-2xl font-semibold">Settings</h1>

    <div role="tablist" class="tabs tabs-bordered">
      <a
        role="tab"
        :class="['tab', activeTab === 'prompts' ? 'tab-active' : '']"
        @click="activeTab = 'prompts'"
      >
        Prompts
      </a>
      <a
        role="tab"
        :class="['tab', activeTab === 'config' ? 'tab-active' : '']"
        @click="activeTab = 'config'"
      >
        Configuration
      </a>
    </div>

    <SettingsPromptEditor v-if="activeTab === 'prompts'" />
    <SettingsConfigTable v-if="activeTab === 'config'" />
  </div>
</template>
