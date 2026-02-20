<script setup>
import { ref, nextTick, watch, computed } from 'vue';
import axios from 'axios';
import 'vue-cropper/dist/index.css'
import { VueCropper } from "vue-cropper";

const API_BASE_URL = `http://${window.location.hostname}:8000`;

const props = defineProps({
  label: String,
  modelValue: [String, Object, File],
  loading: Boolean
});

const emit = defineEmits(['update:modelValue']);

const fileInput = ref(null);
const imageUrl = ref(null);
const originalImageUrl = ref(null); // Store original
const isProcessing = ref(false);
const showCropper = ref(false);
const cropper = ref(null);
const cropperImg = ref('');

// Watch mechanism to sync local state with parent data
watch(() => props.modelValue, (newVal) => {
    if (!newVal) {
        imageUrl.value = null; // Clear if null
    } else if (newVal.dataUrl) {
        imageUrl.value = newVal.dataUrl; // Update if new data
    }
}, { immediate: true, deep: true });

const isDriveLink = computed(() => {
    return typeof imageUrl.value === 'string' && imageUrl.value.includes('drive.google.com');
});

const onFileChange = (e) => {
  const file = e.target.files[0];
  if (!file) return;
  processFile(file);
};

const processFile = (file) => {
  const reader = new FileReader();
  reader.onload = (e) => {
    imageUrl.value = e.target.result;
    // If not a crop result (name doesn't start with cropped_), set as original
    // But better: processFile is called by autoCrop too.
    // Let's explicitly separate "New Upload" vs "Crop Result"
    // For now, if we don't have an original, set it.
    if (!originalImageUrl.value) {
        originalImageUrl.value = e.target.result;
    }
    emit('update:modelValue', { file, dataUrl: e.target.result });
  };
  reader.readAsDataURL(file);
}

const triggerSelect = () => {
  fileInput.value.click();
};

const openCropper = async () => {
    // If we have a modelValue (dataUrl), use that.
    const currentUrl = props.modelValue?.dataUrl || imageUrl.value;
    
    if (!currentUrl) return;

    // Check if it's a Drive Link (in modelValue) or placeholder is set
    // The placeholder is unique: "ssl.gstatic.com"
    const isDriveUrl = typeof currentUrl === 'string' && currentUrl.includes('drive.google.com');

    if (isDriveUrl) {
        try {
            // Use Proxy
            // Note: We MUST use the original Drive URL from modelValue, not the placeholder
            const driveUrl = props.modelValue.dataUrl;
            
            const response = await axios.get(`${API_BASE_URL}/proxy-image`, {
                params: { url: driveUrl }, 
                responseType: 'blob'
            });
            cropperImg.value = URL.createObjectURL(response.data);
            showCropper.value = true;
        } catch (e) {
            console.error(e);
            alert("Gagal memuat gambar dari Drive via Proxy. Cek backend.");
        }
    } else {
        // Local File or other image
        cropperImg.value = imageUrl.value;
        showCropper.value = true;
    }
}

const saveCrop = () => {
    // getCropBlob(callback, type, quality)
    cropper.value.getCropBlob((blob) => {
        // Create a unique filename
        const filename = "cropped_" + (new Date().getTime()) + ".jpg";
        // Create file from blob
        const newFile = new File([blob], filename, { type: "image/jpeg" });
        processFile(newFile);
        showCropper.value = false;
        
        // Clean up object URL if it was a proxy blob
        if (cropperImg.value.startsWith('blob:')) {
            URL.revokeObjectURL(cropperImg.value);
        }
    }, 'image/jpeg', 1.0); // 1.0 = Max Quality
}

const autoCrop = async () => {
  if (!props.modelValue || !props.modelValue.file) return;
  
  isProcessing.value = true;
  const formData = new FormData();
  formData.append('file', props.modelValue.file);
  
  try {
    const response = await axios.post(`${API_BASE_URL}/crop`, formData, {
      responseType: 'blob'
    });
    
    // Create new file from blob
    const croppedFile = new File([response.data], `cropped_${props.modelValue.file.name}`, {
      type: response.data.type,
    });
    
    processFile(croppedFile);
    
  } catch (error) {
    console.error("Auto-crop failed:", error);
    alert("Auto-crop failed. Ensure backend is running.");
  } finally {
    isProcessing.value = false;
  }
};
const isDragging = ref(false);

const handleDrop = (e) => {
  isDragging.value = false;
  const file = e.dataTransfer.files[0];
  if (!file) return;
  if (!file.type.startsWith('image/')) {
      alert("Please upload an image file.");
      return;
  }
  processFile(file);
};

const handleDragOver = (e) => {
  isDragging.value = true;
};

const handleDragLeave = (e) => {
  isDragging.value = false;
};

const showUrlInput = ref(false);
const urlInput = ref('');

const toggleUrlInput = () => {
    showUrlInput.value = !showUrlInput.value;
    if (showUrlInput.value) {
        nextTick(() => {
            // focus input if ref exists
        });
    }
};

const removeImage = () => {
    imageUrl.value = null;
    originalImageUrl.value = null;
    fileInput.value.value = ''; // Reset input
    emit('update:modelValue', null);
};

const restoreOriginal = () => {
    if (originalImageUrl.value) {
        imageUrl.value = originalImageUrl.value;
        // Verify if original was a file or url?
        // If it was a file, we might have lost the File object if we didn't save it.
        // But for display, dataUrl is enough.
        // For submission, we might need to handle it.
        // If we only have dataUrl, we emit that.
        emit('update:modelValue', { file: null, dataUrl: originalImageUrl.value });
    }
}

const saveUrl = async (urlOverride) => {
    const driveUrl = urlOverride || urlInput.value.trim();
    
    if (!driveUrl) return;

    showUrlInput.value = false;

    if (driveUrl.includes('drive.google.com')) {
        isProcessing.value = true;
        try {
            const response = await axios.get(`${API_BASE_URL}/proxy-image`, {
                params: { url: driveUrl }, 
                responseType: 'blob'
            });
            
            const blob = response.data;
            const filename = "drive_" + (new Date().getTime()) + ".jpg";
            const file = new File([blob], filename, { type: "image/jpeg" });
            
            processFile(file);
        } catch (e) {
            console.error(e);
            alert("Gagal mendownload link Drive. Pastikan link publik.");
        } finally {
            isProcessing.value = false;
        }
    } else {
        imageUrl.value = driveUrl;
        emit('update:modelValue', { file: null, dataUrl: driveUrl });
    }
};
</script>

<template>
  <div 
    class="border-2 border-dashed rounded-xl p-4 flex flex-col items-center justify-center min-h-[220px] relative transition group bg-white hover:bg-gray-50"
    :class="isDragging ? 'border-blue-500 bg-blue-50' : 'border-gray-300'"
    @dragover.prevent="handleDragOver"
    @dragleave.prevent="handleDragLeave"
    @drop.prevent="handleDrop"
  >
    <!-- LOADING STATE -->
    <div v-if="isProcessing || loading" class="absolute inset-0 z-40 bg-white/80 flex flex-col items-center justify-center">
        <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        <span class="text-xs text-blue-600 mt-2 font-bold">Downloading...</span>
    </div>

    <!-- URL INPUT OVERLAY -->
    <div v-if="showUrlInput" class="absolute inset-0 bg-white/95 backdrop-blur-sm z-30 flex flex-col items-center justify-center p-6 rounded-xl border border-blue-100 shadow-inner">
        <h4 class="text-sm font-bold text-gray-700 mb-3">Paste Google Drive Link</h4>
        <input 
            v-model="urlInput" 
            ref="urlInputRef" 
             type="text" 
             placeholder="https://drive.google.com/..." 
             class="border border-gray-300 rounded-lg px-3 py-2 w-full text-sm mb-3 focus:ring-2 focus:ring-blue-500 outline-none"
             @keyup.enter="saveUrl"
        />
        <div class="flex gap-2 w-full">
            <button @click="saveUrl" class="flex-1 bg-blue-600 text-white px-3 py-2 rounded-lg text-xs font-bold hover:bg-blue-700 transition">Download</button>
            <button @click="showUrlInput = false" class="flex-1 bg-gray-200 text-gray-700 px-3 py-2 rounded-lg text-xs font-bold hover:bg-gray-300 transition">Cancel</button>
        </div>
    </div>

    <div v-if="imageUrl" class="w-full h-full flex flex-col items-center z-10 relative">
      
      <!-- Drive Link State (Pending Download) -->
      <div v-if="isDriveLink" class="relative w-full h-40 mb-3 bg-blue-50 rounded-lg overflow-hidden flex flex-col items-center justify-center border border-blue-100 p-4 text-center">
          <div class="mb-2 text-blue-500">
            <svg class="w-8 h-8 mx-auto mb-1" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"></path></svg>
          </div>
          <p class="text-[10px] text-gray-500 font-mono break-all line-clamp-2 px-2 leading-tight mb-2">{{ imageUrl }}</p>
          <button @click="saveUrl(imageUrl)" class="bg-blue-600 text-white text-xs px-3 py-1.5 rounded shadow-sm hover:bg-blue-700 font-bold flex items-center gap-1">
              <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"></path></svg> 
              Download
          </button>
      </div>

      <!-- Normal Image Preview -->
      <div v-else class="relative w-full h-40 mb-3 bg-gray-100 rounded-lg overflow-hidden flex items-center justify-center border border-gray-100 group-hover:border-blue-200 transition">
          <img :src="imageUrl" class="max-w-full max-h-full object-contain" />
      </div>
      
      <div class="flex gap-2 flex-wrap justify-center w-full">
         <button @click="triggerSelect" class="flex-1 min-w-[40px] text-xs bg-white border border-gray-300 hover:bg-gray-50 px-2 py-1.5 rounded shadow-sm text-gray-700 flex justify-center items-center" title="Ganti Foto">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"></path></svg>
         </button>
         <button @click="autoCrop" class="flex-1 min-w-[40px] text-xs bg-purple-500 text-white hover:bg-purple-600 px-2 py-1.5 rounded shadow-sm font-bold flex justify-center items-center" title="AI Smart Crop">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path></svg>
         </button>
         <button @click="openCropper" class="flex-1 min-w-[40px] text-xs bg-yellow-500 text-white hover:bg-yellow-600 px-2 py-1.5 rounded shadow-sm font-bold">Crop</button>
         
         <button v-if="imageUrl !== originalImageUrl && originalImageUrl" @click="restoreOriginal" class="flex-1 min-w-[40px] text-xs bg-gray-500 text-white hover:bg-gray-600 px-2 py-1.5 rounded shadow-sm font-bold" title="Restore Original">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 10h10a8 8 0 018 8v2M3 10l6 6m-6-6l6-6"></path></svg>
         </button>

         <button @click="removeImage" class="flex-1 min-w-[40px] text-xs bg-red-50 border border-red-200 text-red-600 hover:bg-red-100 px-2 py-1.5 rounded shadow-sm font-bold" title="Hapus">Remove</button>
      </div>
    </div>
    
    <div v-else class="text-center w-full z-10 relative">
      <div 
        @click="triggerSelect"
        class="cursor-pointer p-4 hover:bg-gray-100 rounded-lg transition mb-3"
        title="Click to Upload File"
      >
          <div class="w-12 h-12 bg-blue-50 text-blue-500 rounded-full flex items-center justify-center mx-auto mb-2">
              <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L17 16m-5-5l1.09-1.09a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"></path></svg>
          </div>
          <p class="text-gray-700 text-sm font-bold mb-1">{{ label }}</p>
          <p class="text-gray-400 text-xs">
            <span v-if="isDragging" class="text-blue-500 font-bold">Drop image here</span>
            <span v-else>Click to Upload File</span>
          </p>
      </div>
      
      <div class="relative w-full max-w-[90%] mx-auto mt-2" @click.stop>
          <div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <svg class="h-4 w-4 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
            </svg>
          </div>
          <input 
            v-model="urlInput" 
            type="text" 
            placeholder="Paste Drive Link..." 
            class="pl-9 pr-10 py-2 w-full text-xs border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition shadow-sm bg-gray-50 hover:bg-white"
            @keyup.enter="saveUrl()"
          />
          <button 
            @click="saveUrl()" 
            class="absolute right-1 top-1 bottom-1 bg-blue-600 text-white rounded-md w-8 flex items-center justify-center hover:bg-blue-700 transition shadow-sm"
            title="Download Link"
          >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"></path></svg>
          </button>
      </div>
    </div>
    
    <!-- Input overlay for clicking background (if not dragging) -->
    <div v-if="!imageUrl && !showUrlInput" class="absolute inset-0 cursor-pointer z-0" @click="triggerSelect"></div>
    
    <input type="file" ref="fileInput" class="hidden" accept="image/*" @change="onFileChange" />

    <!-- CROPPER MODAL (Fixed Z-Index) -->
    <div v-if="showCropper" class="fixed inset-0 z-[60] flex items-center justify-center bg-black bg-opacity-80 p-4">
        <div class="bg-white rounded-xl w-full max-w-2xl h-[500px] flex flex-col overflow-hidden shadow-2xl">
            <div class="p-4 border-b flex justify-between items-center bg-gray-50">
                <h3 class="font-bold text-gray-700">Manual Crop</h3>
                <button @click="showCropper = false" class="text-gray-400 hover:text-gray-600">&times;</button>
            </div>
            <div class="flex-grow relative bg-gray-900">
                <vue-cropper
                    ref="cropper"
                    :img="cropperImg"
                    :outputSize="1"
                    outputType="jpeg"
                    :autoCrop="true"
                    :fixed="false"
                    :full="true"
                ></vue-cropper>
            </div>
            <div class="p-4 border-t flex justify-between items-center bg-white">
                <div class="flex gap-2">
                    <button @click="$refs.cropper.rotateLeft()" class="p-2 border rounded hover:bg-gray-50" title="Rotate Left">↺</button>
                    <button @click="$refs.cropper.rotateRight()" class="p-2 border rounded hover:bg-gray-50" title="Rotate Right">↻</button>
                </div>
                <div class="flex gap-2">
                    <button @click="showCropper = false" class="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-lg text-sm font-bold">Cancel</button>
                    <button @click="saveCrop" class="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm font-bold shadow-lg shadow-blue-200">Save Crop</button>
                </div>
            </div>
        </div>
    </div>
  </div>
</template>
