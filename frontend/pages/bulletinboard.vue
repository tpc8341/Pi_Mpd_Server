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
            <li v-for="bulletin in bulletins" :key="bulletin.id" class="border-b py-2 flex justify-between items-center">
              <div>
                <a :href="getBulletinUrl(bulletin.filename)" target="_blank" class="text-blue-500 hover:underline text-xl">
                  {{ bulletin.title }}
                </a>
                <p class="text-sm text-gray-600">Uploaded by: {{ bulletin.owner.username }}</p>
              </div>
              <button @click="editBulletinTitle(bulletin)" class="ml-4 bg-yellow-500 hover:bg-yellow-700 text-white font-bold py-1 px-2 rounded text-sm">
                Edit
              </button>
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

// Get runtime config
const config = useRuntimeConfig();
const apiBase = config.public.apiBase;


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
    const token = localStorage.getItem('authToken');
    const response = await fetch(`{apibase}/bulletins/`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`
      },
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
    const token = localStorage.getItem('authToken');
    const response = await fetch(`${apiBase}/bulletins/`, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });
    if (response.ok) {
      bulletins.value = await response.json();
    }
  } catch (error) {
    console.error('Error fetching bulletins:', error);
  }
};

const getBulletinUrl = (filename) => {
  return `{apibase}/bulletins/${filename}`;
};

const editBulletinTitle = async (bulletin) => {
  const newTitle = prompt('Enter the new title:', bulletin.title);
  if (!newTitle || newTitle === bulletin.title) {
    return;
  }

  try {
    const token = localStorage.getItem('authToken');
    const response = await fetch(`{apibase}/bulletins/${bulletin.id}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({ title: newTitle }),
    });

    if (response.ok) {
      alert('Title updated successfully!');
      fetchBulletins(); // Refresh the list
    } else {
      alert('Title update failed.');
    }
  } catch (error) {
    console.error('Error updating title:', error);
    alert('An error occurred during title update.');
  }
};

onMounted(() => {
  fetchBulletins();
});
</script>

<style scoped>
/* Scoped styles can be added here if needed */
</style>
