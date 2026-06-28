"use strict";
/* static/accounts/js/login.ts */
document.addEventListener('DOMContentLoaded', () => {
    const card = document.querySelector('.auth-card');
    const interactiveBlob = document.getElementById('interactive-blob');
    const toggleButtons = document.querySelectorAll('.password-toggle');
    // 1. Static Card Spotlight Glow & Background Parallax
    if (card) {
        card.addEventListener('mousemove', (e) => {
            const rect = card.getBoundingClientRect();
            const x = e.clientX - rect.left; // x position inside the card
            const y = e.clientY - rect.top; // y position inside the card
            // Update custom properties for spotlight gradient (visual feedback only)
            card.style.setProperty('--x', `${x}px`);
            card.style.setProperty('--y', `${y}px`);
        });
        card.addEventListener('mouseleave', () => {
            card.style.setProperty('--x', '-9999px');
            card.style.setProperty('--y', '-9999px');
        });
    }
    // 2. Parallax Effect for Surrounding Background Blobs
    const staticBlobs = document.querySelectorAll('.auth-bg-blob:not(.auth-blob-interactive)');
    window.addEventListener('mousemove', (e) => {
        const xc = (e.clientX - window.innerWidth / 2) / (window.innerWidth / 2);
        const yc = (e.clientY - window.innerHeight / 2) / (window.innerHeight / 2);
        staticBlobs.forEach((blob, idx) => {
            // Move blobs slightly in opposite directions for depth perception
            const factor = (idx + 1) * 35; // 35px max shift
            const shiftX = xc * factor * (idx % 2 === 0 ? 1 : -1);
            const shiftY = yc * factor * (idx % 2 === 0 ? 1 : -1);
            blob.style.transform = `translate3d(${shiftX}px, ${shiftY}px, 0)`;
        });
    });
    // 3. Mouse-following Interactive Background Blob
    if (interactiveBlob) {
        let mouseX = window.innerWidth / 2;
        let mouseY = window.innerHeight / 2;
        let blobX = mouseX;
        let blobY = mouseY;
        window.addEventListener('mousemove', (e) => {
            mouseX = e.clientX;
            mouseY = e.clientY;
        });
        // Animate the blob with inertia (ease)
        const animateBlob = () => {
            const ease = 0.08;
            blobX += (mouseX - blobX) * ease;
            blobY += (mouseY - blobY) * ease;
            interactiveBlob.style.left = `${blobX}px`;
            interactiveBlob.style.top = `${blobY}px`;
            requestAnimationFrame(animateBlob);
        };
        animateBlob();
    }
    // 4. Show/Hide Password Toggle
    toggleButtons.forEach((button) => {
        button.addEventListener('click', () => {
            // Find the input associated with this button in the same input-wrapper
            const wrapper = button.closest('.input-wrapper');
            if (wrapper) {
                const input = wrapper.querySelector('input');
                const icon = button.querySelector('i');
                if (input && icon) {
                    if (input.type === 'password') {
                        input.type = 'text';
                        icon.className = 'ri-eye-off-line';
                    }
                    else {
                        input.type = 'password';
                        icon.className = 'ri-eye-line';
                    }
                }
            }
        });
    });
    // 5. Multi-step Signup Navigation & Client Validation
    const signupForm = document.getElementById('signup-form');
    if (signupForm) {
        const step1 = document.getElementById('step-1');
        const step2 = document.getElementById('step-2');
        const btnNext = document.getElementById('btn-next-step');
        const btnPrev = document.getElementById('btn-prev-step');
        const pStep1 = document.getElementById('p-step-1');
        const pStep2 = document.getElementById('p-step-2');
        const progressFill = document.getElementById('progress-line-fill');
        const authFooter = document.querySelector('.auth-footer');
        const inputSchool = document.getElementById('school');
        const inputName = document.getElementById('name');
        const inputEmail = document.getElementById('email');
        const inputPw = document.getElementById('new-password');
        const inputPwConf = document.getElementById('confirm-password');
        // Split terms checkboxes
        const inputTermsAge = document.getElementById('terms-age');
        const inputTermsService = document.getElementById('terms-service');
        const inputTermsPrivacy = document.getElementById('terms-privacy');
        const errSchool = document.getElementById('error-school');
        const errName = document.getElementById('error-name');
        const errEmail = document.getElementById('error-email');
        const errPw = document.getElementById('error-password');
        const errPwConf = document.getElementById('error-confirm-password');
        const errTerms = document.getElementById('error-terms');
        // Live error clearing
        const clearErrorOnInput = (inputEl, errorEl) => {
            if (inputEl && errorEl) {
                inputEl.addEventListener('input', () => {
                    errorEl.textContent = '';
                });
            }
        };
        if (inputSchool && errSchool) {
            inputSchool.addEventListener('change', () => {
                errSchool.textContent = '';
            });
        }
        clearErrorOnInput(inputName, errName);
        clearErrorOnInput(inputEmail, errEmail);
        clearErrorOnInput(inputPw, errPw);
        if (inputPwConf && errPwConf) {
            inputPwConf.addEventListener('input', () => {
                errPwConf.textContent = '';
            });
        }
        const clearTermsError = () => {
            if (errTerms && inputTermsAge && inputTermsService && inputTermsPrivacy) {
                if (inputTermsAge.checked && inputTermsService.checked && inputTermsPrivacy.checked) {
                    errTerms.textContent = '';
                }
            }
        };
        if (inputTermsAge && errTerms) {
            inputTermsAge.addEventListener('change', clearTermsError);
        }
        if (inputTermsService && errTerms) {
            inputTermsService.addEventListener('change', clearTermsError);
        }
        if (inputTermsPrivacy && errTerms) {
            inputTermsPrivacy.addEventListener('change', clearTermsError);
        }
        const validateStep1 = () => {
            if (inputSchool && errSchool) {
                if (!inputSchool.value || inputSchool.value !== '부산대학교') {
                    errSchool.textContent = '현재는 부산대학교만 선택 가능합니다.';
                    return false;
                }
                errSchool.textContent = '';
            }
            return true;
        };
        const validateStep2 = () => {
            let isValid = true;
            // 1) Name Check
            if (inputName && errName) {
                const nameRegex = /^[a-zA-Z가-힣\s]+$/;
                const nameVal = inputName.value.trim();
                if (!nameVal) {
                    errName.textContent = '이름을 입력해주세요.';
                    isValid = false;
                }
                else if (!nameRegex.test(nameVal)) {
                    errName.textContent = '이름은 한글, 영문, 공백만 입력 가능합니다. (특수문자/숫자 제외)';
                    isValid = false;
                }
                else {
                    errName.textContent = '';
                }
            }
            // 2) Email Check
            if (inputEmail && errEmail) {
                const emailRegex = /^[a-zA-Z0-9_.+-]+@pusan\.ac\.kr$/i;
                const emailVal = inputEmail.value.trim();
                if (!emailVal) {
                    errEmail.textContent = '이메일 주소를 입력해주세요.';
                    isValid = false;
                }
                else if (!emailRegex.test(emailVal)) {
                    errEmail.textContent = '부산대학교 이메일 주소 형식이 아닙니다. (예: example@pusan.ac.kr)';
                    isValid = false;
                }
                else {
                    errEmail.textContent = '';
                }
            }
            // 3) Password Check
            if (inputPw && errPw) {
                if (!inputPw.value) {
                    errPw.textContent = '비밀번호를 입력해주세요.';
                    isValid = false;
                }
                else if (inputPw.value.length < 8) {
                    errPw.textContent = '비밀번호는 최소 8자 이상이어야 합니다.';
                    isValid = false;
                }
                else {
                    errPw.textContent = '';
                }
            }
            // 4) Password Confirm Check
            if (inputPw && inputPwConf && errPwConf) {
                if (!inputPwConf.value) {
                    errPwConf.textContent = '비밀번호 확인을 입력해주세요.';
                    isValid = false;
                }
                else if (inputPw.value !== inputPwConf.value) {
                    errPwConf.textContent = '비밀번호가 일치하지 않습니다.';
                    isValid = false;
                }
                else {
                    errPwConf.textContent = '';
                }
            }
            // 5) Terms Agreement Check
            if (errTerms) {
                const ageOk = inputTermsAge ? inputTermsAge.checked : false;
                const serviceOk = inputTermsService ? inputTermsService.checked : false;
                const privacyOk = inputTermsPrivacy ? inputTermsPrivacy.checked : false;
                if (!ageOk || !serviceOk || !privacyOk) {
                    errTerms.textContent = '필수 동의 항목에 모두 동의해주세요.';
                    isValid = false;
                }
                else {
                    errTerms.textContent = '';
                }
            }
            return isValid;
        };
        // Transition to Step 2
        if (btnNext && step1 && step2 && pStep1 && pStep2) {
            btnNext.addEventListener('click', () => {
                if (validateStep1()) {
                    // Slide & Fade step 1 out
                    step1.style.opacity = '0';
                    step1.style.transform = 'translateX(-16px)';
                    if (authFooter) {
                        authFooter.style.opacity = '0';
                        authFooter.style.transition = 'opacity 0.3s ease';
                    }
                    setTimeout(() => {
                        step1.classList.remove('active');
                        step2.classList.add('active');
                        // Force reflow
                        step2.offsetHeight;
                        step2.style.opacity = '1';
                        step2.style.transform = 'translateX(0)';
                        // Update Progress UI
                        pStep1.classList.add('completed');
                        pStep2.classList.add('active');
                        if (progressFill)
                            progressFill.style.width = '100%';
                        if (authFooter)
                            authFooter.style.display = 'none';
                    }, 300);
                }
            });
        }
        // Transition back to Step 1
        if (btnPrev && step1 && step2 && pStep1 && pStep2) {
            btnPrev.addEventListener('click', () => {
                // Slide & Fade step 2 out
                step2.style.opacity = '0';
                step2.style.transform = 'translateX(16px)';
                setTimeout(() => {
                    step2.classList.remove('active');
                    step1.classList.add('active');
                    // Force reflow
                    step1.offsetHeight;
                    step1.style.opacity = '1';
                    step1.style.transform = 'translateX(0)';
                    // Update Progress UI
                    pStep1.classList.remove('completed');
                    pStep2.classList.remove('active');
                    if (progressFill)
                        progressFill.style.width = '0%';
                    if (authFooter) {
                        authFooter.style.display = 'block';
                        authFooter.offsetHeight; // force reflow
                        authFooter.style.opacity = '1';
                    }
                }, 300);
            });
        }
        // Form Submission check
        signupForm.addEventListener('submit', (e) => {
            if (!validateStep1()) {
                e.preventDefault();
                // Force snap back to Step 1
                if (step1 && step2 && pStep1 && pStep2 && progressFill) {
                    step2.classList.remove('active');
                    step1.classList.add('active');
                    step1.style.opacity = '1';
                    step1.style.transform = 'translateX(0)';
                    pStep1.classList.remove('completed');
                    pStep2.classList.remove('active');
                    progressFill.style.width = '0%';
                    if (authFooter) {
                        authFooter.style.display = 'block';
                        authFooter.style.opacity = '1';
                    }
                }
                return;
            }
            if (!validateStep2()) {
                e.preventDefault();
            }
            else {
                // Double submission prevention
                const submitBtn = document.getElementById('btn-submit-signup');
                if (submitBtn) {
                    if (submitBtn.dataset.submitted === 'true') {
                        e.preventDefault();
                        return;
                    }
                    submitBtn.dataset.submitted = 'true';
                    submitBtn.disabled = true;
                    submitBtn.innerHTML = '가입 처리 중... <i class="ri-loader-4-line animate-spin"></i>';
                }
            }
        });
    }
    // 6. Login form double submission prevention
    const loginForm = document.getElementById('login-form');
    const loginSubmitBtn = document.getElementById('btn-submit-login');
    if (loginForm && loginSubmitBtn) {
        loginForm.addEventListener('submit', (e) => {
            if (loginSubmitBtn.dataset.submitted === 'true') {
                e.preventDefault();
                return;
            }
            loginSubmitBtn.dataset.submitted = 'true';
            loginSubmitBtn.disabled = true;
            loginSubmitBtn.innerHTML = '로그인 중... <i class="ri-loader-4-line animate-spin"></i>';
        });
    }
    // 7. Find Password form double submission prevention
    const pwdFindForm = document.getElementById('pwd-find-form');
    const pwdFindSubmitBtn = document.getElementById('btn-submit-pwd-find');
    if (pwdFindForm && pwdFindSubmitBtn) {
        pwdFindForm.addEventListener('submit', (e) => {
            if (pwdFindSubmitBtn.dataset.submitted === 'true') {
                e.preventDefault();
                return;
            }
            pwdFindSubmitBtn.dataset.submitted = 'true';
            pwdFindSubmitBtn.disabled = true;
            pwdFindSubmitBtn.innerHTML = '전송 중... <i class="ri-loader-4-line animate-spin"></i>';
        });
    }
    // 8. Verify Code form double submission prevention
    const pwdVerifyForm = document.getElementById('pwd-verify-form');
    const pwdVerifySubmitBtn = document.getElementById('btn-submit-pwd-verify');
    if (pwdVerifyForm && pwdVerifySubmitBtn) {
        pwdVerifyForm.addEventListener('submit', (e) => {
            if (pwdVerifySubmitBtn.dataset.submitted === 'true') {
                e.preventDefault();
                return;
            }
            pwdVerifySubmitBtn.dataset.submitted = 'true';
            pwdVerifySubmitBtn.disabled = true;
            pwdVerifySubmitBtn.innerHTML = '확인 중... <i class="ri-loader-4-line animate-spin"></i>';
        });
    }
    // 9. Reset Password form double submission prevention
    const pwdResetForm = document.getElementById('pwd-reset-form');
    const pwdResetSubmitBtn = document.getElementById('btn-submit-pwd-reset');
    if (pwdResetForm && pwdResetSubmitBtn) {
        pwdResetForm.addEventListener('submit', (e) => {
            if (pwdResetSubmitBtn.dataset.submitted === 'true') {
                e.preventDefault();
                return;
            }
            pwdResetSubmitBtn.dataset.submitted = 'true';
            pwdResetSubmitBtn.disabled = true;
            pwdResetSubmitBtn.innerHTML = '변경 중... <i class="ri-loader-4-line animate-spin"></i>';
        });
    }
});
