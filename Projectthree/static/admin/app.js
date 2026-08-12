// ADMIN DASHBOARD JAVASCRIPT LOGIC
document.addEventListener("DOMContentLoaded", () => {
    // DOM Elements
    const navItems = document.querySelectorAll(".nav-item");
    const tabContents = document.querySelectorAll(".tab-content");
    const themeToggleBtn = document.getElementById("theme-toggle");
    
    const dropzone = document.getElementById("dropzone");
    const fileInput = document.getElementById("syllabus-file-input");
    const uploadForm = document.getElementById("upload-form");
    const removeFileBtn = document.getElementById("remove-file-btn");
    const filePreviewInfo = document.getElementById("file-preview-info");
    const dropzoneContent = document.querySelector(".dropzone-content");
    const previewFilename = document.getElementById("preview-filename");
    const previewFilesize = document.getElementById("preview-filesize");
    
    const uploadProgressContainer = document.getElementById("upload-progress-container");
    const uploadProgressFill = document.getElementById("upload-progress-fill");
    const uploadProgressText = document.getElementById("upload-progress-text");

    const quickSampleBtn = document.getElementById("quick-sample-btn");
    const copySnippetBtn = document.getElementById("copy-snippet-btn");
    const embedSnippetCode = document.getElementById("embed-snippet-code");
    const refreshUnresolvedBtn = document.getElementById("refresh-unresolved-btn");

    const apiKeyForm = document.getElementById("api-key-form");
    const apiKeyInput = document.getElementById("api-key-input");

    const simChatWindow = document.getElementById("sim-chat-window");
    const simInput = document.getElementById("sim-input");
    const simSendBtn = document.getElementById("sim-send-btn");

    // Initialize Dashboard Data
    fetchCourseInfo();
    fetchAnalytics();
    fetchUnresolvedQuestions();
    fetchApiKeyStatus();
    updateEmbedSnippet();

    // Tab Navigation Logic
    navItems.forEach(item => {
        item.addEventListener("click", (e) => {
            e.preventDefault();
            const targetTab = item.getAttribute("data-tab");
            
            navItems.forEach(n => n.classList.remove("active"));
            tabContents.forEach(t => t.classList.remove("active"));

            item.classList.add("active");
            document.getElementById(`tab-${targetTab}`).classList.add("active");

            // Update Header Title
            const titleMap = {
                "overview": ["Course Dashboard & Syllabus Upload", "Manage your syllabus vector index, track unresolved questions, and get embed snippet"],
                "unresolved": ["Unresolved Student Questions", "Questions students asked that were missing or unclear in the uploaded syllabus"],
                "embed": ["1-Line HTML Snippet Generator", "Embed your course AI chatbot into Canvas, Moodle, or any website"],
                "simulator": ["Live Student Chat Simulator", "Test RAG responses against your uploaded syllabus"],
                "settings": ["API Settings & Configuration", "Configure your Gemini 3.6 Flash API key"]
            };
            if (titleMap[targetTab]) {
                document.getElementById("page-title").textContent = titleMap[targetTab][0];
                document.getElementById("page-subtitle").textContent = titleMap[targetTab][1];
            }
        });
    });

    // Theme Toggle Logic
    themeToggleBtn.addEventListener("click", () => {
        document.body.classList.toggle("light-theme");
        const isLight = document.body.classList.contains("light-theme");
        themeToggleBtn.innerHTML = isLight ? '<i class="fa-solid fa-sun"></i>' : '<i class="fa-solid fa-moon"></i>';
    });

    // File Drag & Drop Setup
    ["dragenter", "dragover"].forEach(eventName => {
        dropzone.addEventListener(eventName, (e) => {
            e.preventDefault();
            dropzone.classList.add("dragover");
        });
    });

    ["dragleave", "drop"].forEach(eventName => {
        dropzone.addEventListener(eventName, (e) => {
            e.preventDefault();
            dropzone.classList.remove("dragover");
        });
    });

    dropzone.addEventListener("drop", (e) => {
        const files = e.dataTransfer.files;
        if (files.length) {
            fileInput.files = files;
            handleFileSelected(files[0]);
        }
    });

    fileInput.addEventListener("change", (e) => {
        if (fileInput.files.length) {
            handleFileSelected(fileInput.files[0]);
        }
    });

    function handleFileSelected(file) {
        previewFilename.textContent = file.name;
        previewFilesize.textContent = formatBytes(file.size);
        dropzoneContent.classList.add("hidden");
        filePreviewInfo.classList.remove("hidden");
    }

    removeFileBtn.addEventListener("click", (e) => {
        e.stopPropagation();
        fileInput.value = "";
        filePreviewInfo.classList.add("hidden");
        dropzoneContent.classList.remove("hidden");
    });

    // Handle Upload Submission
    uploadForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        if (!fileInput.files.length) {
            showToast("Please select a syllabus PDF, TXT or CSV file first.", "error");
            return;
        }

        const formData = new FormData();
        formData.append("file", fileInput.files[0]);
        formData.append("course_id", "default");
        
        const customTitle = document.getElementById("custom-course-name").value.trim();
        if (customTitle) {
            formData.append("custom_course_name", customTitle);
        }

        uploadProgressContainer.classList.remove("hidden");
        uploadProgressFill.style.width = "40%";
        uploadProgressText.textContent = "Parsing document & creating ChromaDB vector index...";

        try {
            const res = await fetch("/api/admin/upload-syllabus", {
                method: "POST",
                body: formData
            });

            const data = await res.json();
            if (res.ok) {
                uploadProgressFill.style.width = "100%";
                uploadProgressText.textContent = "Complete!";
                showToast("Syllabus successfully uploaded and indexed!", "success");
                
                setTimeout(() => {
                    uploadProgressContainer.classList.add("hidden");
                    uploadProgressFill.style.width = "0%";
                }, 2000);

                fetchCourseInfo();
                fetchAnalytics();
            } else {
                throw new Error(data.detail || "Upload failed");
            }
        } catch (err) {
            uploadProgressContainer.classList.add("hidden");
            showToast(err.message, "error");
        }
    });

    // Quick Sample Load
    quickSampleBtn.addEventListener("click", async () => {
        quickSampleBtn.disabled = true;
        quickSampleBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Indexing CS101...';
        
        try {
            const res = await fetch("/api/admin/upload-syllabus", {
                method: "POST",
                body: await createSampleFormData()
            });
            const data = await res.json();
            if (res.ok) {
                showToast("Sample CS101 syllabus indexed successfully!", "success");
                fetchCourseInfo();
                fetchAnalytics();
            } else {
                showToast(data.detail || "Error loading sample", "error");
            }
        } catch (err) {
            showToast("Failed to load sample syllabus: " + err.message, "error");
        } finally {
            quickSampleBtn.disabled = false;
            quickSampleBtn.innerHTML = '<i class="fa-solid fa-wand-magic-sparkles"></i> Load CS101 Sample Syllabus';
        }
    });

    // Helper to generate sample file FormData
    async function createSampleFormData() {
        const res = await fetch("/sample_data/create_sample_syllabus.py"); // check backend route or mock file
        const blob = new Blob([getSampleSyllabusText()], { type: "text/plain" });
        const file = new File([blob], "CS101_Syllabus.txt", { type: "text/plain" });
        const fd = new FormData();
        fd.append("file", file);
        fd.append("course_id", "default");
        fd.append("custom_course_name", "CS 101: Introduction to AI");
        return fd;
    }

    function getSampleSyllabusText() {
        return `
CS 101: Introduction to Computer Science & Artificial Intelligence
Instructor: Dr. Sarah Jenkins (sjenkins@university.edu)
Office Hours: Tuesdays & Thursdays 2:00 PM – 4:00 PM (Tech Hall Room 402)
Head TA: Alex Rivera (arivera@university.edu)
TA Office Hours: Wednesdays 10:00 AM – 12:00 PM & Fridays 1:00 PM – 3:00 PM

Grading Policy:
- Programming Assignments (4): 30%
- Midterm Examination: 25% (October 22 in class)
- Final Capstone Project: 30% (Due December 15)
- Quizzes & Participation: 15%

Assignment Late Policy & Grace Days:
All assignments are due at 11:59 PM EST on Canvas.
Each student receives 3 total slip days for the entire semester.
Once slip days are used, late submissions incur a 15% penalty per 24 hours late.
Submissions over 48 hours late receive 0 credit.

Required Textbook:
Python Crash Course (3rd Edition) by Eric Matthes.
        `;
    }

    // Fetch Active Course Info
    async function fetchCourseInfo() {
        try {
            const res = await fetch("/api/admin/course?course_id=default");
            const data = await res.json();
            
            if (data.has_syllabus) {
                const c = data.course;
                document.getElementById("meta-course-name").textContent = c.course_name;
                document.getElementById("meta-course-code").textContent = c.course_code || "CS101";
                document.getElementById("meta-instructor").textContent = c.instructor || "Dr. Sarah Jenkins";
                document.getElementById("meta-chunk-count").textContent = `${c.chunk_count} Vector Chunks`;
                document.getElementById("meta-filename").textContent = c.syllabus_filename;
                document.getElementById("meta-upload-date").textContent = new Date(c.upload_timestamp).toLocaleDateString();

                document.getElementById("stat-syllabus-file").textContent = c.syllabus_filename;
                document.getElementById("stat-chunks-count").textContent = `${c.chunk_count} Chunks Indexed`;

                document.getElementById("sidebar-course-title").textContent = c.course_name;
                document.getElementById("sidebar-course-status").textContent = `${c.chunk_count} Vector Chunks`;
            }
        } catch (e) {
            console.error("Error fetching course info:", e);
        }
    }

    // Fetch Analytics Summary
    async function fetchAnalytics() {
        try {
            const res = await fetch("/api/admin/analytics?course_id=default");
            const data = await res.json();
            
            document.getElementById("stat-total-queries").textContent = data.total_queries;
            document.getElementById("stat-resolution-rate").textContent = `${data.resolution_rate}% Resolution Rate`;
            document.getElementById("stat-pending-questions").textContent = data.pending_unresolved;
            document.getElementById("unresolved-badge").textContent = data.pending_unresolved;
        } catch (e) {
            console.error("Error fetching analytics:", e);
        }
    }

    // Fetch Unresolved Questions
    async function fetchUnresolvedQuestions() {
        try {
            const res = await fetch("/api/admin/unresolved-questions?course_id=default");
            const data = await res.json();
            const list = data.unresolved_questions;
            const tbody = document.getElementById("unresolved-table-body");

            if (!list || list.length === 0) {
                tbody.innerHTML = `
                    <tr>
                        <td colspan="6" class="empty-state">
                            <i class="fa-solid fa-check-circle"></i>
                            <p>No unresolved questions yet! All student questions have been answered from the syllabus.</p>
                        </td>
                    </tr>
                `;
                return;
            }

            tbody.innerHTML = list.map(q => `
                <tr>
                    <td><span class="chip chip-primary">${q.frequency_count}x</span></td>
                    <td><strong>${escapeHtml(q.question)}</strong></td>
                    <td>${new Date(q.first_asked).toLocaleDateString()}</td>
                    <td>${new Date(q.last_asked).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}</td>
                    <td><span class="chip ${q.status === 'resolved' ? 'chip-success' : 'chip-primary'}">${q.status}</span></td>
                    <td>
                        <button class="btn btn-sm btn-outline" onclick="resolveQuestion(${q.id})"><i class="fa-solid fa-check"></i> Mark Resolved</button>
                        <button class="btn-icon" onclick="deleteQuestion(${q.id})" title="Delete"><i class="fa-solid fa-trash"></i></button>
                    </td>
                </tr>
            `).join("");

        } catch (e) {
            console.error("Error fetching unresolved questions:", e);
        }
    }

    refreshUnresolvedBtn.addEventListener("click", fetchUnresolvedQuestions);

    window.resolveQuestion = async function(id) {
        try {
            await fetch(`/api/admin/unresolved-questions/${id}/status`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ status: "resolved" })
            });
            showToast("Question marked as resolved!", "success");
            fetchUnresolvedQuestions();
            fetchAnalytics();
        } catch (e) {
            showToast("Error updating question status", "error");
        }
    };

    window.deleteQuestion = async function(id) {
        try {
            await fetch(`/api/admin/unresolved-questions/${id}`, { method: "DELETE" });
            showToast("Deleted question.", "success");
            fetchUnresolvedQuestions();
            fetchAnalytics();
        } catch (e) {
            showToast("Error deleting question", "error");
        }
    };

    // Fetch API Key Status
    async function fetchApiKeyStatus() {
        try {
            const res = await fetch("/api/admin/settings/api-key");
            const data = await res.json();
            const statEl = document.getElementById("stat-api-status");
            if (data.configured) {
                statEl.textContent = "Configured";
                statEl.style.color = "var(--accent-green)";
            } else {
                statEl.textContent = "Key Missing";
                statEl.style.color = "var(--accent-orange)";
            }
        } catch (e) {
            console.error("API Key check error:", e);
        }
    }

    // Save API Key
    apiKeyForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        const key = apiKeyInput.value.trim();
        if (!key) return;

        try {
            const res = await fetch("/api/admin/settings/api-key", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ api_key: key })
            });
            if (res.ok) {
                showToast("API key updated successfully!", "success");
                apiKeyInput.value = "";
                fetchApiKeyStatus();
            }
        } catch (e) {
            showToast("Failed to save API key", "error");
        }
    });

    // Copy Embed Snippet
    copySnippetBtn.addEventListener("click", () => {
        const text = embedSnippetCode.textContent;
        navigator.clipboard.writeText(text).then(() => {
            showToast("Embed code copied to clipboard!", "success");
        });
    });

    function updateEmbedSnippet() {
        const origin = window.location.origin;
        embedSnippetCode.textContent = `<script src="${origin}/static/widget/embed.js" data-course-id="default"></script>`;
    }

    // Simulator Chat Logic
    simSendBtn.addEventListener("click", sendSimQuestion);
    simInput.addEventListener("keypress", (e) => {
        if (e.key === "Enter") sendSimQuestion();
    });

    async function sendSimQuestion() {
        const text = simInput.value.trim();
        if (!text) return;

        simInput.value = "";
        appendSimMessage(text, "user");

        // Bot typing indicator
        const typingId = appendSimMessage('<i class="fa-solid fa-spinner fa-spin"></i> Searching syllabus...', "bot");

        try {
            const res = await fetch("/api/chat/query", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ question: text, course_id: "default" })
            });
            const data = await res.json();

            removeSimMessage(typingId);
            appendSimMessage(data.answer, "bot", data.sources);
            fetchAnalytics();
            fetchUnresolvedQuestions();
        } catch (e) {
            removeSimMessage(typingId);
            appendSimMessage("Sorry, an error occurred while reaching the AI assistant.", "bot");
        }
    }

    function appendSimMessage(text, sender, sources = []) {
        const msgDiv = document.createElement("div");
        const id = "msg_" + Date.now();
        msgDiv.id = id;
        msgDiv.className = `chat-msg ${sender}-msg`;
        
        let formattedText = text.replace(/\n/g, "<br>").replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");
        let sourcesHtml = "";
        if (sources && sources.length) {
            sourcesHtml = `<div style="margin-top:8px; font-size:11px; color:var(--text-muted);">📚 Sources: ${sources.join(", ")}</div>`;
        }

        msgDiv.innerHTML = `
            <div class="avatar"><i class="fa-solid ${sender === 'user' ? 'fa-user' : 'fa-robot'}"></i></div>
            <div class="msg-content">${formattedText}${sourcesHtml}</div>
        `;

        simChatWindow.appendChild(msgDiv);
        simChatWindow.scrollTop = simChatWindow.scrollHeight;
        return id;
    }

    function removeSimMessage(id) {
        const el = document.getElementById(id);
        if (el) el.remove();
    }

    // Helper functions
    function showToast(msg, type = "success") {
        const container = document.getElementById("toast-container");
        const toast = document.createElement("div");
        toast.className = `toast ${type}`;
        toast.innerHTML = `<i class="fa-solid ${type === 'success' ? 'fa-circle-check' : 'fa-circle-exclamation'}"></i> <span>${msg}</span>`;
        container.appendChild(toast);
        setTimeout(() => toast.remove(), 4000);
    }

    function formatBytes(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
    }

    function escapeHtml(text) {
        return text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
    }
});
