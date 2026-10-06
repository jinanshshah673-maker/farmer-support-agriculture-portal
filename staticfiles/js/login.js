// ===============================
// Show / Hide Password
// ===============================

function togglePassword() {

    const password = document.getElementById("password");

    const icon = document.querySelector(".toggle");

    if (password.type === "password") {

        password.type = "text";

        icon.classList.remove("fa-eye");

        icon.classList.add("fa-eye-slash");

    } else {

        password.type = "password";

        icon.classList.remove("fa-eye-slash");

        icon.classList.add("fa-eye");

    }

}


// ===============================
// Button Animation
// ===============================

const loginBtn = document.querySelector(".login-btn");

if (loginBtn) {

    loginBtn.addEventListener("mouseover", function () {

        loginBtn.style.transform = "scale(1.03)";

    });

    loginBtn.addEventListener("mouseout", function () {

        loginBtn.style.transform = "scale(1)";

    });

}


// ===============================
// Fade Animation
// ===============================

window.addEventListener("load", () => {

    const card = document.querySelector(".login-box");

    card.style.opacity = "0";

    card.style.transform = "translateY(40px)";

    setTimeout(() => {

        card.style.transition = "0.8s";

        card.style.opacity = "1";

        card.style.transform = "translateY(0px)";

    }, 200);

});