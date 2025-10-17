<template>
  <div class="bg-gray-100 font-sans leading-normal tracking-normal">
    
    <navbar />

    <main class="container mx-auto mt-10 mb-10 p-6 min-h-screen">
      <div class="bg-white p-2 rounded-lg shadow-xl text-center">
        <h1 class="text-5xl font-extrabold text-gray-900 mb-4">我的歌單編輯</h1>
      </div>

      <div class="bg-white p-6 rounded-lg shadow-xl mt-12">
        <h2 class="text-2xl font-bold text-gray-800">建立歌單</h2>
        <p class="text-s mb-1 text-gray-800">輸入「國語 張學友」會搜尋「國語\張學友」資料夾內的所有歌曲.輸入「國語」會搜尋「國語」資料夾內的所有歌曲.</p>
        <div class="flex flex-col sm:flex-row gap-4">
          <input 
            type="text"
            v-model="folderName"
            placeholder="Enter folder name (e.g., 國語)"
            class="flex-grow p-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <button 
            @click="getFiles"
            :disabled="isLoading"
            class="bg-blue-600 text-white font-bold py-3 px-6 rounded-lg hover:bg-blue-700 disabled:bg-gray-400 transition duration-300"
          >
            <span v-if="isLoading">Loading...</span>
            <span v-else>搜尋資料夾</span>
          </button>
        </div>

        <div v-if="errorMessage" class="mt-4 text-red-600 bg-red-100 p-3 rounded-lg">
          {{ errorMessage }}
        </div>
        
        <div v-if="fileList.length > 0" class="mt-6">
          <h3 class="text-xl font-semibold text-gray-800 mb-3">Generated Files:</h3>
          <ul class="list-disc list-inside bg-gray-50 p-4 rounded-lg max-h-96 overflow-y-auto">
            <li v-for="(file, index) in fileList" :key="index" 
                class="text-gray-700 p-1 truncate cursor-pointer"
                :class="{ 'bg-blue-200': filesToSaveFromFolder.includes(file) }"
                @click="toggleSelectionForFolderFiles(file)">
              {{ file }}
            </li>
          </ul>
          <div class="mt-4 flex gap-4">
            <button 
              @click="selectAllFolderFiles"
              class="bg-gray-600 text-white font-bold py-3 px-6 rounded-lg hover:bg-gray-700 transition duration-300"
            >
              Select All
            </button>
            <button 
              @click="deselectAllFolderFiles"
              class="bg-gray-600 text-white font-bold py-3 px-6 rounded-lg hover:bg-gray-700 transition duration-300"
            >
              Deselect All
            </button>
            <button 
              @click="promptForPlaylistName"
              :disabled="filesToSaveFromFolder.length === 0"
              class="bg-green-600 text-white font-bold py-3 px-6 rounded-lg hover:bg-green-700 disabled:bg-gray-400 transition duration-300"
            >
              存入歌單
            </button>
          </div>
        </div>
      </div>

      <!-- Playlist List Section -->
      <div class="bg-white p-6 rounded-lg shadow-xl mt-6">
        <h2 class="text-2xl font-bold mb-4 text-gray-800">你的歌單:(點歌單名字可編輯曲目)</h2>
        <div v-if="playlistsList.length > 0">
          <ul class="list-disc list-inside bg-gray-50 p-4 rounded-lg max-h-96 overflow-y-auto">
            <li v-for="(playlistName, index) in playlistsList" :key="index"
                class="flex justify-between items-center text-gray-700 p-2 border-b border-gray-200 last:border-b-0">
              <span class="cursor-pointer hover:text-blue-600 font-medium" @click="getPlaylistFiles(playlistName)" :class="{ 'bg-blue-200': playlistName === currentSelectedPlaylist }">
                {{ playlistName }}
              </span>
              <button @click="deletePlaylist(playlistName)" class="bg-red-500 text-white py-1 px-3 rounded-lg text-sm hover:bg-red-600 transition duration-300">
                刪除
              </button>
            </li>
          </ul>
        </div>
        <div v-else class="text-gray-600 p-4 text-center">
          No playlists saved yet.
        </div>

        <div v-if="selectedPlaylistFiles.length > 0" class="mt-6">
          <h3 class="text-xl font-semibold text-gray-800 mb-3">歌單-{{ currentSelectedPlaylist }}:</h3>
          
          <div class="mb-4">
            <button 
              @click="editModeForPlaylist = !editModeForPlaylist; selectedFilesInEditMode = []"
              class="bg-blue-600 text-white font-bold py-2 px-4 rounded-lg hover:bg-blue-700 transition duration-300 mr-2"
            >
              {{ editModeForPlaylist ? '離開編輯' : '編輯' }}
            </button>
            <button 
              v-if="editModeForPlaylist"
              @click="deleteSelectedFilesFromPlaylist"
              :disabled="selectedFilesInEditMode.length === 0"
              class="bg-red-600 text-white font-bold py-2 px-4 rounded-lg hover:bg-red-700 disabled:bg-gray-400 transition duration-300"
            >
              刪除
            </button>
            <button 
              v-if="editModeForPlaylist"
              @click="promptToSaveSelection"
              :disabled="selectedFilesInEditMode.length === 0"
              class="bg-green-600 text-white font-bold py-2 px-4 rounded-lg hover:bg-green-700 disabled:bg-gray-400 transition duration-300 ml-2"
            >
              儲存
            </button>
          </div>

          <ul class="list-disc list-inside bg-gray-50 p-4 rounded-lg max-h-96 overflow-y-auto">
            <li v-for="(file, index) in selectedPlaylistFiles" :key="index" 
                class="text-gray-700 p-1 truncate"
                :class="{ 'bg-red-300 cursor-pointer': editModeForPlaylist && selectedFilesInEditMode.includes(file), 'cursor-pointer': editModeForPlaylist && !selectedFilesInEditMode.includes(file), 'cursor-default': !editModeForPlaylist }"
                @click="editModeForPlaylist ? toggleFileSelectionInEditMode(file) : null">
              {{ file }}
            </li>
          </ul>
        </div>
      </div>


      <div v-if="showSaveDialog" class="fixed inset-0 bg-gray-800 bg-opacity-50 flex items-center justify-center">
        <div class="bg-white p-6 rounded-lg shadow-xl">
          <h3 class="text-xl font-bold mb-4">Enter Playlist Name</h3>
          <input 
            type="text"
            v-model="newPlaylistName"
            placeholder="My Awesome Playlist"
            class="w-full p-3 border border-gray-300 rounded-lg mb-4"
          />
          <div class="flex justify-end gap-4">
            <button @click="showSaveDialog = false" class="bg-gray-300 text-gray-800 font-bold py-2 px-4 rounded-lg">Cancel</button>
            <button @click="savePlaylist" class="bg-blue-600 text-white font-bold py-2 px-4 rounded-lg">Save</button>
          </div>
        </div>
      </div>

    <div class="grid md:grid-cols-4 gap-6 mt-6">

    <div class="bg-white p-6 rounded-lg shadow-lg">
    <h2 class="text-2xl font-bold mb-2 text-gray-800">自動產生歌單-類型:</h2>
    <div class="grid grid-cols-3 gap-4">
    <button @click="autoSavePcPlaylist('國語')" class="bg-green-500 text-white py-1 px-3 rounded-lg text-sm hover:bg-green-600 transition duration-300">國語</button>
    <button @click="autoSavePcPlaylist('台語')" class="bg-green-500 text-white py-1 px-3 rounded-lg text-sm hover:bg-green-600 transition duration-300">台語</button>
    <button @click="autoSavePcPlaylist('日語')" class="bg-green-500 text-white py-1 px-3 rounded-lg text-sm hover:bg-green-600 transition duration-300">日語</button>
    <button @click="autoSavePcPlaylist('英語')" class="bg-green-500 text-white py-1 px-3 rounded-lg text-sm hover:bg-green-600 transition duration-300">英語</button>
    <button @click="autoSavePcPlaylist('古典')" class="bg-green-500 text-white py-1 px-3 rounded-lg text-sm hover:bg-green-600 transition duration-300">古典</button>
    <button @click="autoSavePcPlaylist('英語')" class="bg-green-500 text-white py-1 px-3 rounded-lg text-sm hover:bg-green-600 transition duration-300">英語</button>
    <button @click="autoSavePcPlaylist('輕音樂')" class="bg-green-500 text-white py-1 px-3 rounded-lg text-sm hover:bg-green-600 transition duration-300">輕音樂</button>
    <button @click="autoSavePcPlaylist('有聲書')" class="bg-green-500 text-white py-1 px-3 rounded-lg text-sm hover:bg-green-600 transition duration-300">有聲書</button>
    <button @click="autoSavePcPlaylist('播客')" class="bg-green-500 text-white py-1 px-3 rounded-lg text-sm hover:bg-green-600 transition duration-300">播客</button>
    </div>

    </div>
    <div class="bg-white p-6 rounded-lg shadow-lg">
    <h2 class="text-2xl font-bold mb-2 text-gray-800">自動產生歌單-歌手:</h2>
    <div class="grid grid-cols-3 gap-4">
    <button @click="autoSavePcPlaylist('國語 張學友')" class="bg-blue-500 text-white py-1 px-3 rounded-lg text-sm hover:bg-blue-600 transition duration-300">張學友</button>
    <button @click="autoSavePcPlaylist('國語 張學友-演唱會')" class="bg-blue-500 text-white py-1 px-3 rounded-lg text-sm hover:bg-blue-600 transition duration-300">張學友-演唱會</button>
    <button @click="autoSavePcPlaylist('國語 張學友-精選輯')" class="bg-blue-500 text-white py-1 px-3 rounded-lg text-sm hover:bg-blue-600 transition duration-300">張學友-精選輯</button>
    <button @click="autoSavePcPlaylist('國語 劉德華')" class="bg-blue-500 text-white py-1 px-3 rounded-lg text-sm hover:bg-blue-600 transition duration-300">劉德華</button>
    <button @click="autoSavePcPlaylist('國語 孫燕姿')" class="bg-blue-500 text-white py-1 px-3 rounded-lg text-sm hover:bg-blue-600 transition duration-300">孫燕姿</button>
    <button @click="autoSavePcPlaylist('國語 弦子')" class="bg-blue-500 text-white py-1 px-3 rounded-lg text-sm hover:bg-blue-600 transition duration-300">弦子</button>
    <button @click="autoSavePcPlaylist('國語 原子邦妮')" class="bg-blue-500 text-white py-1 px-3 rounded-lg text-sm hover:bg-blue-600 transition duration-300">原子邦妮</button>
    <button @click="autoSavePcPlaylist('英語 Lady_Gaga')" class="bg-blue-500 text-white py-1 px-3 rounded-lg text-sm hover:bg-blue-600 transition duration-300">Lady Gaga</button>
    <button @click="autoSavePcPlaylist('台語 鄭進一')" class="bg-blue-500 text-white py-1 px-3 rounded-lg text-sm hover:bg-blue-600 transition duration-300">鄭進一</button>
    <button @click="autoSavePcPlaylist('英語 Regine')" class="bg-blue-500 text-white py-1 px-3 rounded-lg text-sm hover:bg-blue-600 transition duration-300">Regine</button>
    <button @click="autoSavePcPlaylist('英語 Bryan_Adams')" class="bg-blue-500 text-white py-1 px-3 rounded-lg text-sm hover:bg-blue-600 transition duration-300">Bryan Adams</button>
    <button @click="autoSavePcPlaylist('國語 萬芳')" class="bg-blue-500 text-white py-1 px-3 rounded-lg text-sm hover:bg-blue-600 transition duration-300">萬芳</button>
    <button @click="autoSavePcPlaylist('日語 AKB48')" class="bg-blue-500 text-white py-1 px-3 rounded-lg text-sm hover:bg-blue-600 transition duration-300">AKB48</button>
    <button @click="autoSavePcPlaylist('台語 黃乙玲')" class="bg-blue-500 text-white py-1 px-3 rounded-lg text-sm hover:bg-blue-600 transition duration-300">黃乙玲</button>
    <button @click="autoSavePcPlaylist('台語 秀蘭瑪雅')" class="bg-blue-500 text-white py-1 px-3 rounded-lg text-sm hover:bg-blue-600 transition duration-300">秀蘭瑪雅</button>
    <button @click="autoSavePcPlaylist('台語 蘇宥蓉')" class="bg-blue-500 text-white py-1 px-3 rounded-lg text-sm hover:bg-blue-600 transition duration-300">蘇宥蓉</button>
    <button @click="autoSavePcPlaylist('台語 玖壹壹')" class="bg-blue-500 text-white py-1 px-3 rounded-lg text-sm hover:bg-blue-600 transition duration-300">玖壹壹</button>
    <button @click="autoSavePcPlaylist('國語 張韶涵')" class="bg-blue-500 text-white py-1 px-3 rounded-lg text-sm hover:bg-blue-600 transition duration-300">張韶涵</button>
    <button @click="autoSavePcPlaylist('國語 張韶涵')" class="bg-blue-500 text-white py-1 px-3 rounded-lg text-sm hover:bg-blue-600 transition duration-300">張韶涵</button>
    <button @click="autoSavePcPlaylist('國語 張惠妺')" class="bg-blue-500 text-white py-1 px-3 rounded-lg text-sm hover:bg-blue-600 transition duration-300">張惠妹</button>
    <button @click="autoSavePcPlaylist('國語 任賢齊')" class="bg-blue-500 text-white py-1 px-3 rounded-lg text-sm hover:bg-blue-600 transition duration-300">任賢齊</button>
    <button @click="autoSavePcPlaylist('國語 鄭中基')" class="bg-blue-500 text-white py-1 px-3 rounded-lg text-sm hover:bg-blue-600 transition duration-300">鄭中基</button>
    <button @click="autoSavePcPlaylist('國語 蔡健雅')" class="bg-blue-500 text-white py-1 px-3 rounded-lg text-sm hover:bg-blue-600 transition duration-300">蔡健雅</button>
    <button @click="autoSavePcPlaylist('國語 伍佰')" class="bg-blue-500 text-white py-1 px-3 rounded-lg text-sm hover:bg-blue-600 transition duration-300">伍佰</button>
    <button @click="autoSavePcPlaylist('國語 張靚穎')" class="bg-blue-500 text-white py-1 px-3 rounded-lg text-sm hover:bg-blue-600 transition duration-300">張靚穎</button>
    <button @click="autoSavePcPlaylist('國語 梁靜茹')" class="bg-blue-500 text-white py-1 px-3 rounded-lg text-sm hover:bg-blue-600 transition duration-300">梁靜茹</button>
    <button @click="autoSavePcPlaylist('國語 蘇打綠')" class="bg-blue-500 text-white py-1 px-3 rounded-lg text-sm hover:bg-blue-600 transition duration-300">蘇打綠</button>
    <button @click="autoSavePcPlaylist('國語 高慧君')" class="bg-blue-500 text-white py-1 px-3 rounded-lg text-sm hover:bg-blue-600 transition duration-300">高慧君</button>
    <button @click="autoSavePcPlaylist('國語 張棟樑')" class="bg-blue-500 text-white py-1 px-3 rounded-lg text-sm hover:bg-blue-600 transition duration-300">張棟樑</button>
    <button @click="autoSavePcPlaylist('國語 郁可唯')" class="bg-blue-500 text-white py-1 px-3 rounded-lg text-sm hover:bg-blue-600 transition duration-300">郁可唯</button>
    <button @click="autoSavePcPlaylist('國語 楊丞琳')" class="bg-blue-500 text-white py-1 px-3 rounded-lg text-sm hover:bg-blue-600 transition duration-300">楊丞琳</button>
    <button @click="autoSavePcPlaylist('國語 王心凌')" class="bg-blue-500 text-white py-1 px-3 rounded-lg text-sm hover:bg-blue-600 transition duration-300">王心凌</button>
    <button @click="autoSavePcPlaylist('國語 王傑')" class="bg-blue-500 text-white py-1 px-3 rounded-lg text-sm hover:bg-blue-600 transition duration-300">王傑</button>
    </div>

    </div>
    <div class="bg-white p-6 rounded-lg shadow-lg">
    <h2 class="text-2xl font-bold mb-2 text-gray-800">自動產生歌單-專輯:</h2>
    <div class="grid grid-cols-3 gap-4">
    <button @click="autoSavePcPlaylist('國語 張學友 天下第一流')" class="bg-blue-500 text-white py-1 px-3 rounded-lg text-sm hover:bg-blue-600 transition duration-300">張學友 天下第一流</button>
    <button @click="autoSavePcPlaylist('國語 張學友 吻別')" class="bg-blue-500 text-white py-1 px-3 rounded-lg text-sm hover:bg-blue-600 transition duration-300">張學友 吻別</button>
    <button @click="autoSavePcPlaylist('國語 張學友-演唱會 2003音樂之旅Live演唱會')" class="bg-blue-500 text-white py-1 px-3 rounded-lg text-sm hover:bg-blue-600 transition duration-300">張學友2003音樂之旅演唱會</button>
    <button @click="autoSavePcPlaylist('國語 張惠妺 你在看我嗎')" class="bg-blue-500 text-white py-1 px-3 rounded-lg text-sm hover:bg-blue-600 transition duration-300">張惠妹 你在看我嗎</button>
    <button @click="autoSavePcPlaylist('播客 BBC')" class="bg-purple-500 text-white py-1 px-3 rounded-lg text-sm hover:bg-purple-600 transition duration-300">BBC</button>
    <button @click="autoSavePcPlaylist('播客 Daily')" class="bg-purple-500 text-white py-1 px-3 rounded-lg text-sm hover:bg-purple-600 transition duration-300">Daily</button>
    </div>

    </div>

        <div class="bg-white p-6 rounded-lg shadow-lg">
          <h2 class="text-2xl font-bold mb-2 text-gray-800">下載最新播客:</h2>
          <div class="grid grid-cols-3 gap-4">
          <button @click="autoDownloadPodcast()" class="bg-purple-600 text-white py-4 px-4 rounded-lg text-m hover:bg-purple-700 transition duration-300">下載播客</button>
          </div>
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

const folderName = ref('');
const fileList = ref([]);
const isLoading = ref(false);
const errorMessage = ref('');
const filesToSaveFromFolder = ref([]); // Renamed from selectedFiles
const showSaveDialog = ref(false);
const newPlaylistName = ref('');

// New state variables for playlist list and selected playlist files
const playlistsList = ref([]);
const selectedPlaylistFiles = ref([]);
const currentSelectedPlaylist = ref('');
const selectedFilesInEditMode = ref([]); // To track files selected for deletion from an opened playlist
const editModeForPlaylist = ref(false); // To enable/disable editing mode for playlist files


// Function to fetch the list of playlist names
const getPlaylistsList = async () => {
  isLoading.value = true;
  errorMessage.value = '';
  try {
    const token = localStorage.getItem('authToken');
    if (!token) {
      throw new Error("Authentication token is not available. Please log in.");
    }

    const response = await fetch(`${apiBase}/pc_get_playlist_List`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => null);
      throw new Error(errorData?.detail || `Server responded with status: ${response.status}`);
    }

    const data = await response.json();
    playlistsList.value = data.names; // Assuming the API returns { names: [...] }

  } catch (error) {
    console.error('Failed to fetch playlists list:', error);
    errorMessage.value = error.message;
  } finally {
    isLoading.value = false;
  }
};

// Function to fetch files for a specific playlist
const getPlaylistFiles = async (playlistName) => {
  isLoading.value = true;
  errorMessage.value = '';
  selectedPlaylistFiles.value = [];
  currentSelectedPlaylist.value = playlistName;
  selectedFilesInEditMode.value = []; // Clear selections for deletion when new playlist is loaded
  editModeForPlaylist.value = false; // Exit edit mode when new playlist is loaded

  try {
    const token = localStorage.getItem('authToken');
    if (!token) {
      throw new Error("Authentication token is not available. Please log in.");
    }

    const response = await fetch(`${apiBase}/pc_get_playlist_files/${encodeURIComponent(playlistName)}`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => null);
      throw new Error(errorData?.detail || `Server responded with status: ${response.status}`);
    }

    const data = await response.json();
    selectedPlaylistFiles.value = data;

  } catch (error) {
    console.error(`Failed to fetch files for playlist ${playlistName}:`, error);
    errorMessage.value = error.message;
  } finally {
    isLoading.value = false;
  }
};

// Function to delete a playlist
const deletePlaylist = async (playlistName) => {
  if (!confirm(`Are you sure you want to delete the playlist "${playlistName}"?`)) {
    return;
  }

  isLoading.value = true;
  errorMessage.value = '';

  try {
    const token = localStorage.getItem('authToken');
    if (!token) {
      throw new Error("Authentication token is not available. Please log in.");
    }

    const response = await fetch(`${apiBase}/pc_delete_playlist_list/${encodeURIComponent(playlistName)}`, {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => null);
      throw new Error(errorData?.detail || `Server responded with status: ${response.status}`);
    }

    alert(`Playlist "${playlistName}" deleted successfully!`);
    await getPlaylistsList(); // Refresh the playlist list
    selectedPlaylistFiles.value = []; // Clear displayed files if the deleted playlist was selected
    currentSelectedPlaylist.value = '';
    selectedFilesInEditMode.value = [];
    editModeForPlaylist.value = false;

  } catch (error) {
    console.error(`Failed to delete playlist ${playlistName}:`, error);
    errorMessage.value = error.message;
  } finally {
    isLoading.value = false;
  }
};


const getFiles = async () => {
  if (!folderName.value.trim()) {
    errorMessage.value = 'Folder name cannot be empty.';
    return;
  }

  isLoading.value = true;
  errorMessage.value = '';
  fileList.value = [];
  filesToSaveFromFolder.value = [];

  try {
    const token = localStorage.getItem('authToken');
    if (!token) {
      throw new Error("Authentication token is not available. Please log in.");
    }
    
    const response = await fetch(`${apiBase}/pc_gen_fileslist/${encodeURIComponent(folderName.value)}`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => null);
      throw new Error(errorData?.detail || `Server responded with status: ${response.status}`);
    }

    const data = await response.json();
    fileList.value = data;

  } catch (error) {
    console.error('Failed to fetch files:', error);
    errorMessage.value = error.message;
  } finally {
    isLoading.value = false;
  }
};

// Toggle selection for files generated from a folder
const toggleSelectionForFolderFiles = (file) => {
  const index = filesToSaveFromFolder.value.indexOf(file);
  if (index > -1) {
    filesToSaveFromFolder.value.splice(index, 1);
  } else {
    filesToSaveFromFolder.value.push(file);
  }
};

// Select all files generated from a folder
const selectAllFolderFiles = () => {
  filesToSaveFromFolder.value = [...fileList.value];
};

// Deselect all files generated from a folder
const deselectAllFolderFiles = () => {
  filesToSaveFromFolder.value = [];
};


// Toggle selection for files within a saved playlist (for deletion)
const toggleFileSelectionInEditMode = (file) => {
  const index = selectedFilesInEditMode.value.indexOf(file);
  if (index > -1) {
    selectedFilesInEditMode.value.splice(index, 1);
  } else {
    selectedFilesInEditMode.value.push(file);
  }
};

// Function to delete selected files from the currently viewed playlist
const deleteSelectedFilesFromPlaylist = async () => {
  if (!confirm(`Are you sure you want to delete the selected ${selectedFilesInEditMode.value.length} file(s) from "${currentSelectedPlaylist.value}"?`)) {
    return;
  }

  isLoading.value = true;
  errorMessage.value = '';

  try {
    // Filter out the files marked for deletion
    const updatedFiles = selectedPlaylistFiles.value.filter(
      file => !selectedFilesInEditMode.value.includes(file)
    );

    await updatePlaylistContent(currentSelectedPlaylist.value, updatedFiles);
    alert('Selected files deleted and playlist updated successfully!');
    
    // Refresh the displayed files and exit edit mode
    await getPlaylistFiles(currentSelectedPlaylist.value);
    selectedFilesInEditMode.value = [];
    editModeForPlaylist.value = false;

  } catch (error) {
    console.error('Failed to delete files from playlist:', error);
    errorMessage.value = error.message;
  } finally {
    isLoading.value = false;
  }
};

const promptToSaveSelection = () => {
  const newPlaylistName = prompt('Enter a name for the new playlist:');
  if (newPlaylistName && newPlaylistName.trim()) {
    saveSelectedFilesAsNewPlaylist(newPlaylistName.trim());
  }
};

const saveSelectedFilesAsNewPlaylist = async (playlistName) => {
  isLoading.value = true;
  errorMessage.value = '';

  try {
    await updatePlaylistContent(playlistName, selectedFilesInEditMode.value);
    alert(`Selected files saved to new playlist "${playlistName}" successfully!`);
    
    // Refresh the playlist list and exit edit mode
    await getPlaylistsList();
    selectedFilesInEditMode.value = [];
    editModeForPlaylist.value = false;

  } catch (error) {
    console.error('Failed to save selected files to new playlist:', error);
    errorMessage.value = error.message;
  } finally {
    isLoading.value = false;
  }
};

// Helper function to update playlist content on the backend
const updatePlaylistContent = async (playlistName, content) => {
  const token = localStorage.getItem('authToken');
    if (!token) {
      throw new Error("Authentication token is not available. Please log in.");
    }

    const response = await fetch(`${apiBase}/pc_save_playlists_to_list/${encodeURIComponent(playlistName)}`,
    {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ songs: content })
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => null);
      throw new Error(errorData?.detail || `Server responded with status: ${response.status}`);
    }
}


const promptForPlaylistName = () => {
  showSaveDialog.value = true;
};

const savePlaylist = async () => {
  if (!newPlaylistName.value.trim()) {
    alert('Playlist name cannot be empty.');
    return;
  }

  isLoading.value = true;
  errorMessage.value = '';

  try {
    const token = localStorage.getItem('authToken');
    if (!token) {
      throw new Error("Authentication token is not available. Please log in.");
    }

    const response = await fetch(`${apiBase}/pc_save_playlists_to_list/${encodeURIComponent(newPlaylistName.value)}`,
    {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ songs: filesToSaveFromFolder.value }) // Use filesToSaveFromFolder
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => null);
      throw new Error(errorData?.detail || `Server responded with status: ${response.status}`);
    }

    alert('Playlist saved successfully!');
    showSaveDialog.value = false;
    newPlaylistName.value = '';
    filesToSaveFromFolder.value = [];
    await getPlaylistsList(); // Refresh the playlist list after saving

  } catch (error) {
    console.error('Failed to save playlist:', error);
    errorMessage.value = error.message;
  } finally {
    isLoading.value = false;
  }
};

const autoSavePcPlaylist = async (folder) => {
  isLoading.value = true;
  errorMessage.value = '';
  try {
    const token = localStorage.getItem('authToken');
    if (!token) {
      throw new Error("Authentication token is not available. Please log in.");
    }

    // --- Start of new logic to determine playlistName ---
    let playlistName = folder;
    const firstSpaceIndex = folder.indexOf(' ');
    
    if (firstSpaceIndex !== -1) {
        // If a space is found, take the substring after the first space.
        playlistName = folder.substring(firstSpaceIndex + 1);
    }
    // --- End of new logic ---


    // 1. Get file list
    const genFilesResponse = await fetch(`${apiBase}/pc_gen_fileslist/${encodeURIComponent(folder)}`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    });

    if (!genFilesResponse.ok) {
      const errorData = await genFilesResponse.json().catch(() => null);
      throw new Error(errorData?.detail || `Server responded with status: ${genFilesResponse.status}`);
    }

    const files = await genFilesResponse.json();

    if (files.length === 0) {
      alert(`No files found in folder "${folder}". Playlist not created.`);
      return;
    }

    // 2. Save playlist
    // Use the derived playlistName for saving
    const savePlaylistResponse = await fetch(`${apiBase}/pc_save_playlists_to_list/${encodeURIComponent(playlistName)}`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ songs: files })
    });

    if (!savePlaylistResponse.ok) {
      const errorData = await savePlaylistResponse.json().catch(() => null);
      throw new Error(errorData?.detail || `Server responded with status: ${savePlaylistResponse.status}`);
    }

    alert(`Playlist "${playlistName}" created/updated successfully!`);
    await getPlaylistsList(); // Refresh the playlist list

  } catch (error) {
    console.error(`Failed to auto save playlist for folder ${folder}:`, error);
    errorMessage.value = error.message;
    alert(`Failed to auto save playlist: ${error.message}`);
  } finally {
    isLoading.value = false;
  }
};

// Fetch playlists on component mount
onMounted(() => {
  getPlaylistsList();
});

const autoDownloadPodcast = async () => {
  isLoading.value = true;
  errorMessage.value = '';
  try {
    const token = localStorage.getItem('authToken');
    if (!token) {
      throw new Error("Authentication token is not available. Please log in.");
    }

    const response = await fetch(`${apiBase}/download_podcast`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => null);
      throw new Error(errorData?.detail || `Server responded with status: ${response.status}`);
    }

    const data = await response.json();
    alert(data.message || 'Podcast download process completed.');

  } catch (error) {
    console.error('Failed to start podcast download:', error);
    errorMessage.value = error.message;
    alert(`Failed to start podcast download: ${error.message}`);
  } finally {
    isLoading.value = false;
  }
};

</script>

<style scoped>
.truncate {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
</style>
