<template>
  <div class="bg-gray-100 font-sans leading-normal tracking-normal">
    
    <navbar />

    <main class="container mx-auto mt-10 mb-10 p-6 min-h-screen">
      <div class="bg-white p-2 rounded-lg shadow-xl text-center">
        <h1 class="text-5xl font-extrabold text-gray-900 mb-4">Bulletin Board</h1>
      </div>

      <div class="mt-8">
        <div class="bg-white p-6 rounded-lg shadow-lg">
          <h2 class="text-2xl font-bold mb-4 text-gray-800">Upload a File</h2>
          <div class="flex items-center">
            <input type="file" @change="handleFileUpload" class="p-2 border rounded">
            <button @click="uploadFile" class="ml-4 bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded">
              Upload
            </button>
          </div>
        </div>
      </div>

      <div class="grid md:grid-cols-1 gap-8 mt-12">
        <div class="bg-white p-6 rounded-lg shadow-lg">
          <h2 class="text-2xl font-bold mb-2 text-gray-800">Uploaded Files</h2>
          <ul>
            <li v-for="bulletin in bulletins" :key="bulletin.id" class="border-b py-2">
              <a :href="getBulletinUrl(bulletin.filename)" target="_blank" class="text-blue-500 hover:underline">
                {{ bulletin.title }}
              </a>
            </li>
          </ul>
        </div>
      </div>
      
    </main>

    <footer />

  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';

const isMobileMenuOpen = ref(false);
const fileToUpload = ref(null);
const bulletins = ref([]);

const toggleMobileMenu = () => {
  isMobileMenuOpen.value = !isMobileMenuOpen.value;
};

const handleFileUpload = (event) => {
  fileToUpload.value = event.target.files[0];
};

const uploadFile = async () => {
  if (!fileToUpload.value) {
    alert('Please select a file to upload.');
    return;
  }

  const title = prompt('Enter a title for the upload:');
  if (!title) {
    return;
  }

  const formData = new FormData();
  formData.append('file', fileToUpload.value);
  formData.append('title', title);

  try {
    const response = await fetch('http://localhost:8002/bulletins/', {
      method: 'POST',
      body: formData,
    });

    if (response.ok) {
      alert('File uploaded successfully!');
      fetchBulletins(); // Refresh the list
    } else {
      alert('File upload failed.');
    }
  } catch (error) {
    console.error('Error uploading file:', error);
    alert('An error occurred during upload.');
  }
};

const fetchBulletins = async () => {
  try {
    const response = await fetch('http://localhost:8002/bulletins/');
    if (response.ok) {
      bulletins.value = await response.json();
    }
  } catch (error) {
    console.error('Error fetching bulletins:', error);
  }
};

const getBulletinUrl = (filename) => {
  return `http://localhost:8002/bulletins/${filename}`;
};

onMounted(() => {
  fetchBulletins();
});
</script>

<style scoped>
/* Scoped styles can be added here if needed */
</style>
