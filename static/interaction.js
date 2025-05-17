// interaction.js

document.addEventListener("DOMContentLoaded", () => {
    const root = document.documentElement;
    const input = document.getElementById("youtube_url");
    const thumb = document.getElementById("yt-thumb");
    const preview = document.getElementById("preview");
    const title = document.getElementById("yt-title");
    const button = document.querySelector("button[type='submit']");
    const icon = document.getElementById("theme-icon");
    const toggle = document.querySelector(".theme-toggle");
    const progress = document.getElementById("progressBar");
    const audio = new Audio("/static/sfx/convert.mp3");

    // --- Theme ---
    function setTheme(theme) {
        root.setAttribute("data-theme", theme);
        localStorage.setItem("theme", theme);
        icon.setAttribute("data-lucide", theme === "dark" ? "moon" : "sun");
        lucide.createIcons();
    }

    toggle.addEventListener("click", () => {
        const current = root.getAttribute("data-theme");
        setTheme(current === "light" ? "dark" : "light");
    });

    setTheme(localStorage.getItem("theme") || "light");

    // --- Spotlight follow mouse when input hovered ---
    input.addEventListener("mouseenter", () => root.style.setProperty('--spotlight-visible', '1'));
    input.addEventListener("mouseleave", () => {
        if (!input.matches(":focus")) root.style.setProperty('--spotlight-visible', '0');
    });
    input.addEventListener("focus", () => root.style.setProperty('--spotlight-visible', '1'));
    input.addEventListener("blur", () => root.style.setProperty('--spotlight-visible', '0'));

    document.addEventListener("mousemove", (e) => {
        if (input.matches(":hover, :focus")) {
            root.style.setProperty('--x', `${e.clientX}px`);
            root.style.setProperty('--y', `${e.clientY}px`);
        }
    });

    // --- Extract YouTube video ID ---
    function extractVideoId(url) {
        const reg = /(?:v=|\/(?!user))([0-9A-Za-z_-]{11})/;
        const match = url.match(reg);
        return match ? match[1] : null;
    }

    // --- Live thumbnail + title ---
    input.addEventListener("input", async () => {
        const id = extractVideoId(input.value.trim());

        if (id) {
            thumb.src = `https://img.youtube.com/vi/${id}/hqdefault.jpg`;
            preview.classList.remove("hidden");
            preview.classList.add("visible");
            document.body.classList.remove("centered");

            try {
                const res = await fetch(`https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v=${id}&format=json`);
                const data = await res.json();
                title.textContent = data.title || "Vidéo détectée";
            } catch {
                title.textContent = "Vidéo détectée";
            }
        } else {
            preview.classList.remove("visible");
            preview.classList.add("hidden");
            document.body.classList.add("centered");
        }
    });

    // --- Button click: audio, vibration, progress ---
    button.addEventListener("click", () => {
        audio.currentTime = 0;
        audio.play();
        if (navigator.vibrate) navigator.vibrate([20]);

        progress.classList.remove("hidden");
        progress.querySelector(".progress-bar").style.animation = "progressAnim 2.5s ease forwards";
    });
});