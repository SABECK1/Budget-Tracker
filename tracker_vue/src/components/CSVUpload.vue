<script setup>
import FileUpload from 'primevue/fileupload';
import ProgressSpinner from 'primevue/progressspinner';

axios.defaults.xsrfCookieName = "csrftoken";
axios.defaults.xsrfHeaderName = "X-CSRFToken";
axios.defaults.withCredentials = true;
</script>
<template>
    <div class="card">
        <FileUpload name="file" url="/api/upload-csv/" accept=".csv" :withCredentials="true"
            :customUpload="true" @uploader="onUpload" :disabled="loading">
            <template #empty>
                <p>Drag and drop a CSV file here</p>
            </template>
        </FileUpload>

        <div v-if="loading" class="mt-4 text-center">
            <ProgressSpinner />
            <p class="mt-2">Uploading CSV file...</p>
        </div>

        <div v-if="uploadResult && !loading" class="mt-4">
            <p class="font-semibold">Upload Result:</p>
            <pre>{{ uploadResult }}</pre>
        </div>
    </div>
</template>

<script>
import { ref } from "vue";
import axios from "axios";
import Cookies from 'js-cookie';

const uploadResult = ref(null);
const loading = ref(false);

const onUpload = async (event) => {
    const file = event.files[0];
    if (!file) return;

    loading.value = true;
    uploadResult.value = null;

    const formData = new FormData();
    formData.append("file", file);

    try {
        const response = await axios.post(`${process.env.VUE_APP_API_BASE_URL}/upload-csv/`, formData, {
            headers: {
                "Content-Type": "multipart/form-data",
                'X-CSRFToken': Cookies.get('csrftoken'),
            },
            credentials: 'include',
        });

        uploadResult.value = `Success: ${response.data.message || 'CSV uploaded successfully'}`;
    } catch (error) {
        uploadResult.value = `Error: ${error.response ? error.response.data : error.message}`;
    } finally {
        loading.value = false;
    }
};
</script>
