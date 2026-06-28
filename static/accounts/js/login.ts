/* static/accounts/js/login.ts */

document.addEventListener('DOMContentLoaded', (): void => {
  const card: HTMLElement | null = document.querySelector('.auth-card');
  const interactiveBlob: HTMLElement | null = document.getElementById('interactive-blob');
  const toggleButtons: NodeListOf<HTMLButtonElement> = document.querySelectorAll('.password-toggle');

  // 1. Static Card Spotlight Glow & Background Parallax
  if (card) {
    card.addEventListener('mousemove', (e: MouseEvent): void => {
      const rect: DOMRect = card.getBoundingClientRect();
      const x: number = e.clientX - rect.left; // x position inside the card
      const y: number = e.clientY - rect.top;  // y position inside the card

      // Update custom properties for spotlight gradient (visual feedback only)
      card.style.setProperty('--x', `${x}px`);
      card.style.setProperty('--y', `${y}px`);
    });

    card.addEventListener('mouseleave', (): void => {
      card.style.setProperty('--x', '-9999px');
      card.style.setProperty('--y', '-9999px');
    });
  }

  // 2. Parallax Effect for Surrounding Background Blobs
  const staticBlobs: NodeListOf<HTMLElement> = document.querySelectorAll('.auth-bg-blob:not(.auth-blob-interactive)');
  window.addEventListener('mousemove', (e: MouseEvent): void => {
    const xc: number = (e.clientX - window.innerWidth / 2) / (window.innerWidth / 2);
    const yc: number = (e.clientY - window.innerHeight / 2) / (window.innerHeight / 2);

    staticBlobs.forEach((blob: HTMLElement, idx: number): void => {
      // Move blobs slightly in opposite directions for depth perception
      const factor: number = (idx + 1) * 35; // 35px max shift
      const shiftX: number = xc * factor * (idx % 2 === 0 ? 1 : -1);
      const shiftY: number = yc * factor * (idx % 2 === 0 ? 1 : -1);
      blob.style.transform = `translate3d(${shiftX}px, ${shiftY}px, 0)`;
    });
  });

  // 3. Mouse-following Interactive Background Blob
  if (interactiveBlob) {
    let mouseX: number = window.innerWidth / 2;
    let mouseY: number = window.innerHeight / 2;
    let blobX: number = mouseX;
    let blobY: number = mouseY;

    window.addEventListener('mousemove', (e: MouseEvent): void => {
      mouseX = e.clientX;
      mouseY = e.clientY;
    });

    // Animate the blob with inertia (ease)
    const animateBlob = (): void => {
      const ease: number = 0.08;
      blobX += (mouseX - blobX) * ease;
      blobY += (mouseY - blobY) * ease;

      interactiveBlob.style.left = `${blobX}px`;
      interactiveBlob.style.top = `${blobY}px`;

      requestAnimationFrame(animateBlob);
    };

    animateBlob();
  }

  // 4. Show/Hide Password Toggle
  toggleButtons.forEach((button: HTMLButtonElement): void => {
    button.addEventListener('click', (): void => {
      // Find the input associated with this button in the same input-wrapper
      const wrapper: HTMLElement | null = button.closest('.input-wrapper');
      if (wrapper) {
        const input: HTMLInputElement | null = wrapper.querySelector('input');
        const icon: HTMLElement | null = button.querySelector('i');

        if (input && icon) {
          if (input.type === 'password') {
            input.type = 'text';
            icon.className = 'ri-eye-off-line';
          } else {
            input.type = 'password';
            icon.className = 'ri-eye-line';
          }
        }
      }
    });
  });

  // 5. Multi-step Signup Navigation & Client Validation
  const signupForm: HTMLFormElement | null = document.getElementById('signup-form') as HTMLFormElement;
  if (signupForm) {
    const step1: HTMLElement | null = document.getElementById('step-1');
    const step2: HTMLElement | null = document.getElementById('step-2');
    const btnNext: HTMLElement | null = document.getElementById('btn-next-step');
    const btnPrev: HTMLElement | null = document.getElementById('btn-prev-step');
    const pStep1: HTMLElement | null = document.getElementById('p-step-1');
    const pStep2: HTMLElement | null = document.getElementById('p-step-2');
    const progressFill: HTMLElement | null = document.getElementById('progress-line-fill');
    const authFooter: HTMLElement | null = document.querySelector('.auth-footer');

    const inputSchool: HTMLSelectElement | null = document.getElementById('school') as HTMLSelectElement;
    const inputName: HTMLInputElement | null = document.getElementById('name') as HTMLInputElement;
    const inputEmail: HTMLInputElement | null = document.getElementById('email') as HTMLInputElement;
    const inputPw: HTMLInputElement | null = document.getElementById('new-password') as HTMLInputElement;
    const inputPwConf: HTMLInputElement | null = document.getElementById('confirm-password') as HTMLInputElement;
    
    // Split terms checkboxes
    const inputTermsAge: HTMLInputElement | null = document.getElementById('terms-age') as HTMLInputElement;
    const inputTermsService: HTMLInputElement | null = document.getElementById('terms-service') as HTMLInputElement;
    const inputTermsPrivacy: HTMLInputElement | null = document.getElementById('terms-privacy') as HTMLInputElement;

    const errSchool: HTMLElement | null = document.getElementById('error-school');
    const errName: HTMLElement | null = document.getElementById('error-name');
    const errEmail: HTMLElement | null = document.getElementById('error-email');
    const errPw: HTMLElement | null = document.getElementById('error-password');
    const errPwConf: HTMLElement | null = document.getElementById('error-confirm-password');
    const errTerms: HTMLElement | null = document.getElementById('error-terms');

    // Live error clearing
    const clearErrorOnInput = (inputEl: HTMLInputElement | null, errorEl: HTMLElement | null): void => {
      if (inputEl && errorEl) {
        inputEl.addEventListener('input', (): void => {
          errorEl.textContent = '';
        });
      }
    };

    if (inputSchool && errSchool) {
      inputSchool.addEventListener('change', (): void => {
        errSchool.textContent = '';
      });
    }
    clearErrorOnInput(inputName, errName);
    clearErrorOnInput(inputEmail, errEmail);
    clearErrorOnInput(inputPw, errPw);
    if (inputPwConf && errPwConf) {
      inputPwConf.addEventListener('input', (): void => {
        errPwConf.textContent = '';
      });
    }
    
    const clearTermsError = (): void => {
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

    const validateStep1 = (): boolean => {
      if (inputSchool && errSchool) {
        if (!inputSchool.value || inputSchool.value !== '부산대학교') {
          errSchool.textContent = '현재는 부산대학교만 선택 가능합니다.';
          return false;
        }
        errSchool.textContent = '';
      }
      return true;
    };

    const validateStep2 = (): boolean => {
      let isValid: boolean = true;

      // 1) Name Check
      if (inputName && errName) {
        const nameRegex: RegExp = /^[a-zA-Z가-힣\s]+$/;
        const nameVal: string = inputName.value.trim();
        if (!nameVal) {
          errName.textContent = '이름을 입력해주세요.';
          isValid = false;
        } else if (!nameRegex.test(nameVal)) {
          errName.textContent = '이름은 한글, 영문, 공백만 입력 가능합니다. (특수문자/숫자 제외)';
          isValid = false;
        } else {
          errName.textContent = '';
        }
      }

      // 2) Email Check
      if (inputEmail && errEmail) {
        const emailRegex: RegExp = /^[a-zA-Z0-9_.+-]+@pusan\.ac\.kr$/i;
        const emailVal: string = inputEmail.value.trim();
        if (!emailVal) {
          errEmail.textContent = '이메일 주소를 입력해주세요.';
          isValid = false;
        } else if (!emailRegex.test(emailVal)) {
          errEmail.textContent = '부산대학교 이메일 주소 형식이 아닙니다. (예: example@pusan.ac.kr)';
          isValid = false;
        } else {
          errEmail.textContent = '';
        }
      }

      // 3) Password Check
      if (inputPw && errPw) {
        if (!inputPw.value) {
          errPw.textContent = '비밀번호를 입력해주세요.';
          isValid = false;
        } else if (inputPw.value.length < 8) {
          errPw.textContent = '비밀번호는 최소 8자 이상이어야 합니다.';
          isValid = false;
        } else {
          errPw.textContent = '';
        }
      }

      // 4) Password Confirm Check
      if (inputPw && inputPwConf && errPwConf) {
        if (!inputPwConf.value) {
          errPwConf.textContent = '비밀번호 확인을 입력해주세요.';
          isValid = false;
        } else if (inputPw.value !== inputPwConf.value) {
          errPwConf.textContent = '비밀번호가 일치하지 않습니다.';
          isValid = false;
        } else {
          errPwConf.textContent = '';
        }
      }

      // 5) Terms Agreement Check
      if (errTerms) {
        const ageOk: boolean = inputTermsAge ? inputTermsAge.checked : false;
        const serviceOk: boolean = inputTermsService ? inputTermsService.checked : false;
        const privacyOk: boolean = inputTermsPrivacy ? inputTermsPrivacy.checked : false;

        if (!ageOk || !serviceOk || !privacyOk) {
          errTerms.textContent = '필수 동의 항목에 모두 동의해주세요.';
          isValid = false;
        } else {
          errTerms.textContent = '';
        }
      }

      return isValid;
    };

    // Transition to Step 2
    if (btnNext && step1 && step2 && pStep1 && pStep2) {
      btnNext.addEventListener('click', (): void => {
        if (validateStep1()) {
          // Slide & Fade step 1 out
          step1.style.opacity = '0';
          step1.style.transform = 'translateX(-16px)';
          if (authFooter) {
            authFooter.style.opacity = '0';
            authFooter.style.transition = 'opacity 0.3s ease';
          }

          setTimeout((): void => {
            step1.classList.remove('active');
            step2.classList.add('active');

            // Force reflow
            step2.offsetHeight;

            step2.style.opacity = '1';
            step2.style.transform = 'translateX(0)';

            // Update Progress UI
            pStep1.classList.add('completed');
            pStep2.classList.add('active');
            if (progressFill) progressFill.style.width = '100%';

            if (authFooter) authFooter.style.display = 'none';
          }, 300);
        }
      });
    }

    // Transition back to Step 1
    if (btnPrev && step1 && step2 && pStep1 && pStep2) {
      btnPrev.addEventListener('click', (): void => {
        // Slide & Fade step 2 out
        step2.style.opacity = '0';
        step2.style.transform = 'translateX(16px)';

        setTimeout((): void => {
          step2.classList.remove('active');
          step1.classList.add('active');

          // Force reflow
          step1.offsetHeight;

          step1.style.opacity = '1';
          step1.style.transform = 'translateX(0)';

          // Update Progress UI
          pStep1.classList.remove('completed');
          pStep2.classList.remove('active');
          if (progressFill) progressFill.style.width = '0%';

          if (authFooter) {
            authFooter.style.display = 'block';
            authFooter.offsetHeight; // force reflow
            authFooter.style.opacity = '1';
          }
        }, 300);
      });
    }

    // Form Submission check
    signupForm.addEventListener('submit', (e: Event): void => {
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
      } else {
        // Double submission prevention
        const submitBtn: HTMLButtonElement | null = document.getElementById('btn-submit-signup') as HTMLButtonElement;
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
  const loginForm: HTMLFormElement | null = document.getElementById('login-form') as HTMLFormElement;
  const loginSubmitBtn: HTMLButtonElement | null = document.getElementById('btn-submit-login') as HTMLButtonElement;
  if (loginForm && loginSubmitBtn) {
    loginForm.addEventListener('submit', (e: Event): void => {
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
  const pwdFindForm: HTMLFormElement | null = document.getElementById('pwd-find-form') as HTMLFormElement;
  const pwdFindSubmitBtn: HTMLButtonElement | null = document.getElementById('btn-submit-pwd-find') as HTMLButtonElement;
  if (pwdFindForm && pwdFindSubmitBtn) {
    pwdFindForm.addEventListener('submit', (e: Event): void => {
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
  const pwdVerifyForm: HTMLFormElement | null = document.getElementById('pwd-verify-form') as HTMLFormElement;
  const pwdVerifySubmitBtn: HTMLButtonElement | null = document.getElementById('btn-submit-pwd-verify') as HTMLButtonElement;
  if (pwdVerifyForm && pwdVerifySubmitBtn) {
    pwdVerifyForm.addEventListener('submit', (e: Event): void => {
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
  const pwdResetForm: HTMLFormElement | null = document.getElementById('pwd-reset-form') as HTMLFormElement;
  const pwdResetSubmitBtn: HTMLButtonElement | null = document.getElementById('btn-submit-pwd-reset') as HTMLButtonElement;
  if (pwdResetForm && pwdResetSubmitBtn) {
    pwdResetForm.addEventListener('submit', (e: Event): void => {
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
