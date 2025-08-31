<script setup>
import FileUpload from 'primevue/fileupload';

axios.defaults.xsrfCookieName = "csrftoken";
axios.defaults.xsrfHeaderName = "X-CSRFToken";
axios.defaults.withCredentials = true;
</script>
<template>
    <div class="card">
        <FileUpload name="file" url="/api/upload-csv/" accept=".csv" :auto="true" :withCredentials="true"
            :customUpload="true" @uploader="onUpload">
            <template #empty>
                <p>Drag and drop a CSV file here</p>
            </template>
        </FileUpload>

        <div v-if="uploadResult" class="mt-4">
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

const onUpload = async (event) => {
    const file = event.files[0];
    if (!file) return;

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

        uploadResult.value = response.data;
            } catch (error) {
                uploadResult.value = `Error: ${error.response ? error.response.data : error.message}`;
            }
};
</script>
