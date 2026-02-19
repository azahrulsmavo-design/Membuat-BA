<script setup>
import { ref, reactive, watch } from 'vue';
import axios from 'axios';
import ImageUploader from './components/ImageUploader.vue';

const bu = ref('');
const lokasi = ref('');
const showLayoutSettings = ref(false);

// Dynamic Backend URL
const API_BASE_URL = `http://${window.location.hostname}:8000`;

const units = ref([{
    nopol: '',
    images: {
        front: null,
        back: null,
        right: null,
        left: null,
        stnk: null,
        tax: null,
        kir: null,
        kir_card: null
    }
}]);

const activeIndex = ref(0);
const isGenerating = ref(false);

// Default Layout Settings (Matches Backend Defaults)
const layout = reactive({
    stnk: { x: 15, y: 40, w: 180, h: 60 },
    tax: { x: 15, y: 110, w: 180, h: 60 },
    kir: { x: 15, y: 180, w: 180, h: 60 },
    front: { x: 10, y: 50, w: 90, h: 80 },
    back: { x: 110, y: 50, w: 90, h: 80 },
    right: { x: 10, y: 140, w: 90, h: 80 },
    left: { x: 110, y: 140, w: 90, h: 80 }
});

const addUnit = () => {
    units.value.push({
        nopol: '',
        images: {
            front: null,
            back: null,
            right: null,
            left: null,
            stnk: null,
            tax: null,
            kir: null,
            kir_card: null
        }
    });
    activeIndex.value = units.value.length - 1;
};

const removeUnit = (index) => {
    if (confirm("Hapus unit ini?")) {
        if (units.value.length > 1) {
            units.value.splice(index, 1);
            if (activeIndex.value >= units.value.length) {
                activeIndex.value = units.value.length - 1;
            }
        } else {
            alert("Minimal satu unit harus ada.");
        }
    }
};

const generateReport = async () => {
    isGenerating.value = true;
    try {
        if (!bu.value || !lokasi.value) {
            alert("Harap isi Unit Bisnis dan Lokasi terlebih dahulu.");
            isGenerating.value = false;
            return;
        }

        const payload = {
            units: units.value.map(u => ({
                nopol: u.nopol || 'UNKNOWN',
                bu: bu.value,
                lokasi: lokasi.value,
                images: {
                    front: u.images.front?.dataUrl,
                    back: u.images.back?.dataUrl,
                    right: u.images.right?.dataUrl,
                    left: u.images.left?.dataUrl,
                    stnk: u.images.stnk?.dataUrl,
                    tax: u.images.tax?.dataUrl,
                    kir: u.images.kir?.dataUrl,
                    kir_card: u.images.kir_card?.dataUrl
                }
            })),
            layout: layout // Send layout config
        };
        
        const response = await axios.post(`${API_BASE_URL}/generate-multiset`, payload, {
            responseType: 'blob'
        });
        
        const url = window.URL.createObjectURL(new Blob([response.data]));
        const link = document.createElement('a');
        link.href = url;
        
        // Use first unit's Nopol for filename
        const firstNopol = units.value.length > 0 && units.value[0].nopol ? units.value[0].nopol.replace(/\s+/g, '_') : 'Unknown';
        link.setAttribute('download', `Asset_Report_${firstNopol}_${lokasi.value}_${new Date().toISOString().slice(0,10)}.pdf`);
        
        document.body.appendChild(link);
        link.click();
        
    } catch (e) {
        console.error(e);
        alert("Gagal membuat PDF. Cek console untuk detail.");
    } finally {
        isGenerating.value = false;
    }
};

const generateReportDocx = async () => {
    if (!bu.value || !lokasi.value) {
        alert("Harap isi Unit Bisnis dan Lokasi terlebih dahulu.");
        return;
    }
    
    isGenerating.value = true;
    try {
        const payload = {
            units: units.value.map(u => ({
                nopol: u.nopol || 'UNKNOWN',
                bu: bu.value,
                lokasi: lokasi.value,
                images: {
                    front: u.images.front?.dataUrl,
                    back: u.images.back?.dataUrl,
                    right: u.images.right?.dataUrl,
                    left: u.images.left?.dataUrl,
                    stnk: u.images.stnk?.dataUrl,
                    tax: u.images.tax?.dataUrl,
                    kir: u.images.kir?.dataUrl,
                    kir_card: u.images.kir_card?.dataUrl
                }
            })),
            layout: layout
        };
        
        const response = await axios.post(`${API_BASE_URL}/generate-multiset-docx`, payload, {
            responseType: 'blob'
        });
        
        const url = window.URL.createObjectURL(new Blob([response.data], { type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' }));
        const link = document.createElement('a');
        link.href = url;
        
        // Use first unit's Nopol for filename
        const firstNopol = units.value.length > 0 && units.value[0].nopol ? units.value[0].nopol.replace(/\s+/g, '_') : 'Unknown';
        link.setAttribute('download', `Asset_Report_${firstNopol}_${lokasi.value}_${new Date().getTime()}.docx`);
        
        document.body.appendChild(link);
        link.click();
        
    } catch (e) {
        console.error(e);
        alert("Gagal membuat laporan Word (DOCX). Cek console untuk detail.");
    } finally {
        isGenerating.value = false;
    }
};

const previewActiveUnit = async () => {
    if (!bu.value || !lokasi.value) {
        alert("Harap isi Unit Bisnis dan Lokasi terlebih dahulu.");
        return;
    }

    try {
        const currentUnit = units.value[activeIndex.value];
        const payload = {
            units: [{
                nopol: currentUnit.nopol || 'UNKNOWN',
                bu: bu.value,
                lokasi: lokasi.value,
                images: {
                    front: currentUnit.images.front?.dataUrl,
                    back: currentUnit.images.back?.dataUrl,
                    right: currentUnit.images.right?.dataUrl,
                    left: currentUnit.images.left?.dataUrl,
                    stnk: currentUnit.images.stnk?.dataUrl,
                    tax: currentUnit.images.tax?.dataUrl,
                    kir: currentUnit.images.kir?.dataUrl,
                    kir_card: currentUnit.images.kir_card?.dataUrl
                }
            }],
            layout: layout
        };
        
        // Open in new tab (preview)
        const response = await axios.post(`${API_BASE_URL}/generate-multiset`, payload, {
            responseType: 'blob'
        });
        
        const url = window.URL.createObjectURL(new Blob([response.data], { type: 'application/pdf' }));
        window.open(url, '_blank');
        
    } catch (e) {
        console.error(e);
        alert("Gagal melakukan preview. Pastikan backend berjalan.");
    }
};
const isSidebarOpen = ref(false);

// --- Bulk Import Logic ---
const showBulkImport = ref(false);
const bulkImportData = ref('');
const bulkDelimiter = ref('\t'); // Default to Tab

const isDownloadingAll = ref(false);
const isDownloadMinimized = ref(false);
const downloadProgress = ref({ current: 0, total: 0 });
const currentDownloadingTarget = ref(null); // { uIdx, key }

// Auto-switch unit when downloading
// Auto-switch unit when downloading - DISABLED by user request
// watch(currentDownloadingTarget, (newTarget) => {
//     if (newTarget && isDownloadingAll.value) {
//         if (newTarget.uIdx !== activeIndex.value) {
//             activeIndex.value = newTarget.uIdx;
//         }
//     }
// });

const deleteAllUnits = () => {
    if (confirm("⚠️ YAKIN HAPUS SEMUA UNIT? Data tidak bisa dikembalikan.")) {
        units.value = [{
            nopol: '',
            images: {
                front: null, back: null, right: null, left: null,
                stnk: null, tax: null, kir: null, kir_card: null
            }
        }];
        activeIndex.value = 0;
    }
};

const downloadAllDriveImages = async () => {
    // Collect all downloadable targets
    const targets = [];
    units.value.forEach((unit, uIdx) => {
        Object.keys(unit.images).forEach(key => {
            const imgData = unit.images[key];
            if (imgData && imgData.dataUrl && typeof imgData.dataUrl === 'string' && imgData.dataUrl.includes('drive.google.com')) {
                 targets.push({ uIdx, key, url: imgData.dataUrl });
            }
        });
    });

    if (targets.length === 0) {
        alert("Tidak ada link Google Drive yang ditemukan untuk di-download.");
        return;
    }

    if (!confirm(`Ditemukan ${targets.length} link gambar. Download semua sekarang?`)) return;

    isDownloadingAll.value = true;
    downloadProgress.value = { current: 0, total: targets.length };

    let successCount = 0;
    let failCount = 0;

    for (const target of targets) {
        currentDownloadingTarget.value = { uIdx: target.uIdx, key: target.key };
        try {
            const response = await axios.get(`${API_BASE_URL}/proxy-image`, {
                params: { url: target.url }, 
                responseType: 'blob'
            });
            
            const blob = response.data;
            
            // Validate content type
            if (!blob.type.startsWith('image/')) {
                throw new Error(`Invalid content type: ${blob.type}`);
            }

            const unitNopol = units.value[target.uIdx].nopol ? units.value[target.uIdx].nopol.replace(/\s+/g, '_') : `Unit_${target.uIdx + 1}`;
            const filename = `${unitNopol}_${target.key}_${new Date().getTime()}.jpg`;
            
            // Convert blob to base64 for local storage
            const reader = new FileReader();
            reader.readAsDataURL(blob);
            await new Promise(resolve => {
                reader.onloadend = () => {
                    // Update state directly
                    units.value[target.uIdx].images[target.key] = {
                        file: new File([blob], filename, { type: "image/jpeg" }),
                        dataUrl: reader.result
                    };
                    successCount++;
                    resolve();
                };
            });

        } catch (e) {
            console.error(`Failed to download ${target.url}`, e);
            failCount++;
        }
        
        downloadProgress.value.current++;
    }

    isDownloadingAll.value = false;
    currentDownloadingTarget.value = null;
    
    if (failCount > 0) {
        alert(`Proses selesai. ${successCount} berhasil, ${failCount} gagal. \nPeriksa koneksi ke server (Port 8000) atau Firewall.`);
    } else {
        alert(`Sukses! Semua ${successCount} gambar berhasil di-download.`);
    }
};

const processBulkImport = () => {
    if (!bulkImportData.value.trim()) return;

    const lines = bulkImportData.value.trim().split('\n');
    let importedCount = 0;

    lines.forEach((line, index) => {
        // Skip header row if it contains "FOTO STNK"
        if (line.includes('FOTO STNK') && line.includes('NOPOL')) return;
        
        // Use selected delimiter
        const delimiter = bulkDelimiter.value === '\\t' ? '\t' : bulkDelimiter.value;
        const cols = line.split(delimiter).map(c => c.trim());
        
        // Ensure we have enough columns (User provided 11 columns)
        // gracefully handle shorter lines if key data exists
        if (cols.length < 2) return; 

        // Mapping based on user provided order:
        // 0: STNK, 1: PAJAK, 2: KIR KERTAS, 3: KIR KARTU
        // 4: DEPAN, 5: BELAKANG, 6: KANAN, 7: KIRI
        // 8: CHECKLIST (Skip), 9: STATUS (Skip), 10: NOPOL

        const newUnit = {
            nopol: cols[10] || 'UNKNOWN',
            images: {
                stnk: cols[0] && cols[0] !== '-' ? { dataUrl: cols[0] } : null,
                tax: cols[1] && cols[1] !== '-' ? { dataUrl: cols[1] } : null,
                kir: cols[2] && cols[2] !== '-' ? { dataUrl: cols[2] } : null,
                kir_card: cols[3] && cols[3] !== '-' ? { dataUrl: cols[3] } : null,
                front: cols[4] && cols[4] !== '-' ? { dataUrl: cols[4] } : null,
                back: cols[5] && cols[5] !== '-' ? { dataUrl: cols[5] } : null,
                right: cols[6] && cols[6] !== '-' ? { dataUrl: cols[6] } : null,
                left: cols[7] && cols[7] !== '-' ? { dataUrl: cols[7] } : null
            }
        };

        // If it's the very first empty unit, replace it. Otherwise append.
        if (units.value.length === 1 && !units.value[0].nopol && !units.value[0].images.front) {
            units.value[0] = newUnit;
        } else {
            units.value.push(newUnit);
        }
        importedCount++;
    });

    if (importedCount > 0) {
        alert(`Berhasil mengimpor ${importedCount} unit!`);
        showBulkImport.value = false;
        bulkImportData.value = '';
        activeIndex.value = units.value.length - 1; // Switch to last
    } else {
        alert("Tidak ada data valid yang ditemukan.");
    }
};
</script>

<template>
  <div class="min-h-screen bg-gray-50 flex flex-col font-sans text-gray-900">
    <!-- Header -->
    <header class="bg-white shadow sticky top-0 z-30">
        <div class="max-w-7xl mx-auto px-4 h-16 flex justify-between items-center">
            
            <!-- Logo & Hamburger -->
            <div class="flex items-center gap-3">
                <button 
                    class="md:hidden p-2 -ml-2 rounded-md text-gray-600 hover:bg-gray-100" 
                    @click="isSidebarOpen = !isSidebarOpen"
                >
                    <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16"></path></svg>
                </button>
                <h1 class="text-lg md:text-xl font-bold text-gray-800 truncate">
                    Auto-AssetOpname <span class="text-blue-600 hidden sm:inline">Multi-Set</span>
                </h1>
            </div>
            
            <!-- Desktop Controls -->
            <div class="hidden md:flex items-center gap-2">
                 <!-- 1. Inputs Group -->
                 <div class="flex items-center gap-2 mr-2">
                    <input v-model="bu" type="text" placeholder="Unit Bisnis" class="border border-gray-300 rounded-lg px-3 py-1.5 text-xs w-28 focus:ring-2 focus:ring-blue-500 outline-none shadow-sm transition" />
                    <input v-model="lokasi" type="text" placeholder="Lokasi" class="border border-gray-300 rounded-lg px-3 py-1.5 text-xs w-32 focus:ring-2 focus:ring-blue-500 outline-none shadow-sm transition" />
                 </div>
                 
                 <div class="h-6 w-px bg-gray-200 mx-1"></div>

                 <!-- 2. Edit Actions -->
                 <div class="flex items-center gap-1">
                     <button @click="showBulkImport = true" class="text-gray-600 hover:text-blue-600 hover:bg-blue-50 font-medium text-xs px-3 py-1.5 rounded-lg transition border border-transparent hover:border-blue-100 flex items-center gap-1" title="Bulk Import">
                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path></svg>
                        Import
                     </button>

                     <button @click="showLayoutSettings = !showLayoutSettings" class="text-gray-600 hover:text-purple-600 hover:bg-purple-50 font-medium text-xs px-3 py-1.5 rounded-lg transition border border-transparent hover:border-purple-100 flex items-center gap-1" title="Layout Settings">
                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 5a1 1 0 011-1h14a1 1 0 011 1v2a1 1 0 01-1 1H5a1 1 0 01-1-1V5zM4 13a1 1 0 011-1h6a1 1 0 011 1v6a1 1 0 01-1 1H5a1 1 0 01-1-1v-6zM16 13a1 1 0 011-1h2a1 1 0 011 1v6a1 1 0 01-1 1h-2a1 1 0 01-1-1v-6z"></path></svg>
                        Layout
                     </button>
                    
                    <button @click="downloadAllDriveImages" :disabled="isDownloadingAll" class="text-gray-600 hover:text-green-600 hover:bg-green-50 font-medium text-xs px-3 py-1.5 rounded-lg transition border border-transparent hover:border-green-100 flex items-center gap-1" title="Download Semua Gambar Drive">
                        <span v-if="isDownloadingAll" class="flex items-center gap-1">
                            <svg class="animate-spin h-3 w-3" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
                            Saving...
                        </span>
                        <span v-else class="flex items-center gap-1">
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"></path></svg>
                            Save All
                        </span>
                     </button>
                 </div>

                 <div class="h-6 w-px bg-gray-200 mx-1"></div>

                 <!-- 3. Report Actions -->
                 <div class="flex items-center gap-2">
                     <button @click="previewActiveUnit" class="text-gray-600 hover:text-gray-900 border border-gray-200 hover:border-gray-300 font-medium py-1.5 px-3 rounded-lg text-xs transition shadow-sm flex items-center gap-1">
                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"></path></svg>
                        Preview
                     </button>
                     
                     <div class="flex items-center bg-blue-50 rounded-lg p-0.5 border border-blue-100">
                         <button 
                            @click="generateReport" 
                            :disabled="isGenerating"
                            class="text-blue-700 hover:bg-blue-100 hover:text-blue-800 font-bold py-1 px-3 rounded-md text-xs transition flex items-center gap-1 disabled:opacity-50">
                            PDF
                         </button>
                         <div class="w-px h-4 bg-blue-200 mx-1"></div>
                         <button 
                            @click="generateReportDocx" 
                            :disabled="isGenerating"
                            class="text-blue-700 hover:bg-blue-100 hover:text-blue-800 font-bold py-1 px-3 rounded-md text-xs transition flex items-center gap-1 disabled:opacity-50">
                            Word
                         </button>
                     </div>
                 </div>
            </div>

            <!-- Mobile Actions -->
             <div class="md:hidden flex gap-2">
                <button @click="showBulkImport = true" class="p-2 text-gray-600 bg-gray-50 rounded-full text-sm font-medium">Bulk</button>
                <button @click="previewActiveUnit" class="p-2 text-green-600 bg-green-50 rounded-full text-sm font-medium">View</button>
                <button @click="generateReport" :disabled="isGenerating" class="p-2 text-blue-600 bg-blue-50 rounded-full disabled:opacity-50">
                     <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"></path></svg>
                </button>
             </div>
        </div>

        <!-- Mobile Settings Drawer (Expandable) -->
        <div class="md:hidden px-4 pb-4 border-t border-gray-100 bg-gray-50 slide-down" v-if="!bu || !lokasi">
            <div class="grid grid-cols-2 gap-2 mt-2">
                <input v-model="bu" type="text" placeholder="Unit Bisnis (BU)" class="border rounded px-3 py-2 text-sm w-full" />
                <input v-model="lokasi" type="text" placeholder="Lokasi" class="border rounded px-3 py-2 text-sm w-full" />
            </div>
        </div>
    </header>

    <div class="flex flex-1 max-w-7xl mx-auto w-full relative">
        
        <!-- Mobile Sidebar Backdrop -->
        <div v-if="isSidebarOpen" @click="isSidebarOpen = false" class="fixed inset-0 bg-black/50 backdrop-blur-sm z-40 md:hidden transition-opacity"></div>

        <!-- Sidebar -->
        <div 
            class="fixed inset-y-0 left-0 w-72 bg-white shadow-2xl transform transition-transform duration-300 ease-in-out z-50 md:sticky md:top-16 md:translate-x-0 md:w-64 md:shadow-none md:bg-transparent flex flex-col h-full md:h-[calc(100vh-4rem)] border-r md:border-none"
            :class="isSidebarOpen ? 'translate-x-0' : '-translate-x-full'"
        >
            <div class="p-4 border-b bg-gray-50 md:bg-transparent flex justify-between items-center">
                <h2 class="font-bold text-gray-700 flex items-center gap-2">
                    Daftar Unit
                    <button @click="deleteAllUnits" class="text-xs font-normal text-red-500 hover:text-red-700 bg-red-50 hover:bg-red-100 px-2 py-0.5 rounded transition" title="Hapus Semua" v-if="units.length > 0">
                        Clear
                    </button>
                </h2>
                 <button @click="isSidebarOpen = false" class="md:hidden text-gray-500">
                    <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg>
                </button>
                <div class="flex gap-1">
                    <button @click="addUnit" class="text-white bg-blue-600 hover:bg-blue-700 rounded-full w-8 h-8 flex items-center justify-center shadow-sm font-bold text-lg" title="Tambah Unit">+</button>
                </div>
            </div>

            <!-- ... existing sidebar list ... -->
            <div class="flex-1 overflow-y-auto p-2 space-y-2">
                <div 
                    v-for="(unit, index) in units" 
                    :key="index"
                    @click="activeIndex = index; isSidebarOpen = false"
                    class="p-3 rounded-lg cursor-pointer border transition flex justify-between items-center group relative overflow-hidden"
                    :class="activeIndex === index ? 'bg-white border-blue-500 shadow-md ring-1 ring-blue-500 z-10' : 'bg-white border-gray-200 hover:bg-gray-50'"
                >
                    <div class="flex items-center gap-3">
                         <div class="w-8 h-8 rounded-full bg-blue-100 text-blue-600 flex items-center justify-center font-bold text-xs">
                            {{ index + 1 }}
                         </div>
                         <div>
                            <div class="font-bold text-sm text-gray-800">{{ unit.nopol || 'Tanpa Nopol' }}</div>
                            <div class="text-[10px] text-gray-500 uppercase tracking-wider">Unit #{{ index + 1 }}</div>
                        </div>
                    </div>
                    <button 
                        @click.stop="removeUnit(index)" 
                        class="text-gray-300 hover:text-red-500 p-1 rounded-md transition"
                        title="Hapus Unit"
                    >
                        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 3 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path></svg>
                    </button>
                </div>
            </div>

            <div class="p-4 bg-gray-50 md:bg-transparent text-xs text-center text-gray-400 border-t md:border-none">
                Total {{ units.length }} Unit
            </div>
        </div>

        <!-- Main Content (Active Unit) -->
        <div class="flex-1 flex flex-col w-full">
            <main class="flex-1 p-4 md:p-6 pb-24 md:pb-6" :key="activeIndex">
                
                <!-- Unit Header Input -->
                 <div class="bg-white rounded-xl shadow-sm p-4 mb-6 border border-gray-100">
                    <label class="block text-xs font-bold text-gray-400 uppercase tracking-widest mb-1">Nomor Polisi (Nopol)</label>
                    <input 
                        v-model="units[activeIndex].nopol" 
                        type="text" 
                        placeholder="Contoh: B 1234 CD" 
                        class="text-3xl font-black text-gray-800 border-none p-0 outline-none w-full bg-transparent placeholder-gray-200" 
                     />
                 </div>

                <!-- Page 1: Documents -->
                <div class="mb-8">
                     <h3 class="text-sm font-bold text-gray-500 uppercase tracking-widest mb-4 flex items-center gap-2">
                        <span class="w-2 h-2 bg-blue-500 rounded-full"></span>
                        Dokumen Kendaraan
                     </h3>
                     <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-2 gap-4">
                         <ImageUploader label="STNK" v-model="units[activeIndex].images.stnk" class="col-span-1 lg:col-span-2" :loading="currentDownloadingTarget?.uIdx === activeIndex && currentDownloadingTarget?.key === 'stnk'" />
                         <ImageUploader label="Pajak" v-model="units[activeIndex].images.tax" class="col-span-1 lg:col-span-2" :loading="currentDownloadingTarget?.uIdx === activeIndex && currentDownloadingTarget?.key === 'tax'" />
                         <ImageUploader label="KIR (Kertas)" v-model="units[activeIndex].images.kir" :loading="currentDownloadingTarget?.uIdx === activeIndex && currentDownloadingTarget?.key === 'kir'" />
                         <ImageUploader label="KIR (Kartu)" v-model="units[activeIndex].images.kir_card" :loading="currentDownloadingTarget?.uIdx === activeIndex && currentDownloadingTarget?.key === 'kir_card'" />
                     </div>
                </div>

                <!-- Page 2: Physical Photos -->
                <div>
                     <h3 class="text-sm font-bold text-gray-500 uppercase tracking-widest mb-4 flex items-center gap-2">
                        <span class="w-2 h-2 bg-purple-500 rounded-full"></span>
                        Fisik Kendaraan
                     </h3>
                     <div class="grid grid-cols-2 gap-3 sm:gap-4">
                         <ImageUploader label="Tampak Depan" v-model="units[activeIndex].images.front" :loading="currentDownloadingTarget?.uIdx === activeIndex && currentDownloadingTarget?.key === 'front'" />
                         <ImageUploader label="Tampak Belakang" v-model="units[activeIndex].images.back" :loading="currentDownloadingTarget?.uIdx === activeIndex && currentDownloadingTarget?.key === 'back'" />
                         <ImageUploader label="Samping Kanan" v-model="units[activeIndex].images.right" :loading="currentDownloadingTarget?.uIdx === activeIndex && currentDownloadingTarget?.key === 'right'" />
                         <ImageUploader label="Samping Kiri" v-model="units[activeIndex].images.left" :loading="currentDownloadingTarget?.uIdx === activeIndex && currentDownloadingTarget?.key === 'left'" />
                     </div>
                </div>
            </main>
        </div>
        
        <!-- Bulk Import Modal -->
        <div v-if="showBulkImport" class="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50 backdrop-blur-sm p-4">
             <div class="bg-white rounded-xl shadow-2xl w-full max-w-2xl flex flex-col max-h-[90vh]">
                 <div class="p-4 border-b flex justify-between items-center">
                    <h2 class="font-bold text-gray-800">Bulk Import Data</h2>
                    <button @click="showBulkImport = false" class="text-gray-400 hover:text-gray-600 bg-gray-100 rounded-full p-1">&times;</button>
                </div>
                <div class="p-4 flex-1 flex flex-col">
                    <div class="mb-6 bg-blue-50 p-4 rounded-xl border border-blue-100">
                        <label class="block text-xs font-bold text-blue-800 uppercase tracking-wider mb-3">Pilih Pemisah Kolom (Delimiter)</label>
                        <div class="flex flex-wrap gap-2">
                            <label class="flex items-center gap-2 text-xs cursor-pointer bg-white px-3 py-2 rounded-lg border border-blue-100 hover:border-blue-300 transition shadow-sm">
                                <input type="radio" v-model="bulkDelimiter" value="\t" class="text-blue-600 focus:ring-blue-500">
                                <span class="font-medium">Tab (Excel)</span>
                            </label>
                            <label class="flex items-center gap-2 text-xs cursor-pointer bg-white px-3 py-2 rounded-lg border border-blue-100 hover:border-blue-300 transition shadow-sm">
                                <input type="radio" v-model="bulkDelimiter" value=";" class="text-blue-600 focus:ring-blue-500">
                                <span class="font-medium">Titik Koma ( ; )</span>
                            </label>
                            <label class="flex items-center gap-2 text-xs cursor-pointer bg-white px-3 py-2 rounded-lg border border-blue-100 hover:border-blue-300 transition shadow-sm">
                                <input type="radio" v-model="bulkDelimiter" value="," class="text-blue-600 focus:ring-blue-500">
                                <span class="font-medium">Koma ( , )</span>
                            </label>
                            <label class="flex items-center gap-2 text-xs cursor-pointer bg-white px-3 py-2 rounded-lg border border-blue-100 hover:border-blue-300 transition shadow-sm">
                                <input type="radio" v-model="bulkDelimiter" value="|" class="text-blue-600 focus:ring-blue-500">
                                <span class="font-medium">Pipa ( | )</span>
                            </label>
                        </div>
                    </div>

                    <div class="flex justify-between items-center mb-2">
                        <label class="text-xs font-bold text-gray-500 uppercase">Data (Paste Here)</label>
                        <span class="text-[10px] text-gray-400">Format: STNK | PAJAK | ... | NOPOL</span>
                    </div>
                    <textarea 
                        v-model="bulkImportData" 
                        class="w-full flex-1 border rounded-xl p-4 font-mono text-xs focus:ring-2 focus:ring-blue-500 outline-none resize-none bg-gray-50 text-gray-700 leading-relaxed"
                        placeholder="Paste tabular data here..."
                    ></textarea>
                </div>
                <div class="p-4 border-t flex justify-end gap-3 bg-gray-50 rounded-b-xl">
                    <button @click="showBulkImport = false" class="px-5 py-2.5 text-gray-600 hover:bg-gray-200 rounded-xl text-sm font-bold transition">Batal</button>
                    <button @click="processBulkImport" class="px-6 py-2.5 bg-blue-600 text-white rounded-xl hover:bg-blue-700 text-sm font-bold shadow-lg hover:shadow-xl transition transform active:scale-95">Proses Import</button>
                </div>
             </div>
        </div>

        <!-- Layout Settings Modal -->
        <div v-if="showLayoutSettings" class="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50 backdrop-blur-sm p-4">
             <div class="bg-white rounded-xl shadow-2xl w-full max-w-sm flex flex-col max-h-[90vh]">
                 <div class="p-4 border-b flex justify-between items-center">
                    <h2 class="font-bold text-gray-800">Pengaturan Layout</h2>
                    <button @click="showLayoutSettings = false" class="text-gray-400 hover:text-gray-600 bg-gray-100 rounded-full p-1">&times;</button>
                </div>
                <div class="flex-1 overflow-y-auto p-4 space-y-6">
                    <p class="text-xs text-gray-500 bg-yellow-50 p-3 rounded-lg border border-yellow-100">
                        ⚠️ Atur posisi kotak gambar di PDF jika tidak pas.
                    </p>
                    
                    <div v-for="(val, key) in layout" :key="key" class="bg-gray-50 p-3 rounded-lg border">
                        <h3 class="font-bold text-xs uppercase text-blue-600 mb-2">{{ key }}</h3>
                        <div class="grid grid-cols-2 gap-4 mb-2">
                            <div>
                                <label class="text-[10px] block text-gray-400 mb-1">POSISI X (mm)</label>
                                <input type="range" min="0" max="210" v-model.number="val.x" class="w-full accent-blue-600">
                                <div class="text-right text-xs font-mono">{{ val.x }}</div>
                            </div>
                            <div>
                                <label class="text-[10px] block text-gray-400 mb-1">POSISI Y (mm)</label>
                                <input type="range" min="0" max="297" v-model.number="val.y" class="w-full accent-blue-600">
                                <div class="text-right text-xs font-mono">{{ val.y }}</div>
                            </div>
                        </div>
                        <div class="grid grid-cols-2 gap-4">
                             <div>
                                <label class="text-[10px] block text-gray-400 mb-1">WIDTH (mm)</label>
                                <input type="range" min="10" max="200" v-model.number="val.w" class="w-full accent-purple-600">
                                <div class="text-right text-xs font-mono">{{ val.w }}</div>
                            </div>
                            <div>
                                <label class="text-[10px] block text-gray-400 mb-1">HEIGHT (mm)</label>
                                <input type="range" min="10" max="200" v-model.number="val.h" class="w-full accent-purple-600">
                                <div class="text-right text-xs font-mono">{{ val.h }}</div>
                            </div>
                        </div>
                    </div>
                </div>
                <div class="p-4 border-t">
                    <button @click="showLayoutSettings = false" class="w-full bg-blue-600 text-white font-bold py-3 rounded-lg active:scale-95 transition">Simpan & Tutup</button>
                </div>
             </div>
        </div>

        <!-- Floating Download Progress -->
        <div v-if="isDownloadingAll" class="fixed bottom-4 right-4 z-50 bg-white rounded-lg shadow-xl border border-gray-200 overflow-hidden w-80 transition-all duration-300">
             
             <!-- Header (Always Visible) -->
             <div class="bg-gray-50 p-3 flex justify-between items-center cursor-pointer border-b md:border-none" @click="isDownloadMinimized = !isDownloadMinimized">
                <div class="flex items-center gap-2">
                    <div class="w-2 h-2 rounded-full bg-blue-500 animate-pulse"></div>
                    <div class="flex flex-col">
                        <h3 class="text-xs font-bold text-gray-700">Downloading...</h3>
                        <span v-if="currentDownloadingTarget && units[currentDownloadingTarget.uIdx]" class="text-[10px] text-gray-500 font-mono">
                            {{ units[currentDownloadingTarget.uIdx].nopol || `Unit ${currentDownloadingTarget.uIdx + 1}` }} - {{ currentDownloadingTarget.key.toUpperCase() }}
                        </span>
                    </div>
                </div>
                <div class="flex items-center gap-2">
                    <button class="text-gray-400 hover:text-gray-600">
                        <svg v-if="isDownloadMinimized" class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 15l7-7 7 7"></path></svg>
                        <svg v-else class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path></svg>
                    </button>
                </div>
             </div>

             <!-- Expanded Content -->
             <div class="p-4" v-if="!isDownloadMinimized">
                 <div class="flex justify-between text-xs text-gray-500 mb-2">
                    <span>Progress</span>
                    <span>{{ downloadProgress.current }} / {{ downloadProgress.total }}</span>
                 </div>
                 
                 <div class="w-full bg-gray-100 rounded-full h-2 mb-4 overflow-hidden">
                    <div class="bg-blue-600 h-2 rounded-full transition-all duration-300 ease-out" :style="{ width: `${(downloadProgress.current / downloadProgress.total) * 100}%` }"></div>
                 </div>

                 <button @click="isDownloadingAll = false, isDownloadMinimized = false" class="w-full text-center text-red-500 hover:text-red-700 text-xs font-bold hover:bg-red-50 py-2 rounded transition">
                    Batal Download
                 </button>
             </div>
        </div>

    </div>
  </div>
</template>
