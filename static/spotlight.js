const input = document.querySelector('input[type="url"]');
const root = document.documentElement;

document.addEventListener("mousemove", (e) => {
    if (!input.matches(":hover, :focus")) return;
    root.style.setProperty('--x', `${e.clientX}px`);
    root.style.setProperty('--y', `${e.clientY}px`);
});

input.addEventListener("mouseenter", () => {
    root.style.setProperty('--spotlight-visible', '1');
});

input.addEventListener("mouseleave", () => {
    if (!input.matches(":focus")) {
        root.style.setProperty('--spotlight-visible', '0');
    }
});

input.addEventListener("focus", () => {
    root.style.setProperty('--spotlight-visible', '1');
});

input.addEventListener("blur", () => {
    root.style.setProperty('--spotlight-visible', '0');
});
