document.addEventListener("DOMContentLoaded", () => {
    const title = "One More Descent";
    const titleElement = document.getElementById("title-animation");
    const saveSlotsContainer = document.getElementById("save-slots-container");

    let index = 0;

    function typeTitle() {
        if (index < title.length) {
            titleElement.textContent += title[index];
            index++;
            setTimeout(typeTitle, 150); // Adjust typing speed here
        } else {
            // Show the save slots after the typing animation
            setTimeout(() => {
                titleElement.classList.add("shrink");
                setTimeout(() => {
                    saveSlotsContainer.style.display = "block";
                }, 1000);
            }, 500);
        }
    }

    typeTitle();
});