const button = document.querySelector(".menu-button");
const menu = document.querySelector(".menu");

if (button && menu) {
  button.addEventListener("click", () => {
    const isOpen = button.getAttribute("aria-expanded") === "true";
    button.setAttribute("aria-expanded", String(!isOpen));
    menu.classList.toggle("is-open");
  });
}
