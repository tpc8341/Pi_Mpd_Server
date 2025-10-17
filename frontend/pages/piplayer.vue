<template>
  <div class="bg-gray-100 font-sans leading-normal tracking-normal">
    
    <navbar />

    <main class="container mx-auto mt-10 mb-10 p-6 min-h-screen">
      <div class="bg-white p-2 rounded-lg shadow-xl text-center">
        <h1 class="text-5xl font-extrabold text-gray-900 mb-4">Pi Audio Player</h1>

      </div>

      <div class="grid md:grid-cols-3 gap-8 mt-12">
        <div class="bg-white p-6 rounded-lg shadow-lg">
          <h2 class="text-2xl font-bold mb-2 text-gray-800">Feature One</h2>
          <p class="text-gray-700">Explore the first amazing feature we have to offer. It's designed to make your life easier and more productive.</p>
        </div>

        <div class="bg-white p-6 rounded-lg shadow-lg">
          <h2 class="text-2xl font-bold mb-2 text-gray-800">Feature Two</h2>
          <p class="text-gray-700">Discover how our second feature can help you achieve your goals faster than ever before.</p>
        </div>

        <div class="bg-white p-6 rounded-lg shadow-lg">
          <h2 class="text-2xl font-bold mb-2 text-gray-800">Feature Three</h2>
          <p class="text-gray-700">Our third feature is revolutionary, providing insights and capabilities you won't find anywhere else.</p>
        </div>
      </div>
      
    </main>

    <footer />

  </div>
</template>

<script setup>
import { ref } from 'vue';

const isMobileMenuOpen = ref(false);

const toggleMobileMenu = () => {
  isMobileMenuOpen.value = !isMobileMenuOpen.value;
};
</script>

<style scoped>
/* Scoped styles can be added here if needed */
</style>